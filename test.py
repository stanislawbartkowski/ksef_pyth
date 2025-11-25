from ksef import KSEFSDK
from ksef import KONWDOKUMENT
from tests import test_mix as T
import datetime


def KS():
    K = KSEFSDK.initsdk(KSEFSDK.DEVKSEF, nip=T.NIP, token=T.TOKEN)
    return K


def _today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def gen_numer_faktry():
    nr = "FV"
    data_f = datetime.datetime.now().isoformat()
    return nr + data_f


def test1():
    K = KS()
    K.start_session()
    K.close_session()
    K.session_terminate()


def _send_invoice(path):
    print(path)
    with open(path, "r") as f:
        invoice = f.read()
    K = KS()
    K.start_session()
    status = K.send_invoice(invoice=invoice)
    print(status)
    K.close_session()
    K.session_terminate()
    return status


def test2():
    path = T.testdatadir("FA_3_Przykład_9.xml")
    _send_invoice(path)


def _prepare_invoice():
    inpath = T.testdatadir("FA_3_Przykład_9_pattern.xml")
    outpath = T.workdatadir("faktura.xml")
    zmienne = {
        KONWDOKUMENT.DATA_WYSTAWIENIA: _today(),
        KONWDOKUMENT.NIP: T.NIP,
        KONWDOKUMENT.NIP_NABYWCA: T.NIP_NABYWCA,
        KONWDOKUMENT.NUMER_FAKTURY: gen_numer_faktry()
    }
    KONWDOKUMENT.konwertuj(sou=inpath, dest=outpath, zmienne=zmienne)
    return outpath


def test3():
    _prepare_invoice()


def test4():
    outpath = _prepare_invoice()
    status = _send_invoice(path=outpath)
    print(status)


if __name__ == "__main__":
    # test2()
    # test1()
    # test3()
    test4()
