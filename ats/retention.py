"""Datenaufbewahrung (UC-AR-13 / UC-MB-06): konfigurierbare Loeschfrist.

Eine Wahrheit fuer Command UND Verwaltungsseite: die Frist kommt aus dem
SystemSetting RETENTION_DAYS (Default 180 Tage = 6 Monate), die
Trockenlauf-Vorschau zaehlt, was der naechste Lauf anonymisieren wuerde -
als reine Zahlen, ohne Namen (die Seite ist fuer DSB/HR-Admin, nicht fuer
Einzelfall-Recherche).
"""
import datetime

from django.db.models import QuerySet
from django.utils import timezone

from .models import Application, SystemSetting

RETENTION_DAYS_KEY = "RETENTION_DAYS"
DEFAULT_RETENTION_DAYS = 180
# Leitplanken: unter 30 Tagen waere die Frist praktisch eine Sofort-Loeschung
# laufender Nachweispflichten (AGG: 2+ Monate Klagefrist), ueber 3 Jahren
# kaum mit Datenminimierung vereinbar.
MIN_DAYS, MAX_DAYS = 30, 1095


def configured_retention_days() -> int:
    row = SystemSetting.objects.filter(key=RETENTION_DAYS_KEY).first()
    try:
        days = int((row.value if row else "") or DEFAULT_RETENTION_DAYS)
    except (TypeError, ValueError):
        return DEFAULT_RETENTION_DAYS
    return max(MIN_DAYS, min(MAX_DAYS, days))


def retention_queryset(days: "int | None" = None) -> "QuerySet[Application]":
    """Bewerbungen, die der naechste Lauf anonymisieren wuerde - exakt die
    Kriterien des data_retention-Commands (eine Wahrheit)."""
    days = days if days is not None else configured_retention_days()
    cutoff = timezone.now() - datetime.timedelta(days=days)
    return Application.objects.filter(
        status__in=['REJECTED', 'WITHDRAWN'],
        updatedAt__lt=cutoff,
        consentTalentPool=False)


def dry_run_preview(days: "int | None" = None) -> dict:
    """Trockenlauf als Aggregat: Anzahl je Status + Gesamtzahl, keine Namen."""
    days = days if days is not None else configured_retention_days()
    qs = retention_queryset(days)
    by_status: dict[str, int] = {}
    for status in qs.values_list('status', flat=True):
        by_status[status] = by_status.get(status, 0) + 1
    return {
        'days': days,
        'total': sum(by_status.values()),
        'rejected': by_status.get('REJECTED', 0),
        'withdrawn': by_status.get('WITHDRAWN', 0),
    }
