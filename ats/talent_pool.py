"""Talent-Pool-Abgleich (C3): passende Pool-Personen zu einer Stelle finden.

Der Talent-Pool ist datensparsam: je Person nur die Kriterien, die ohnehin aus
ihren Bewerbungen abgeleitet wurden (Jobfamilien, Standorte) plus eine
Consent-Frist. Beim Veröffentlichen einer Stelle wird der Pool geprüft, damit
aus dem Archiv ein aktives Werkzeug wird: „3 Personen im Pool passen — anschreiben?"
"""
import json
from typing import TYPE_CHECKING

from django.utils import timezone

from .models import TalentPoolSubscription, email_blind_index

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from .models import JobPosting


def pool_matches_for_job(job: "JobPosting") -> list[TalentPoolSubscription]:
    """Aktive Pool-Personen, deren Kriterien zur Stelle passen (Familie ODER Standort).

    Nur nicht abgelaufene Einwilligungen; leere Kriterien matchen nie."""
    now = timezone.now()
    fam_id = str(job.jobFamily_id) if job.jobFamily_id else None
    loc_id = str(job.location_id) if job.location_id else None
    out: list[TalentPoolSubscription] = []
    for sub in TalentPoolSubscription.objects.filter(expiresAt__gte=now):
        try:
            crit = json.loads(sub.criteria or "{}")
        except (ValueError, TypeError):
            continue
        fam_ids = set(crit.get("job_families") or [])
        loc_ids = set(crit.get("locations") or [])
        if (fam_id and fam_id in fam_ids) or (loc_id and loc_id in loc_ids):
            out.append(sub)
    return out


def pool_person(sub: TalentPoolSubscription) -> dict:
    """Anzeigbare Person zum Pool-Eintrag.

    Der Pool selbst speichert datensparsam nur die E-Mail. Name und die letzte
    Bewerbung kommen ueber den E-Mail-Blind-Index aus dem Bewerber-Datensatz -
    ohne den Klartext preiszugeben. Fehlt der Datensatz, bleibt die E-Mail.
    """
    from .models import Applicant, Application
    name = sub.email
    last_app_id = None
    applicant = Applicant.objects.filter(
        emailHash=email_blind_index(sub.email)).first()
    if applicant:
        full = f"{applicant.firstName} {applicant.lastName}".strip()
        name = full or sub.email
        last = (Application.objects.filter(applicant=applicant)
                .order_by("-createdAt").values_list("id", flat=True).first())
        last_app_id = last
    return {"sub": sub, "name": name, "email": sub.email,
            "last_application_id": last_app_id}


def pool_candidates_for_job(job: "JobPosting") -> list[dict]:
    """Passende Pool-Personen mit Namen und Ansprache-Stand fuer die Anzeige.

    Je Treffer: Name, Link-Ziel fuer den Profil-Blick und ob die Person zu
    DIESER Stelle schon angeschrieben wurde (Einmal-Aktion: dann nicht erneut).
    """
    from .models import TalentPoolContact
    matches = pool_matches_for_job(job)
    if not matches:
        return []
    contacted = dict(TalentPoolContact.objects
                     .filter(jobPosting=job, subscription__in=matches)
                     .values_list("subscription_id", "sentAt"))
    out = []
    for sub in matches:
        entry = pool_person(sub)
        entry["contacted_at"] = contacted.get(sub.id)
        out.append(entry)
    return out


def invite_pool_person(sub: TalentPoolSubscription, job: "JobPosting",
                       user: "User | None") -> bool:
    """Laedt eine Pool-Person zur Bewerbung auf diese Stelle ein.

    Rueckgabe True, wenn wirklich angeschrieben wurde; False, wenn die Person
    fuer diese Stelle bereits kontaktiert wurde oder die Einwilligung abgelaufen
    ist. Die Doppel-Ansprache verhindert zusaetzlich unique_together im Modell -
    wer im Pool ist, hat in gelegentliche Hinweise eingewilligt, nicht in
    Dauer-Werbung.
    """
    import logging

    from .audit import write_audit
    from .models import TalentPoolContact

    logger = logging.getLogger(__name__)
    if not sub.is_active:
        return False
    _, created = TalentPoolContact.objects.get_or_create(
        subscription=sub, jobPosting=job,
        defaults={"sentBy": user if user is not None and user.pk else None})
    if not created:
        return False
    try:
        from django.core.mail import send_mail
        send_mail(
            f"Eine Stelle, die zu Ihnen passen könnte: {job.title}",
            (f"Guten Tag,\n\nSie sind in unserem Talent-Pool – und wir haben "
             f"eine neue Stelle, die zu Ihren bisherigen Bewerbungen passt:\n\n"
             f"{job.title}"
             f"{' – ' + job.location.name if job.location_id else ''}\n"
             f"Details und Bewerbung: /jobs/{job.id}/\n\n"
             "Kein Interesse mehr? In Ihrem Bewerbungsportal können Sie "
             "jederzeit aus dem Talent-Pool austreten.\n\nFreundliche Grüße"),
            None, [sub.email], fail_silently=True)
    except Exception:
        logger.exception("Talent-Pool-Ansprache fehlgeschlagen")
    write_audit("TALENT_POOL_CONTACTED", user=user,
                subscription=str(sub.id), job_id=str(job.id))
    return True
