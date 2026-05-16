from typing import Optional
import io
import tempfile
import unittest
import zipfile

import xml.etree.ElementTree as et

import test_mix as T
from tests.testabstract.testabstract import TestKsefMixim


class TestAuthToken(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        T.def_logger()
        cls.ksef = T.KS()

    @classmethod
    def tearDownClass(cls):
        cls.ksef.session_terminate()


class TestKsefBatch(TestAuthToken, TestKsefMixim):

    @staticmethod
    def _zip_b(b: str, b1: Optional[str] = None):
        with tempfile.NamedTemporaryFile(mode="w"), io.BytesIO() as fileobj:
            with zipfile.ZipFile(fileobj, 'w') as zip:
                zip.writestr("name.zip", b)
                if b1 is not None:
                    zip.writestr("name1.zip", b1)
            return fileobj.getvalue()

    def _wyslij_batch(self, payload: list[bytes]):

        def _wez_upo(i, upo_xml):
            print(i, upo_xml)
            _ = et.fromstring(upo_xml)

        res = self.ksef.send_batch_session_bytes(
            payload=(b for b in payload), wez_upo=_wez_upo)
        return res

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
        self.assertIn('Nieprawidłowy zakres uprawnień Sprzedawca', i.msg)

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
        _ = et.fromstring(upo)
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
        self._wez_fakture(ksef_number=i0.ksefNumber, invoice_n=invoice_n)
        self._wez_fakture(ksef_number=i1.ksefNumber, invoice_n=invoice_n1)

    def test_wyslij_fakture_poprawna_i_niepoprawna(self):
        invoice, invoice_n = self._prepare_invoice()
        invoice_zla, _ = self._prepare_invoice(patt=T.PRZYKLAD_ZAKUP)
        zzip = self._zip_b(b=invoice, b1=invoice_zla)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        print(ok, msg, invoices)
        self.assertTrue(ok)
        self.assertEqual(2, len(invoices))
        i0 = invoices[0]
        i1 = invoices[1]
        self._wez_fakture(ksef_number=i0.ksefNumber, invoice_n=invoice_n)
        self.assertFalse(i1.ok)

    def test_wyslij_fakture_o_zduplikowanym_numerze(self):
        invoice, invoice_n = self._prepare_invoice()
        zzip = self._zip_b(b=invoice)
        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        print(ok, msg, invoices)
        self.assertTrue(ok)

        ok, msg, invoices = self._wyslij_batch(payload=[zzip])
        print(ok, msg, invoices)
        self.assertFalse(ok)
        i = invoices[0]
        self.assertIn("Duplikat faktury", i.msg)


class TestKsefBatchGet(TestAuthToken, TestKsefMixim):

    def test_oodczyt_duzego_przedzialu_faktur(self):
        liczba_faktur, _ = self.ksef.get_batch_invoices(
            subject=self.ksef.SUBJECT1, date_from="2025-11-01", date_to="2025-12-31")
        print(liczba_faktur)

    def test_wyslij_i_odczytaj_fakture(self):
        invoice, _ = self._prepare_invoice()
        self.ksef.start_session()
        status = self.ksef.send_invoice(invoice=invoice)
        self.ksef.session_terminate()
        print(status)
        date_from, date_to = T.daj_przedzial_dat()
        num, zip_data = self.ksef.get_batch_invoices(
            date_from=date_from, date_to=date_to, subject=self.ksef.SUBJECT1)
        print(num)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            for name in z.namelist():
                print(name)
                data = z.read(name)
                txt = data.decode("utf-8")
                print(txt)
                if ".xml" in name:
                    _ = et.fromstring(data)
