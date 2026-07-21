"""Governance & Sicherheit: Workflow-Zustaende, Datenschutzhinweis-Versionen, Rollen, Alt-User-Modell."""
import uuid

from django.db import models
from django.utils import timezone

from .organization import Facility

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
