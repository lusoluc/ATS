"""HRIS-Export (z. B. SAP SuccessFactors) – ehrliche Fassung.

WARUM DIESE DATEI NEU GESCHRIEBEN WURDE
---------------------------------------
Die vorherige Fassung hat **Erfolg erfunden**: Sie stellte nie eine HTTP-Anfrage,
sondern baute eine Schein-Antwort (`mock_response`), schrieb eine **frei erfundene
SAP-ID** in die Bewerberakte und protokollierte `HRIS_EXPORT_SUCCESS` mit
`"target": "SAP_SF_PRODUCTION"` im Audit-Log.

Das ist aus drei Gruenden inakzeptabel:
1. Das Audit-Log ist der Compliance-Nachweis (manipulationssichere Kette). Es
   darf keine Unwahrheiten enthalten - sonst ist die gesamte Beweiskraft wertlos.
2. Ein Betreiber haette geglaubt, Bewerberdaten seien an SAP uebertragen worden.
   Es wurde nie etwas uebertragen.
3. Es widerspricht dem Projektprinzip (.agents/AGENTS.md, execute_workflow_actions):
   lieber ehrlich nichts tun als Erfolg simulieren.

VERHALTEN JETZT
---------------
* Ohne Konfiguration (HRIS_ENDPOINT) wird ABGEBROCHEN - kein Audit-Eintrag,
  keine erfundene ID, klare Fehlermeldung.
* Mit Konfiguration wird WIRKLICH uebertragen (HTTP POST, Timeout, Statuspruefung).
  Protokolliert wird ausschliesslich das *tatsaechliche* Ergebnis.
* --dry-run zeigt, WAS uebertragen wuerde - ohne Uebertragung, ohne PII im Klartext.
* Bereits erfolgreich uebertragene Bewerbungen werden uebersprungen (Audit-Log als
  Quelle der Wahrheit), --all erzwingt die erneute Uebertragung.

DATENSCHUTZ
-----------
Der Export sendet personenbezogene Daten an ein Drittsystem. Das ist eine bewusste
Betreiber-Entscheidung (Auftragsverarbeitung pruefen!) - deshalb muss der Endpunkt
explizit gesetzt werden. Im Audit-Log landen KEINE Klartext-PII (nur IDs/Status).
"""
import json
import os
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ats.models import Application, AuditLog


class Command(BaseCommand):
    help = ("Ueberträgt eingeladene Bewerbungen an ein HRIS (z. B. SAP "
            "SuccessFactors). Erfordert HRIS_ENDPOINT; ohne Konfiguration "
            "wird NICHTS uebertragen und NICHTS vorgetaeuscht.")

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true',
                            help='Auch bereits uebertragene Bewerbungen erneut senden.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Nur anzeigen, was uebertragen wuerde (kein Versand).')
        parser.add_argument('--status', default='INVITED',
                            help='Zu uebertragender Status (Standard: INVITED).')

    def handle(self, *args, **options):
        endpoint = os.environ.get('HRIS_ENDPOINT', '').strip()
        token = os.environ.get('HRIS_TOKEN', '').strip()
        dry_run = options['dry_run']

        if not endpoint and not dry_run:
            raise CommandError(
                "HRIS_ENDPOINT ist nicht gesetzt - es wird NICHTS uebertragen.\n"
                "Fruehere Fassungen dieses Befehls haben hier einen Erfolg samt "
                "erfundener SAP-ID vorgetaeuscht; das tut er nicht mehr.\n"
                "Setzen Sie HRIS_ENDPOINT (und ggf. HRIS_TOKEN), oder nutzen Sie "
                "--dry-run, um den Datensatz zu pruefen.")

        status = options['status'].upper()
        qs = (Application.objects
              .filter(status=status)
              .select_related('applicant', 'jobPosting', 'jobPosting__location'))

        if not options['all']:
            done = set(AuditLog.objects
                       .filter(action='HRIS_EXPORT_SUCCESS')
                       .values_list('applicationId', flat=True))
            qs = [a for a in qs if str(a.id) not in done]
        else:
            qs = list(qs)

        if not qs:
            self.stdout.write(self.style.WARNING(
                f"Keine Bewerbungen im Status '{status}' zu uebertragen."))
            return

        self.stdout.write(f"{len(qs)} Bewerbung(en) im Status '{status}'.")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "DRY-RUN: Es wird NICHTS uebertragen."))

        ok = failed = 0
        for app in qs:
            payload = self._payload(app)
            self.stdout.write(f"  -> Bewerbung {app.id} ...")

            if dry_run:
                # Struktur zeigen, Werte NICHT - kein PII ins Terminal/Log.
                self.stdout.write("     Felder: " + ", ".join(
                    sorted(payload['candidate'].keys())))
                continue

            try:
                remote_id, code = self._post(endpoint, token, payload)
            except Exception as exc:                    # noqa: BLE001
                failed += 1
                self.stdout.write(self.style.ERROR(f"     [FEHLER] {exc}"))
                AuditLog.objects.create(
                    action="HRIS_EXPORT_FAILED",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({
                        "endpoint": endpoint, "error": str(exc)[:300]}))
                continue

            ok += 1
            # Nur ECHTE Werte protokollieren. Liefert das Zielsystem keine
            # Referenz, steht auch keine da - wir erfinden keine.
            AuditLog.objects.create(
                action="HRIS_EXPORT_SUCCESS",
                applicationId=str(app.id),
                metadataJson=json.dumps({
                    "endpoint": endpoint,
                    "httpStatus": code,
                    "remoteId": remote_id}))
            if remote_id:
                stamp = timezone.now().strftime('%d.%m.%Y %H:%M')
                app.internalNotes = ((app.internalNotes or "")
                                     + f"\n[{stamp}] HRIS-Export: uebertragen "
                                       f"(Referenz {remote_id}).")
                app.save(update_fields=['internalNotes'])
            self.stdout.write(self.style.SUCCESS(
                f"     [OK] HTTP {code}"
                + (f", Referenz {remote_id}" if remote_id
                   else " (Zielsystem gab keine Referenz zurueck)")))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"DRY-RUN beendet: {len(qs)} Bewerbung(en) waeren uebertragen worden."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"HRIS-Export beendet. Erfolgreich: {ok}, fehlgeschlagen: {failed}."))

    # ------------------------------------------------------------------ intern
    def _payload(self, app):
        loc = getattr(app.jobPosting, 'location', None)
        return {
            "source": "SecurATS",
            "timestamp": timezone.now().isoformat(),
            "candidate": {
                "uuid": str(app.applicant.id),
                "firstName": app.applicant.firstName,
                "lastName": app.applicant.lastName,
                "email": app.applicant.email,
                "phone": app.applicant.phone or "",
            },
            "jobReq": {
                "postingId": str(app.jobPosting.id),
                "title": app.jobPosting.title,
                "location": getattr(loc, 'city', '') or "",
            },
            "evaluation": {
                # Kein erfundener Score: leer bleibt leer.
                "screeningScore": app.aiScore or "",
                "screeningRationale": app.aiRationale or "",
            },
        }

    def _post(self, endpoint, token, payload):
        """Echte Uebertragung. Wirft bei Fehler - kein stiller Schein-Erfolg."""
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.getcode()
            if not (200 <= code < 300):
                raise RuntimeError(f"HTTP {code} vom Zielsystem")
            body = resp.read().decode('utf-8', errors='replace')
        remote_id = ""
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                for key in ('id', 'sapId', 'candidateId', 'remoteId'):
                    if parsed.get(key):
                        remote_id = str(parsed[key])
                        break
        except ValueError:
            pass          # Antwort ohne JSON: kein Grund zu scheitern
        return remote_id, code
