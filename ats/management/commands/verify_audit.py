"""Prüft die Integrität der Audit-Log-Hashkette (UC-MB-12, UC-NS-02)."""
from django.core.management.base import BaseCommand

from ats.audit import verify_audit_chain


class Command(BaseCommand):
    help = "Verifiziert die Integrität (Hash-Kette) des Audit-Logs."

    def handle(self, *args, **options):
        r = verify_audit_chain()
        if r["ok"]:
            self.stdout.write(self.style.SUCCESS(
                f"Audit-Kette intakt. Geprüft: {r['checked']}, "
                f"ohne Hash (Alt-Einträge): {r['unchained']}."))
        else:
            self.stdout.write(self.style.ERROR(
                f"INTEGRITÄTSBRUCH bei Eintrag {r['broken_id']} "
                f"(nach {r['checked']} gültigen Einträgen)."))
