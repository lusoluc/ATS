"""Prüft die Integrität der Audit-Log-Hashkette (UC-MB-12, UC-NS-02).

Ein Bruch beendet das Kommando mit einem FEHLER (CommandError, Exit-Code 1).
Vorher wurde er nur als Text gemeldet und das Kommando endete mit 0 — der
Zeitplan-Dienst vermerkte den Lauf damit als "in Ordnung". Ausgerechnet der
Job, der Manipulation erkennen soll, hätte sie grün abgehakt: Cron und
Monitoring reagieren auf Exit-Codes, nicht auf Textfarben.

Zusätzlich geht bei einem Bruch eine Nachricht an alle HR-Admins mit
hinterlegter Adresse — Datenschutzbeauftragte und Betriebsrat müssen davon
erfahren, bevor jemand den Nachweis braucht.
"""
from django.core.management.base import BaseCommand, CommandError

from ats.audit import verify_audit_chain


class Command(BaseCommand):
    help = "Verifiziert die Integrität (Hash-Kette) des Audit-Logs."

    def handle(self, *args, **options):
        r = verify_audit_chain()
        if r["ok"]:
            self.stdout.write(self.style.SUCCESS(
                f"Audit-Kette intakt. Geprüft: {r['checked']}, "
                f"ohne Hash (Alt-Einträge): {r['unchained']}."))
            return

        befund = (f"INTEGRITÄTSBRUCH bei Eintrag {r['broken_id']} "
                  f"(nach {r['checked']} gültigen Einträgen).")
        self.stdout.write(self.style.ERROR(befund))

        # Menschen alarmieren, bevor der Fehler-Vermerk untergeht. Der
        # Versand ist Beigabe — die Meldung, auf die Cron und Scheduler
        # reagieren, ist der CommandError unten. Ein Versandfehler darf den
        # deshalb nicht verhindern; send_notice wirft nicht.
        from django.contrib.auth.models import Group

        from ats.mail_send import send_notice
        admins = Group.objects.filter(name="HR-Admin").first()
        adressen = ([u.email for u in admins.user_set.all() if u.email]
                    if admins else [])
        if adressen:
            send_notice(
                "SecurATS: Integritätsbruch im Audit-Log",
                befund + "\n\n"
                "Das Protokoll ist ab dieser Stelle als Nachweis nicht mehr "
                "belastbar. Bitte Datenschutzbeauftragte und Betriebsrat "
                "informieren. Details: Einstellungen -> Audit-Log -> "
                "Integrität prüfen.",
                None, adressen, context="Audit-Integritätsalarm")

        raise CommandError(befund)
