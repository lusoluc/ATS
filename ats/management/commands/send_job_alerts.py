"""Job-Alert-Versand + DSGVO-Aufräumen (Cron, z.B. stündlich oder täglich).

  0 8 * * *  cd /app && python manage.py send_job_alerts --hours 24

- Matcht neue veröffentlichte Stellen gegen aktive Abos (Scope: global /
  Stichwort / Einrichtung / km-Umkreis) und versendet je Treffer eine Mail
  (fail_silently; jeder Treffer wird als JobAlertLog ALERT_SENT protokolliert,
  damit der Lauf auch ohne Mail-Infrastruktur nachvollziehbar ist).
- Löscht verfallene Abos (12 Monate ohne Bestätigung) und INAKTIVE Abmeldungen –
  Datensparsamkeit statt Vorratshaltung. Jede Löschung landet im Audit-Log.
"""
import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.job_alerts import is_expired, match_subscribers_for_job
from ats.mail_send import send_notice
from ats.models import JobAlertLog, JobAlertSubscription, JobPosting


class Command(BaseCommand):
    help = "Versendet Job-Alerts für neue Stellen und räumt verfallene Abos auf."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24,
                            help="Stellen der letzten N Stunden berücksichtigen (Default 24).")

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(hours=options["hours"])
        jobs = (JobPosting.objects
                .filter(workflowState__name="published", createdAt__gte=since)
                .select_related("location", "facility"))

        sent = fehlgeschlagen = 0
        for job in jobs:
            for sub in match_subscribers_for_job(job):
                zugestellt = send_notice(
                    f"Neue Stelle: {job.title}",
                    (f"Passend zu Ihrem Job-Alert: {job.title} "
                     f"({getattr(job.location, 'name', '—')}).\n"
                     f"Abmelden/verwalten: /job-alert/manage/{sub.managementToken}/"),
                    None, [sub.email], context="Job-Alert")
                if not zugestellt:
                    # KEIN Log, KEIN Zeitstempel: Der naechste Lauf wiederholt
                    # den Alert. Vorher wurde beides VOR dem Versand gesetzt -
                    # ein voruebergehender Mailserver-Ausfall verlor die
                    # Benachrichtigung endgueltig, und das Protokoll
                    # behauptete ALERT_SENT ueber eine Mail, die nie rausging.
                    fehlgeschlagen += 1
                    continue
                JobAlertLog.objects.create(
                    subscription=sub, action="ALERT_SENT",
                    metadata=json.dumps({"job": job.title, "job_id": str(job.id)}))
                sub.lastAlertSentAt = timezone.now()
                sub.save(update_fields=["lastAlertSentAt", "updatedAt"])
                sent += 1

        # DSGVO-Aufräumen: verfallene + abgemeldete Abos löschen
        purged = 0
        for sub in JobAlertSubscription.objects.all():
            if sub.status == "INACTIVE" or is_expired(sub):
                # Blind-Index statt Pythons hash(): Der ist seit
                # PYTHONHASHSEED pro Prozess randomisiert - derselbe Eintrag
                # bekam bei jedem Lauf einen anderen Wert. Als Nachweis, WELCHES
                # Abo geloescht wurde, war das Feld damit wertlos.
                from ats.models import email_blind_index
                write_audit("JOB_ALERT_PURGED",
                            subscription_email_hash=email_blind_index(sub.email)[:16],
                            reason="INACTIVE" if sub.status == "INACTIVE" else "EXPIRED")
                sub.delete()
                purged += 1

        self.stdout.write(self.style.SUCCESS(
            f"{jobs.count()} neue Stelle(n) geprüft, {sent} Alert(s) zugestellt, "
            f"{fehlgeschlagen} fehlgeschlagen (werden wiederholt), "
            f"{purged} Abo(s) DSGVO-konform entfernt."))
        if fehlgeschlagen and not sent:
            # Alles fehlgeschlagen = systemisches Problem (Mailserver), kein
            # Einzelfall. Der Job-Vermerk muss rot sein, sonst faellt es
            # niemandem auf. Teilfehler bleiben gruen: Eine einzelne kaputte
            # Adresse darf den Job nicht dauerhaft roeten - sie wird ohnehin
            # beim naechsten Lauf erneut versucht.
            from django.core.management.base import CommandError
            raise CommandError(
                f"Kein einziger von {fehlgeschlagen} Alert(s) zugestellt - "
                "Mailversand pruefen (Einstellungen -> E-Mail-Versand).")
