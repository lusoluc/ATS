import os
import sqlite3

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from ats.models import (
    AILearningSample,
    Applicant,
    ApplicantToken,
    Application,
    ApprovalStep,
    ApprovalTicket,
    AppStep,
    AppTicket,
    AppWorkflowDef,
    AuditLog,
    Benefit,
    CareerPath,
    ContactPerson,
    Department,
    DepartmentContactPerson,
    EmailTemplate,
    Facility,
    FacilityContactPerson,
    FacilityProfile,
    Interview,
    InterviewSlot,
    JobAlertLog,
    JobAlertSubscription,
    JobFamily,
    JobPosting,
    JobTemplate,
    Location,
    Message,
    Organization,
    Page,
    PrivacyNoticeVersion,
    Role,
    RoleDelegation,
    ScreeningQuestion,
    SystemSetting,
    TalentPoolSubscription,
    TextSnippet,
    User,
    UserFacility,
    WorkflowDefinition,
    WorkflowState,
)


class Command(BaseCommand):
    help = "Migrates all existing data securely from the old Prisma SQLite database to the new Django schema."

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='frontend/prisma/dev.db',
            help='Path to the source Prisma SQLite database file.'
        )

    def parse_date(self, date_val):
        if not date_val:
            return None
        # SQLite datetime strings might have Z or space
        if isinstance(date_val, (int, float)):
            import datetime
            dt = datetime.datetime.fromtimestamp(date_val / 1000)
        else:
            try:
                date_str = date_val.replace('Z', '+00:00')
                dt = parse_datetime(date_str)
                if not dt:
                    import datetime
                    dt = datetime.datetime.fromisoformat(date_str)
            except Exception:
                return None
        if dt and dt.tzinfo is None:
            dt = make_aware(dt)
        return dt

    def handle(self, *args, **options):
        source_path = options['source']

        if not os.path.exists(source_path):
            self.stdout.write(self.style.ERROR(f"Quell-Datenbank unter '{source_path}' existiert nicht!"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starte Datenmigration aus: {source_path}..."))

        # Connect to source database
        conn = sqlite3.connect(source_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Helper to get all dict rows from table
        def get_rows(table_name):
            try:
                cur.execute(f"SELECT * FROM {table_name}")
                return [dict(row) for row in cur.fetchall()]
            except sqlite3.OperationalError:
                self.stdout.write(self.style.WARNING(f"Tabelle '{table_name}' existiert nicht in Quelle. Überspringe."))
                return []

        try:
            with transaction.atomic():
                # --- TRUNCATE ALL EXISTING TARGET TABLES TO AVOID CONFLICTS ---
                self.stdout.write("Bereinige bestehende Tabellen im Zielsystem...")
                AILearningSample.objects.all().delete()
                AuditLog.objects.all().delete()
                RoleDelegation.objects.all().delete()
                ScreeningQuestion.objects.all().delete()
                EmailTemplate.objects.all().delete()
                SystemSetting.objects.all().delete()
                JobAlertLog.objects.all().delete()
                JobAlertSubscription.objects.all().delete()
                Page.objects.all().delete()
                TalentPoolSubscription.objects.all().delete()
                Message.objects.all().delete()
                InterviewSlot.objects.all().delete()
                Interview.objects.all().delete()
                AppStep.objects.all().delete()
                AppTicket.objects.all().delete()
                AppWorkflowDef.objects.all().delete()
                Application.objects.all().delete()
                ApplicantToken.objects.all().delete()
                Applicant.objects.all().delete()
                ApprovalStep.objects.all().delete()
                ApprovalTicket.objects.all().delete()
                WorkflowDefinition.objects.all().delete()
                JobPosting.objects.all().delete()
                TextSnippet.objects.all().delete()
                Benefit.objects.all().delete()
                JobTemplate.objects.all().delete()
                UserFacility.objects.all().delete()
                User.objects.all().delete()
                Role.objects.all().delete()
                PrivacyNoticeVersion.objects.all().delete()
                WorkflowState.objects.all().delete()
                DepartmentContactPerson.objects.all().delete()
                FacilityContactPerson.objects.all().delete()
                ContactPerson.objects.all().delete()
                CareerPath.objects.all().delete()
                JobFamily.objects.all().delete()
                Location.objects.all().delete()
                Department.objects.all().delete()
                FacilityProfile.objects.all().delete()
                Facility.objects.all().delete()
                Organization.objects.all().delete()

                # --- 1. MIGRATION LEVEL 1: Independent Tables ---
                self.stdout.write("Migriere Level 1: Unabhängige Stammdaten...")

                # Organization
                for r in get_rows('Organization'):
                    Organization.objects.create(id=r['id'], name=r['name'], createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt']))

                # Location
                for r in get_rows('Location'):
                    Location.objects.create(
                        id=r['id'], name=r['name'], address=r['address'], city=r['city'], postalCode=r['postalCode'],
                        lat=r['lat'], lng=r['lng'], archived=bool(r['archived']),
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # JobFamily
                for r in get_rows('JobFamily'):
                    JobFamily.objects.create(
                        id=r['id'], name=r['name'], description=r['description'], archived=bool(r['archived']),
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # CareerPath
                for r in get_rows('CareerPath'):
                    CareerPath.objects.create(
                        id=r['id'], name=r['name'], description=r['description'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # ContactPerson
                for r in get_rows('ContactPerson'):
                    ContactPerson.objects.create(
                        id=r['id'], firstName=r['firstName'], lastName=r['lastName'], email=r['email'],
                        phone=r['phone'], photoUrl=r['photoUrl'], quote=r['quote'], globalJobTitle=r['globalJobTitle'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # WorkflowState
                for r in get_rows('WorkflowState'):
                    WorkflowState.objects.create(
                        id=r['id'], name=r['name'], description=r['description'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # PrivacyNoticeVersion
                for r in get_rows('PrivacyNoticeVersion'):
                    PrivacyNoticeVersion.objects.create(
                        id=r['id'], version=r['version'], content=r['content'], active=bool(r['active']),
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Role
                for r in get_rows('Role'):
                    Role.objects.create(
                        id=r['id'], name=r['name'], description=r['description'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # JobTemplate
                for r in get_rows('JobTemplate'):
                    JobTemplate.objects.create(
                        id=r['id'], title=r['title'], content=r['content'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Benefit
                for r in get_rows('Benefit'):
                    Benefit.objects.create(id=r['id'], name=r['name'], icon=r['icon'], description=r['description'])

                # ScreeningQuestion
                for r in get_rows('ScreeningQuestion'):
                    ScreeningQuestion.objects.create(
                        id=r['id'], question=r['question'], archived=bool(r['archived']), createdAt=self.parse_date(r['createdAt'])
                    )

                # SystemSetting
                for r in get_rows('SystemSetting'):
                    SystemSetting.objects.create(id=r['id'], key=r['key'], value=r['value'], updatedAt=self.parse_date(r['updatedAt']))

                # EmailTemplate
                for r in get_rows('EmailTemplate'):
                    EmailTemplate.objects.create(
                        id=r['id'], name=r['name'], subject=r['subject'], htmlContent=r['htmlContent'],
                        textContent=r['textContent'], updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Page
                for r in get_rows('Page'):
                    Page.objects.create(
                        id=r['id'], title=r['title'], slug=r['slug'], content=r['content'], status=r['status'],
                        navEnabled=bool(r['navEnabled']), navLabel=r['navLabel'], navParent=r['navParent'],
                        navOrder=r['navOrder'], metaDesc=r['metaDesc'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # JobAlertSubscription
                for r in get_rows('JobAlertSubscription'):
                    JobAlertSubscription.objects.create(
                        id=r['id'], email=r['email'], status=r['status'], globalAlert=bool(r['globalAlert']),
                        categories=r['categories'], locations=r['locations'], radiusKm=r['radiusKm'],
                        confirmationToken=r['confirmationToken'], managementToken=r['managementToken'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt']),
                        lastConfirmedAt=self.parse_date(r['lastConfirmedAt']), lastAlertSentAt=self.parse_date(r['lastAlertSentAt'])
                    )

                # Applicant (Contains PII - Django Field auto-encrypts!)
                for r in get_rows('Applicant'):
                    Applicant.objects.create(
                        id=r['id'], firstName=r['firstName'], lastName=r['lastName'], email=r['email'], phone=r['phone'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # TalentPoolSubscription
                for r in get_rows('TalentPoolSubscription'):
                    TalentPoolSubscription.objects.create(
                        id=r['id'], email=r['email'], criteria=r['criteria'], consentId=r['consentId'],
                        expiresAt=self.parse_date(r['expiresAt']), createdAt=self.parse_date(r['createdAt']),
                        updatedAt=self.parse_date(r['updatedAt'])
                    )

                # AuditLog
                for r in get_rows('AuditLog'):
                    AuditLog.objects.create(
                        id=r['id'], action=r['action'], userId=r['userId'], applicationId=r['applicationId'],
                        metadataJson=r['metadataJson'], createdAt=self.parse_date(r['createdAt'])
                    )

                # --- 2. MIGRATION LEVEL 2: Simple relations ---
                self.stdout.write("Migriere Level 2: Einfache Relationen...")

                # Facility
                for r in get_rows('Facility'):
                    Facility.objects.create(
                        id=r['id'], name=r['name'], description=r['description'],
                        organization_id=r['organizationId'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # User
                for r in get_rows('User'):
                    User.objects.create(
                        id=r['id'], email=r['email'], passwordHash=r['passwordHash'], role_id=r['roleId'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # ApplicantToken
                for r in get_rows('ApplicantToken'):
                    ApplicantToken.objects.create(
                        id=r['id'], token=r['token'], applicant_id=r['applicantId'],
                        expiresAt=self.parse_date(r['expiresAt']), createdAt=self.parse_date(r['createdAt'])
                    )

                # JobAlertLog
                for r in get_rows('JobAlertLog'):
                    JobAlertLog.objects.create(
                        id=r['id'], subscription_id=r['subscriptionId'], action=r['action'],
                        metadata=r['metadata'], createdAt=self.parse_date(r['createdAt'])
                    )

                # TextSnippet
                for r in get_rows('TextSnippet'):
                    TextSnippet.objects.create(
                        id=r['id'], category=r['category'], content=r['content'],
                        jobFamily_id=r['jobFamilyId'], createdAt=self.parse_date(r['createdAt'])
                    )

                # --- 3. MIGRATION LEVEL 3: Core relations ---
                self.stdout.write("Migriere Level 3: Core-Relationen...")

                # FacilityProfile
                for r in get_rows('FacilityProfile'):
                    FacilityProfile.objects.create(
                        id=r['id'], facility_id=r['facilityId'], description=r['description'],
                        images=r['images'], slug=r['slug'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Department
                for r in get_rows('Department'):
                    Department.objects.create(
                        id=r['id'], name=r['name'], description=r['description'], slug=r['slug'],
                        facility_id=r['facilityId'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # UserFacility
                for r in get_rows('UserFacility'):
                    UserFacility.objects.create(id=r['id'], user_id=r['userId'], facility_id=r['facilityId'])

                # FacilityContactPerson
                for r in get_rows('FacilityContactPerson'):
                    FacilityContactPerson.objects.create(
                        id=r['id'], facility_id=r['facilityId'], contactPerson_id=r['contactPersonId'], roleTitle=r['roleTitle']
                    )

                # WorkflowDefinition
                for r in get_rows('WorkflowDefinition'):
                    WorkflowDefinition.objects.create(
                        id=r['id'], name=r['name'], facility_id=r['facilityId'],
                        stepsJson=r['stepsJson'], createdAt=self.parse_date(r['createdAt'])
                    )

                # AppWorkflowDef
                for r in get_rows('AppWorkflowDef'):
                    AppWorkflowDef.objects.create(
                        id=r['id'], name=r['name'], facility_id=r['facilityId'],
                        locationIdsJson=r['locationIdsJson'], categoryIdsJson=r['categoryIdsJson'],
                        jobIdsJson=r['jobIdsJson'], stepsJson=r['stepsJson'],
                        createdAt=self.parse_date(r['createdAt'])
                    )

                # RoleDelegation: seit WP3 auf Django-Auth-User umgestellt.
                # Alt-Datensätze referenzieren Prisma-User-UUIDs und sind nicht
                # automatisch zuordenbar -> bewusst übersprungen (manuell neu anlegen).
                skipped_delegations = len(get_rows('RoleDelegation'))
                if skipped_delegations:
                    self.stdout.write(self.style.WARNING(
                        f"RoleDelegation: {skipped_delegations} Alt-Einträge übersprungen "
                        "(FK zeigt jetzt auf Django-Auth-User)."))

                # --- 4. MIGRATION LEVEL 4: Department Link & JobPosting ---
                self.stdout.write("Migriere Level 4: Jobs & Abteilungskontakte...")

                # DepartmentContactPerson
                for r in get_rows('DepartmentContactPerson'):
                    DepartmentContactPerson.objects.create(
                        id=r['id'], department_id=r['departmentId'], contactPerson_id=r['contactPersonId'], roleTitle=r['roleTitle']
                    )

                # JobPosting
                for r in get_rows('JobPosting'):
                    JobPosting.objects.create(
                        id=r['id'], title=r['title'], description=r['description'],
                        tasksJson=r['tasksJson'], requirementsJson=r['requirementsJson'],
                        screeningQuestionsJson=r['screeningQuestionsJson'],
                        contactPerson_id=r['contactPersonId'], organization_id=r['organizationId'],
                        facility_id=r['facilityId'], department_id=r['departmentId'],
                        location_id=r['locationId'], jobFamily_id=r['jobFamilyId'],
                        workflowState_id=r['workflowStateId'], jobTemplate_id=r['jobTemplateId'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Many-to-Many: Benefit to JobPosting (Prisma Implicit _BenefitToJobPosting)
                benefit_m2m = get_rows('_BenefitToJobPosting')
                for edge in benefit_m2m:
                    try:
                        job = JobPosting.objects.get(id=edge['B'])
                        benefit = Benefit.objects.get(id=edge['A'])
                        job.benefits.add(benefit)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"M2M-Mapping fehlgeschlagen für Benefit {edge.get('A')} -> Job {edge.get('B')}: {str(e)}"))

                # --- 5. MIGRATION LEVEL 5: Tickets, Slots, Applications ---
                self.stdout.write("Migriere Level 5: Bewerbungen & Tickets...")

                # ApprovalTicket
                for r in get_rows('ApprovalTicket'):
                    ApprovalTicket.objects.create(
                        id=r['id'], jobPosting_id=r['jobPostingId'], status=r['status'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Application (Contains PII - Django ORM auto-encrypts!)
                for r in get_rows('Application'):
                    Application.objects.create(
                        id=r['id'], applicant_id=r['applicantId'], jobPosting_id=r['jobPostingId'],
                        cvStorageId=r['cvStorageId'], coverLetterTxt=r['coverLetterTxt'],
                        screeningAnswersJson=r['screeningAnswersJson'],
                        aiScore=r['aiScore'], aiRationale=r['aiRationale'],
                        status=r['status'], withdrawReason=r['withdrawReason'],
                        privacyNoticeVersion_id=r['privacyNoticeVersionId'],
                        consentTalentPool=bool(r['consentTalentPool']), internalNotes=r['internalNotes'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # --- 6. MIGRATION LEVEL 6: Steps & Interviews ---
                self.stdout.write("Migriere Level 6: Schritte & Interviews...")

                # ApprovalStep
                for r in get_rows('ApprovalStep'):
                    ApprovalStep.objects.create(
                        id=r['id'], approvalTicket_id=r['approvalTicketId'], stepOrder=r['stepOrder'],
                        assignedRoleId=r['assignedRoleId'], assignedUserId=r['assignedUserId'],
                        status=r['status'], comments=r['comments'],
                        actionTakenAt=self.parse_date(r['actionTakenAt']), actionTakenBy_id=r['actionTakenById']
                    )

                # AppTicket
                for r in get_rows('AppTicket'):
                    AppTicket.objects.create(
                        id=r['id'], application_id=r['applicationId'], workflow_id=r['workflowId'],
                        status=r['status'], createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # Interview
                for r in get_rows('Interview'):
                    Interview.objects.create(
                        id=r['id'], application_id=r['applicationId'], scheduledAt=self.parse_date(r['scheduledAt']),
                        locationType=r['locationType'], meetingLink=r['meetingLink'], outcome=r['outcome'],
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # InterviewSlot
                for r in get_rows('InterviewSlot'):
                    InterviewSlot.objects.create(
                        id=r['id'], jobPosting_id=r['jobPostingId'],
                        startTime=self.parse_date(r['startTime']), endTime=self.parse_date(r['endTime']),
                        isBooked=bool(r['isBooked']), application_id=r['applicationId'],
                        createdAt=self.parse_date(r['createdAt'])
                    )

                # Message
                for r in get_rows('Message'):
                    Message.objects.create(
                        id=r['id'], application_id=r['applicationId'], direction=r['direction'],
                        content=r['content'], readStatus=bool(r['readStatus']),
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

                # AILearningSample
                for r in get_rows('AILearningSample'):
                    AILearningSample.objects.create(
                        id=r['id'], application_id=r['applicationId'], categoryId=r['categoryId'],
                        facilityId=r['facilityId'], feedbackType=r['feedbackType'],
                        anonymizedProfileJson=r['anonymizedProfileJson'], createdAt=self.parse_date(r['createdAt'])
                    )

                # --- 7. MIGRATION LEVEL 7: AppSteps ---
                self.stdout.write("Migriere Level 7: App-Arbeitsablauf-Schritte...")

                # AppStep
                for r in get_rows('AppStep'):
                    AppStep.objects.create(
                        id=r['id'], appTicket_id=r['appTicketId'], stepOrder=r['stepOrder'],
                        assignedUser_id=r['assignedUserId'], status=r['status'], comments=r['comments'],
                        actionTakenAt=self.parse_date(r['actionTakenAt']),
                        createdAt=self.parse_date(r['createdAt']), updatedAt=self.parse_date(r['updatedAt'])
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ TRANS-FEHLER: Fehler bei Datenübertragung. Rollback ausgeführt! Detail: {str(e)}"))
            raise e

        # Success message
        self.stdout.write(self.style.SUCCESS("DATEN-MIGRATION ERFOLGREICH BEENDET!"))
        self.stdout.write(self.style.SUCCESS("Alle Prisma-Datensätze wurden sauber in Ihr neues Django-System geladen."))
