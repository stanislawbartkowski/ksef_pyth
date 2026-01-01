import datetime
import os
import logging

from ksef import KSEFSDK

from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12

TOKEN = "20251116-EC-0317C65000-2CA83C40D9-73|nip-7497725064|80be6cfced7f44eb860aeeb644e8cffdd59bbad9e218415296db90a39e6e5370"
NIP = "7497725064"

NIP_NABYWCA = "7952809480"
TOKEN_MABYWCA = "20251210-EC-49CD637000-C47EF8923C-D7|nip-7952809480|4dfe5e94a46a49f1846747dd3891e60a2912a922e90640eaaf44a64eee3971d5"


PRZYKLAD_ZAKUP = "FA_3_Przykład_zakup_25.xml"
PRZYKLAD_ZAKUP_8 = "FA_3_Przykład_zakup_8.xml"


def _load_pfx(file_path, password):
    with open(file_path, 'rb') as fp:
        return pkcs12.load_key_and_certificates(
            fp.read(),
            password.encode("utf8"),
            backends.default_backend()
        )


def def_logger():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")


def testdatadir(filexml: str) -> str:
    dir = os.path.join(os.path.dirname(__file__), "testdata")
    return os.path.join(dir, filexml)


def workdatadir(filexml: str) -> str:
    dir = os.path.join(os.path.dirname(__file__), "worktemp")
    if not os.path.isdir(dir):
        os.mkdir(dir)
    return os.path.join(dir, filexml)


def KS():
    K = KSEFSDK.initsdk(KSEFSDK.DEVKSEF, nip=NIP, token=TOKEN)
    return K


def KSNABYWCA():
    K = KSEFSDK.initsdk(KSEFSDK.DEVKSEF, nip=NIP_NABYWCA, token=TOKEN_MABYWCA)
    return K

def _toiso(date: datetime.date) -> str:
    return date.strftime("%Y-%m-%d")

def today():
    return _toiso(datetime.datetime.now())


def gen_numer_faktry():
    nr = "FV"
    data_f = datetime.datetime.now().isoformat()
    return nr + data_f


def read_cert() -> tuple[bytes, bytes]:
    K = 'keyStore.p12'
    p12 = testdatadir(K)
    p12pk, p12pc, _ = _load_pfx(p12, password='1234')
    return p12pk, p12pc


def KS_CERT():
    p12pk, p12pc = read_cert()
    K = KSEFSDK.initsdkcert(KSEFSDK.DEVKSEF, nip=NIP, p12pk=p12pk, p12pc=p12pc)
    return K

def daj_przedzial_dat() -> tuple[str,str]:
    d2 = datetime.datetime.now() + datetime.timedelta(days=2)
    d1 = d2 - datetime.timedelta(days=7)
    return _toiso(d1),_toiso(d2)
