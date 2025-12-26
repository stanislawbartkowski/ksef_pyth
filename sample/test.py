from typing import Callable
from ksef import KSEFSDK
from tests import test_mix as T
import datetime
from tests.konwdokument import KONWDOKUMENT

T.def_logger()


def KS() -> KSEFSDK:
    return T.KS()


def KS_NABYWCA() -> KSEFSDK:
    return T.KSNABYWCA()


def _today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def gen_numer_faktry():
    nr = "FV"
    data_f = datetime.datetime.now().isoformat()
    return nr + data_f


def test1():
    # PRZYKLAD 1: Otworz sesję i zamknij sesję
    K = KS()
    K.start_session()
    K.close_session()
    K.session_terminate()


def _send_invoice_K(K: KSEFSDK, path: str, action: Callable | None = None):
    print(path)
    with open(path, "r") as f:
        invoice = f.read()
    K.start_session()
    status = K.send_invoice(invoice=invoice)
    print(status)
    if action is not None:
        action(K, status)
    K.close_session()
    K.session_terminate()
    return status


def _send_invoice(path, action: Callable | None = None):
    K = KS()
    return _send_invoice_K(K, path, action)


def test2():
    # PRZYKLAD 2: wyślij niepoprawną fakture do KSEF
    path = T.testdatadir("FA_3_Przykład_9.xml")
    _send_invoice(path)


def _prepare_invoice(patt: str = "FA_3_Przykład_9_sprzedaz_pattern.xml"):
    inpath = T.testdatadir(patt)
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
    # PRZYKŁAD 4: wyślij poprawną fakturę do KSEF
    outpath = _prepare_invoice()
    status = _send_invoice(path=outpath)
    print(status)


def test5():
    # PRZYKŁAD 5: wyslij poprawną fakturę do KSEF i pobierz UPO
    outpath = _prepare_invoice()

    def wez_upo(K: KSEFSDK, status):
        ok, _, _ = status
        assert ok
        print("Pobierz UPO dla wysłanej faktury")
        upo = K.pobierz_upo()
        print(upo)

    status = _send_invoice(path=outpath, action=wez_upo)
    print(status)


def test6():
    # PRZYKLAD 6: Pobierz istniejącą fakturę
    K = KS()
    faktura_ksef = "7497725064-20251207-0100A07C1B9B-7C"
    print(f"Pobierz fakturę o numerze: {faktura_ksef}")
    faktura = K.get_invoice(ksef_number=faktura_ksef)
    print(faktura)
    K.session_terminate()


def test7():
    K = KS_NABYWCA()
    outpath = _prepare_invoice(patt=T.PRZYKLAD_ZAKUP_8)
    status = _send_invoice_K(K, path=outpath)
    print(status)
    ok, errmess, numer_ksef = status


def test8():
    K = KS()
    res = K.get_invoices_zakupowe_metadata(
        date_from="2025-11-01", date_to="2025-12-31")
    print(res)
    K.session_terminate()

def test9():
    K = KS()
    b = b'111111111'
    K.send_batch_session_bytes(payload=[b])
    K.session_terminate()

if __name__ == "__main__":
    # test2()
    # test1()
    # test3()
    # test4()
    # test5()
    # test6()
    # test7()
    #test8()
    test9()
