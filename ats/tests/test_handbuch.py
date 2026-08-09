"""Ein Handbuch kann genauso lügen wie Code — nur merkt es niemand.

Der Unterschied zum Code: Wenn eine Funktion verschwindet, schlägt irgendwann
ein Test fehl. Wenn ein Kapitel eine Seite beschreibt, die es nicht mehr gibt,
merkt es erst die Person, die davor sitzt und den Knopf sucht.

Diese Wächter machen die Handbuchpflege zum Teil desselben Gates, das schon
jeden Commit prüft:

1. Jede interne Seite kommt im Handbuch vor — oder steht mit Begründung in der
   Ausnahmeliste (die ihrerseits auf tote Einträge geprüft wird).
2. Jede im Handbuch genannte Adresse existiert wirklich.
3. Jeder zitierte Schaltflächentext ist in einer Vorlage auffindbar.
4. Kein Screenshot ist veraltet (Vorlagen-Hash im Manifest).
"""
import pathlib
import re

from django.test import TestCase
from django.urls import reverse

from ..handbuch import ALLE, veraltete_bilder
from .utils import make_user


def _handbuch() -> str:
    pfad = pathlib.Path(__file__).resolve().parent.parent.parent / "HANDBUCH.md"
    return pfad.read_text(encoding="utf-8")


class HandbuchIstErreichbarTestCase(TestCase):
    """Ein Handbuch, das niemand findet, ist keins."""

    def setUp(self):
        self.client.force_login(make_user("leser", role="Recruiter"))

    def test_the_help_page_renders_the_handbook(self):
        r = self.client.get(reverse('ats:hilfe'))
        self.assertEqual(r.status_code, 200)
        inhalt = r.content.decode()
        self.assertIn("Die ersten 20 Minuten", inhalt)
        self.assertIn("Weg 3", inhalt)

    def test_the_menu_links_to_it(self):
        r = self.client.get(reverse('ats:dashboard'))
        self.assertContains(r, reverse('ats:hilfe'))

    def test_the_images_are_delivered(self):
        r = self.client.get(reverse('ats:hilfe_bild', args=["01-anmeldung.png"]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/png")

    def test_no_path_traversal_through_the_image_name(self):
        """Der Name kommt aus der Adresszeile - `../` darf nie eine andere
        Datei erreichbar machen."""
        for boese in ("..%2F..%2Fmanage.py", "geheim.txt", "a/b.png"):
            with self.subTest(name=boese):
                r = self.client.get(f"/hilfe/bild/{boese}")
                self.assertIn(r.status_code, (404, 301),
                              "Unerlaubter Dateiname wurde ausgeliefert.")

    def test_a_viewer_may_read_the_handbook_too(self):
        """Gerade wer nur zusieht, braucht die Erklaerung."""
        self.client.force_login(make_user("leser-viewer", role="Viewer"))
        self.assertEqual(self.client.get(reverse('ats:hilfe')).status_code, 200)


class GuardrailHandbuchBleibtWahrTestCase(TestCase):
    """Die vier Prüfungen, die das Handbuch am Leben halten."""

    #: Seiten-Name (URL-Name) -> warum das Handbuch sie (noch) nicht erklaert.
    #: Teil 1+2 decken den Alltag ab; Einrichtung und Sonderfaelle folgen in
    #: Teil 3-6. Jeder Eintrag ist eine SCHULD, kein Freibrief.
    NOCH_NICHT_ERKLAERT = {
        'stats_page': 'Teil 4 (Einrichten)',
        'process_page': 'Teil 4 (Einrichten)',
        'templates_page': 'Teil 4 (Einrichten)',
        'ki_page': 'Teil 4 (Einrichten)',
        'learned_scoring': 'Teil 4 (Einrichten)',
        'hris_page': 'Teil 4 (Einrichten)',
        'retention': 'Teil 4 (Einrichten)',
        'scheduled_jobs': 'Teil 5 (Wenn etwas klemmt)',
        'audit_log': 'Teil 6 (Nachweis)',
        'governance': 'Teil 3 (Wenn mehrere mitreden)',
        'panel_defaults': 'Teil 3 (Wenn mehrere mitreden)',
        'delegations': 'Teil 3 (Wenn mehrere mitreden)',
        'talent_pool': 'Teil 2, Weg 3 - Ergaenzung geplant',
        'analytics': 'Teil 4 (Auswertung)',
        'global_search': 'in Teil 1.4 als Suchfeld erklaert, keine eigene Seite',
    }

    def test_every_chapter_points_to_a_real_page(self):
        """Kapitel über eine Seite, die es nicht mehr gibt."""
        from django.urls import NoReverseMatch, resolve
        from django.urls.exceptions import Resolver404
        text = _handbuch()
        adressen = set(re.findall(r"`(/[a-z0-9/_-]+/)`", text))
        tot = []
        for adresse in sorted(adressen):
            try:
                resolve(adresse)
            except (Resolver404, NoReverseMatch):
                tot.append(adresse)
        self.assertEqual(tot, [],
                         f"Das Handbuch nennt Adressen, die es nicht gibt: {tot}")

    def test_every_named_control_exists_in_a_template(self):
        """Umbenannter Knopf -> das Handbuch schickt Leute ins Leere.

        Erkannt werden Bedienelemente an der Schreibkonvention des Handbuchs:
        fett UND in typografischen Anfuehrungszeichen. Die erste Fassung
        dieses Waechters hielt jedes fett gesetzte Wort fuer eine Schaltflaeche
        - und meldete deshalb Betonungen wie „Ziel:" als fehlende Knoepfe.
        Eine eindeutige Konvention ist hier mehr wert als eine schlaue Heuristik.
        """
        text = _handbuch()
        knoepfe = set(re.findall(r"\*\*„([^“]{2,40})“\*\*", text))
        self.assertGreaterEqual(
            len(knoepfe), 8,
            "Kaum Bedienelemente gefunden - wurde die Schreibkonvention "
            "geaendert? Dann prueft dieser Waechter nichts mehr.")
        wurzel = pathlib.Path(__file__).resolve().parent.parent.parent / "templates"
        alle_vorlagen = "\n".join(
            p.read_text(encoding="utf-8", errors="ignore")
            for p in wurzel.rglob("*.html"))
        self.assertGreater(len(alle_vorlagen), 10000,
                           "Der Vorlagen-Scan findet fast nichts - er prueft "
                           "ins Leere.")
        fehlend = sorted(k for k in knoepfe if k not in alle_vorlagen)
        self.assertEqual(
            fehlend, [],
            "Das Handbuch nennt Bedienelemente, die in keiner Vorlage "
            f"vorkommen - umbenannt oder entfernt? {fehlend}")

    def test_no_screenshot_is_out_of_date(self):
        """Vorlage geändert -> Bild zeigt einen alten Stand."""
        veraltet = veraltete_bilder()
        self.assertEqual(
            veraltet, [],
            "Screenshot veraltet: Die zugehoerige Vorlage hat sich seit der "
            "Aufnahme geaendert. Bitte neu erzeugen:\n"
            "  python manage.py handbuch_bilder\n"
            f"Betroffen: {veraltet}")

    def test_every_image_file_exists(self):
        wurzel = pathlib.Path(__file__).resolve().parent.parent.parent
        fehlend = [b.datei for b in ALLE if not (wurzel / b.datei).exists()]
        self.assertEqual(fehlend, [],
                         f"Im Handbuch angekuendigte Bilder fehlen: {fehlend}")

    def test_every_image_has_an_alt_text(self):
        """Barrierefreiheit: Ein Bild ohne Beschreibung ist fuer
        Screenreader-Nutzende nicht vorhanden - im Handbuch einer Plattform,
        die mit Barrierefreiheit wirbt, waere das besonders peinlich."""
        ohne = [b.name for b in ALLE if len(b.beschreibung.strip()) < 20]
        self.assertEqual(ohne, [], f"Bild ohne brauchbaren Alt-Text: {ohne}")
        text = _handbuch()
        leere = re.findall(r"!\[\s*\]\(", text)
        self.assertEqual(leere, [], "Bild ohne Alt-Text im Handbuch-Text.")

    def test_the_exception_list_has_no_dead_entries(self):
        """Eine Begruendung fuer eine Seite, die es nicht mehr gibt, ist eine
        stehen gebliebene Schuld - sie verdeckt spaeter eine echte Luecke."""
        from django.urls import NoReverseMatch
        from django.urls import reverse as rev
        tot = []
        for name in self.NOCH_NICHT_ERKLAERT:
            try:
                rev(f"ats:{name}")
            except NoReverseMatch:
                tot.append(name)
        self.assertEqual(tot, [], f"Ausnahme ohne zugehoerige Seite: {tot}")
