"""Audit & Compliance: manipulationssichere Protokollkette ueber alle relevanten Vorgaenge."""
import uuid

from django.db import models
from django.utils import timezone

# ============================================================================
# 9. AUDIT & COMPLIANCE
# ============================================================================

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=100)  # READ_CV, STATUS_CHANGE, DELETE_APPLICANT
    userId = models.CharField(max_length=255, blank=True, null=True)
    applicationId = models.CharField(max_length=255, blank=True, null=True)
    # BEWUSST TextField, kein JSONField: der String ist die kanonische Form,
    # die in die Hash-Kette eingeht (audit._entry_hash). Ein Dict-Roundtrip
    # könnte die Serialisierung ändern und die Kette für Bestandsdaten brechen.
    metadataJson = models.TextField(default="{}")
    createdAt = models.DateTimeField(default=timezone.now)
    # WP2/UC-MB-12: Integritäts-Hashkette (Append-Only-Nachweis, Manipulationserkennung)
    prevHash = models.CharField(max_length=64, blank=True, null=True)
    entryHash = models.CharField(max_length=64, blank=True, null=True)
    # Verbindliche Kettenordnung. createdAt taugt nicht als Ordnung: bei
    # Timestamp-Kollision (Uhr-Auflösung) entscheidet sonst die zufällige
    # UUID – die Verifikation meldet dann falschen Manipulations-Alarm.
    # unique=True erzwingt zudem eine lineare Kette bei parallelen Schreibern.
    seq = models.BigIntegerField(unique=True, blank=True, null=True, editable=False)

    class Meta:
        # Audit-Viewer-Filter, DSGVO-Export je Bewerbung, Zeitreihen
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["applicationId"]),
            models.Index(fields=["createdAt"]),
        ]

    def __str__(self):
        return f"{self.action} at {self.createdAt}"
