"""DSGVO-Betroffenenauskunft / Datenexport (Art. 15 & 20) – UC-MB-07, UC-AY-09.

Erzeugt einen vollständigen, maschinenlesbaren Export aller zu einer Person
gespeicherten Daten. `internalNotes` sind interne Bewertungen und werden bewusst
NICHT exportiert (kein Auskunftsanspruch auf interne Vermerke Dritter).
"""
from .models import Application, ApplicationDocument, AuditLog


def build_applicant_export(applicant) -> dict:
    """Baut das Export-Dict für eine bewerbende Person."""
    apps = (Application.objects
            .filter(applicant=applicant)
            .select_related("jobPosting")
            .order_by("createdAt"))

    applications = []
    for a in apps:
        docs = ApplicationDocument.objects.filter(application=a).values_list("name", flat=True)
        applications.append({
            "id": str(a.id),
            "stelle": a.jobPosting.title if a.jobPosting_id else None,
            "status": a.status,
            "quelle": a.source,
            "ki_score": a.aiScore,
            "ki_begruendung": a.aiRationale,
            "anschreiben": a.coverLetterTxt or "",
            "eingegangen_am": a.createdAt.isoformat(),
            "nachweise": list(docs),
            "einwilligung_talentpool": a.consentTalentPool,
        })

    app_ids = [str(a.id) for a in apps]
    audit = list(AuditLog.objects
                 .filter(applicationId__in=app_ids)
                 .order_by("createdAt")
                 .values("action", "userId", "applicationId", "createdAt"))
    for row in audit:
        row["createdAt"] = row["createdAt"].isoformat()

    return {
        "betroffene_person": {
            "id": str(applicant.id),
            "vorname": applicant.firstName,
            "nachname": applicant.lastName,
            "email": applicant.email,
            "telefon": applicant.phone or "",
            "erfasst_am": applicant.createdAt.isoformat(),
        },
        "bewerbungen": applications,
        "zugriffsprotokoll": audit,
        "hinweis": ("Interne Bewertungsvermerke sind nicht Teil dieser Auskunft. "
                    "Export gemäß DSGVO Art. 15 & 20."),
    }
