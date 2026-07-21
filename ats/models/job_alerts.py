"""Job-Alerts: E-Mail-Abonnements auf neue Stellen samt Protokoll der Zustellungen."""
import uuid

from django.db import models
from django.utils import timezone

from .organization import Facility

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
