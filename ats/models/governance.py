"""Governance & Sicherheit: Workflow-Zustaende und Datenschutzhinweis-Versionen."""
import uuid

from django.db import models
from django.utils import timezone

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

# Hier standen Role/User/UserFacility - eine eigene Benutzer-, Rollen- und
# Zuordnungstabelle aus dem Prisma-Vorgaenger. Angemeldet hat sich damit nie
# jemand: Authentifizierung, Rollen und Zugriffsbereiche laufen ueber Djangos
# Benutzermodell, Gruppen und `UserScope`. Die Tabellen blieben leer und waren
# nicht nur nutzlos, sondern schaedlich - ein Fremdschluessel auf dieses tote
# User-Modell hat die Freigabe-Urheber jahrelang unbefuellbar gemacht.
