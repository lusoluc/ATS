"""Helle Träger-Palette darf keine Eingabefelder auslassen.

WAS SCHIEFLIEF: `branding_css.html` stellt im LIGHT-Modus Karten, Titel, Tabs,
Kopf- und Fußbereich um — die Formularfelder standen nicht auf der Liste. Sie
behielten die dunklen Werte aus `base.html` (`rgba(11,13,25,0.5)` mit weißer
Schrift). Über weißem Grund ergibt das einen grauen Kasten mit weißer Schrift:
rund 3,6:1 für den Text, etwa 2,3:1 für den Platzhalter — beides unter den
geforderten 4,5:1.

Betroffen war das Bewerbungsformular. Also der eine Bildschirm, an dem
Bewerbende ihre Daten eintippen, bei jedem Träger mit heller Corporate
Identity.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from ..models import Organization


def _branding_css() -> str:
    """Alle Träger-Regeln – universelle UND nur-hell."""
    pfad = Path(settings.BASE_DIR) / "templates" / "includes" / "branding_css.html"
    return pfad.read_text(encoding="utf-8")


def _light_block() -> str:
    """Nur der `{% if brand.mode == 'LIGHT' %}`-Teil mit den Komponenten."""
    return _branding_css().split("{% if brand.mode == 'LIGHT' %}")[-1]


class LightBrandingCoversFormFieldsTestCase(TestCase):
    def test_form_fields_are_in_the_light_overrides(self):
        block = _light_block()
        for wahl in (".form-input", ".form-textarea", "::placeholder"):
            self.assertIn(wahl, block,
                          f"{wahl} fehlt in den LIGHT-Regeln – Felder blieben "
                          f"dunkel auf hellem Grund.")

    def test_the_apply_page_ships_the_override(self):
        """Der Nachweis am gerenderten Bildschirm, nicht nur in der Datei."""
        from .factories import make_job, make_world
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        Organization.objects.update(brandEnabled=True, brandMode="LIGHT",
                                    brandPrimary="#0065bd")
        html = self.client.get(reverse('ats:bewerben', args=[job.id])).content.decode()
        self.assertIn("brand-css", html)
        felder = html.split("brand-css", 1)[1]
        self.assertIn(".form-input", felder)
        self.assertIn("--text-main", felder)


class GuardrailDarkOnlyControlsTestCase(TestCase):
    """Bedienelement, das eine dunkle Palette fest verdrahtet, ohne helles Gegenstück.

    Die Fehlerklasse ist nicht „ein Feld vergessen", sondern: In `base.html`
    stehen Regeln, die Hintergrund UND Schriftfarbe hart setzen (dunkler Kasten,
    weiße Schrift). Jede davon ist auf einer hell gebrandeten Seite ein
    Kontrastloch, solange sie in den LIGHT-Regeln fehlt. Genau so ist das
    Bewerbungsformular durchgerutscht.
    """

    #: Regeln, die absichtlich dunkel bleiben – mit Grund.
    ERLAUBT = {
        # Der Lebenslauf-Upload liegt unsichtbar hinter seiner Dropzone.
        ".file-upload-input",
    }

    def test_every_hardcoded_dark_control_has_a_light_counterpart(self):
        pfad = Path(settings.BASE_DIR) / "templates" / "base.html"
        css = pfad.read_text(encoding="utf-8")
        # Gegen die GANZE Branding-Datei: Manche Bedienelemente werden in den
        # universellen Regeln umgestellt (z. B. die Knöpfe), nicht erst im
        # LIGHT-Zweig. Nur gegen den LIGHT-Zweig zu prüfen gäbe Fehlalarm.
        block = _branding_css()

        # Regelblöcke: `selektor { ... }` innerhalb des <style>-Bereichs.
        offen = []
        for treffer in re.finditer(r"([.#a-zA-Z][^{}]*?)\{([^{}]*)\}", css):
            selektor, koerper = treffer.group(1).strip(), treffer.group(2)
            if "background" not in koerper or "color:" not in koerper:
                continue
            dunkel = re.search(r"background:\s*(#0|#1|rgba\(\s*(?:0|11|15|23)\b)",
                               koerper)
            hell = re.search(r"color:\s*(#fff|#ffffff|white|rgb\(255)", koerper)
            if not (dunkel and hell):
                continue
            klassen = re.findall(r"\.[a-zA-Z][\w-]*", selektor)
            if not klassen or any(k in self.ERLAUBT for k in klassen):
                continue
            if not any(k in block for k in klassen):
                offen.append(selektor)

        self.assertFalse(
            offen,
            "Diese Regeln verdrahten eine dunkle Palette fest und fehlen in den "
            "LIGHT-Regeln von branding_css.html – auf einer hell gebrandeten "
            f"Seite jeweils ein Kontrastloch: {offen}")

    def test_the_exception_list_has_no_dead_entries(self):
        """Eine Ausnahme fuer eine Regel, die es nicht mehr gibt, koennte
        spaeter eine gleichnamige neue durchlassen."""
        from pathlib import Path
        css = (Path(settings.BASE_DIR) / "templates" / "base.html").read_text(
            encoding="utf-8")
        tot = sorted(k for k in self.ERLAUBT if k not in css)
        self.assertEqual(tot, [], f"Ausnahme ohne zugehoerige Regel: {tot}")
