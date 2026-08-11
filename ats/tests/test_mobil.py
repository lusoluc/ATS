"""Die Bewerberstrecke am Handy — und der Wächter, der sie prüft.

Gefunden hat `manage.py mobil_pruefen` drei Dinge, die alle drei unsichtbar
waren, solange man am großen Bildschirm entwickelt:

1. Die Footer-Zeile brach nicht um. „KI-Transparenz" (EU AI Act Art. 86) und
   „ATS-Dashboard" ragten hinaus und waren nicht anklickbar.
2. Weil das Dokument dadurch 529 px breit wurde, rechnete der
   Barrierefreiheits-Knopf (`position:fixed; right:30px`) gegen diese 529 px
   und stand bei 443..499 px — am Handy außerhalb des Bildes. Ausgerechnet der
   Knopf für Kontrast und Schriftgröße.
3. Auf dem Stellendetail schob ein deutsches Kompositum die Grid-Spalte auf
   410 px. Betroffen: **„One-Click bewerben"** — der wichtigste Knopf des
   Produkts, am Telefon nicht klickbar.

`body { overflow-x: hidden }` macht das lautlos: Überstehendes wird
abgeschnitten statt scrollbar. Dieselbe Falle wie einst bei den Tabellen.

Die Layout-Prüfung selbst braucht einen echten Browser (deshalb das
Kommando). Was hier steht, hält die vier Regeln fest, die es behoben haben —
und stellt sicher, dass der Wächter nicht an einer neuen Seite vorbeiläuft.
"""
import pathlib
import re

from django.test import TestCase
from django.urls import Resolver404, resolve

from ..management.commands.mobil_pruefen import BREITE, SEITEN

VORLAGEN = pathlib.Path(__file__).resolve().parent.parent.parent / "templates"


def _css(name: str) -> str:
    """Vorlage ohne CSS-Kommentare.

    Die Kommentare erklären hier genau die Regeln, die geprüft werden — und
    enthalten dabei geschweifte Klammern (`body{overflow-x:hidden}`). Wer sie
    stehen lässt, sucht den Block-Anfang im Fließtext. Der erste Anlauf dieses
    Tests ist genau darüber gestolpert.
    """
    quelle = (VORLAGEN / name).read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", quelle, flags=re.S)


class WaechterDeckungTestCase(TestCase):
    """Ein Wächter, der die neue Seite nicht kennt, prüft sie auch nicht."""

    def test_every_checked_path_really_exists(self):
        """Eine tote Adresse in der Liste ist eine Prüfung, die nichts trifft."""
        tot = []
        for name, pfad in SEITEN:
            probe = pfad.replace("{job}",
                                 "00000000-0000-0000-0000-000000000000")
            try:
                resolve(probe)
            except Resolver404:
                tot.append(f"{name} ({pfad})")
        self.assertEqual(tot, [], f"Adresse existiert nicht (mehr): {tot}")

    def test_the_applicant_path_is_covered_completely(self):
        """Jede öffentliche Seite, die eine bewerbende Person erreicht, muss
        in der Prüfliste stehen — sonst wächst genau dort die nächste Lücke."""
        gedeckt = {p for _, p in SEITEN}
        pflicht = {"/", "/jobs/", "/jobs/{job}/", "/jobs/{job}/bewerben/",
                   "/job-alert/", "/barrierefreiheit/", "/ki-transparenz/"}
        self.assertEqual(
            pflicht - gedeckt, set(),
            "Öffentliche Seite ohne Handy-Prüfung: " + str(pflicht - gedeckt))

    def test_the_narrowest_common_device_is_used(self):
        """375 px ist das iPhone SE. Wer breiter prüft, prüft weniger."""
        self.assertLessEqual(BREITE, 375)


class LayoutRegelnTestCase(TestCase):
    """Die vier Regeln, die den Überstand behoben haben. Fällt eine weg,
    kommt der Fehler zurück — und zwar unsichtbar."""

    def test_the_footer_row_may_wrap(self):
        quelle = _css("base.html")
        block = quelle.split(".footer-links {", 1)[1].split("}", 1)[0]
        self.assertIn(
            "flex-wrap", block,
            "Ohne Umbruch schiebt die Footer-Zeile das ganze Dokument über "
            "den Handy-Rand — und mit ihm den Barrierefreiheits-Knopf, der "
            "position:fixed gegen die Dokumentbreite rechnet.")

    def test_the_job_detail_columns_may_shrink(self):
        quelle = _css("job_detail.html")
        self.assertIn(
            "min-width: 0", quelle,
            "Ein Grid-Element schrumpft ohne min-width:0 nie unter sein "
            "längstes Wort. Deutsche Komposita reichen, um „One-Click "
            "bewerben\" vom Handy-Bildschirm zu schieben.")

    def test_long_compound_words_can_break(self):
        """Deutsch ist die eigentliche Ursache: Ein einziges Wort wie
        „Schwerbehindertenvertretung" ist breiter als ein Telefon."""
        for vorlage in ("home.html", "job_detail.html"):
            self.assertIn("overflow-wrap: break-word", _css(vorlage), vorlage)

    def test_the_menu_button_is_big_enough_for_a_thumb(self):
        """Das Symbol allein mass 19x27 px — unter dem Mindestmass 24x24
        (WCAG 2.5.8). Ausgerechnet der Knopf, der am Handy das GANZE Menue
        oeffnet: Wer ihn nicht trifft, kommt nirgendwo hin."""
        quelle = _css("base.html")
        block = quelle.split(".mobile-toggle {", 1)[1].split("}", 1)[0]
        self.assertIn("min-width: 44px", block)
        self.assertIn("min-height: 44px", block)

    def test_the_hero_headline_shrinks_on_small_screens(self):
        """56 px sind eine Bildschirm-Überschrift, keine Handy-Überschrift."""
        quelle = _css("home.html")
        mobil = quelle.split("@media (max-width: 900px)", 1)[1]
        self.assertIn("font-size: 34px", mobil)
