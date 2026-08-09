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

from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.mail_send import send_notice
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

        sent = fehlgeschlagen = 0
        for iv in due:
            app = iv.application
            when = timezone.localtime(iv.scheduledAt).strftime("%d.%m.%Y um %H:%M")
            where = iv.meetingLink or ("vor Ort" if iv.locationType == "IN_PERSON"
                                       else "Details in Ihrer Einladung")

            # 1) Bewerber:in – Mail + Portal-Nachricht
            zugestellt = send_notice(
                f"Erinnerung: Ihr Gespräch am {when} Uhr",
                (f"Guten Tag {app.applicant.firstName},\n\n"
                 f"morgen ist es so weit: Ihr Gespräch zur Stelle "
                 f"'{app.jobPosting.title}' findet am {when} Uhr statt.\n"
                 f"Ort/Link: {where}\n\n"
                 "Falls etwas dazwischenkommt, antworten Sie einfach auf diese "
                 "E-Mail – wir finden einen neuen Termin.\n\nFreundliche Grüße"),
                None, [app.applicant.email], context="Termin-Erinnerung")
            if not zugestellt:
                # Weder Marker noch Portal-Nachricht: Der naechste Lauf
                # wiederholt beides zusammen. Vorher galt die Erinnerung als
                # verschickt, sobald der VERSUCH stattgefunden hatte - ein
                # Mailserver-Ausfall am Morgen hiess: niemand erinnert die
                # Person je wieder, und das Audit behauptete das Gegenteil.
                fehlgeschlagen += 1
                continue
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
                team_ok = send_notice(
                    f"Erinnerung: {iv.kind_label} {when} Uhr – "
                    f"{app.applicant.firstName} {app.applicant.lastName}",
                    (f"Kurze Erinnerung: Am {when} Uhr – {iv.kind_label} mit "
                     f"{app.applicant.firstName} {app.applicant.lastName} "
                     f"({app.jobPosting.title}).\nOrt/Link: {where}\n\n"
                     "Details im Team-Kalender: /recruiter/interviews/"),
                    None, sorted(team_emails), context="Termin-Erinnerung")
                if not team_ok:
                    # Zaehlt als Fehlschlag, verhindert den Marker aber nicht:
                    # Die bewerbende Person ist erinnert; sie morgen erneut
                    # anzuschreiben, weil das TEAM nicht erreichbar war, waere
                    # der falsche Preis.
                    fehlgeschlagen += 1

            iv.reminderSentAt = now
            iv.save(update_fields=["reminderSentAt"])
            write_audit("INTERVIEW_REMINDER_SENT", application_id=str(app.id),
                        interview_id=str(iv.id))
            sent += 1

        self.stdout.write(self.style.SUCCESS(
            f"{sent} Erinnerung(en) zugestellt, {fehlgeschlagen} fehlgeschlagen "
            f"(Fenster: {options['hours']} h)."))
        if fehlgeschlagen and not sent:
            from django.core.management.base import CommandError
            raise CommandError(
                f"Keine einzige von {fehlgeschlagen} Erinnerung(en) zugestellt - "
                "Mailversand pruefen (Einstellungen -> E-Mail-Versand).")
