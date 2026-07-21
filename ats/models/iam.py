"""Zugriffssteuerung: Vertretungsregelungen (Delegation) und Sichtbarkeits-Silos je Auth-User (BOLA)."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .organization import Facility, Location

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
