"""Entgelttransparenz (EU-RL 2023/970) — zentrale Durchsetzungslogik.

Phase E1: Publish-Gate nach Art. 5 Abs. 1 — Bewerbende müssen das
Einstiegsentgelt bzw. dessen Spanne VOR dem Gespräch erfahren (bei uns:
direkt in der veröffentlichten Anzeige). Ohne Entgeltband geht deshalb
keine Stelle online — durchgesetzt in create_job und toggle_job_active.

Bewusst als eigenes Modul: die Wächter der Folgephasen (Frageverbot nach
Gehaltshistorie, Art.-4-Tätigkeitsbewertung, Spannen-Konsistenz) docken
hier an, ohne Views oder Modelle zu verstreuen.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import JobPosting


PAY_GATE_MESSAGE = (
    "Entgelttransparenz: Ohne Vergütungsangabe (Entgeltband) darf die Stelle "
    "nicht veröffentlicht werden (EU-RL 2023/970, Art. 5). Die Stelle wurde als "
    "Entwurf gespeichert — bitte im Stellen-Editor ein Entgeltband wählen."
)


def pay_blocked_reason(job: "JobPosting") -> str | None:
    """Grund, warum die Stelle (noch) nicht veröffentlicht werden darf — oder None."""
    if job.payBand_id is None:
        return PAY_GATE_MESSAGE
    return None
