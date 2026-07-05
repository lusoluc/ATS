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


def email_blind_index(email: str) -> str:
    """Deterministischer Blind-Index für E-Mail-Adressen (WP2-Nachtrag, Go-Live-Blocker).

    Fernet ist nicht-deterministisch, daher kann die verschlüsselte E-Mail-Spalte
    weder unique sein noch per Lookup gefunden werden. Lösung: HMAC-SHA256 über die
    normalisierte Adresse (lower/strip) mit dem PII-Schlüssel als HMAC-Key.
    - HMAC statt reinem Hash: ohne Schlüssel kein Wörterbuch-/Brute-Force-Angriff
      auf die Indexspalte.
    - Deterministisch: unique-Constraint + get_or_create funktionieren weiter.
    - Schlüsselrotation rotiert zwingend AUCH den Index (Neuberechnung nötig).
    """
    import hmac as _hmac
    key_str = getattr(settings, 'PII_ENCRYPTION_KEY', 'securats-fallback-super-secure-encryption-key-for-pii-at-rest=')
    normalized = (email or "").strip().lower().encode("utf-8")
    return _hmac.new(key_str.encode("utf-8"), normalized, hashlib.sha256).hexdigest()

class EncryptedCharField(models.CharField):
    """CharField that encrypts data at-rest using Fernet.

    WICHTIG:
    - Der Ciphertext ist deutlich laenger als der Klartext (Fernet-Overhead).
      Daher wird die Spalte als TEXT angelegt (get_internal_type -> 'TextField'),
      damit auf strikten Datenbanken (PostgreSQL/MySQL) kein
      "value too long for type varchar(n)" Fehler auftritt. max_length gilt
      weiterhin fuer die Formular-/Klartext-Validierung.
    - Fernet ist nicht-deterministisch (Zufalls-IV + Timestamp). Exakte Lookups
      wie filter(firstName="...") oder __icontains funktionieren daher NICHT und
      liefern immer 0 Treffer. Suche/Filter auf diesen Feldern vermeiden.
    """
    def get_internal_type(self):
        # Ciphertext in einer laengenlosen TEXT-Spalte ablegen.
        return 'TextField'

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
    """TextField that encrypts data at-rest using Fernet.

    Hinweis: Fernet ist nicht-deterministisch, exakte Lookups auf diesem Feld
    funktionieren daher nicht.
    """
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
    # --- Corporate Identity / Branding der oeffentlichen Seiten ------------
    # Muster-Analyse (TUM/UKE/BwKrankenhaus/DB/Telekom): EINE Primaerfarbe,
    # heller Grund, Logo oben links, Kontrast automatisch. Das Recruiter-ATS
    # behaelt die SecurATS-Identitaet; Branding wirkt NUR auf Bewerberseiten.
    brandEnabled = models.BooleanField(default=False)
    brandMode = models.CharField(max_length=10, default="LIGHT")  # LIGHT|DARK
    brandPrimary = models.CharField(max_length=9, default="#0065bd")
    brandAccent = models.CharField(max_length=9, blank=True, default="")
    brandLogoUrl = models.CharField(max_length=500, blank=True, default="")
    brandHeroUrl = models.CharField(max_length=500, blank=True, default="")
    # Gremien-Default dieser Ebene (Sichtungs-Gremium): wird von Stellen
    # geerbt, wenn keine spezifischere Ebene greift. Sentinel ["NONE"] =
    # "hier bewusst KEIN Gremium" (unterbricht die Vererbung).
    panelUserIdsJson = models.TextField(default="[]")
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
    # UC-JF-01: mitbestimmungspflichtige Einrichtung -> Anzeigen laufen durchs Freigabe-Gate
    requiresApproval = models.BooleanField(default=False)
    # Individuelle Freigabekette dieser Einrichtung (kommagetrennte Gruppennamen,
    # z.B. "Hiring-Manager,Betriebsrat,HR-Admin"). Leer = globale APPROVAL_CHAIN.
    # Governance-Garantie: Eine leere Kette schaltet das Gate NICHT ab –
    # requiresApproval bleibt der einzige Schalter; die Kette bestimmt nur WER.
    approvalChain = models.CharField(max_length=255, blank=True, default="")
    # Stellenfreigabe: Genehmigungskette fuer PERSONALBEDARF (vor der
    # Ausschreibung), kommaseparierte Rollen; leer = Fallback (approvals.py)
    requisitionChain = models.CharField(max_length=255, blank=True, default="")
    # Gremien-Default dieser Ebene (Sichtungs-Gremium): wird von Stellen
    # geerbt, wenn keine spezifischere Ebene greift. Sentinel ["NONE"] =
    # "hier bewusst KEIN Gremium" (unterbricht die Vererbung).
    panelUserIdsJson = models.TextField(default="[]")


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
    # Gremien-Default dieser Ebene (Sichtungs-Gremium): wird von Stellen
    # geerbt, wenn keine spezifischere Ebene greift. Sentinel ["NONE"] =
    # "hier bewusst KEIN Gremium" (unterbricht die Vererbung).
    panelUserIdsJson = models.TextField(default="[]")
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
    # Gremien-Default dieser Ebene (Sichtungs-Gremium): wird von Stellen
    # geerbt, wenn keine spezifischere Ebene greift. Sentinel ["NONE"] =
    # "hier bewusst KEIN Gremium" (unterbricht die Vererbung).
    panelUserIdsJson = models.TextField(default="[]")
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
    # Gremien-Default dieser Ebene (Sichtungs-Gremium): wird von Stellen
    # geerbt, wenn keine spezifischere Ebene greift. Sentinel ["NONE"] =
    # "hier bewusst KEIN Gremium" (unterbricht die Vererbung).
    panelUserIdsJson = models.TextField(default="[]")
    description = models.TextField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    # Vorstands-Governance: Mindest-Screening-Fragen dieser Jobfamilie.
    # Werden beim Speichern jeder Stelle SERVERSEITIG gemergt (fehlende wieder
    # eingefuegt, isMandatory erzwungen) – unabhaengig davon, was UI,
    # Prozess-Gedaechtnis oder Import liefern. Pflege: nur HR-Admin.
    minimumQuestionsJson = models.TextField(default="[]")
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
    # WP4/B12: Versionierung – gleicher Titel erzeugt neue Version statt Duplikat
    version = models.IntegerField(default=1)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                               related_name='versions')  # zeigt auf Vorgänger-Version
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
    descriptionEasy = models.TextField(blank=True, null=True)  # WP1: Leichte-Sprache-Variante
    
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
    # Sichtungs-Gremium fuer hoehere Positionen: User-IDs (als Strings) derer,
    # die VOR einer Einladung abstimmen. Leer = kein Gremium (Normalfall).
    # Regel: absolute Mehrheit DAFUER gibt die Einladung frei (HR-Admin kann
    # mit Audit uebersteuern). Durchsetzung serverseitig an allen Pfaden.
    panelUserIdsJson = models.TextField(default="[]")
    # Mehrfachbedarf: "3 Stellen gleicher Art" als EINE Ausschreibung
    headcount = models.PositiveIntegerField(default=1)
    # Gremium-Governance je Stelle: Quorum (null = absolute Mehrheit der
    # Sitze) und Abstimmungs-Frist in Tagen ab Bewerbungseingang (null = keine)
    panelQuorum = models.PositiveSmallIntegerField(blank=True, null=True)
    panelDeadlineDays = models.PositiveSmallIntegerField(blank=True, null=True)
    # P1-11: Gespraechsrunden als formale Zustaende (["Erstgespraech", ...]);
    # leer = Bestandsverhalten (Einladung -> Einstellung ohne Rundenpflicht)
    interviewRoundsJson = models.TextField(default="[]")

    @property
    def interview_rounds_csv(self):
        return ", ".join(interview_rounds(self))
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

class ApplicantManager(models.Manager):
    """Lookups über den Blind-Index statt über die verschlüsselte E-Mail-Spalte."""

    def get_by_email(self, email):
        return self.get(emailHash=email_blind_index(email))

    def get_or_create_by_email(self, email, defaults=None):
        normalized = (email or "").strip().lower()
        return self.get_or_create(
            emailHash=email_blind_index(normalized),
            defaults={**(defaults or {}), "email": normalized},
        )


class Applicant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = EncryptedCharField(max_length=100)
    lastName = EncryptedCharField(max_length=100)
    # WP2-Nachtrag (Go-Live-Blocker): E-Mail jetzt verschlüsselt at-rest.
    # Eindeutigkeit + Lookups laufen über den deterministischen Blind-Index.
    email = EncryptedCharField(max_length=254)
    emailHash = models.CharField(max_length=64, unique=True, null=True, editable=False)
    phone = EncryptedCharField(max_length=50, blank=True, null=True)
    address = EncryptedCharField(max_length=300, blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    objects = ApplicantManager()

    def save(self, *args, **kwargs):
        # Blind-Index immer aus der (normalisierten) E-Mail ableiten
        if self.email:
            self.email = self.email.strip().lower()
            self.emailHash = email_blind_index(self.email)
        if kwargs.get("update_fields") and "email" in kwargs["update_fields"]:
            kwargs["update_fields"] = list(set(kwargs["update_fields"]) | {"emailHash"})
        super().save(*args, **kwargs)

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
    
    status = models.CharField(max_length=50, default="NEW")
    interviewRound = models.PositiveSmallIntegerField(default=0)  # abgeschlossen  # NEW, IN_REVIEW, MISSING_DOCS, INVITED, REJECTED, WITHDRAWN
    hiredAt = models.DateTimeField(blank=True, null=True)  # Einstellungs-Ereignis (Time-to-Fill)
    source = models.CharField(max_length=50, default="DIRECT")  # DIRECT, STEPSTONE, BA, GOOGLE, REFERRAL, …
    boardOrder = models.IntegerField(default=0)  # B10: Position innerhalb der Kanban-Spalte
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

# Gesprächsformate: von schriftlicher Aufgabe bis Assessment – die Prüfung
# einer Bewerbung ist selten EIN Interviewtyp. Gespeichert in
# Interview.locationType / InterviewSlot.kind (CharField, abwärtskompatibel:
# Altwerte REMOTE/IN_PERSON werden auf VIDEO/ON_SITE gemappt).
INTERVIEW_KINDS = [
    ("PHONE", "Telefonat"),
    ("VIDEO", "Video-Gespräch"),
    ("ON_SITE", "Gespräch vor Ort"),
    ("TRIAL_WORK", "Probearbeit / Hospitation"),
    ("ASSESSMENT", "Assessment / Auswahltag"),
    ("WRITTEN", "Schriftliche Aufgabe"),
]
_LEGACY_KINDS = {"REMOTE": "VIDEO", "IN_PERSON": "ON_SITE",
                 "NACH_ABSPRACHE": "ON_SITE"}


def interview_rounds(job) -> list[str]:
    """Definierte Gespraechsrunden einer Stelle (leer = keine Rundenpflicht).
    Robust gegen kaputtes JSON; hart gekappt auf 6 Runden a 60 Zeichen."""
    import json as _json
    try:
        parsed = _json.loads(getattr(job, 'interviewRoundsJson', None) or "[]")
        if not isinstance(parsed, list):
            return []
        return [str(r).strip()[:60] for r in parsed if str(r).strip()][:6]
    except (ValueError, TypeError):
        return []


def rounds_state(app) -> dict:
    """Formaler Runden-Zustand einer Bewerbung fuer Gate + Anzeige."""
    rounds = interview_rounds(app.jobPosting)
    total = len(rounds)
    done = min(app.interviewRound or 0, total)
    return {
        'rounds': rounds, 'total': total, 'done': done,
        'complete': done >= total,
        'current_label': rounds[done] if done < total else None,
    }


def get_interview_kinds():
    """Konfigurierbare Formate: SystemSetting INTERVIEW_KINDS_JSON
    ([{"code","label"}, ...]) ueberschreibt den Code-Default. Ungueltig
    oder leer -> Default. Bestehende Termine behalten ihr Label ueber
    interview_kind_label, auch wenn ein Format spaeter entfernt wird."""
    import json as _json
    try:
        setting = SystemSetting.objects.filter(
            key="INTERVIEW_KINDS_JSON").first()
        if setting and setting.value:
            parsed = _json.loads(setting.value)
            kinds = [(str(k.get("code", "")).strip().upper()[:40],
                      str(k.get("label", "")).strip()[:80])
                     for k in parsed
                     if str(k.get("code", "")).strip()
                     and str(k.get("label", "")).strip()]
            if kinds:
                return kinds
    except (ValueError, TypeError):
        pass
    return list(INTERVIEW_KINDS)


def interview_kind_label(value):
    value = _LEGACY_KINDS.get(value or "", value or "")
    for code, label in get_interview_kinds():
        if code == value:
            return label
    return dict(INTERVIEW_KINDS).get(value, value or "offen")

# Gespraechsergebnis: bewusst schlank – die WEITERE Entscheidung (Zusage/Absage)
# lebt im Bewerbungsstatus (Kanban); hier geht es nur darum, OB und WIE der
# Termin stattfand. Das macht No-Show-Quoten und Format-Vergleiche messbar.
INTERVIEW_OUTCOMES = [
    ("COMPLETED", "Stattgefunden"),
    ("NO_SHOW", "Nicht erschienen"),
    ("CANCELLED", "Kurzfristig abgesagt"),
]


def interview_outcome_label(value):
    return dict(INTERVIEW_OUTCOMES).get(value or "", value or "offen")


def interview_kind_label(value):
    value = _LEGACY_KINDS.get(value or "", value or "")
    return dict(INTERVIEW_KINDS).get(value, value or "Gespräch")


class Interview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    scheduledAt = models.DateTimeField()
    locationType = models.CharField(max_length=50)  # REMOTE, IN_PERSON
    meetingLink = models.CharField(max_length=255, blank=True, null=True)
    outcome = models.CharField(max_length=50, blank=True, null=True)
    # No-Show-Praevention: wann wurde die Erinnerung verschickt? (einmalig)
    reminderSentAt = models.DateTimeField(blank=True, null=True)
    # Interview-Team: alle internen Teilnehmenden (Fachbereich, Leitung, ...)
    # -> Benachrichtigung bei Buchung, Team-Erinnerung, sichtbar im Kalender.
    participants = models.ManyToManyField('auth.User', blank=True,
                                          related_name='interviewParticipations')

    @property
    def kind_label(self):
        return interview_kind_label(self.locationType)

    @property
    def outcome_label(self):
        return interview_outcome_label(self.outcome)
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
    # Gesprächsformat des Slots (Probearbeit braucht 4 h, Telefonat 20 Min –
    # Bewerbende sollen VOR der Buchung wissen, was sie erwartet).
    kind = models.CharField(max_length=50, blank=True, default="")

    @property
    def kind_label(self):
        return interview_kind_label(self.kind)

    # Kollaboration verteilter Teams: wer bietet diesen Slot an?
    # Sichtbar im Kalender ("Slot von Petra W."), löschbar nur durch
    # Ersteller:in oder HR-Admin.
    createdBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                  blank=True, null=True,
                                  related_name='createdInterviewSlots')
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
    # criteria: JSON {"job_families": [...], "locations": [...]} – abgeleitet aus
    # den bisherigen Bewerbungen beim Opt-in im Portal (Datensparsamkeit: kein
    # Freitext-Skill-Profil, nur was ohnehin im Haus ist).
    criteria = models.TextField(default="{}")
    consentId = models.CharField(max_length=255)
    expiresAt = models.DateTimeField()
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return self.expiresAt >= timezone.now()

    def __str__(self):
        return self.email


class ApplicationVote(models.Model):
    """Gremien-Stimme zu einer Bewerbung (vor der Einladung).

    Eine Stimme je Person und Bewerbung (unique_together), aenderbar –
    jede Aenderung wird auditiert. Kommentare/Fragen des Gremiums laufen in
    die internen Notizen der Bewerbung (ein Ort fuer den 360-Grad-Blick).
    """
    VOTES = [("FOR", "Dafür"), ("AGAINST", "Dagegen")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE,
                                    related_name='votes')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                             related_name='applicationVotes')
    vote = models.CharField(max_length=10, choices=VOTES)
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('application', 'user')]


INTERVIEW_RECOMMENDATIONS = [
    ("STRONG_YES", "Klar dafür"),
    ("YES", "Eher dafür"),
    ("NEUTRAL", "Unentschieden"),
    ("NO", "Eher dagegen"),
    ("STRONG_NO", "Klar dagegen"),
]

# Standard-Bewertungskriterien als klare Aussagen, prozentbasiert (0–100 %).
# Bewusst kurz und branchenneutral; kundenspezifische Kriterien sind eine
# spaetere Ausbaustufe (Gate).
DEFAULT_FEEDBACK_CRITERIA = [
    "Passt ins Team",
    "Ist motiviert",
    "Ist fachlich versiert",
    "Kommuniziert klar",
]


def derive_recommendation(score):
    """Leitet aus einem Gesamt-Score (0–100) eine Empfehlung ab, damit der
    schnelle Weg = nur Slider ziehen genuegt (Empfehlung optional)."""
    if score is None:
        return "NEUTRAL"
    if score >= 85:
        return "STRONG_YES"
    if score >= 70:
        return "YES"
    if score >= 45:
        return "NEUTRAL"
    if score >= 25:
        return "NO"
    return "STRONG_NO"


class InterviewFeedback(models.Model):
    """Strukturiertes Feedback einer Person zu einem Bewerbungsgespraech.

    Zweck: Die zweite Runde und die finale Entscheidung sollen auf
    dokumentiertem Feedback stehen – nicht auf Flurfunk. Jede:r
    Interviewer:in hinterlaesst je Runde eine Bewertung mit einer klaren
    Empfehlung, Kriterien-Noten, Staerken und – bewusst als eigenes,
    nicht uebersehbares Feld – BEDENKEN. So geht keine Sorge verloren,
    nur weil niemand daran gedacht hat, sie weiterzugeben.

    Eine Rueckmeldung je Person, Bewerbung und Runde (aenderbar, jede
    Aenderung auditiert – Korrektur ist Haus-Prinzip).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE,
                                    related_name='feedback')
    interview = models.ForeignKey('Interview', on_delete=models.SET_NULL,
                                  blank=True, null=True,
                                  related_name='feedback')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                               related_name='interviewFeedback')
    round = models.PositiveSmallIntegerField(default=0)  # 0 = ohne Runde
    recommendation = models.CharField(max_length=20,
                                      choices=INTERVIEW_RECOMMENDATIONS)
    ratingsJson = models.TextField(default="{}")   # {"Kriterium": 1..4}
    strengths = models.TextField(blank=True, default="")
    concerns = models.TextField(blank=True, default="")   # Bedenken
    comment = models.TextField(blank=True, default="")
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('application', 'author', 'round')]
        ordering = ['round', 'createdAt']

    @property
    def ratings(self):
        import json as _json
        try:
            data = _json.loads(self.ratingsJson or "{}")
            return data if isinstance(data, dict) else {}
        except (ValueError, TypeError):
            return {}

    @property
    def overall_score(self):
        """Mittelwert der Prozent-Bewertungen (0–100) oder None."""
        vals = [v for v in self.ratings.values()
                if isinstance(v, (int, float))]
        return round(sum(vals) / len(vals)) if vals else None

    @property
    def recommendation_label(self):
        return dict(INTERVIEW_RECOMMENDATIONS).get(self.recommendation,
                                                   self.recommendation)

    @property
    def is_positive(self):
        return self.recommendation in ("STRONG_YES", "YES")


def feedback_for_application(app):
    """Alle Feedbacks einer Bewerbung, nach Runde gruppiert, plus eine
    kompakte Zusammenfassung fuer Entscheidungspunkte."""
    items = list(InterviewFeedback.objects.filter(application=app)
                 .select_related('author').order_by('round', 'createdAt'))
    by_round = {}
    open_concerns = 0
    rec_counts = {}
    for f in items:
        by_round.setdefault(f.round, []).append(f)
        if f.concerns.strip():
            open_concerns += 1
        rec_counts[f.recommendation] = rec_counts.get(f.recommendation, 0) + 1
    return {
        'items': items, 'by_round': sorted(by_round.items()),
        'total': len(items), 'open_concerns': open_concerns,
        'rec_counts': rec_counts,
    }


def pending_feedback_participants(interview, round_index):
    """Teilnehmer:innen eines Gespraechs mit E-Mail, die zu dieser Runde
    noch KEIN Feedback abgegeben haben. Basis fuer die Feedback-Bitte."""
    given = set(InterviewFeedback.objects
                .filter(application=interview.application,
                        round=round_index)
                .values_list('author_id', flat=True))
    return [p for p in interview.participants.all()
            if p.email and p.id not in given]


def feedback_summaries(application_ids):
    """Bulk-Zusammenfassung fuer viele Bewerbungen in EINEM Query (Board,
    kein N+1). Liefert {app_id: {count, avg_score, open_concerns,
    positive}}. avg_score = Mittel der Feedback-Gesamt-Scores (nur die mit
    Bewertungen); positive = Zahl der Empfehlungen dafuer."""
    import json as _json
    out = {}
    qs = (InterviewFeedback.objects
          .filter(application_id__in=list(application_ids))
          .values_list('application_id', 'ratingsJson', 'concerns',
                       'recommendation'))
    acc = {}
    for app_id, ratings_json, concerns, rec in qs:
        a = acc.setdefault(app_id, {'count': 0, 'score_sum': 0,
                                    'score_n': 0, 'open_concerns': 0,
                                    'positive': 0})
        a['count'] += 1
        if (concerns or '').strip():
            a['open_concerns'] += 1
        if rec in ('STRONG_YES', 'YES'):
            a['positive'] += 1
        try:
            vals = [v for v in _json.loads(ratings_json or '{}').values()
                    if isinstance(v, (int, float))]
        except (ValueError, TypeError):
            vals = []
        if vals:
            a['score_sum'] += sum(vals) / len(vals)
            a['score_n'] += 1
    for app_id, a in acc.items():
        out[app_id] = {
            'count': a['count'],
            'avg_score': (round(a['score_sum'] / a['score_n'])
                          if a['score_n'] else None),
            'open_concerns': a['open_concerns'],
            'positive': a['positive'],
        }
    return out


class LandingPage(models.Model):
    """Kampagnen-Landingpage: /k/<slug>/ – fuer Messen, Einrichtungen,
    Abteilungen oder Aktionen.

    Eigene Ansprache + gescopte Stellenliste + eingebaute Messung: der Slug
    IST die Quelle (Session), damit haengt jede Bewerbung an der Kampagne
    und der Trichter Aufrufe → Bewerbungen → Einladungen ist auswertbar.
    Scope-Felder sind UND-verknuepft; alle leer = alle veroeffentlichten
    Stellen. Traeger-Branding wirkt automatisch (oeffentlicher Pfad).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=50, unique=True)
    headline = models.CharField(max_length=200, blank=True, default="")
    introText = models.TextField(blank=True, default="")
    heroUrl = models.CharField(max_length=500, blank=True, default="")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL,
                                 blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                   blank=True, null=True)
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.SET_NULL,
                                  blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                 blank=True, null=True)
    contactPerson = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL,
                                      blank=True, null=True)
    blocksJson = models.TextField(default="[]")  # CMS-Baukasten (ats/blocks.py)
    active = models.BooleanField(default=True)
    expiresAt = models.DateTimeField(blank=True, null=True)  # Kampagnen-Ende
    views = models.IntegerField(default=0)  # Bot-Rauschen inklusive (ehrlich)
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class SourceChannel(models.Model):
    """Recruiting-Kanal/Kampagne (Jobmesse, Aushang, Anzeige, Empfehlung).

    Antwort auf "war die Jobmesse erfolgreich?": Der Kanal bekommt einen
    Link + QR-Code (?src=SLUG); jede darueber eingehende Bewerbung traegt
    die Quelle, die Auswertung zeigt Menge UND Qualitaet (Einladungsquote).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=50, unique=True)
    note = models.CharField(max_length=255, blank=True, default="")
    # Kampagnenkosten strukturiert (statt Freitext/SystemSetting):
    # speist "Kosten je Einstellung" direkt.
    costAmount = models.DecimalField(max_digits=10, decimal_places=2,
                                     blank=True, null=True)
    expiresAt = models.DateTimeField(blank=True, null=True)  # Kampagnen-Ende
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class TalentPoolContact(models.Model):
    """Nachweis: welcher Pool-Eintrag wurde wann auf welche Stelle hingewiesen?

    unique_together verhindert Doppel-Ansprachen – wer im Pool ist, hat in eine
    gelegentliche, passende Ansprache eingewilligt, nicht in Dauer-Werbung.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(TalentPoolSubscription,
                                     on_delete=models.CASCADE,
                                     related_name='contacts')
    jobPosting = models.ForeignKey(JobPosting, on_delete=models.CASCADE,
                                   related_name='talentPoolContacts')
    sentBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                               blank=True, null=True)
    sentAt = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [('subscription', 'jobPosting')]


# ============================================================================
# CMS PAGE MANAGEMENT
# ============================================================================

class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(default="")
    blocksJson = models.TextField(default="[]")  # CMS-Baukasten (ats/blocks.py)
    views = models.IntegerField(default=0)  # Aufrufe (Bot-Rauschen inklusive)
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
    email = models.EmailField(unique=True)  # genau EIN Abo je E-Mail (keine Duplikate)
    status = models.CharField(max_length=50, default="PENDING")  # PENDING, ACTIVE, INACTIVE

    globalAlert = models.BooleanField(default=False)
    categories = models.TextField(default="[]")
    locations = models.TextField(default="[]")   # Location-IDs als Umkreis-Zentren
    radiusKm = models.IntegerField(blank=True, null=True)
    # Alarm-Scope (UC-AY-11/12): Stichwort im Jobtitel und/oder Einrichtung ("Firma")
    keyword = models.CharField(max_length=120, blank=True, default="")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL,
                                 blank=True, null=True, related_name="jobAlerts")

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

class StaffingRequest(models.Model):
    """UC-MD-01: Personalbedarf melden – die Vorstufe jeder Ausschreibung.

    Fachbereiche (Hiring-Manager) melden strukturiert, WAS sie brauchen;
    Recruiting entscheidet und ueberfuehrt in eine Ausschreibung. Das ersetzt
    Zuruf-Mails ("wir braeuchten mal wieder jemanden") durch einen
    nachvollziehbaren, auditierten Vorgang.
    """
    STATUS = [("OPEN", "Offen"), ("IN_APPROVAL", "In Genehmigung"),
              ("RETURNED", "Zur Nachbesserung"), ("ACCEPTED", "Angenommen"),
              ("DECLINED", "Abgelehnt"), ("CONVERTED", "Ausschreibung erstellt")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)                 # z.B. "Pflegefachkraft Nachtdienst"
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE,
                                 related_name='staffingRequests')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='staffingRequests')
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.SET_NULL,
                                  blank=True, null=True)
    headcount = models.PositiveSmallIntegerField(default=1)
    desiredStart = models.DateField(blank=True, null=True)
    justification = models.TextField()                       # warum, was passiert sonst
    answersJson = models.TextField(default="{}")             # Antworten des Regel-Formulars
    status = models.CharField(max_length=20, choices=STATUS, default="OPEN")
    requestedBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                    blank=True, null=True,
                                    related_name='staffingRequests')
    decisionNote = models.TextField(blank=True, default="")
    decidedBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                  blank=True, null=True,
                                  related_name='decidedStaffingRequests')
    decidedAt = models.DateTimeField(blank=True, null=True)
    # Traceability: welche Ausschreibung ist aus diesem Bedarf entstanden?
    convertedJob = models.ForeignKey(JobPosting, on_delete=models.SET_NULL,
                                     blank=True, null=True,
                                     related_name='staffingRequest')
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Bedarf: {self.title} ({self.get_status_display()})"



class RequisitionRule(models.Model):
    """No-Code Routing-Matrix der Stellenfreigabe.

    Eine Regel = Geltungsbereich (Wildcards ueber NULL) + Formular-Fragen +
    Genehmigungskette + Pflicht-Flag. Aufloesung: spezifischste Regel gewinnt
    (Einrichtung > Abteilung > Jobfamilie gewichtet), bei Gleichstand die
    zuletzt angelegte. Bewusst OHNE Mandanten-Dimension: SecurATS ist
    on-prem EIN Traeger je Installation (Architektur-Entscheidung).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE,
                                 blank=True, null=True,
                                 related_name='requisitionRules')
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   blank=True, null=True,
                                   related_name='requisitionRules')
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.CASCADE,
                                  blank=True, null=True,
                                  related_name='requisitionRules')
    chain = models.CharField(max_length=255)                 # Rollen, kommasep.
    formQuestionsJson = models.TextField(default="[]")       # ats/questions.py
    mandatory = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    createdAt = models.DateTimeField(default=timezone.now)

    @property
    def specificity(self):
        return ((4 if self.facility_id else 0)
                + (2 if self.department_id else 0)
                + (1 if self.jobFamily_id else 0))

    def __str__(self):
        return self.name


class RequisitionStep(models.Model):
    """Eine Stufe der Stellenfreigabe (sequenziell, Rolle = Gruppe).

    Bewusst eigenes, schlankes Modell statt Wiederverwendung des
    Job-ApprovalTickets: der Bedarf ist VOR der Stelle, ein Job-FK
    existiert noch nicht.
    """
    STATUS = [("PENDING", "Ausstehend"), ("APPROVED", "Genehmigt"),
              ("RETURNED", "Zur Nachbesserung"), ("REJECTED", "Abgelehnt")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(StaffingRequest, on_delete=models.CASCADE,
                                related_name="steps")
    role = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")
    decidedBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                  blank=True, null=True,
                                  related_name='requisitionDecisions')
    decidedAt = models.DateTimeField(blank=True, null=True)
    comment = models.TextField(blank=True, default="")
    viaDelegation = models.BooleanField(default=False)  # i. V. entschieden
    # Quorum der Parallelgruppe (Anzahl noetiger Zustimmungen bei gleicher
    # order). 0 = alle noetig (Bestandsverhalten fuer Altdaten).
    groupQuorum = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

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
    # WP3: auf kanonisches Django-Auth-User umgestellt (Prisma-Schatten-User ist Alt-Referenz)
    delegator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delegationsGiven')
    delegatee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delegationsReceived')
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
    # WP2/UC-MB-12: Integritäts-Hashkette (Append-Only-Nachweis, Manipulationserkennung)
    prevHash = models.CharField(max_length=64, blank=True, null=True)
    entryHash = models.CharField(max_length=64, blank=True, null=True)

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


# ============================================================================
# 11. BOLA – SCOPING (Standort-/Einrichtungs-Silos je Auth-User)
# ============================================================================

class UserScope(models.Model):
    """Begrenzt, welche Standorte/Einrichtungen ein Auth-User sehen darf.

    full_access=True (Default) => keine Einschränkung (rückwärtskompatibel).
    HR-Admin und Superuser sehen unabhängig davon immer alles.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scope")
    full_access = models.BooleanField(default=True)
    locations = models.ManyToManyField(Location, blank=True, related_name="scopedUsers")
    facilities = models.ManyToManyField(Facility, blank=True, related_name="scopedUsers")
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Scope({self.user})"


class MediaAsset(models.Model):
    """B18: hochgeladene Medien/Dateien (Bilder, Downloads) für CMS-Seiten."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    altText = models.CharField(max_length=255, blank=True, default="")  # WP8/WCAG 1.1.1
    file = models.FileField(upload_to="uploads/")
    contentType = models.CharField(max_length=100, blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class ApplicationDocument(models.Model):
    """WP1: zusätzliche Bewerbungsnachweise (Zeugnisse, Zertifikate, Approbation).

    Ergänzt den primären CV (Application.cvStorageId) um beliebig viele Belege –
    wichtig für hochqualifizierte Bewerbungen (z.B. Facharzt-Anerkennung).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="application_docs/")
    docType = models.CharField(max_length=50, default="OTHER")  # CV, CERTIFICATE, APPROBATION, OTHER
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.application_id})"


class AiTask(models.Model):
    """WP7/L6: DB-gestützte Async-Queue für KI-Aufgaben.

    Bewusst ohne externe Broker (Redis/Celery) – On-Prem-/Air-Gap-freundlich.
    Ein Worker-Prozess (`manage.py ai_worker`) arbeitet PENDING-Tasks ab; die UI
    blockiert dadurch nie auf LLM-Latenz.
    """
    STATUS = ["PENDING", "RUNNING", "DONE", "FAILED"]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taskType = models.CharField(max_length=50)          # z.B. SCORE_APPLICATION
    payloadJson = models.TextField(default="{}")
    status = models.CharField(max_length=20, default="PENDING")
    resultJson = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    maxAttempts = models.IntegerField(default=3)
    createdAt = models.DateTimeField(default=timezone.now)
    startedAt = models.DateTimeField(blank=True, null=True)
    finishedAt = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.taskType} [{self.status}]"
