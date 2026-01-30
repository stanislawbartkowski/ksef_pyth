from typing import Optional
import io
import tempfile

import unittest
import zipfile

import xml.etree.ElementTree as et


import test_mix as T
from tests.testabstract.testabstract import AbstractTestKsefOnLine, TestKsefMixim


class TestAuthToken(unittest.TestCase):

    # ---------------------
    # test fixture
    # ---------------------

    @classmethod
    def setUpClass(cls):
        T.def_logger()
        cls.ksef = T.KS()

    # ---------------------
    @classmethod
    def tearDownClass(cls):
        cls.ksef.session_terminate()


class TestAuthCert(unittest.TestCase):

    # ---------------------
    # test fixture
    # ---------------------

    @classmethod
    def setUpClass(cls):
        T.def_logger()
        cls.ksef = T.KS_CERT()

    # ---------------------
    @classmethod
    def tearDownClass(cls):
        cls.ksef.session_terminate()


class TestTokenOnLine(TestAuthToken, AbstractTestKsefOnLine):

    def test_init_and_terminate(self):
        self._test_init_and_terminate()

    def test_start_and_close_online(self):
        self._test_start_and_close_online()

    def test_send_incorrect_invoice(self):
        self._test_send_incorrect_invoice()

    def test_konwertuj_plik(self):
        self._test_konwertuj_plik()

    def test_wyslij_do_ksef(self):
        self._test_wyslij_do_ksef()

    def test_wyslij_do_ksef_i_pobierz_sprzedazy(self):
        self._test_wyslij_do_ksef_i_pobierz_sprzedazy()

    def test_wyslij_do_ksef_i_wez_upo(self):
        self._test_wyslij_do_ksef_i_wez_upo

    def test_pobierz_fakture_o_zlym_formacie_numeru(self):
        self._test_pobierz_fakture_o_zlym_formacie_numeru()

    def test_pobierz_fakture_o_nieistniejacym_numerze(self):
        self._test_pobierz_fakture_o_nieistniejacym_numerze()

    def test_pobierz_istniejaca_fakture(self):
        self._test_pobierz_istniejaca_fakture()

    def test_wyslij_fakture_blad_zalacznik(self):
        self._test_wyslij_fakture_blad_zalacznik()

    def test_wyslij_fakture_zakupowa_i_pobierz_metadane(self):
        self._test_wyslij_fakture_zakupowa_i_pobierz_metadane()

    def test_pobierz_metadane_i_fakture_zakupowa(self):
        self._test_pobierz_metadane_i_fakture_zakupowa()

    def test_niepoprawny_token_dla_nip(self):
        self._test_niepoprawny_token_dla_nip()

    def test_niepoprawny_nip(self):
        self._test_niepoprawny_nip()


class TestCertfOnLine(TestAuthCert, AbstractTestKsefOnLine):

    def test_init_and_terminate(self):
        self._test_init_and_terminate()

    def test_start_and_close_online(self):
        self._test_start_and_close_online()

    def test_send_incorrect_invoice(self):
        self._test_send_incorrect_invoice()

    def test_konwertuj_plik(self):
        self._test_konwertuj_plik()

    def test_wyslij_do_ksef(self):
        self._test_wyslij_do_ksef()

    def test_wyslij_do_ksef_i_pobierz_sprzedazy(self):
        self._test_wyslij_do_ksef_i_pobierz_sprzedazy()

    def test_wyslij_do_ksef_i_wez_upo(self):
        self._test_wyslij_do_ksef_i_wez_upo

    def test_pobierz_fakture_o_zlym_formacie_numeru(self):
        self._test_pobierz_fakture_o_zlym_formacie_numeru()

    def test_pobierz_fakture_o_nieistniejacym_numerze(self):
        self._test_pobierz_fakture_o_nieistniejacym_numerze()

    def test_pobierz_istniejaca_fakture(self):
        self._test_pobierz_istniejaca_fakture()

    def test_wyslij_fakture_blad_zalacznik(self):
        self._test_wyslij_fakture_blad_zalacznik()

    def test_wyslij_fakture_zakupowa_i_pobierz_metadane(self):
        self._test_wyslij_fakture_zakupowa_i_pobierz_metadane()

    def test_pobierz_metadane_i_fakture_zakupowa(self):
        self._test_pobierz_metadane_i_fakture_zakupowa()

    def test_niepoprawny_token_dla_nip(self):
        self._test_niepoprawny_token_dla_nip()

    def test_niepoprawny_nip(self):
        self._test_niepoprawny_nip()

    def test_oodczyt_duzego_przedzialu_faktur(self):
        self._test_odczyt_duzego_przedzialu_metadanych()


class TestKsefBatch(TestAuthToken, TestKsefMixim):

    # -----------
    # helper
    # -----------

    @staticmethod
    def _zip_b(b: str, b1: Optional[str] = None):
        fileobj = io.BytesIO()

        with tempfile.NamedTemporaryFile(mode="w") as t, io.BytesIO() as fileobj:
            with zipfile.ZipFile(fileobj, 'w') as zip:
                zip.writestr("name.zip", b)
                if b1 is not None:
                    zip.writestr("name1.zip", b1)

            zzip = fileobj.getvalue()
            return zzip

    def _wyslij_batch(self, payload: list[bytes]):

        def _wez_upo(i, upo_xml):
            print(i, upo_xml)
            _ = et.fromstring(upo_xml)

        res = self.ksef.send_batch_session_bytes(
            payload=(b for b in payload), wez_upo=_wez_upo)
        return res

    # -------------
    # test cases
    # -------------

    def test_zla_kompresja(self):
        b = b'111111111'
        ok, msg, _ = self._wyslij_batch(payload=[b])
        self.assertFalse(ok)
        print(msg)
        self.assertIn("Błąd dekompresji", msg)

    def test_błędna_faktura(self):
        b = '111111111'
        zzip = self._zip_b(b)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
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
        invoice, _ = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP)
        zzip = self._zip_b(invoice)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        self.assertFalse(ok)
        print(msg)
        self.assertIn('brak poprawnych', msg)
        print(invoices)
        i = invoices[0]
        self.assertFalse(i.ok)
        self.assertIn('nie może być późniejsza niż data', i.msg)

    def test_wyslij_fakture_sprzedazy(self):
        invoice, invoice_n = self._prepare_invoice()
        zzip = self._zip_b(invoice)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        print(ok, msg, invoices)
        self.assertEqual(1, len(invoices))
        i = invoices[0]
        self.assertTrue(i.ok)
        self.assertIn('Sukces', i.msg)
        self.assertIsNotNone(i.ksefNumber)
        self.assertEqual(invoice_n, i.invoiceNumber)
        return i

    def test_wyslij_fakture_sprzedazy_wez_upo(self):
        i = self.test_wyslij_fakture_sprzedazy()
        referenceNumber = i.referenceNumber
        upo = self.ksef.pobierz_upo(invoicereferencenumber=referenceNumber)
        print(upo)
        # sprawdz xml
        _ = et.fromstring(upo)
        # wez fakture
        ksef_number = i.ksefNumber
        self._wez_fakture(ksef_number=ksef_number, invoice_n=i.invoiceNumber)

    def test_wyslij_dwie_faktury(self):
        invoice, invoice_n = self._prepare_invoice()
        invoice1, invoice_n1 = self._prepare_invoice()
        zzip = self._zip_b(b=invoice, b1=invoice1)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        self.assertTrue(ok)
        print(ok, msg, invoices)
        self.assertEqual(2, len(invoices))
        i0 = invoices[0]
        i1 = invoices[1]
        # pierwsza faktura
        ksef_number = i0.ksefNumber
        self._wez_fakture(ksef_number=ksef_number, invoice_n=invoice_n)
        # druga faktura
        ksef_number = i1.ksefNumber
        self._wez_fakture(ksef_number=ksef_number, invoice_n=invoice_n1)

    def test_wyslij_fakture_poprawna_i_niepoprawna(self):
        invoice, invoice_n = self._prepare_invoice()
        invoice_zla, _ = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP)
        zzip = self._zip_b(b=invoice, b1=invoice_zla)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        print(ok, msg, invoices)
        # powinno być ok, awet jesli faktura błędna
        self.assertTrue(ok)
        # pierwsza faktura poprawna
        self.assertEqual(2, len(invoices))
        i0 = invoices[0]
        i1 = invoices[1]
        ksef_number = i0.ksefNumber
        self._wez_fakture(ksef_number=ksef_number, invoice_n=invoice_n)
        # druga niepoprawna
        self.assertFalse(i1.ok)
