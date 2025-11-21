import os
import shutil

import xml.etree.ElementTree as et

from konwdocs.konwxml import KONWXML


def _worktempdir() -> str:
    """Zwraca ścieżkę do katalogu tymczasowego SDK KSeF."""
    dir = os.path.join(os.path.dirname(__file__), "..", "worktemp")
    os.makedirs(dir, exist_ok=True)
    return dir


def _patterndir(patt: str) -> str:
    """Zwraca ścieżkę do katalogu ze wzorcami dokumentów KSeF."""
    dir = os.path.join(os.path.dirname(__file__), "..", "testdata")
    return os.path.join(dir, patt)


class KONWDOKUMENT:

    DATA_WYTWORZENIA = "DATA_WYTWORZENIA"
    DATA_WYSTAWIENIA = "DATA_WYSTAWIENIA"
    NIP = "NIP"
    NIP_NABYWCA = "NIP_NABYWCA"
    NUMER_FAKTURY = "NUMER_FAKTURY"

    @staticmethod
    def zrob_dokument_xml(zmienne: dict) -> str:
        """Generuje XML dokumentu KSeF na podstawie słownika zmienn."""
        sou = _patterndir("FA_3_Przykład_9.xml")
        dest = os.path.join(_worktempdir(), "dokument_ksef.xml")
        shutil.copyfile(sou, dest)
        return dest

    @staticmethod
    def konwertuj(sou: str, dest: str, zmienne: dict) -> None:
        tree = et.parse(sou)
        root = tree.getroot()
        K = KONWXML(root=root)
        K.replace_all(d=zmienne)
        tree.write(dest)
