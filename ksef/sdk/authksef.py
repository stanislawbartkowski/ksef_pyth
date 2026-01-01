import os
import tempfile

from xml_konwerter import konwertujdok

from .encrypt import encrypt_token
from .httphook import HOOKHTTP
from .xades_sign import sign_xades


class ABSTRACTTOKEN:

    def set_params(self, timestamp, kseftoken_certificate):
        pass

    def auth_ksef(self, H: HOOKHTTP, nip: str, challenge: str) -> tuple[str, str]:
        raise NotImplementedError


class AUTHTOKEN(ABSTRACTTOKEN):

    def __init__(self, token: str):
        super(AUTHTOKEN, self).__init__()
        self._token = token

    def set_params(self, timestamp: str, kseftoken_certificate: str):
        self._timestamp = timestamp
        self._kseftoken_certificate = kseftoken_certificate

    def auth_ksef(self, H: HOOKHTTP, nip: str, challenge: str) -> tuple[str, str]:
        encrypted_token = encrypt_token(
            kseftoken=self._token,
            timestamp=self._timestamp,
            public_certificate=self._kseftoken_certificate
        )
        context = {
            'type:': 'Nip',
            'value': nip
        }
        body = {
            'contextIdentifier': context,
            'challenge': challenge,
            'encryptedToken': encrypted_token
        }
        response = H._hook(
            'auth/ksef-token', body=body, bearer=H._NOBEARER)
        referenceNumber = response['referenceNumber']
        token = response['authenticationToken']['token']
        return referenceNumber, token


def _daj_request_auth(nip: str, challenge: str) -> bytes:
    patt_xml = os.path.join(os.path.dirname(__file__),
                            "..", "pattern", "request.xml")
    with tempfile.NamedTemporaryFile("rb", delete=False) as f:
        dest = f.name
        d = {
            'CHALLENGE': challenge,
            'NIP': nip
        }
        konwertujdok(sou=patt_xml, dest=dest, d=d)

    with open(dest, "rb") as f:
        xml_auth = f.read()

    return xml_auth


class AUTHCERT(ABSTRACTTOKEN):
    def __init__(self, p12pk: bytes, p12pc: bytes):
        super(AUTHCERT, self).__init__()
        self._p12pk = p12pk
        self._p12pc = p12pc

    def auth_ksef(self, H: HOOKHTTP, nip: str, challenge: str) -> tuple[str, str]:
        xml_aut = _daj_request_auth(nip=nip, challenge=challenge)
        xades_xml = sign_xades(
            auth_xml=xml_aut, p12pk=self._p12pk, p12pc=self._p12pc)
        end_point = 'auth/xades-signature'
        response = H._hook_response(
            endpoint=end_point, bearer=H._NOBEARER, xml_data=xades_xml)
        result = response.json()
        referenceNumber = result['referenceNumber']
        token = result['authenticationToken']['token']
        return referenceNumber, token
