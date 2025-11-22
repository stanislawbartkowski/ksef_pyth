import datetime
import os
from ksef import KSEFSDK

TOKEN = "20251116-EC-0317C65000-2CA83C40D9-73|nip-7497725064|80be6cfced7f44eb860aeeb644e8cffdd59bbad9e218415296db90a39e6e5370"
NIP = "7497725064"
NIP_NABYWCA = "7952809480"


def testdatadir(filexml: str) -> str:
    dir = os.path.join(os.path.dirname(__file__), "testdata")
    return os.path.join(dir, filexml)


def workdatadir(filexml: str) -> str:
    dir = os.path.join(os.path.dirname(__file__), "worktemp")
    os.makedirs(dir)
    return os.path.join(dir, filexml)

def KS():
    K = KSEFSDK.initsdk(KSEFSDK.DEVKSEF, nip=T.NIP, token=T.TOKEN)
    return K


def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def gen_numer_faktry():
    nr = "FV"
    data_f = datetime.datetime.now().isoformat()
    return nr + data_f

