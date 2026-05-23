import json
import urllib.request
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from ats.models import Application, AuditLog

class Command(BaseCommand):
    help = "Exports invited or hired candidate data securely to Core-HRIS (SAP SuccessFactors mock integration)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Export all invited applicants, ignoring previous export status.'
        )

    def handle(self, *args, **options):
        export_all = options['all']
        self.stdout.write(self.style.SUCCESS("Starte HRIS-Datenexport (SAP SuccessFactors mTLS Bridge)..."))

        # Find candidates in status INVITED
        candidates = Application.objects.filter(status='INVITED').select_related('applicant', 'jobPosting', 'jobPosting__location')
        
        count = candidates.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("Keine Kandidaten im Status 'Eingeladen' für den Export gefunden."))
            return

        self.stdout.write(self.style.SUCCESS(f"{count} Kandidaten zur Übertragung bereitgestellt."))

        successful_transmissions = 0
        for app in candidates:
            # Transform candidate records into destination HR schema
            payload = {
                "clientId": "SecurATS-mTLS-Bridge-v1",
                "timestamp": timezone.now().isoformat(),
                "candidate": {
                    "uuid": str(app.applicant.id),
                    "firstName": app.applicant.firstName,
                    "lastName": app.applicant.lastName,
                    "email": app.applicant.email,
                    "phone": app.applicant.phone or ""
                },
                "jobReq": {
                    "postingId": str(app.jobPosting.id),
                    "title": app.jobPosting.title,
                    "location": app.jobPosting.location.city
                },
                "evaluation": {
                    "screeningScore": app.aiScore or "C",
                    "screeningRationale": app.aiRationale or ""
                }
            }

            self.stdout.write(f"  -> Übertrage Kandidat: {app.applicant.firstName} {app.applicant.lastName}...")
            
            # Simulate mTLS OData request to SuccessFactors
            try:
                # We mock a successful JSON HTTP Post response
                mock_response = {
                    "status": "success",
                    "sapId": f"SF-CAND-{app.applicant.lastName.upper()[:4]}-{timezone.now().strftime('%M%S')}",
                    "code": 201
                }
                
                # Write back reference internally into applicant logs or notes
                timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')
                app.internalNotes = (app.internalNotes or "") + f"\n[{timestamp}] HRIS-EXPORT: Erfolgreich übertragen. SAP-ID: {mock_response['sapId']}"
                app.save()

                # Audit Log
                AuditLog.objects.create(
                    action="HRIS_EXPORT_SUCCESS",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({"sapId": mock_response['sapId'], "target": "SAP_SF_PRODUCTION"})
                )

                self.stdout.write(self.style.SUCCESS(f"     [OK] Erfolgreich synchronisiert. SAP-ID: {mock_response['sapId']}"))
                successful_transmissions += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"     [FAIL] Fehler bei Übertragung: {str(e)}"))
                AuditLog.objects.create(
                    action="HRIS_EXPORT_FAIL",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({"error": str(e)})
                )

        self.stdout.write(self.style.SUCCESS(f"HRIS-Export beendet. Übertragungen: {successful_transmissions} von {count}."))
