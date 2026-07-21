"""Systemeinstellungen, E-Mail-Vorlagen, Personalbedarf/Stellenfreigabe und CMS-Inhalte."""
import uuid

from django.db import models
from django.utils import timezone

from .jobs import JobPosting
from .organization import ContactPerson, Department, Facility, JobFamily, Location

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
    answersJson = models.JSONField(default=dict)             # Antworten des Regel-Formulars
    status = models.CharField(max_length=20, choices=STATUS, default="OPEN", db_index=True)
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
    formQuestionsJson = models.JSONField(default=list)       # ats/questions.py
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
    blocksJson = models.JSONField(default=list)  # CMS-Baukasten (ats/blocks.py)
    active = models.BooleanField(default=True)
    expiresAt = models.DateTimeField(blank=True, null=True)  # Kampagnen-Ende
    views = models.IntegerField(default=0)  # Bot-Rauschen inklusive (ehrlich)
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


# ============================================================================
# CMS PAGE MANAGEMENT
# ============================================================================

class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(default="")
    blocksJson = models.JSONField(default=list)  # CMS-Baukasten (ats/blocks.py)
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
