from typing import Callable
from time import sleep
import io
import tempfile

import unittest
import zlib
import zipfile

import xml.etree.ElementTree as et

from ksef.sdk.ksefsdk import KSEFSDK

from konwdokument import KONWDOKUMENT
import test_mix as T


class TestKsefMixim(unittest.TestCase):

    # ---------------------
    # helpers
    # ---------------------
    def _konw_invoice(self, patt: str) -> str:
        inpath = T.testdatadir(patt)
        outpath = T.workdatadir("faktura.xml")
        zmienne = {
            KONWDOKUMENT.DATA_WYSTAWIENIA: T.today(),
            KONWDOKUMENT.NIP: T.NIP,
            KONWDOKUMENT.NIP_NABYWCA: T.NIP_NABYWCA,
            KONWDOKUMENT.NUMER_FAKTURY: T.gen_numer_faktry()
        }
        KONWDOKUMENT.konwertuj(sou=inpath, dest=outpath, zmienne=zmienne)
        return outpath

    def _prepare_invoice(self, patt: str = "FA_3_Przykład_9_sprzedaz_pattern.xml") -> str:
        outpath = self._konw_invoice(patt=patt)
        # odczytaj skonwertowany plik
        with open(outpath, "r") as f:
            invoice = f.read()
        self.assertIn(T.NIP, invoice)
        self.assertIn(T.NIP_NABYWCA, invoice)
        return invoice

    # ---------------------
    # test fixture
    # ---------------------

    @classmethod
    def setUpClass(cls):
        T.def_logger()
        cls.ksef = T.KS()

    @classmethod
    def tearDownClass(cls):
        cls.ksef.session_terminate()


class TestKsefOnLine(TestKsefMixim):

    # ---------------------
    # helpers
    # ---------------------

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

    # -------------------
    # test suite
    # -------------------

    def test_init_and_terminate(self):
        pass

    def test_start_and_close_online(self):
        self.ksef.start_session()
        self.ksef.close_session()

    def test_send_incorrect_invoice(self):
        path = T.testdatadir("FA_3_Przykład_9.xml")
        print(path)
        with open(path, "r") as f:
            invoice = f.read()
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, description, _ = status
        self.assertFalse(ok)
        self.assertIn(
            "Błąd weryfikacji semantyki dokumentu faktury", description)

    def test_konwertuj_plik(self):
        self._prepare_invoice()

    def test_wyslij_do_ksef(self):
        invoice = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, description, numerksef = status
        self.assertTrue(ok)
        self.assertEqual("Sukces", description)
        self.assertNotEqual("", numerksef)

    def test_wyslij_do_ksef_i_wez_upo(self):

        def wez_upo():
            upo = self.ksef.pobierz_upo()
            print(upo)
            # sprawdz, czy plik xml
            # wyrzuci błąd, jeśli nie jest poprawny xml
            _ = et.fromstring(upo)

        invoice = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice, action=wez_upo)
        ok, description, numerksef = status
        self.assertTrue(ok)
        self.assertEqual("Sukces", description)
        self.assertNotEqual("", numerksef)

    def test_pobierz_fakture_o_zlym_formacie_numeru(self):
        with self.assertRaises(Exception) as context:
            self.ksef.get_invoice(ksef_number="999999999999999999")
        print(context.exception)
        self.assertIn("is not in the correct format", str(context.exception))

    def test_pobierz_fakture_o_nieistniejacym_numerze(self):
        with self.assertRaises(Exception) as context:
            self.ksef.get_invoice(
                ksef_number="7497725064-20251206-0100403420A2-99")
        print(context.exception)
        self.assertIn("nie została znaleziona", str(context.exception))

    def test_pobierz_istniejaca_fakture(self):
        invoice = self._prepare_invoice()
        status = self._wyslij_ksef(invoice=invoice)
        ok, _, numerksef = status
        self.assertTrue(ok)
        for i in range(1, 5):
            print(f"Próba pobrania faktury z KSeF, numer próby: {numerksef}")
            try:
                invoice_ksef = self.ksef.get_invoice(ksef_number=numerksef)
                print(invoice_ksef)
                _ = et.fromstring(invoice_ksef)
                self.assertIn("<KSeFNumber>", invoice_ksef)
                return
            except Exception as e:
                print(f"{i} Błąd pobrania faktury: {e}")
                sleep(2*i)

    def test_wyslij_fakture_blad_zalacznik(self):
        invoice = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP)
        print(invoice)
        status = self._wyslij_ksef(invoice=invoice)
        print(status)
        ok, description, _ = status
        self.assertFalse(ok)
        self.assertIn(
            "Brak możliwości wysyłania faktury z załącznikiem", description)

    def test_wyslij_fakture_zakupowa_i_pobierz_metadane(self):
        K = T.KSNABYWCA()
        invoice = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP_8)
        status = self._wyslij_ksef_K(K, invoice=invoice)
        K.session_terminate()
        print(status)
        ok, description, numerksef = status
        self.assertTrue(ok)
        self.assertEqual("Sukces", description)
        self.assertNotEqual("", numerksef)

        res = self.ksef.get_invoices_zakupowe_metadata(
            date_from="2025-11-01", date_to="2025-12-31")
        print(res)
        self.assertIsInstance(res, list)
        self.assertLess(0, len(res))

        invoice_meta = res[-1]
        ksef_number = invoice_meta["ksefNumber"]
        # odczytaj
        invoice_ksef = self.ksef.get_invoice(ksef_number=ksef_number)
        print(invoice_ksef)
        _ = et.fromstring(invoice_ksef)

    def test_niepoprawny_token_dla_nip(self):
        self.assertRaises(ValueError, lambda: KSEFSDK.initsdk(
            KSEFSDK.DEVKSEF, nip=T.NIP, token="xxxxxx yyyyyy"))

    def test_niepoprawny_nip(self):
        self.assertRaises(ValueError, lambda: KSEFSDK.initsdk(
            KSEFSDK.DEVKSEF, nip="9999999999", token="xxxxxx yyyyyy"))


class TestKsefBatch(TestKsefMixim):

    # -----------
    # helper
    # -----------

    @staticmethod
    def _zip_b(b: str):
        fileobj = io.BytesIO()

        with tempfile.NamedTemporaryFile(mode="w") as t, io.BytesIO() as fileobj:
            with zipfile.ZipFile(fileobj, 'w') as zip:
                zip.writestr(t.name, b)
            zzip = fileobj.getvalue()
            return zzip

    def test_zla_kompresja(self):
        b = b'111111111'
        ok, msg = self.ksef.send_batch_session_bytes(payload=[b])
        self.assertFalse(ok)
        print(msg)
        self.assertIn("Błąd dekompresji", msg)

    def test_błędna_faktura(self):
        b = '111111111'
        zzip = self._zip_b(b)
        ok, msg, invoices = self.ksef.send_batch_session_bytes(payload=[zzip])
        self.assertFalse(ok)
        print(msg)
        # kompresja jest teraz poprawna
        self.assertIn('brak poprawnych', msg)
        print(invoices)
        self.assertEqual(1, len(invoices))
        i = invoices[0]
        self.assertFalse(i.ok)
        self.assertIn('Nieprawidłowy XML', i.msg)

    def test_proba_wyslania(self):
        invoice = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP)
        zzip = self._zip_b(invoice)
        ok, msg, invoices = self.ksef.send_batch_session_bytes(payload=[zzip])
        self.assertFalse(ok)
        print(msg)
        self.assertIn('brak poprawnych', msg)
        print(invoices)
        i = invoices[0]
        self.assertFalse(i.ok)
        self.assertIn('nie może być późniejsza niż data', i.msg)
