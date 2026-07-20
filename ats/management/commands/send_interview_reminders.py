"""Termin-Erinnerungen: No-Show-Prävention für Bewerbende UND das Team.

Betrieb (Cron, siehe OPERATIONS.md):
    0 7 * * *  python manage.py send_interview_reminders

Verhalten:
- Erinnert an Gespräche im Fenster [jetzt, jetzt + --hours] (Default 24 h).
- Genau EINE Erinnerung je Interview (`reminderSentAt`-Marker) – der Cron
  darf beliebig oft laufen, ohne zu spammen.
- Bewerbende: E-Mail + Portal-Nachricht (das Portal ist die verlässliche
  Quelle, falls die Mail im Spam landet).
- Kollaboration: Die Person, die den gebuchten Slot angeboten hat
  (`InterviewSlot.createdBy`), bekommt ebenfalls eine kurze Mail – in
  verteilten Teams geht ein morgen anstehendes Gespräch sonst leicht unter.
- Abgesagte/zurückgezogene Bewerbungen werden nie erinnert.
"""
import datetime

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.models import Interview, Message


class Command(BaseCommand):
    help = "Verschickt einmalige Erinnerungen für anstehende Interviews (Cron-tauglich)."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24,
                            help="Erinnerungsfenster in Stunden (Default 24).")

    def handle(self, *args, **options):
        now = timezone.now()
        window_end = now + datetime.timedelta(hours=max(1, options["hours"]))
        due = (Interview.objects
               .filter(scheduledAt__gte=now, scheduledAt__lte=window_end,
                       reminderSentAt__isnull=True,
                       application__status="INVITED")
               .select_related("application__applicant",
                               "application__jobPosting",
                               "application__interviewSlot__createdBy"))

        sent = 0
        for iv in due:
            app = iv.application
            when = timezone.localtime(iv.scheduledAt).strftime("%d.%m.%Y um %H:%M")
            where = iv.meetingLink or ("vor Ort" if iv.locationType == "IN_PERSON"
                                       else "Details in Ihrer Einladung")

            # 1) Bewerber:in – Mail + Portal-Nachricht
            send_mail(
                f"Erinnerung: Ihr Gespräch am {when} Uhr",
                (f"Guten Tag {app.applicant.firstName},\n\n"
                 f"morgen ist es so weit: Ihr Gespräch zur Stelle "
                 f"'{app.jobPosting.title}' findet am {when} Uhr statt.\n"
                 f"Ort/Link: {where}\n\n"
                 "Falls etwas dazwischenkommt, antworten Sie einfach auf diese "
                 "E-Mail – wir finden einen neuen Termin.\n\nFreundliche Grüße"),
                None, [app.applicant.email], fail_silently=True)
            Message.objects.create(
                application=app, direction="OUTBOUND",
                content=f"Erinnerung: Ihr Gespräch findet am {when} Uhr statt. "
                        f"Ort/Link: {where}")

            # 2) Team: ALLE Beteiligten erinnern (Interview-Team + Slot-Anbieter:in)
            slot = getattr(app, "interviewSlot", None)
            team_emails = {m.email for m in iv.participants.all() if m.email}
            if slot and slot.createdBy_id and slot.createdBy.email:
                team_emails.add(slot.createdBy.email)
            if team_emails:
                send_mail(
                    f"Erinnerung: {iv.kind_label} {when} Uhr – "
                    f"{app.applicant.firstName} {app.applicant.lastName}",
                    (f"Kurze Erinnerung: Am {when} Uhr – {iv.kind_label} mit "
                     f"{app.applicant.firstName} {app.applicant.lastName} "
                     f"({app.jobPosting.title}).\nOrt/Link: {where}\n\n"
                     "Details im Team-Kalender: /recruiter/interviews/"),
                    None, sorted(team_emails), fail_silently=True)

            iv.reminderSentAt = now
            iv.save(update_fields=["reminderSentAt"])
            write_audit("INTERVIEW_REMINDER_SENT", application_id=str(app.id),
                        interview_id=str(iv.id))
            sent += 1

        self.stdout.write(self.style.SUCCESS(
            f"{sent} Erinnerung(en) verschickt (Fenster: {options['hours']} h)."))
