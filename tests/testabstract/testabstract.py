from typing import Callable
from time import sleep

import pytest
import xml.etree.ElementTree as et

from ksef.sdk.ksefsdk import KSEFSDK

from konwdokument import KONWDOKUMENT
import test_mix as T


class AbstractTestCase:

    ksef: KSEFSDK


class TestKsefMixim(AbstractTestCase):

    def _konw_invoice(self, patt: str) -> tuple[str, str]:
        inpath = T.testdatadir(patt)
        outpath = T.workdatadir("faktura.xml")
        invoice_n = T.gen_numer_faktry()
        zmienne = {
            KONWDOKUMENT.DATA_WYSTAWIENIA: T.today(),
            KONWDOKUMENT.NIP: T.NIP,
            KONWDOKUMENT.NIP_NABYWCA: T.NIP_NABYWCA,
            KONWDOKUMENT.NUMER_FAKTURY: invoice_n
        }
        KONWDOKUMENT.konwertuj(sou=inpath, dest=outpath, zmienne=zmienne)
        return outpath, invoice_n

    def _prepare_invoice(self, patt: str = "FA_3_Przykład_9_sprzedaz_pattern.xml") -> tuple[str, str]:
        outpath, invoice_n = self._konw_invoice(patt=patt)
        with open(outpath, "r") as f:
            invoice = f.read()
        assert T.NIP in invoice
        assert T.NIP_NABYWCA in invoice
        return invoice, invoice_n

    def _wez_fakture(self, ksef_number, invoice_n):
        for i in range(1, 5):
            print(f"Próba pobrania faktury z KSeF, numer próby: {ksef_number}")
            try:
                invoice_ksef = self.ksef.get_invoice(ksef_number=ksef_number)
                print(invoice_ksef)
                _ = et.fromstring(invoice_ksef)
                assert invoice_n in invoice_ksef
                return
            except Exception as e:
                print(f"{i} Błąd pobrania faktury: {e}")
                sleep(2 * i)
        raise ValueError("Nie można pobrac faktury")


class AbstractTestKsefOnLine(TestKsefMixim):

    def _wyslij_ksef_K(self, K: KSEFSDK, invoice: str, action: Callable | None = None) -> tuple[bool, str, str]:
        K.start_session()
        status = K.send_invoice(invoice=invoice)
        print(status)
        if action is not None:
            action()
        K.close_session()
        return status

    def _wyslij_ksef(self, invoice: str, action: Callable | None = None) -> tuple[bool, str, str]:
        return self._wyslij_ksef_K(self.ksef, invoice, action)

    def _test_init_and_terminate(self):
        pass

    def _test_start_and_close_online(self):
        self.ksef.start_session()
        self.ksef.close_session()

    def _test_send_incorrect_invoice(self):
        path = T.testdatadir("FA_3_Przykład_9.xml")
        print(path)
        with open(path, "r") as f:
            invoice = f.read()
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, description, _ = status
        assert not ok
        assert "Nieprawidłowy zakres uprawnień Kontekst" in description

    def _test_konwertuj_plik(self):
        self._prepare_invoice()

    def _test_wyslij_do_ksef(self):
        invoice, _ = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, description, numerksef = status
        assert ok
        assert description == "Sukces"
        assert numerksef != ""
        return numerksef

    def _test_wyslij_do_ksef_i_pobierz_sprzedazy(self):
        numerksef = self._test_wyslij_do_ksef()
        print(numerksef)
        d1, d2 = T.daj_przedzial_dat()
        res = self.ksef.get_invoices_metadata(
            date_from=d1, date_to=d2, subject=KSEFSDK.SUBJECT1)
        print(res)
        assert isinstance(res, list)
        assert len(res) > 0
        invoice_meta = res[-1]
        seller = invoice_meta["seller"]["nip"]
        assert seller == T.NIP

    def _test_wyslij_do_ksef_i_wez_upo(self):

        def wez_upo():
            upo = self.ksef.pobierz_upo()
            print(upo)
            _ = et.fromstring(upo)

        invoice, _ = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice, action=wez_upo)
        ok, description, numerksef = status
        assert ok
        assert description == "Sukces"
        assert numerksef != ""

    def _test_pobierz_fakture_o_zlym_formacie_numeru(self):
        with pytest.raises(Exception) as exc_info:
            self.ksef.get_invoice(ksef_number="999999999999999999")
        print(exc_info.value)
        assert "is not in the correct format" in str(exc_info.value)

    def _test_pobierz_fakture_o_nieistniejacym_numerze(self):
        with pytest.raises(Exception) as exc_info:
            self.ksef.get_invoice(ksef_number="7497725064-20251206-0100403420A2-99")
        print(exc_info.value)
        assert "nie została znaleziona" in str(exc_info.value)

    def _test_pobierz_istniejaca_fakture(self):
        invoice, invoice_n = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice)
        ok, _, numerksef = status
        assert ok
        self._wez_fakture(ksef_number=numerksef, invoice_n=invoice_n)

    def _test_wyslij_fakture_blad_zalacznik(self):
        invoice, _ = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP)
        print(invoice)
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, description, _ = status
        assert not ok
        assert "Brak możliwości wysyłania faktury z załącznikiem" in description

    def _test_wyslij_fakture_zakupowa_i_pobierz_metadane(self):
        K = T.KSNABYWCA()
        invoice, _ = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP_8)
        status = self._wyslij_ksef_K(K, invoice=invoice)
        K.session_terminate()
        print(status)
        ok, description, numerksef = status
        assert ok
        assert description == "Sukces"
        assert numerksef != ""

    def _test_pobierz_metadane_i_fakture_zakupowa(self):
        d1, d2 = T.daj_przedzial_dat()
        res = self.ksef.get_invoices_zakupowe_metadata(date_from=d1, date_to=d2)
        print(res)
        assert isinstance(res, list)
        assert len(res) > 0
        invoice_meta = res[-1]
        ksef_number = invoice_meta["ksefNumber"]
        invoice_ksef = self.ksef.get_invoice(ksef_number=ksef_number)
        print(invoice_ksef)
        _ = et.fromstring(invoice_ksef)
        seller = invoice_meta["seller"]["nip"]
        assert seller == T.NIP_NABYWCA

    def _test_niepoprawny_token_dla_nip(self):
        with pytest.raises(ValueError):
            KSEFSDK.initsdk(KSEFSDK.UNITTEST, nip=T.NIP, token="xxxxxx yyyyyy")

    def _test_niepoprawny_nip(self):
        with pytest.raises(ValueError):
            KSEFSDK.initsdk(KSEFSDK.UNITTEST, nip="9999999999", token="xxxxxx yyyyyy")

    def _test_odczyt_duzego_przedzialu_metadanych(self):
        d1 = "2025-12-01"
        d2 = "2025-12-31"
        res = self.ksef.get_invoices_metadata(
            date_from=d1, date_to=d2, subject=KSEFSDK.SUBJECT1)
        print(f"Odczytano {len(res)} metadanych faktur sprzedaży")
        assert isinstance(res, list)
        assert len(res) > 0

    def _test_wyslij_fakture_o_istniejacym_numerze(self):
        invoice, invoice_n = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice)
        ok, _, numerksef = status
        assert ok
        self._wez_fakture(ksef_number=numerksef, invoice_n=invoice_n)
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, mess, numerksef = status
        assert not ok
        assert "Duplikat faktury" in mess
