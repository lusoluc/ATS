"""Zeitplan-Dienst: führt die wiederkehrenden Jobs aus.

Warum im Projekt statt per Cron: `OPERATIONS.md` schlug einen Cron-Eintrag
vor, der ausgelieferte `docker-compose.yml` enthielt aber keinen. Wer der
Installationsanleitung folgte, bekam die Jobs nie — einschließlich der
Anonymisierung nach Fristablauf, die die Oberfläche als „automatisch" zusagt.

Bewusst schlicht gehalten (siehe `ats/jobs.py`): ein Dienst im selben Image,
der alle paar Minuten nachsieht, was fällig ist. Der Träger betreibt das Haus
selbst; was er im Störungsfall nicht lesen kann, hilft ihm nicht.
"""
import time

from django.core.management.base import BaseCommand

from ats.jobs import JOBS, due_jobs, run_job


class Command(BaseCommand):
    help = ("Fuehrt faellige wiederkehrende Jobs aus (Aufbewahrungsfristen, "
            "Job-Alerts, Erinnerungen, Audit-Pruefung, Wochenbericht).")

    def add_arguments(self, parser):
        parser.add_argument(
            '--once', action='store_true',
            help='Nur einmal nachsehen und beenden (fuer Cron oder Tests).')
        parser.add_argument(
            '--interval', type=int, default=300,
            help='Sekunden zwischen zwei Durchlaeufen im Dauerbetrieb.')
        parser.add_argument(
            '--list', action='store_true',
            help='Zeitplan anzeigen und beenden - ohne etwas auszufuehren.')

    def handle(self, *args, **options):
        if options['list']:
            for spec in JOBS:
                wann = ('wöchentlich' if spec.weekday is not None else 'täglich')
                pflicht = ' [Pflicht]' if spec.pflicht else ''
                self.stdout.write(
                    f"{spec.name:<26} {wann} {spec.hour:02d}:{spec.minute:02d}"
                    f"{pflicht}  {spec.label}")
            return

        while True:
            faellig = due_jobs()
            for spec in faellig:
                self.stdout.write(f"Starte {spec.name} ...")
                ok = run_job(spec)
                self.stdout.write(
                    self.style.SUCCESS(f"  {spec.name}: erledigt") if ok
                    else self.style.ERROR(f"  {spec.name}: fehlgeschlagen "
                                          f"(Grund im Protokoll)"))
            if not faellig:
                self.stdout.write("Nichts faellig.")
            if options['once']:
                return
            time.sleep(max(30, options['interval']))
