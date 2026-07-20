"""Zentraler Helfer für revisionssichere, integritätsgesicherte Audit-Logs.

Jeder Eintrag hasht seinen Vorgänger (Hash-Kette). Nachträgliche Änderung oder
Löschung eines Eintrags bricht die Kette und ist per `verify_audit_chain()`
erkennbar (UC-MB-12, UC-NS-02).

Die Kettenordnung ist die monotone Sequenz `seq` – NICHT createdAt: auf
schnellen Systemen kollidieren Timestamps (Uhr-Auflösung), und die zufällige
UUID würde die Reihenfolge dann nichtdeterministisch machen, sodass die
Verifikation falschen Manipulations-Alarm schlägt.
"""
import hashlib
import json
import uuid
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AuditLog


def _entry_hash(prev: str | None, action: str | None, user_id: str | None,
                application_id: str | None, metadata_json: str | None,
                created_iso: str | None) -> str:
    payload = "|".join([
        prev or "", action or "", user_id or "", application_id or "",
        metadata_json or "", created_iso or "",
    ])
    return hashlib.sha256(payload.encode("utf-8", "ignore")).hexdigest()


def create_chained_audit(action: str, user_id: str | None = None,
                         application_id: str | None = None,
                         metadata_json: str = "{}") -> AuditLog:
    """Legt einen Audit-Eintrag an und verkettet ihn mit dem letzten Eintrag.

    Die Unique-Constraint auf `seq` erzwingt eine lineare Kette auch bei
    parallelen Schreibern (kein Fork mit zwei gleichen Vorgängern);
    Kollisionen werden per Retry aufgelöst.
    """
    for _attempt in range(5):
        try:
            with transaction.atomic():
                last = (AuditLog.objects.select_for_update()
                        .filter(seq__isnull=False).order_by("-seq").first())
                prev = last.entryHash if last and last.entryHash else ""
                created = timezone.now()
                digest = _entry_hash(prev, action, user_id, application_id,
                                     metadata_json, created.isoformat())
                return AuditLog.objects.create(
                    action=action, userId=user_id, applicationId=application_id,
                    metadataJson=metadata_json, createdAt=created,
                    prevHash=prev, entryHash=digest,
                    # seq ist per Filter nie None; `or 0` nur fuer die Typpruefung
                    seq=((last.seq or 0) + 1) if last else 1,
                )
        except IntegrityError:
            continue
    raise IntegrityError(
        "Audit-Kette: Sequenznummer nach 5 Versuchen weiterhin belegt.")


def write_audit(action: str, user: Any = None,
                application_id: str | uuid.UUID | None = None,
                **metadata: Any) -> AuditLog:
    """Schreibt einen verketteten Audit-Eintrag (bevorzugter Einstiegspunkt)."""
    username = None
    if user is not None and getattr(user, "is_authenticated", False):
        username = user.get_username()
    return create_chained_audit(
        action=action,
        user_id=username,
        application_id=str(application_id) if application_id else None,
        metadata_json=json.dumps(metadata, default=str),
    )


def verify_audit_chain() -> dict:
    """Prüft die Integrität der Hash-Kette (in `seq`-Ordnung).

    Rückgabe: dict mit ok(bool), checked(int), unchained(int) und ggf. broken_id.
    - unchained: Alt-/Fremd-Einträge ohne Hash (vor Einführung der Kette) werden
      übersprungen, aber gezählt – sie brechen die Kette nicht.
    """
    prev = ""
    checked = 0
    unchained = (AuditLog.objects.filter(entryHash__isnull=True).count()
                 + AuditLog.objects.filter(entryHash="").count())
    chain = (AuditLog.objects.exclude(entryHash__isnull=True)
             .exclude(entryHash="").order_by("seq"))
    for e in chain.iterator():
        expected = _entry_hash(prev, e.action, e.userId, e.applicationId,
                               e.metadataJson, e.createdAt.isoformat())
        if expected != e.entryHash or (e.prevHash or "") != prev:
            return {"ok": False, "checked": checked, "unchained": unchained,
                    "broken_id": str(e.id)}
        prev = e.entryHash
        checked += 1
    return {"ok": True, "checked": checked, "unchained": unchained}
