"""DSGVO-Betroffenenauskunft: Export aller Daten einer Person (UC-MB-07/UC-AY-09)."""
import json

from django.core.management.base import BaseCommand, CommandError

from ats.audit import write_audit
from ats.dsgvo import build_applicant_export
from ats.models import Applicant


class Command(BaseCommand):
    help = "Exportiert alle zu einer E-Mail gespeicherten Personendaten als JSON."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--out", help="Zieldatei (Default: stdout)")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        try:
            applicant = Applicant.objects.get_by_email(email)  # Blind-Index-Lookup
        except Applicant.DoesNotExist as exc:
            raise CommandError(f"Keine Person mit E-Mail {email} gefunden.") from exc
        data = build_applicant_export(applicant)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        write_audit("DATA_EXPORT", application_id=None, subject_email=email)
        if options.get("out"):
            with open(options["out"], "w", encoding="utf-8") as fh:
                fh.write(payload)
            self.stdout.write(self.style.SUCCESS(f"Export geschrieben: {options['out']}"))
        else:
            self.stdout.write(payload)
