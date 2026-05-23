import uuid
import base64
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from cryptography.fernet import Fernet

# Helper to get a secure Fernet cipher using the settings key
def get_fernet_cipher():
    key_str = getattr(settings, 'PII_ENCRYPTION_KEY', 'securats-fallback-super-secure-encryption-key-for-pii-at-rest=')
    key_hash = hashlib.sha256(key_str.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(key_hash)
    return Fernet(key_b64)

class EncryptedCharField(models.CharField):
    """CharField that encrypts data at-rest using Fernet."""
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        cipher = get_fernet_cipher()
        return cipher.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        cipher = get_fernet_cipher()
        try:
            return cipher.decrypt(value.encode()).decode()
        except Exception:
            return value  # Return as-is if decryption fails (e.g. migration / unencrypted legacy)

class EncryptedTextField(models.TextField):
    """TextField that encrypts data at-rest using Fernet."""
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        cipher = get_fernet_cipher()
        return cipher.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        cipher = get_fernet_cipher()
        try:
            return cipher.decrypt(value.encode()).decode()
        except Exception:
            return value

# ============================================================================
# 1. ORGANIZATION DOMAIN
# ============================================================================

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Facility(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='facilities')
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Facilities"

    def __str__(self):
        return self.name

class FacilityProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.OneToOneField(Facility, on_delete=models.CASCADE, related_name='profile')
    description = models.TextField(blank=True, null=True)
    images = models.TextField(default="[]")  # JSON string
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.facility.name}"

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='departments')
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.facility.name})"

class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class JobFamily(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Job Families"

    def __str__(self):
        return self.name

class CareerPath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ContactPerson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    photoUrl = models.CharField(max_length=255, blank=True, null=True)
    quote = models.TextField(blank=True, null=True)
    globalJobTitle = models.CharField(max_length=150, blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName}"

class FacilityContactPerson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='contacts')
    contactPerson = models.ForeignKey(ContactPerson, on_delete=models.CASCADE, related_name='facility_links')
    roleTitle = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        unique_together = ('facility', 'contactPerson')

    def __str__(self):
        return f"{self.contactPerson} at {self.facility}"

class DepartmentContactPerson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='contacts')
    contactPerson = models.ForeignKey(ContactPerson, on_delete=models.CASCADE, related_name='department_links')
    roleTitle = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        unique_together = ('department', 'contactPerson')

    def __str__(self):
        return f"{self.contactPerson} in {self.department}"


# ============================================================================
# 2. GOVERNANCE & SECURITY DOMAIN
# ============================================================================

class WorkflowState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PrivacyNoticeVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=50)
    content = models.TextField()
    active = models.BooleanField(default=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Version {self.version}"

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    passwordHash = models.CharField(max_length=255, default="")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class UserFacility(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_facilities')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='user_facilities')

    class Meta:
        unique_together = ('user', 'facility')

    def __str__(self):
        return f"{self.user} - {self.facility}"


# ============================================================================
# 3. JOB DOMAIN & MODULARITY
# ============================================================================

class JobTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Benefit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class TextSnippet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=100)  # TASKS, REQUIREMENTS, INTRO
    content = models.TextField()
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.SET_NULL, blank=True, null=True, related_name='textSnippets')
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.category} Snippet"

class JobPosting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    tasksJson = models.TextField(default="[]")
    requirementsJson = models.TextField(default="[]")
    screeningQuestionsJson = models.TextField(default="[]")

    contactPerson = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, blank=True, null=True, related_name='jobPostings')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='jobPostings')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='jobPostings')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name='jobPostings')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='jobPostings')
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.CASCADE, related_name='jobPostings')
    workflowState = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name='jobPostings')
    jobTemplate = models.ForeignKey(JobTemplate, on_delete=models.SET_NULL, blank=True, null=True, related_name='jobPostings')
    benefits = models.ManyToManyField(Benefit, related_name='jobPostings', blank=True)

    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ============================================================================
# WORKFLOW & APPROVAL ENGINE
# ============================================================================

class WorkflowDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='workflows')
    stepsJson = models.TextField(default="[]")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class ApprovalTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jobPosting = models.OneToOneField(JobPosting, on_delete=models.CASCADE, related_name='approvalTicket')
    status = models.CharField(max_length=50, default="PENDING")
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket for {self.jobPosting.title}"

class ApprovalStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    approvalTicket = models.ForeignKey(ApprovalTicket, on_delete=models.CASCADE, related_name='steps')
    stepOrder = models.IntegerField()
    assignedRoleId = models.CharField(max_length=255, blank=True, null=True)
    assignedUserId = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, default="PENDING")
    comments = models.TextField(blank=True, null=True)
    actionTakenAt = models.DateTimeField(blank=True, null=True)
    actionTakenBy = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='approvalSteps')

    def __str__(self):
        return f"Step {self.stepOrder} for {self.approvalTicket}"


# ============================================================================
# 4. APPLICATION DOMAIN (ATS & Workflow)
# ============================================================================

class Applicant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = EncryptedCharField(max_length=100)
    lastName = EncryptedCharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = EncryptedCharField(max_length=50, blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName}"

class ApplicantToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=255, unique=True)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='tokens')
    expiresAt = models.DateTimeField()
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Token for {self.applicant}"

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='applications')
    jobPosting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    
    cvStorageId = models.CharField(max_length=255, blank=True, null=True)
    coverLetterTxt = EncryptedTextField(blank=True, null=True)
    screeningAnswersJson = models.TextField(default="{}")

    aiScore = models.CharField(max_length=10, blank=True, null=True)  # A, B, C, D
    aiRationale = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=50, default="NEW")  # NEW, IN_REVIEW, MISSING_DOCS, INVITED, REJECTED, WITHDRAWN
    withdrawReason = models.TextField(blank=True, null=True)
    
    privacyNoticeVersion = models.ForeignKey(PrivacyNoticeVersion, on_delete=models.SET_NULL, blank=True, null=True, related_name='applications')
    consentTalentPool = models.BooleanField(default=False)
    internalNotes = models.TextField(default="", blank=True)

    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application by {self.applicant} for {self.jobPosting}"

class AppWorkflowDef(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='appWorkflows', blank=True, null=True)
    locationIdsJson = models.TextField(default="[]")
    categoryIdsJson = models.TextField(default="[]")
    jobIdsJson = models.TextField(default="[]")
    stepsJson = models.TextField(default="[]")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class AppTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='appTicket')
    workflow = models.ForeignKey(AppWorkflowDef, on_delete=models.CASCADE, related_name='appTickets')
    status = models.CharField(max_length=50, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, CANCELLED
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AppTicket for {self.application}"

class AppStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appTicket = models.ForeignKey(AppTicket, on_delete=models.CASCADE, related_name='steps')
    stepOrder = models.IntegerField()
    assignedUser = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='appSteps')
    status = models.CharField(max_length=50, default="PENDING")  # PENDING, APPROVED, REJECTED, RETURNED
    comments = models.TextField(blank=True, null=True)
    actionTakenAt = models.DateTimeField(blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AppStep {self.stepOrder} for {self.appTicket}"

class Interview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    scheduledAt = models.DateTimeField()
    locationType = models.CharField(max_length=50)  # REMOTE, IN_PERSON
    meetingLink = models.CharField(max_length=255, blank=True, null=True)
    outcome = models.CharField(max_length=50, blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interview on {self.scheduledAt}"

class InterviewSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jobPosting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='interviewSlots')
    startTime = models.DateTimeField()
    endTime = models.DateTimeField()
    isBooked = models.BooleanField(default=False)
    application = models.OneToOneField(Application, on_delete=models.SET_NULL, blank=True, null=True, related_name='interviewSlot')
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Slot {self.startTime} - {self.endTime}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    direction = models.CharField(max_length=20)  # INBOUND, OUTBOUND
    content = models.TextField()
    readStatus = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message {self.direction} - {self.createdAt}"

class TalentPoolSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    criteria = models.TextField(default="{}")
    consentId = models.CharField(max_length=255)
    expiresAt = models.DateTimeField()
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


# ============================================================================
# CMS PAGE MANAGEMENT
# ============================================================================

class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(default="")
    status = models.CharField(max_length=50, default="published")  # published, draft, archived
    navEnabled = models.BooleanField(default=True)
    navLabel = models.CharField(max_length=150, blank=True, null=True)
    navParent = models.CharField(max_length=255, blank=True, null=True)
    navOrder = models.IntegerField(default=0)
    metaDesc = models.TextField(blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ============================================================================
# 6. JOB ALERTS SUBSYSTEM
# ============================================================================

class JobAlertSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=50, default="PENDING")  # PENDING, ACTIVE, INACTIVE

    globalAlert = models.BooleanField(default=False)
    categories = models.TextField(default="[]")
    locations = models.TextField(default="[]")
    radiusKm = models.IntegerField(blank=True, null=True)

    confirmationToken = models.CharField(max_length=255, unique=True, blank=True, null=True)
    managementToken = models.CharField(max_length=255, unique=True, blank=True, null=True)

    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)
    lastConfirmedAt = models.DateTimeField(default=timezone.now)
    lastAlertSentAt = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.email

class JobAlertLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(JobAlertSubscription, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    metadata = models.TextField(default="{}")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Log for {self.subscription.email} - {self.action}"


# ============================================================================
# 7. SYSTEM SETTINGS & TEMPLATES
# ============================================================================

class SystemSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key

class EmailTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255)
    htmlContent = models.TextField()
    textContent = models.TextField(blank=True, null=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ScreeningQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    archived = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question


# ============================================================================
# 8. IAM & DELEGATION OF AUTHORITY
# ============================================================================

class RoleDelegation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delegator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegationsGiven')
    delegatee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegationsReceived')
    scopeType = models.CharField(max_length=50)  # ALL, FACILITY, JOB
    scopeId = models.CharField(max_length=255, blank=True, null=True)
    validFrom = models.DateTimeField()
    validUntil = models.DateTimeField()
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('delegator', 'delegatee', 'scopeType', 'scopeId')

    def __str__(self):
        return f"Delegation from {self.delegator} to {self.delegatee}"


# ============================================================================
# 9. AUDIT & COMPLIANCE
# ============================================================================

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=100)  # READ_CV, STATUS_CHANGE, DELETE_APPLICANT
    userId = models.CharField(max_length=255, blank=True, null=True)
    applicationId = models.CharField(max_length=255, blank=True, null=True)
    metadataJson = models.TextField(default="{}")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} at {self.createdAt}"


# ============================================================================
# 10. AI LEARNING & CONTEXTUAL RAG
# ============================================================================

class AILearningSample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='aiLearningSample')
    categoryId = models.CharField(max_length=255, blank=True, null=True)
    facilityId = models.CharField(max_length=255, blank=True, null=True)
    feedbackType = models.CharField(max_length=50)  # POSITIVE, NEGATIVE
    anonymizedProfileJson = models.TextField(default="{}")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Learning sample for {self.application.id}"
