"""WP7/L6: Minimale, abhängigkeitsfreie Async-Queue für KI-Aufgaben.

Nutzung:
    from ats.queue import enqueue
    enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})

Abarbeitung:
    python manage.py ai_worker --loop     (Betrieb, z.B. als systemd-Service)
    python manage.py ai_worker --once     (einmalig abarbeiten, z.B. Cron/Tests)
"""
import json
import logging

from django.db import transaction
from django.utils import timezone

from .models import AiTask

logger = logging.getLogger(__name__)


def enqueue(task_type: str, payload: dict) -> AiTask:
    return AiTask.objects.create(taskType=task_type,
                                 payloadJson=json.dumps(payload, default=str))


# --- Handler ------------------------------------------------------------------

def _handle_score_application(payload: dict) -> dict:
    """Scort eine Bewerbung asynchron (nutzt die injection-sichere Pipeline)."""
    from .models import Application
    from .views import evaluate_with_local_gemma
    app = Application.objects.get(id=payload["application_id"])
    score, rationale = evaluate_with_local_gemma(
        app.coverLetterTxt or "", app.jobPosting.requirementsJson)
    app.aiScore = score
    app.aiRationale = rationale
    app.save(update_fields=["aiScore", "aiRationale", "updatedAt"])
    return {"score": score}


HANDLERS = {
    "SCORE_APPLICATION": _handle_score_application,
}


# --- Worker-Kern ---------------------------------------------------------------

def claim_next() -> AiTask | None:
    """Nimmt atomar den ältesten PENDING-Task (kein Doppel-Claim bei mehreren Workern)."""
    with transaction.atomic():
        task = (AiTask.objects.select_for_update(skip_locked=True)
                .filter(status="PENDING").order_by("createdAt").first())
        if not task:
            return None
        task.status = "RUNNING"
        task.startedAt = timezone.now()
        task.attempts += 1
        task.save(update_fields=["status", "startedAt", "attempts"])
        return task


def process(task: AiTask) -> None:
    handler = HANDLERS.get(task.taskType)
    try:
        if handler is None:
            raise ValueError(f"Unbekannter taskType: {task.taskType}")
        result = handler(json.loads(task.payloadJson or "{}"))
        task.status = "DONE"
        task.resultJson = json.dumps(result or {}, default=str)
        task.error = None
    except Exception as e:
        logger.exception("AiTask %s fehlgeschlagen (Versuch %s/%s)",
                         task.id, task.attempts, task.maxAttempts)
        task.error = str(e)[:1000]
        task.status = "FAILED" if task.attempts >= task.maxAttempts else "PENDING"
    task.finishedAt = timezone.now()
    task.save(update_fields=["status", "resultJson", "error", "finishedAt"])


def run_pending(limit: int = 50) -> int:
    """Arbeitet bis zu `limit` Tasks ab; Rückgabe: Anzahl verarbeitet."""
    n = 0
    while n < limit:
        task = claim_next()
        if not task:
            break
        process(task)
        n += 1
    return n


def queue_depth() -> dict:
    from django.db.models import Count
    rows = AiTask.objects.values("status").annotate(c=Count("id"))
    return {r["status"]: r["c"] for r in rows}
