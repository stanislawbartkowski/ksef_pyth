import pytest

import test_mix as T
from tests.testabstract.testabstract import AbstractTestKsefOnLine


class TestOnLine(AbstractTestKsefOnLine):

    @pytest.fixture(autouse=True, params=[T.KS, T.KS_CERT], ids=["token", "cert"], scope="class")
    def ksef_setup(self, request):
        T.def_logger()
        k = request.param()
        request.cls.ksef = k
        yield
        k.session_terminate()

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
        self._test_wyslij_do_ksef_i_wez_upo()

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

    def test_wyslij_fakture_o_istniejacym_numerze(self):
        self._test_wyslij_fakture_o_istniejacym_numerze()

    def test_odczyt_duzego_przedzialu_faktur(self):
        self._test_odczyt_duzego_przedzialu_metadanych()
