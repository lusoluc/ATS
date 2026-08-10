"""Screenshots für das Benutzerhandbuch erzeugen — reproduzierbar.

    python manage.py handbuch_bilder

WARUM ein Kommando und keine Handarbeit: Bilder veralten schneller als Text,
und ein Bild, das einen Knopf zeigt, den es nicht mehr gibt, ist genau die
Sorte Lüge, die wir aus dem Code werfen. Eine Aktualisierung nach einem Umbau
soll eine Minute kosten, nicht einen Nachmittag.

WORAUS die Bilder entstehen: aus einer **eigenen Testdatenbank** mit
Demo-Daten, nie aus der Arbeitsdatenbank. Ein Handbuch geht per Mail herum
und landet auf Schulungsrechnern — echte Bewerberdaten haben darin nichts
verloren (Art. 5 Abs. 1 lit. c DSGVO). Die Datenbank wird angelegt, benutzt
und wieder weggeräumt.
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

from ats.handbuch import (
    ALLE,
    BREITE,
    HOEHE,
    Bild,
    manifest_schreiben,
    template_hash,
)

#: Passwort der Demo-Konten, die dieses Kommando anlegt. Sie leben nur in
#: der weggeworfenen Testdatenbank.
PASSWORT = "handbuch-nur-fuer-bilder"

#: Rolle -> Benutzername in der Bilder-Datenbank.
KONTEN = {
    "HR-Admin": "bild-admin",
    "Recruiter": "bild-recruiter",
    "Hiring-Manager": "bild-hm",
    "Viewer": "bild-viewer",
}


class Command(BaseCommand):
    help = ("Erzeugt die Screenshots des Benutzerhandbuchs in docs/handbuch/ "
            "(braucht playwright: pip install -r requirements-dev.txt und "
            "python -m playwright install chromium).")

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--nur", default="",
            help="Nur Bilder, deren Name diesen Text enthält (z.B. --nur 30-).")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise CommandError(
                "playwright fehlt. Einmalig einrichten:\n"
                "  pip install -r requirements-dev.txt\n"
                "  python -m playwright install chromium") from None

        auswahl = [b for b in ALLE if options["nur"] in b.name]
        if not auswahl:
            raise CommandError(f"Kein Bild passt zu --nur {options['nur']!r}.")

        self.stdout.write("Lege Bilder-Datenbank an (die Arbeitsdatenbank "
                          "bleibt unberührt) ...")
        alt = setup_databases(verbosity=0, interactive=False)
        server = None
        try:
            # `seed_demo` verweigert ohne DEMO_MODE den Dienst, weil es Konten
            # mit bekanntem Passwort anlegt - ein richtiges Gate. Hier ist es
            # unbedenklich: Die Konten leben ausschliesslich in der gleich
            # wieder geloeschten Bilder-Datenbank, nie in der Arbeits- oder
            # Produktionsdatenbank. Deshalb NUR fuer diesen Lauf angehoben.
            with override_settings(DEMO_MODE=True):
                call_command("seed_demo", verbosity=0)
            self._konten_anlegen()
            self._medien_anlegen()
            from django.contrib.staticfiles.handlers import StaticFilesHandler
            server = LiveServerThread("127.0.0.1", StaticFilesHandler,
                                      connections_override={})
            server.daemon = True
            server.start()
            server.is_ready.wait()
            if server.error:
                raise server.error
            basis = f"http://127.0.0.1:{server.port}"
            self.stdout.write(f"Testserver läuft auf {basis}")

            manifest = {}
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                for bild in auswahl:
                    self._aufnehmen(browser, basis, bild)
                    if bild.templates:
                        manifest[bild.name] = template_hash(bild.templates)
                    self.stdout.write(f"  {bild.datei}")
                browser.close()
            self._manifest_ergaenzen(manifest, bool(options["nur"]))
        finally:
            if server is not None:
                server.terminate()
            teardown_databases(alt, verbosity=0)

        self.stdout.write(self.style.SUCCESS(
            f"{len(auswahl)} Bild(er) erzeugt. Die Bilder-Datenbank wurde "
            f"wieder entfernt."))

    # -- Innereien ---------------------------------------------------------

    def _konten_anlegen(self) -> None:
        from django.contrib.auth.models import Group, User
        for rolle, name in KONTEN.items():
            nutzer, _ = User.objects.get_or_create(username=name)
            nutzer.set_password(PASSWORT)
            nutzer.first_name = "Demo"
            nutzer.save()
            nutzer.groups.clear()
            nutzer.groups.add(Group.objects.get(name=rolle))

    def _medien_anlegen(self) -> None:
        """Beispiel-Medien fuer Kapitel 7.3.

        `seed_demo` legt keine MediaAssets an - die Mediathek stand im Bild
        deshalb leer da („Noch keine Medien") und konnte ausgerechnet das
        nicht zeigen, worum es in dem Kapitel geht: Bereichsangabe und
        Blaetterung. Ein Screenshot, der den erklaerten Zustand nicht
        herstellt, erklaert nichts.

        62 Eintraege, weil erst ueber der Seitengroesse (50) eine zweite
        Seite entsteht - „1-50 von 62" und „Seite 1 von 2" sind genau die
        Angaben, die der Text beschreibt. Reine Datensaetze ohne Dateien:
        Die Tabelle zeigt Name, Typ und Datum, keine Vorschaubilder.
        """
        import datetime

        from django.utils import timezone

        from ats.models import MediaAsset

        neueste = [
            ("Teamfoto Pflege Station 3", "team-pflege-station-3.jpg", "image/jpeg"),
            ("Klinik Nord Aussenansicht", "klinik-nord-aussen.jpg", "image/jpeg"),
            ("Logo Traeger RGB", "logo-traeger-rgb.png", "image/png"),
            ("Ausbildungsflyer 2026", "ausbildung-2026.pdf", "application/pdf"),
            ("Empfang Haus B", "empfang-haus-b.jpg", "image/jpeg"),
            ("Physiotherapie Uebungsraum", "physio-uebungsraum.jpg", "image/jpeg"),
            ("Messestand Pflegetag", "messestand-pflegetag.jpg", "image/jpeg"),
            ("Leitbild Kurzfassung", "leitbild-kurz.pdf", "application/pdf"),
            ("Kantine Mittagsangebot", "kantine-mittag.jpg", "image/jpeg"),
            ("Nachtdienst Uebergabe", "nachtdienst-uebergabe.jpg", "image/jpeg"),
            ("Fuhrpark Ambulanz", "fuhrpark-ambulanz.jpg", "image/jpeg"),
            ("Fortbildungsraum", "fortbildungsraum.jpg", "image/jpeg"),
        ]
        jetzt = timezone.now()
        zeilen = []
        for i, (name, datei, typ) in enumerate(neueste):
            zeilen.append(MediaAsset(
                name=name, altText=f"{name} - Beispielbild der Demo-Daten",
                file=f"uploads/{datei}", contentType=typ,
                createdAt=jetzt - datetime.timedelta(days=i)))
        for i in range(len(neueste), 62):
            zeilen.append(MediaAsset(
                name=f"Anzeigenmotiv Archiv {i - len(neueste) + 1:02d}",
                altText="Archiviertes Anzeigenmotiv der Demo-Daten",
                file=f"uploads/anzeige-archiv-{i:02d}.jpg",
                contentType="image/jpeg",
                createdAt=jetzt - datetime.timedelta(days=i)))
        MediaAsset.objects.bulk_create(zeilen)

    def _aufnehmen(self, browser: Any, basis: str, bild: Bild) -> None:
        groesse = ({"width": 390, "height": 844} if bild.mobil
                   else {"width": BREITE, "height": HOEHE})
        # Aufloesung 1:1. Mit doppelter Pixeldichte wog ein Bild rund 1,4 MB -
        # bei ueber 40 Bildern waere das Repository um mehrere Dutzend Megabyte
        # gewachsen, ohne dass jemand die Bilder je so gross braucht. 1280 px
        # Breite sind am Bildschirm scharf und ergeben gedruckt auf 16 cm rund
        # 200 dpi.
        kontext = browser.new_context(viewport=groesse,
                                      device_scale_factor=1,
                                      locale="de-DE")
        seite = kontext.new_page()
        try:
            if bild.rolle in KONTEN:
                seite.goto(f"{basis}/recruiter/login/")
                seite.fill("input[name=username]", KONTEN[bild.rolle])
                seite.fill("input[name=password]", PASSWORT)
                seite.click("button[type=submit]")
                seite.wait_for_load_state("networkidle")
            seite.goto(f"{basis}{bild.pfad}")
            seite.wait_for_load_state("networkidle")
            for selektor in bild.klicks:
                seite.click(selektor)
                seite.wait_for_timeout(300)
            # Bewegung anhalten: Animationen sollen das Bild nicht verwackeln.
            seite.add_style_tag(content="*{animation:none!important;"
                                        "transition:none!important}")
            # Auf die Schriften warten. `networkidle` allein genuegt nicht:
            # Die Icon-Schrift wird erst angefordert, wenn ein Symbol
            # tatsaechlich gezeichnet wird - sonst stehen im Bild leere
            # Kaestchen statt der Symbole.
            seite.evaluate("document.fonts.ready")
            seite.wait_for_timeout(600)
            ziel = bild.datei
            if bild.ausschnitt:
                element = seite.query_selector(bild.ausschnitt)
                if element is None:
                    raise CommandError(
                        f"{bild.name}: Ausschnitt {bild.ausschnitt!r} gibt es "
                        f"auf {bild.pfad} nicht (mehr).")
                element.screenshot(path=ziel)
            else:
                seite.screenshot(path=ziel, full_page=False)
        finally:
            kontext.close()

    def _manifest_ergaenzen(self, neu: dict[str, str], teilmenge: bool) -> None:
        from ats.handbuch import manifest_lesen
        eintraege = manifest_lesen() if teilmenge else {}
        eintraege.update(neu)
        manifest_schreiben(eintraege)


if __name__ == "__main__":       # pragma: no cover - nur zur Sicherheit
    sys.exit("Bitte über manage.py aufrufen.")
