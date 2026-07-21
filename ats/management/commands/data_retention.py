import datetime

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ats.models import Application


class Command(BaseCommand):
    help = "Performs GDPR-compliant (DSGVO) anonymization of rejected candidates older than 6 months who did not opt-in to the talent pool."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=180,  # 6 months
            help='Anonymize applications rejected older than this number of days.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate anonymization without making changes to the database.'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        self.stdout.write(self.style.WARNING(f"Staging anonymization for applications before: {cutoff_date}"))

        # Find applications matching DSGVO criteria:
        # Rejected or Withdrawn, older than cutoff, and did not consent to talent pool retention
        apps_to_anonymize = Application.objects.filter(
            status__in=['REJECTED', 'WITHDRAWN'],
            updatedAt__lt=cutoff_date,
            consentTalentPool=False
        ).select_related('applicant')

        count = apps_to_anonymize.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Keine zu anonymisierenden Bewerbungen gefunden. DSGVO konform!"))
            return

        self.stdout.write(self.style.WARNING(f"Gefundene Datensätze für Anonymisierung: {count}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("[DRY-RUN] Keine Änderungen vorgenommen."))
            for app in apps_to_anonymize:
                self.stdout.write(f"  -> Würde anonymisieren: App ID {app.id} (Kandidat: {app.applicant.email})")
            return

        anonymized_count = 0
        with transaction.atomic():
            for app in apps_to_anonymize:
                applicant = app.applicant

                # Delete uploaded CV from local storage
                if app.cvStorageId:
                    try:
                        if default_storage.exists(app.cvStorageId):
                            default_storage.delete(app.cvStorageId)
                            self.stdout.write(f"Lebenslauf gelöscht: {app.cvStorageId}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Fehler beim Löschen des Lebenslaufs {app.cvStorageId}: {str(e)}"))

                # 1. Anonymize Application fields
                app.coverLetterTxt = "ANONYMISIERT"
                app.screeningAnswersJson = {}
                app.internalNotes = "Dieser Datensatz wurde gemäß DSGVO-Vorgaben anonymisiert."
                app.cvStorageId = None
                app.save()

                # 2. Anonymize Applicant fields if they have no other active applications
                other_active_apps = Application.objects.filter(
                    applicant=applicant
                ).exclude(id=app.id).exclude(status__in=['REJECTED', 'WITHDRAWN'])

                if not other_active_apps.exists():
                    applicant.firstName = "Maximilian/a"
                    applicant.lastName = "Anonymisiert"
                    # Generate a unique anonymous email to preserve unique database index
                    applicant.email = f"anon-{app.id}@securats.de"
                    applicant.phone = None
                    applicant.save()
                    self.stdout.write(f"Bewerber-Details anonymisiert: {applicant.id}")

                anonymized_count += 1

                # Write AuditLog (in Integritätskette)
                from ats.audit import write_audit
                write_audit("ANONYMIZE_DSGVO", application_id=str(app.id),
                            days_threshold=days)

        self.stdout.write(self.style.SUCCESS(f"Erfolgreich anonymisiert: {anonymized_count} Datensätze."))
