
def sign_xades(auth_xml: bytes, p12pk: bytes, p12pc: bytes) -> bytes:
    """
        Create an enveloped XAdES-XL signature over `auth_xml`.

        :param auth_xml: the XML to be signed, as a byte string
        :param p12pk:     the private‑key PKCS#12 blob (bytes)
        :param p12pc:     the certificate chain PKCS#12 blob (bytes)
        :return:          signed XML (bytes)
        """
    # instantiate the signer, give it the key/cert material; if your PKCS#12 is
    # password‑protected supply the password argument here
    return None
