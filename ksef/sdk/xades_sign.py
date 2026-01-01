from lxml import etree
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec

from signxml import XMLSigner, SignatureMethod, SignatureConstructionMethod
from endesive import xades
from asn1crypto import core

# ------------------------------------------------------------------------
# Contrib: https://github.com/m32/ksef/blob/v2.0/t-03-auth-02-sign.py
# ------------------------------------------------------------------------


def sign_xades(auth_xml: bytes, p12pk: bytes, p12pc: bytes) -> bytes:

    useenveloped = False
    useendesive = True
    if useendesive:
        assert isinstance(p12pk, rsa.RSAPrivateKey) or isinstance(
            p12pk, ec.EllipticCurvePrivateKey)
        assert isinstance(p12pc, x509.Certificate)
        if isinstance(p12pk, rsa.RSAPrivateKey):
            signaturemethod = None
        else:
            signaturemethod = 'http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256'

        def signproc(tosign, algosig):
            if isinstance(p12pk, rsa.RSAPrivateKey):
                sig = p12pk.sign(
                    tosign,
                    padding.PKCS1v15(),
                    getattr(hashes, algosig.upper())(),
                )
            else:
                sig = p12pk.sign(
                    tosign,
                    ec.ECDSA(getattr(hashes, algosig.upper())())
                )
                length = 32  # =256/8 czyli aes-256 TODO zamienić na zmienną zależną od długości klucza
                d = core.load(sig)
                dr = d[0].native.to_bytes(length, byteorder="big")
                ds = d[1].native.to_bytes(length, byteorder="big")
                sig = dr+ds
            return sig

        cert = p12pc
        certcontent = cert.public_bytes(serialization.Encoding.DER)

        cls = xades.BES()
        if useenveloped:
            doc = cls.enveloped(
                auth_xml,
                cert,
                certcontent,
                signproc,
                None,
                None,
                signaturemethod=signaturemethod
            )
        else:
            doc = cls.enveloping(
                "dokument.xml",
                auth_xml,
                "application/xml",
                cert,
                certcontent,
                signproc,
                False,
                True,
                signaturemethod=signaturemethod
            )
        data = etree.tostring(doc, encoding="UTF-8",
                              xml_declaration=True, standalone=False)
    else:
        if isinstance(p12pk, rsa.RSAPrivateKey):
            signature_algorithm = SignatureMethod.RSA_SHA256
        elif isinstance(p12pk, ec.EllipticCurvePrivateKey):
            signature_algorithm = SignatureMethod.ECDSA_SHA256
        else:
            assert False, "Unsupported private key type"

        root = etree.fromstring(auth_xml)
        signed_root = XMLSigner(
            signature_algorithm=signature_algorithm,
            method=SignatureConstructionMethod.enveloped if useenveloped else SignatureConstructionMethod.enveloping
        ).sign(
            root, key=p12pk, cert=[p12pc]
        )
        data = etree.tostring(signed_root, encoding="UTF-8",
                              xml_declaration=True, standalone=False)

    return data
