"""Bewerbungs-Domaene: Bewerbende, Bewerbungen, Gespraeche, Feedback, Nachrichten, Talentpool und Quellen."""
import uuid

from django.db import models
from django.utils import timezone

from .base import EncryptedCharField, EncryptedTextField, email_blind_index
from .governance import PrivacyNoticeVersion
from .jobs import JobPosting
from .organization import Facility
from .system import SystemSetting

# ============================================================================
# 4. APPLICATION DOMAIN (ATS & Workflow)
# ============================================================================

def disability_value_disclosed(value: "str | None") -> bool:
    """§ 164: Zaehlt ein severeDisability-Wert als erteilte Angabe?

    Die Anwendung schreibt ausschliesslich 'JA' (oder leer). Alles andere -
    insbesondere roher Fernet-Ciphertext, den EncryptedCharField bei einem
    Key-Wechsel unentschluesselt zurueckgibt - ist KEINE Angabe. Ohne diese
    Schranke wuerden kaputte Altwerte still als Schwerbehinderten-Angabe in
    SBV-Kennzahlen, Steckbrief-Chip und Portal-Anzeige einfliessen.
    """
    return (value or "").strip().upper() == "JA"


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
    screeningAnswersJson = models.JSONField(default=dict)

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
    # § 164 SGB IX / § 178 Abs. 2: FREIWILLIGE Angabe einer Schwerbehinderung/
    # Gleichstellung. Art.-9-DSGVO-Datum -> verschluesselt at-rest, nur durch
    # ausdrueckliches Ankreuzen gesetzt ('JA', sonst leer). Loest die
    # SBV-Unterrichtung aus. NIEMALS Eingabe fuer Scoring/Lernen (Waechter-Test).
    # Lesen IMMER ueber disability_value_disclosed(): EncryptedCharField gibt
    # bei Key-Wechsel den rohen Ciphertext zurueck - der darf nie als Angabe
    # zaehlen (sonst kippen SBV-Kennzahlen und Portal-Anzeige still).
    severeDisability = EncryptedCharField(max_length=10, blank=True, default="")

    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        # Meistgenutzte Filterfelder (Board-Spalten, Quellen-Analytics, Zeitreihen)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
            models.Index(fields=["createdAt"]),
        ]

    def __str__(self):
        return f"Application by {self.applicant} for {self.jobPosting}"

class AppWorkflowDef(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='appWorkflows', blank=True, null=True)
    locationIdsJson = models.JSONField(default=list)
    categoryIdsJson = models.JSONField(default=list)
    jobIdsJson = models.JSONField(default=list)
    stepsJson = models.JSONField(default=list)
    createdAt = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

WORKFLOW_TASK_STATUS = [("OPEN", "Offen"), ("DONE", "Erledigt")]


class WorkflowTask(models.Model):
    """Aufgabe/Erinnerung aus der Prozess-Automatik (CREATE_TASK).

    Zweck: Die Automatik soll nicht nur Mails verschicken, sondern echte
    Arbeit anstossen – "Referenzen einholen", "Fuehrungszeugnis pruefen".
    Zugewiesen wird an eine ROLLE (nicht an eine Person), damit Urlaub oder
    Fluktuation die Aufgabe nicht verwaisen laesst; jede/r mit der Rolle im
    Zugriffsbereich sieht und erledigt sie.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE,
                                    related_name='workflowTasks')
    title = models.CharField(max_length=255)
    role = models.CharField(max_length=100, blank=True, default="")
    dueAt = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default="OPEN",
                              choices=WORKFLOW_TASK_STATUS)
    doneBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                               blank=True, null=True,
                               related_name='doneWorkflowTasks')
    doneAt = models.DateTimeField(blank=True, null=True)
    sourceState = models.CharField(max_length=50, blank=True, default="")
    createdAt = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['status', 'dueAt', 'createdAt']

    @property
    def overdue(self):
        return bool(self.status == "OPEN" and self.dueAt
                    and self.dueAt < timezone.now())


# Hier standen AppTicket/AppStep - eine zweite, nie benutzte Freigabekette fuer
# Bewerbungen aus dem Prisma-Vorgaenger. Was tatsaechlich laeuft: AppWorkflowDef
# (bleibt, siehe oben) treibt die Automatik, Entscheidungen stehen an der
# Bewerbung selbst und im Audit-Log.

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
    Robust gegen kaputte Daten; hart gekappt auf 6 Runden a 60 Zeichen."""
    parsed = getattr(job, 'interviewRoundsJson', None) or []
    if not isinstance(parsed, list):
        return []
    return [str(r).strip()[:60] for r in parsed if str(r).strip()][:6]


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

    class Meta:
        # Kalender-Bereiche, Erinnerungs-Command, No-Show-Auswertung
        indexes = [
            models.Index(fields=["scheduledAt"]),
            models.Index(fields=["outcome"]),
            models.Index(fields=["reminderSentAt"]),
        ]

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
    ratingsJson = models.JSONField(default=dict)   # {"Kriterium": 1..4}
    # Leitfaden-Abdeckung (Voice-Studien-Learning): welche Themen des
    # Stellen-Leitfadens wurden in DIESEM Gespraech behandelt?
    guideCoverageJson = models.JSONField(default=list)
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
        data = self.ratingsJson or {}
        return data if isinstance(data, dict) else {}

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
        ratings = ratings_json if isinstance(ratings_json, dict) else {}
        vals = [v for v in ratings.values() if isinstance(v, (int, float))]
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
