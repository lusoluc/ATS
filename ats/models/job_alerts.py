"""Job-Alerts: E-Mail-Abonnements auf neue Stellen samt Protokoll der Zustellungen."""
import uuid

from django.db import models
from django.utils import timezone

from .base import EncryptedCharField, email_blind_index
from .organization import Facility

# ============================================================================
# 6. JOB ALERTS SUBSYSTEM
# ============================================================================

class JobAlertManager(models.Manager):
    """Lookups ueber den Blind-Index statt ueber die verschluesselte Spalte.

    Ohne diesen Weg landet jeder Aufrufer bei `filter(email=...)` - und das
    liefert nach der Verschluesselung stillschweigend NULL Treffer statt eines
    Fehlers. Beim Talent-Pool ist genau diese Falle zugeschnappt.
    """

    def get_by_email(self, email):
        return self.get(emailHash=email_blind_index(email))

    def filter_by_email(self, email):
        return self.filter(emailHash=email_blind_index(email))

    def get_or_create_by_email(self, email, defaults=None):
        normalized = (email or "").strip().lower()
        return self.get_or_create(
            emailHash=email_blind_index(normalized),
            defaults={**(defaults or {}), "email": normalized})


class JobAlertSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Die private Adresse einer interessierten Person - nirgends
    # veroeffentlicht, anders als die Kontaktdaten auf der Stellenanzeige.
    # Wie bei Applicant und TalentPoolSubscription: Fernet plus
    # deterministischer Blind-Index, damit Eindeutigkeit und `get_or_create`
    # weiter funktionieren.
    email = EncryptedCharField(max_length=254)
    emailHash = models.CharField(max_length=64, unique=True, null=True,
                                 editable=False)  # genau EIN Abo je E-Mail (keine Duplikate)
    status = models.CharField(max_length=50, default="PENDING")  # PENDING, ACTIVE, INACTIVE

    globalAlert = models.BooleanField(default=False)
    categories = models.TextField(default="[]")
    locations = models.TextField(default="[]")   # Location-IDs als Umkreis-Zentren
    radiusKm = models.IntegerField(blank=True, null=True)
    # Alarm-Scope (UC-AY-11/12): Stichwort im Jobtitel und/oder Einrichtung ("Firma")
    # Frei getipptes Suchwort der Person - anders als die ID-Listen
    # `categories`/`locations` echter Freitext ("Teilzeit Nachtdienst"), der
    # etwas ueber sie aussagt. Verschluesselt moeglich, weil das Matching in
    # Python laeuft (job_alerts.match_subscribers_for_job), nie per DB-Filter.
    keyword = EncryptedCharField(max_length=120, blank=True, default="")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL,
                                 blank=True, null=True, related_name="jobAlerts")

    confirmationToken = models.CharField(max_length=255, unique=True, blank=True, null=True)
    managementToken = models.CharField(max_length=255, unique=True, blank=True, null=True)

    createdAt = models.DateTimeField(default=timezone.now)

    objects = JobAlertManager()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
            self.emailHash = email_blind_index(self.email)
        if kwargs.get("update_fields") and "email" in kwargs["update_fields"]:
            kwargs["update_fields"] = list(
                set(kwargs["update_fields"]) | {"emailHash"})
        super().save(*args, **kwargs)
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
