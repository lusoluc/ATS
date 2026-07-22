"""KI-Domaene: Best-Performer-Profile (Embeddings) und die Async-Task-Queue."""
import uuid

from django.db import models
from django.utils import timezone

from .organization import JobFamily

# ============================================================================
# 10. AI LEARNING & CONTEXTUAL RAG
# ============================================================================

class BestPerformerProfile(models.Model):
    """Semantisches Profil eines "Best-Performer"-Lebenslaufs.

    Zweck: Das Sichtungs-Team kann anonymisierte Lebenslaeufe besonders
    geeigneter Mitarbeitender einspeisen. Daraus wird per lokalem Ollama ein
    Embedding (Vektor) erzeugt und gespeichert. Neue Bewerbungen lassen sich
    dann semantisch mit diesen Profilen vergleichen (Kosinus-Aehnlichkeit).

    EHRLICHKEIT: Es wird NUR gespeichert, was Ollama tatsaechlich geliefert
    hat. Ist Ollama nicht erreichbar, entsteht KEIN Profil (kein Schein).

    DATENSCHUTZ: Der Roh-Lebenslauf wird NICHT gespeichert - nur der Vektor
    und eine kurze, vom Betreiber vergebene Bezeichnung. Der Vektor ist nicht
    zurueckrechenbar in den Originaltext.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          editable=False)
    label = models.CharField(max_length=200)
    jobFamily = models.ForeignKey(JobFamily, on_delete=models.SET_NULL,
                                  blank=True, null=True,
                                  related_name='bestPerformerProfiles')
    model = models.CharField(max_length=100)
    dim = models.IntegerField(default=0)
    vectorJson = models.JSONField()          # JSON-Liste floats (Embedding)
    createdBy = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                  blank=True, null=True)
    createdAt = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-createdAt']

    def vector(self):
        return self.vectorJson if isinstance(self.vectorJson, list) else []


class AiTask(models.Model):
    """WP7/L6: DB-gestützte Async-Queue für KI-Aufgaben.

    Bewusst ohne externe Broker (Redis/Celery) – On-Prem-/Air-Gap-freundlich.
    Ein Worker-Prozess (`manage.py ai_worker`) arbeitet PENDING-Tasks ab; die UI
    blockiert dadurch nie auf LLM-Latenz.
    """
    STATUS = ["PENDING", "RUNNING", "DONE", "FAILED"]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taskType = models.CharField(max_length=50)          # z.B. SCORE_APPLICATION
    payloadJson = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="PENDING")
    resultJson = models.JSONField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    maxAttempts = models.IntegerField(default=3)
    createdAt = models.DateTimeField(default=timezone.now)
    startedAt = models.DateTimeField(blank=True, null=True)
    finishedAt = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.taskType} [{self.status}]"
