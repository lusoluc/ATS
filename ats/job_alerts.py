"""Job-Alert-Matching (UC-AY-11/12, UC-RI-10) – reine, testbare Funktionen.

Scope-Möglichkeiten je Abo (kombinierbar, ODER-verknüpft):
- globalAlert: alle neuen Stellen
- keyword:    Stichwort im Jobtitel (z.B. "Pflege")
- facility:   nur Stellen einer Einrichtung ("Firma")
- locations + radiusKm: Umkreis in Kilometern um gewählte Standorte (Haversine
  auf Location.lat/lng; fehlen Koordinaten, zählt Standort-Gleichheit)

DSGVO / Verfall:
- Ein Abo verfällt ALERT_TTL_DAYS nach der letzten Bestätigung (lastConfirmedAt).
  Verfallene Abos werden nicht mehr beliefert und vom Versand-Command gelöscht
  (Datensparsamkeit statt ewiger Vorratshaltung).
- Abmeldung jederzeit über managementToken-Link; Bestätigung (Double-Opt-in)
  über confirmationToken.
"""
import json
import math
from datetime import timedelta

from django.utils import timezone

ALERT_TTL_DAYS = 365  # Verfall: 12 Monate nach letzter Bestätigung


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Großkreis-Distanz in km."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def is_expired(sub, now=None) -> bool:
    now = now or timezone.now()
    anchor = sub.lastConfirmedAt or sub.createdAt
    return anchor < now - timedelta(days=ALERT_TTL_DAYS)


def _within_radius(sub, job, location_by_id) -> bool:
    if not job.location_id:
        return False
    try:
        center_ids = json.loads(sub.locations or "[]")
    except (ValueError, TypeError):
        center_ids = []
    if not center_ids:
        return False
    job_loc = job.location
    for cid in center_ids:
        center = location_by_id.get(str(cid))
        if center is None:
            continue
        if str(job.location_id) == str(cid):
            return True  # gleicher Standort zählt immer
        if (sub.radiusKm and center.lat is not None and center.lng is not None
                and job_loc.lat is not None and job_loc.lng is not None):
            if haversine_km(center.lat, center.lng, job_loc.lat, job_loc.lng) <= sub.radiusKm:
                return True
    return False


def subscription_matches_job(sub, job, location_by_id) -> bool:
    """Prüft, ob ein aktives, nicht verfallenes Abo auf eine Stelle passt."""
    if sub.status != "ACTIVE" or is_expired(sub):
        return False
    if sub.globalAlert:
        return True
    if sub.keyword and sub.keyword.strip().lower() in (job.title or "").lower():
        return True
    if sub.facility_id and sub.facility_id == job.facility_id:
        return True
    return _within_radius(sub, job, location_by_id)


def match_subscribers_for_job(job):
    """Alle Abos, die auf diese Stelle passen (für den Versand)."""
    from .models import JobAlertSubscription, Location
    location_by_id = {str(l.id): l for l in Location.objects.all()}
    return [sub for sub in JobAlertSubscription.objects.filter(status="ACTIVE")
            .select_related("facility")
            if subscription_matches_job(sub, job, location_by_id)]
