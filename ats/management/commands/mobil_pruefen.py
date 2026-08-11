"""Prüft die Bewerberstrecke am Handy-Bildschirm — mit einem echten Browser.

    python manage.py mobil_pruefen

WARUM ein eigenes Kommando: Diese Fehlerklasse ist im HTML nicht zu sehen.
Ob ein Element über den Rand ragt, entscheidet sich erst beim Layout — aus
Schriftgröße, Wortlänge und Flex-Regeln zusammen. Ein Django-Test kann das
nicht wissen, und am 27-Zoll-Bildschirm sieht es niemand.

Gefunden hat der erste Lauf zwei Dinge, die es beide in kein Auge geschafft
hatten: Die Footer-Zeile brach nicht um und schnitt „KI-Transparenz"
(EU AI Act Art. 86) sowie „ATS-Dashboard" ab — und weil das Dokument dadurch
529 px breit wurde, rechnete der Barrierefreiheits-Knopf (position:fixed,
right:30px) gegen diese 529 px und stand bei 443..499 px. Am Handy also
außerhalb des Bildes. Ausgerechnet der Knopf, der Kontrast und Schriftgröße
einstellt.

`body { overflow-x: hidden }` macht das lautlos: Überstehendes wird
ABGESCHNITTEN statt scrollbar — dieselbe Falle, die bei Tabellen schon einmal
zugeschlagen hat (deshalb der Wrapper-Wächter in test_guardrails).

Braucht playwright (requirements-dev.txt). Endet mit Exit-Code 1, wenn etwas
über den Rand ragt.
"""
from __future__ import annotations

import sys
from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test.testcases import LiveServerThread
from django.test.utils import (
    override_settings,
    setup_databases,
    teardown_databases,
)

#: Schmalstes verbreitetes Geraet (iPhone SE). Wer hier durchkommt, kommt
#: ueberall durch.
BREITE, HOEHE = 375, 812

#: Die oeffentliche Strecke: Was eine bewerbende Person am Telefon sieht.
#: Job-abhaengige Adressen bekommen `{job}` eingesetzt.
SEITEN: tuple[tuple[str, str], ...] = (
    ("Startseite", "/"),
    ("Stellenliste", "/jobs/"),
    ("Stellendetail", "/jobs/{job}/"),
    ("Bewerbungsformular", "/jobs/{job}/bewerben/"),
    ("Job-Alert", "/job-alert/"),
    ("Barrierefreiheitserklärung", "/barrierefreiheit/"),
    ("KI-Transparenz", "/ki-transparenz/"),
    ("Anmeldung", "/recruiter/login/"),
)

#: Wie viele Pixel Ueberstand toleriert werden (Rundung im Browser).
TOLERANZ = 2


class Command(BaseCommand):
    help = ("Prüft die öffentlichen Seiten bei 375 px Breite auf Inhalte, "
            "die über den Rand ragen (braucht playwright).")

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--breite", type=int, default=BREITE,
                            help=f"Viewport-Breite (Standard: {BREITE}).")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise CommandError(
                "playwright fehlt. Einmalig einrichten:\n"
                "  pip install -r requirements-dev.txt\n"
                "  python -m playwright install chromium") from None

        breite = int(options["breite"])
        self.stdout.write(f"Prüfe bei {breite} px Breite …")
        alt = setup_databases(verbosity=0, interactive=False)
        server = None
        try:
            with override_settings(DEMO_MODE=True):
                call_command("seed_demo", verbosity=0)
            from ats.models import JobPosting
            job = (JobPosting.objects.filter(workflowState__name="published")
                   .values_list("id", flat=True).first())
            if job is None:
                raise CommandError("Keine veröffentlichte Stelle in den "
                                   "Demo-Daten – die Bewerberstrecke lässt "
                                   "sich so nicht prüfen.")

            from django.contrib.staticfiles.handlers import StaticFilesHandler
            server = LiveServerThread("127.0.0.1", StaticFilesHandler,
                                      connections_override={})
            server.daemon = True
            server.start()
            server.is_ready.wait()
            if server.error:
                raise server.error
            basis = f"http://127.0.0.1:{server.port}"

            befunde = []
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                kontext = browser.new_context(
                    viewport={"width": breite, "height": HOEHE},
                    device_scale_factor=1, locale="de-DE")
                seite = kontext.new_page()
                for name, pfad in SEITEN:
                    adresse = basis + pfad.format(job=job)
                    seite.goto(adresse, wait_until="networkidle")
                    seite.evaluate("document.fonts.ready")
                    seite.wait_for_timeout(250)
                    ergebnis = seite.evaluate(_MESSUNG, TOLERANZ)
                    if ergebnis["ueberstehend"]:
                        befunde.append((name, ergebnis))
                        self.stdout.write(self.style.ERROR(
                            f"FEHLER {name}: Dokument {ergebnis['scrollBreite']} px "
                            f"breit bei {breite} px Fenster"))
                        for e in ergebnis["ueberstehend"][:5]:
                            self.stdout.write(f"    {e}")
                        if ergebnis["unerreichbar"]:
                            self.stdout.write(self.style.ERROR(
                                "    NICHT ANKLICKBAR: "
                                + ", ".join(ergebnis["unerreichbar"])))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"OK   {name}"))
                browser.close()
        finally:
            if server is not None:
                server.terminate()
            teardown_databases(alt, verbosity=0)

        if befunde:
            self.stdout.write(self.style.ERROR(
                f"\n{len(befunde)} von {len(SEITEN)} Seiten ragen über den "
                f"Rand. `body {{ overflow-x: hidden }}` schneidet das ab, "
                f"statt es scrollbar zu machen – am Handy ist der Inhalt "
                f"dann schlicht weg."))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS(
            f"\n{len(SEITEN)} Seiten geprüft, nichts ragt über den Rand."))


#: Im Browser ausgeführt: Was steht rechts außerhalb des Fensters?
_MESSUNG = """
(toleranz) => {
  const w = document.documentElement.clientWidth;
  const alle = [...document.querySelectorAll('body *')]
    .map(el => ({el, r: el.getBoundingClientRect()}))
    .filter(o => o.r.width > 0 && o.r.height > 0 && o.r.right > w + toleranz);
  const beschreibe = (o) => {
    const k = (o.el.className || '').toString().trim().split(/\\s+/)[0];
    return `${o.el.tagName.toLowerCase()}${k ? '.' + k : ''} reicht bis `
         + `${Math.round(o.r.right)} px (Fenster ${w})`;
  };
  const bedienbar = alle
    .filter(o => ['A','BUTTON','INPUT','SELECT','TEXTAREA'].includes(o.el.tagName))
    .map(o => `"${(o.el.innerText || o.el.value || o.el.name || '').trim().slice(0, 30)}"`);
  return {
    scrollBreite: document.documentElement.scrollWidth,
    ueberstehend: alle.sort((a,b) => b.r.right - a.r.right).map(beschreibe),
    unerreichbar: [...new Set(bedienbar)]
  };
}
"""
