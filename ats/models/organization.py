"""Organisations-Domaene: Traeger, Einrichtungen, Abteilungen, Standorte, Jobfamilien, Ansprechpartner."""
import uuid

from django.db import models
from django.utils import timezone

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
    panelUserIdsJson = models.JSONField(default=list)
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
    panelUserIdsJson = models.JSONField(default=list)


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
    panelUserIdsJson = models.JSONField(default=list)
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
    panelUserIdsJson = models.JSONField(default=list)
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
    panelUserIdsJson = models.JSONField(default=list)
    description = models.TextField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    # Vorstands-Governance: Mindest-Screening-Fragen dieser Jobfamilie.
    # Werden beim Speichern jeder Stelle SERVERSEITIG gemergt (fehlende wieder
    # eingefuegt, isMandatory erzwungen) – unabhaengig davon, was UI,
    # Prozess-Gedaechtnis oder Import liefern. Pflege: nur HR-Admin.
    minimumQuestionsJson = models.JSONField(default=list)
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
