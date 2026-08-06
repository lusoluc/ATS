"""Feedback-Nachfassen: Interviewer:innen an ausstehendes Feedback erinnern.

Betrieb (Cron, siehe OPERATIONS.md):
    0 9 * * *  python manage.py send_feedback_requests

Philosophie (konsistent zu den anderen Erinnerungen): Die erste Bitte um
Feedback geht ereignisgetrieben raus, sobald ein Gespraech auf
„stattgefunden" gesetzt wird (siehe interview_outcome). Dieser Cron faengt
die Nachzuegler: Teilnehmer:innen, die --days (Default 2) Tage nach dem
Gespraech noch kein Feedback abgegeben haben, werden GENAU EINMAL erinnert
(Audit-Marker FEEDBACK_REMINDER_SENT). Kein Spam, keine Doppelmails.
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.mail_send import send_notice
from ats.models import AuditLog, Interview, pending_feedback_participants


class Command(BaseCommand):
    help = "Erinnert Interviewer:innen einmalig an ausstehendes Feedback."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=2,
                            help="Erinnern ab N Tagen nach dem Gespräch.")

    def _already(self, iv_id, user_id):
        marker = f'"marker": "FB:{iv_id}:{user_id}"'
        return AuditLog.objects.filter(action="FEEDBACK_REMINDER_SENT",
                                       metadataJson__contains=marker).exists()

    def handle(self, *args, **options):
        cutoff = timezone.now() - datetime.timedelta(
            days=max(1, options["days"]))
        sent = 0
        # Stattgefundene Gespraeche, die laenger als cutoff zurueckliegen
        interviews = (Interview.objects
                      .filter(outcome="COMPLETED", scheduledAt__lte=cutoff)
                      .select_related("application__applicant",
                                      "application__jobPosting")
                      .prefetch_related("participants"))
        for iv in interviews:
            app = iv.application
            # Runde, die dieses Gespraech betraf: da die Kopplung die Runde
            # beim Abschluss vorrueckt, ist die betroffene Runde in der Regel
            # interviewRound-1; wir pruefen defensiv beide (0 als Fallback).
            candidate_rounds = {max(0, (app.interviewRound or 0) - 1),
                                app.interviewRound or 0, 0}
            name = f"{app.applicant.firstName} {app.applicant.lastName}"
            for rnd in candidate_rounds:
                for person in pending_feedback_participants(iv, rnd):
                    if self._already(iv.id, person.id):
                        continue
                    send_notice(
                        f"Erinnerung: Feedback zu {name} steht noch aus",
                        (f"Ihr Gespräch mit {name} "
                         f"({app.jobPosting.title}) liegt einige Tage "
                         "zurück – Ihre Einschätzung fehlt noch. Bitte "
                         "kurz erfassen, damit die Entscheidung auf realem "
                         "Feedback steht.\nFeedback: /recruiter/interviews/"),
                        None, [person.email], context="Feedback-Anfrage")
                    write_audit("FEEDBACK_REMINDER_SENT",
                                marker=f"FB:{iv.id}:{person.id}")
                    sent += 1
                break  # eine Runde reicht – Doppelmail vermeiden
        self.stdout.write(self.style.SUCCESS(
            f"{sent} Feedback-Erinnerung(en) verschickt "
            f"(ab {options['days']} Tagen)."))
