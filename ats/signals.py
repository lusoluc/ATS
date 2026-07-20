"""Entgelttransparenz E3: gerichtsfeste Verankerung veröffentlichter Spannen.

Jede Entgeltspanne, die öffentlich wird (Stelle geht auf 'published' oder
eine veröffentlichte Stelle wechselt das Entgeltband), wird als Eintrag
PAY_RANGE_PUBLISHED in der Audit-HASH-KETTE verankert. Ein Träger kann
damit manipulationssicher nachweisen, WELCHE Spanne WANN für WELCHE
Stelle öffentlich war (Art. 5 Abs. 1 — Nachweis statt Behauptung).

Als Signal statt Einzel-Aufrufen: JEDER Pfad, der eine Stelle
veröffentlicht (Editor, Schnell-Toggle, Freigabe-Automatik, künftige
Wege), läuft über JobPosting.save() — und wird damit automatisch erfasst.
"""
import json
from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import JobPosting


@receiver(pre_save, sender=JobPosting, dispatch_uid="pay_range_pre_snapshot")
def _snapshot_publish_state(sender: type, instance: JobPosting, **kwargs: Any) -> None:
    """Merkt sich vor dem Speichern, ob die Stelle publiziert war und mit welchem Band."""
    if instance._state.adding:
        instance._pre_pay_state = False, None
        return
    row = (JobPosting.objects.filter(pk=instance.pk)
           .values_list("workflowState__name", "payBand_id").first())
    if row is None:
        instance._pre_pay_state = False, None
    else:
        instance._pre_pay_state = row[0] == "published", row[1]


@receiver(post_save, sender=JobPosting, dispatch_uid="pay_range_published")
def _record_published_range(sender: type, instance: JobPosting, **kwargs: Any) -> None:
    was_published, old_band_id = getattr(instance, "_pre_pay_state", (False, None))
    is_published = (instance.workflowState_id is not None
                    and instance.workflowState.name == "published")
    if not (is_published and instance.payBand_id):
        return
    if was_published and old_band_id == instance.payBand_id:
        return  # unverändert öffentlich — kein Doppel-Eintrag
    from .audit import create_chained_audit
    band = instance.payBand
    if band is None:  # nur für die Typprüfung — payBand_id ist oben geprüft
        return
    create_chained_audit(
        "PAY_RANGE_PUBLISHED",
        metadata_json=json.dumps({
            "jobId": str(instance.id),
            "job": instance.title,
            "band": band.name,
            "min": str(band.minAmount),
            "max": str(band.maxAmount),
            "period": band.period,
            "tariff": band.collectiveAgreement,
            "evaluated": band.has_evaluation,  # Art.-4-Bewertung vorhanden?
            "event": "BAND_CHANGED" if was_published else "PUBLISHED",
        }, ensure_ascii=False))
