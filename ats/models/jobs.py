"""Stellen-Domaene: Vorlagen, Benefits, Textbausteine, Entgeltbaender, Ausschreibungen und Freigabe-Engine."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .governance import WorkflowState
from .organization import (
    ContactPerson,
    Department,
    Facility,
    JobFamily,
    Location,
    Organization,
)

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

class PayBand(models.Model):
    """Entgeltband — tarif-native Entgelttransparenz (EU-RL 2023/970, Art. 5).

    Ein Band beschreibt die Einstiegsentgelt-Spanne einer Stelle auf objektiver,
    geschlechtsneutraler Grundlage: entweder als Tarif-Referenz (TVöD/AVR mit
    Entgeltgruppe und Stufenspanne) oder als Haustarif-Band. Stellen referenzieren
    Bänder statt Freitext — gleiche Tätigkeit heißt damit systembedingt gleiche
    veröffentlichte Spanne (Spannen-Konsistenz)."""
    TARIFF_SYSTEMS = [
        ("TVOED", "TVöD / TV-L"),
        ("AVR_CARITAS", "AVR Caritas"),
        ("AVR_DIAKONIE", "AVR Diakonie"),
        ("HAUSTARIF", "Haustarif / eigenes Band"),
    ]
    PERIODS = [("MONTH", "pro Monat"), ("YEAR", "pro Jahr")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)  # z. B. "TVöD-P 7 (Stufe 2–6)"
    tariffSystem = models.CharField(max_length=30, choices=TARIFF_SYSTEMS, default="HAUSTARIF")
    minAmount = models.DecimalField(max_digits=9, decimal_places=2)
    maxAmount = models.DecimalField(max_digits=9, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIODS, default="MONTH")
    # Art. 5 Abs. 1 lit. b: Hinweis auf einschlägige Tarifvertrags-Bestimmungen
    collectiveAgreement = models.CharField(max_length=255, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")  # z. B. "zzgl. Schichtzulagen"
    # E3 / Art. 4: Tätigkeitsbewertung je Band — die vier objektiven,
    # geschlechtsneutralen Kriterien der Richtlinie. Am BAND (nicht an der
    # einzelnen Stelle): das Band bündelt gleichwertige Tätigkeiten, die
    # Begründung gilt damit einheitlich für alle Stellen im Band.
    criteriaSkills = models.TextField(blank=True, default="")           # Kompetenzen & Qualifikation
    criteriaEffort = models.TextField(blank=True, default="")           # Belastungen
    criteriaResponsibility = models.TextField(blank=True, default="")   # Verantwortung
    criteriaWorkingConditions = models.TextField(blank=True, default="")  # Arbeitsbedingungen
    archived = models.BooleanField(default=False)
    createdAt = models.DateTimeField(default=timezone.now)

    @property
    def has_evaluation(self):
        return bool(self.criteriaSkills.strip() and self.criteriaEffort.strip()
                    and self.criteriaResponsibility.strip()
                    and self.criteriaWorkingConditions.strip())

    @property
    def range_label(self):
        def fmt(v):
            return f"{v:,.0f}".replace(",", ".")
        period = dict(self.PERIODS).get(self.period, self.period)
        return f"{fmt(self.minAmount)} – {fmt(self.maxAmount)} € {period}"

    def __str__(self):
        return f"{self.name} ({self.range_label})"


class JobPosting(models.Model):
    # Transienter Zustand der Entgelttransparenz-Signale (ats/signals.py):
    # (war_publiziert, altes_band_id) vor dem aktuellen save().
    _pre_pay_state: "tuple[bool, uuid.UUID | None]"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    descriptionEasy = models.TextField(blank=True, null=True)  # WP1: Leichte-Sprache-Variante

    tasksJson = models.JSONField(default=list)
    requirementsJson = models.JSONField(default=list)
    screeningQuestionsJson = models.JSONField(default=list)

    contactPerson = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, blank=True, null=True, related_name='jobPostings')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='jobPostings')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='jobPostings')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name='jobPostings')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='jobPostings')
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.CASCADE, related_name='jobPostings')
    workflowState = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name='jobPostings')
    jobTemplate = models.ForeignKey(JobTemplate, on_delete=models.SET_NULL, blank=True, null=True, related_name='jobPostings')
    # Entgelttransparenz (EU-RL 2023/970, Art. 5): ohne Entgeltband keine
    # Veröffentlichung — durchgesetzt in create_job/toggle_job_active
    # (ats/pay_transparency.py), nicht auf Modellebene (Bestandsdaten/Entwürfe).
    payBand = models.ForeignKey(PayBand, on_delete=models.PROTECT, blank=True, null=True, related_name='jobPostings')
    # Sichtungs-Gremium fuer hoehere Positionen: User-IDs (als Strings) derer,
    # die VOR einer Einladung abstimmen. Leer = kein Gremium (Normalfall).
    # Regel: absolute Mehrheit DAFUER gibt die Einladung frei (HR-Admin kann
    # mit Audit uebersteuern). Durchsetzung serverseitig an allen Pfaden.
    panelUserIdsJson = models.JSONField(default=list)
    # Mehrfachbedarf: "3 Stellen gleicher Art" als EINE Ausschreibung
    headcount = models.PositiveIntegerField(default=1)
    # Gremium-Governance je Stelle: Quorum (null = absolute Mehrheit der
    # Sitze) und Abstimmungs-Frist in Tagen ab Bewerbungseingang (null = keine)
    panelQuorum = models.PositiveSmallIntegerField(blank=True, null=True)
    panelDeadlineDays = models.PositiveSmallIntegerField(blank=True, null=True)
    # P1-11: Gespraechsrunden als formale Zustaende (["Erstgespraech", ...]);
    # leer = Bestandsverhalten (Einladung -> Einstellung ohne Rundenpflicht)
    interviewRoundsJson = models.JSONField(default=list)

    @property
    def interview_rounds_csv(self):
        # Spaeter Import: bricht den Zyklus jobs <-> applications auf Modulebene.
        from .applications import interview_rounds
        return ", ".join(interview_rounds(self))

    # Voice-Studien-Learning "kontrollierte Varianz": Der messbare Vorteil
    # KI-gefuehrter Interviews war die konsequente Leitfaden-Treue - alle
    # Bewerbenden bekommen ein gleich gruendliches, vergleichbares Gespraech.
    # Dieselbe Konsistenz geben wir MENSCHLICHEN Interviews: Themen-Leitfaden
    # je Stelle, im Feedback als abhakbare Checkliste mit Abdeckungs-Anzeige.
    interviewGuideJson = models.JSONField(default=list)

    @property
    def interview_guide(self):
        parsed = self.interviewGuideJson or []
        if not isinstance(parsed, list):
            return []
        return [str(t).strip()[:80] for t in parsed if str(t).strip()][:12]

    @property
    def interview_guide_csv(self):
        return ", ".join(self.interview_guide)
    benefits = models.ManyToManyField(Benefit, related_name='jobPostings', blank=True)

    @property
    def is_template_outdated(self):
        if not self.jobTemplate:
            return False
        latest = JobTemplate.objects.filter(title__iexact=self.jobTemplate.title).order_by('-version').first()
        return latest and latest.id != self.jobTemplate.id

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
    stepsJson = models.JSONField(default=list)
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
    # Der Urheber zeigte frueher auf das Prisma-Alt-Modell `User`, mit dem sich
    # in dieser Anwendung niemand anmeldet - das Feld war also nicht befuellbar
    # und blieb in jeder Freigabe leer. Jetzt der echte Anmelde-Benutzer, damit
    # eine Zustimmung einen Namen hat (§ 99 BetrVG-Nachweis).
    actionTakenBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                      blank=True, null=True, related_name='approvalSteps')

    def __str__(self):
        return f"Step {self.stepOrder} for {self.approvalTicket}"
