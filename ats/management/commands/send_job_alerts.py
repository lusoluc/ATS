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

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.job_alerts import match_subscribers_for_job, is_expired
from ats.models import JobAlertSubscription, JobAlertLog, JobPosting


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

        sent = 0
        for job in jobs:
            for sub in match_subscribers_for_job(job):
                JobAlertLog.objects.create(
                    subscription=sub, action="ALERT_SENT",
                    metadata=json.dumps({"job": job.title, "job_id": str(job.id)}))
                send_mail(
                    f"Neue Stelle: {job.title}",
                    (f"Passend zu Ihrem Job-Alert: {job.title} "
                     f"({getattr(job.location, 'name', '—')}).\n"
                     f"Abmelden/verwalten: /job-alert/manage/{sub.managementToken}/"),
                    None, [sub.email], fail_silently=True)
                sub.lastAlertSentAt = timezone.now()
                sub.save(update_fields=["lastAlertSentAt", "updatedAt"])
                sent += 1

        # DSGVO-Aufräumen: verfallene + abgemeldete Abos löschen
        purged = 0
        for sub in JobAlertSubscription.objects.all():
            if sub.status == "INACTIVE" or is_expired(sub):
                write_audit("JOB_ALERT_PURGED", subscription_email_hash=hash(sub.email) % 10**8,
                            reason="INACTIVE" if sub.status == "INACTIVE" else "EXPIRED")
                sub.delete()
                purged += 1

        self.stdout.write(self.style.SUCCESS(
            f"{jobs.count()} neue Stelle(n) geprüft, {sent} Alert(s) versendet, "
            f"{purged} Abo(s) DSGVO-konform entfernt."))
