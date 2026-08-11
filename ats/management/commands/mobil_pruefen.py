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

#: Die geprueften Seiten: (Name, Pfad, Rolle). Rolle "" = oeffentlich.
#: Job-abhaengige Adressen bekommen `{job}` eingesetzt.
#:
#: Die interne Strecke steht bewusst mit drin: Genau fuer sie wurde
#: "mobil fuer Entscheider" gebaut - Hiring-Manager geben Freigaben am Handy,
#: zwischen zwei Terminen. Wenn dort ein Knopf nicht zu treffen ist, bleibt
#: eine Stelle liegen.
SEITEN: tuple[tuple[str, str, str], ...] = (
    # Oeffentlich - die Bewerberstrecke
    ("Startseite", "/", ""),
    ("Stellenliste", "/jobs/", ""),
    ("Stellendetail", "/jobs/{job}/", ""),
    ("Bewerbungsformular", "/jobs/{job}/bewerben/", ""),
    ("Job-Alert", "/job-alert/", ""),
    ("Barrierefreiheitserklärung", "/barrierefreiheit/", ""),
    ("KI-Transparenz", "/ki-transparenz/", ""),
    ("Anmeldung", "/recruiter/login/", ""),
    # Intern - die Entscheider-Strecke
    ("Dashboard", "/recruiter/dashboard/", "Recruiter"),
    ("Freigaben", "/recruiter/approvals/", "Hiring-Manager"),
    ("Personalbedarf", "/recruiter/bedarf/", "Hiring-Manager"),
    ("Termine", "/recruiter/interviews/", "Recruiter"),
    ("Sammel-Postfach", "/recruiter/postfach/", "Recruiter"),
    ("Aufgaben", "/recruiter/aufgaben/", "Recruiter"),
)

#: Rolle -> Benutzername in der Wegwerf-Datenbank (Muster: handbuch_bilder).
KONTEN = {
    "HR-Admin": "mobil-admin",
    "Recruiter": "mobil-recruiter",
    "Hiring-Manager": "mobil-hm",
}
PASSWORT = "mobil-nur-fuer-die-pruefung"

#: Wie viele Pixel Ueberstand toleriert werden (Rundung im Browser).
TOLERANZ = 2

#: Mindestmass fuer ein Bedienelement (WCAG 2.5.8, Stufe AA). 44 px waeren
#: bequem (2.5.5, AAA) - geprueft wird die verbindliche Schwelle, damit der
#: Waechter nicht an Geschmacksfragen scheitert.
MIN_ZIEL = 24

#: Geprueft werden nur FORMULAR-Elemente. Links im Fliesstext sind nach
#: 2.5.8 ausdruecklich ausgenommen ("inline"), und sie mitzuzaehlen haette
#: den Waechter mit Rauschen unbrauchbar gemacht. Ein Kontrollkaestchen ist
#: nie ausgenommen.
ZIEL_AUSWAHL = "input:not([type=hidden]), select, textarea, button"


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
            self._konten_anlegen()
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
                angemeldet = ""
                for name, pfad, rolle in SEITEN:
                    if rolle and rolle != angemeldet:
                        self._anmelden(seite, basis, rolle)
                        angemeldet = rolle
                    adresse = basis + pfad.format(job=job)
                    seite.goto(adresse, wait_until="networkidle")
                    seite.evaluate("document.fonts.ready")
                    seite.wait_for_timeout(250)
                    ergebnis = seite.evaluate(
                        _MESSUNG, {"toleranz": TOLERANZ, "minZiel": MIN_ZIEL,
                                   "auswahl": ZIEL_AUSWAHL})
                    schief = ergebnis["ueberstehend"] or ergebnis["zuKlein"]
                    if not schief:
                        self.stdout.write(self.style.SUCCESS(f"OK   {name}"))
                        continue
                    befunde.append((name, ergebnis))
                    self.stdout.write(self.style.ERROR(f"FEHLER {name}"))
                    if ergebnis["ueberstehend"]:
                        self.stdout.write(
                            f"    Dokument {ergebnis['scrollBreite']} px breit "
                            f"bei {breite} px Fenster:")
                        for e in ergebnis["ueberstehend"][:5]:
                            self.stdout.write(f"      {e}")
                        if ergebnis["unerreichbar"]:
                            self.stdout.write(self.style.ERROR(
                                "      NICHT ANKLICKBAR: "
                                + ", ".join(ergebnis["unerreichbar"])))
                    if ergebnis["zuKlein"]:
                        self.stdout.write(
                            f"    Bedienelement unter {MIN_ZIEL} px "
                            f"(WCAG 2.5.8):")
                        for e in ergebnis["zuKlein"][:6]:
                            self.stdout.write(f"      {e}")
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


    # -- Innereien ---------------------------------------------------------

    def _konten_anlegen(self) -> None:
        from django.contrib.auth.models import Group, User
        for rolle, name in KONTEN.items():
            nutzer, _ = User.objects.get_or_create(username=name)
            nutzer.set_password(PASSWORT)
            nutzer.save()
            nutzer.groups.clear()
            nutzer.groups.add(Group.objects.get(name=rolle))

    def _anmelden(self, seite: Any, basis: str, rolle: str) -> None:
        seite.goto(f"{basis}/recruiter/login/")
        seite.fill("input[name=username]", KONTEN[rolle])
        seite.fill("input[name=password]", PASSWORT)
        seite.click("button[type=submit]")
        seite.wait_for_load_state("networkidle")


#: Im Browser ausgeführt: Was ragt hinaus, was ist zu klein zum Treffen?
_MESSUNG = r"""
(cfg) => {
  const w = document.documentElement.clientWidth;

  // Ein Element in einem waagerecht scrollbaren Kasten ragt nicht "hinaus" -
  // es ist erreichbar, man schiebt den Kasten. Genau dafuer gibt es den
  // .table-scroll-Wrapper. Ohne diese Unterscheidung meldet die Pruefung
  // jede breite Tabelle als Fehler und wird ignoriert.
  const imScroller = (el) => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const ox = getComputedStyle(p).overflowX;
      if ((ox === 'auto' || ox === 'scroll') && p.scrollWidth > p.clientWidth) return true;
    }
    return false;
  };

  const raus = [...document.querySelectorAll('body *')]
    .map(el => ({el, r: el.getBoundingClientRect()}))
    .filter(o => o.r.width > 0 && o.r.height > 0 && o.r.right > w + cfg.toleranz)
    .filter(o => !imScroller(o.el))
    .sort((a,b) => b.r.right - a.r.right);

  const beschreibe = (o) => {
    const k = (o.el.className || '').toString().trim().split(/\s+/)[0];
    return `${o.el.tagName.toLowerCase()}${k ? '.' + k : ''} reicht bis `
         + `${Math.round(o.r.right)} px (Fenster ${w})`;
  };
  const bedienbar = raus
    .filter(o => ['A','BUTTON','INPUT','SELECT','TEXTAREA'].includes(o.el.tagName))
    .map(o => `"${(o.el.innerText || o.el.value || o.el.name || '').trim().slice(0, 30)}"`);

  const sichtbar = (el) => {
    const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
  };
  const zuKlein = [...document.querySelectorAll(cfg.auswahl)]
    .filter(el => sichtbar(el))
    .map(el => ({el, r: el.getBoundingClientRect()}))
    .filter(o => o.r.width > 0 && o.r.height > 0
                 && (o.r.width < cfg.minZiel || o.r.height < cfg.minZiel))
    .map(o => {
      const name = (o.el.getAttribute('aria-label') || o.el.innerText
                    || o.el.name || o.el.type || '').trim().slice(0, 26);
      return `${o.el.tagName.toLowerCase()}[${o.el.type || '-'}] "${name}" `
           + `${Math.round(o.r.width)}x${Math.round(o.r.height)} px`;
    });

  // Ein Element, das hinausragt, ohne das Dokument zu verbreitern, und das
  // niemand bedienen kann, ist Deko (Hintergrund-Verlaeufe bluten absichtlich
  // ueber den Rand). Nur melden, wenn das DOKUMENT breiter wird oder ein
  // Bedienelement draussen liegt - sonst erzeugt der Waechter Rauschen, und
  // ein Waechter, den man wegen Rauschen ignoriert, prueft nichts mehr.
  const dokBreite = document.documentElement.scrollWidth;
  const echterUeberstand = (dokBreite > w + cfg.toleranz) || bedienbar.length > 0;

  return {
    scrollBreite: dokBreite,
    ueberstehend: echterUeberstand ? raus.map(beschreibe) : [],
    unerreichbar: [...new Set(bedienbar)],
    zuKlein: [...new Set(zuKlein)]
  };
}
"""
