"""DSGVO-Betroffenenauskunft / Datenexport (Art. 15 & 20) – UC-MB-07, UC-AY-09.

Erzeugt einen vollständigen, maschinenlesbaren Export aller zu einer Person
gespeicherten Daten.

Der Export war lange nur über einen Management-Befehl zu bekommen – also nur
für jemanden mit Server-Zugang. Weder Bewerbende noch die Personalabteilung
kamen an ihn heran, obwohl Art. 12 Abs. 3 DSGVO eine Frist von einem Monat
setzt. Seit U4 hängen zwei Einstiege an derselben Funktion: der Selbstbedienung
im Bewerberportal und ein Knopf für HR-Admins.

Zum Umfang: Ausgelassen wird nur, was ausdrücklich benannt ist (Abschnitt
`nicht_enthalten`). Alles andere – auch die KI-Einordnung, der Absagegrund und
die Anschrift aus Bestandsimporten – gehört hinein, weil es sonst niemand
sehen kann.
"""
import json
from typing import Any

from .models import (
    Applicant,
    Application,
    ApplicationDocument,
    AuditLog,
    Message,
    PrivacyNoticeVersion,
    TalentPoolSubscription,
)
from .models.applications import disability_value_disclosed

#: Was NICHT im Export steht – und warum. Steht so auch in der Auskunft, damit
#: die betroffene Person nicht raten muss, ob etwas fehlt oder nicht existiert.
EXCLUDED_WITH_REASON = {
    "Datei-Inhalte": ("Lebenslauf und Nachweise sind als Liste enthalten; die "
                      "Dateien selbst gibt es über das Bewerberportal."),
    "Zugangs-Token": ("Magic-Link-Token sind Sicherheitsmerkmale. Ihre Heraus"
                      "gabe würde fremden Zugriff ermöglichen (Art. 15 Abs. 4)."),
    "Interne Vermerke": ("Interne Notizen der Fachabteilung werden auf "
                         "ausdrückliche Anforderung einzeln geprüft und, "
                         "soweit sie personenbezogene Daten enthalten, "
                         "nachgereicht. Sie sind nicht pauschal ausgenommen."),
}


def active_privacy_notice() -> "PrivacyNoticeVersion | None":
    """Die aktuell gültige Fassung des Datenschutzhinweises.

    Art. 7 Abs. 1 verlangt den Nachweis, *worin* eingewilligt wurde. Das Feld
    dafür gibt es seit der ersten Migration – befüllt hat es nie jemand, also
    ließ sich zu keiner Bewerbung sagen, welchen Text die Person gesehen hat.

    Bewusst ohne Auto-Anlage: Eine selbst erzeugte Fassung wäre ein Nachweis
    über einen Text, den nie jemand freigegeben hat. Fehlt sie, sagt
    `privacy_notice_status()` das offen.
    """
    return (PrivacyNoticeVersion.objects.filter(active=True)
            .order_by("-createdAt").first())


def privacy_notice_status() -> dict[str, Any]:
    """Zustand der Nachweiskette für die Governance-Sicht.

    `missing` heißt: Für neue Bewerbungen kann gar kein Einwilligungs-Nachweis
    entstehen. `unlinked` zählt den Altbestand – nicht rückwirkend heilbar,
    aber auch nicht zu verschweigen.
    """
    notice = active_privacy_notice()
    total = Application.objects.count()
    unlinked = Application.objects.filter(privacyNoticeVersion__isnull=True).count()
    return {
        "notice": notice,
        "version": notice.version if notice else None,
        "missing": notice is None,
        "applications_total": total,
        "applications_unlinked": unlinked,
        "applications_linked": total - unlinked,
    }


def _answers(app: Application) -> list[dict[str, str]]:
    raw = app.screeningAnswersJson or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            raw = {}
    if not isinstance(raw, dict):
        return []
    return [{"frage": str(k), "antwort": str(v)} for k, v in raw.items()]


def _talent_pool(applicant: Applicant) -> dict[str, Any] | None:
    """Der Einwilligungs-Beleg zum Talent-Pool.

    Die consentId wurde beim Opt-in vergeben, war danach aber nirgends
    abrufbar. Ein Nachweis, den niemand nachschlagen kann, ist keiner
    (Art. 7 Abs. 1).
    """
    sub = TalentPoolSubscription.objects.filter(email=applicant.email).first()
    if sub is None:
        return None
    try:
        criteria = json.loads(sub.criteria or "{}")
    except (TypeError, ValueError):
        criteria = {}
    return {
        "einwilligung_id": sub.consentId,
        "erteilt_am": sub.createdAt.isoformat(),
        "gueltig_bis": sub.expiresAt.isoformat(),
        "aktiv": sub.is_active,
        "suchkriterien": criteria,
        "widerruf": "jederzeit über den Abmelde-Link in jeder Benachrichtigung",
    }


def build_applicant_export(applicant: Applicant) -> dict[str, Any]:
    """Baut das Export-Dict für eine bewerbende Person."""
    apps = (Application.objects
            .filter(applicant=applicant)
            .select_related("jobPosting", "privacyNoticeVersion")
            .order_by("createdAt"))

    applications: list[dict[str, Any]] = []
    for a in apps:
        docs = ApplicationDocument.objects.filter(application=a).order_by("createdAt")
        msgs = Message.objects.filter(application=a).order_by("createdAt")
        entry: dict[str, Any] = {
            "id": str(a.id),
            "stelle": a.jobPosting.title if a.jobPosting_id else None,
            "status": a.status,
            "quelle": a.source,
            "ki_score": a.aiScore,
            "ki_begruendung": a.aiRationale,
            # Art. 15 Abs. 1 h: über eine automatisierte Einordnung ist samt
            # ihrer Tragweite zu informieren – die Note allein genügt nicht.
            "ki_hinweis": ("Lesehilfe, keine Entscheidung. Über Einladung und "
                           "Absage entscheiden immer Menschen."),
            "anschreiben": a.coverLetterTxt or "",
            "antworten_auf_rueckfragen": _answers(a),
            "eingegangen_am": a.createdAt.isoformat(),
            "zuletzt_geaendert": a.updatedAt.isoformat(),
            "gespraechsrunde": a.interviewRound,
            "nachweise": [{"name": d.name, "art": d.docType,
                           "hochgeladen_am": d.createdAt.isoformat()}
                          for d in docs],
            "nachrichten": [{"richtung": ("von Ihnen" if m.direction == "INBOUND"
                                          else "an Sie"),
                             "zeitpunkt": m.createdAt.isoformat(),
                             "inhalt": m.content}
                            for m in msgs],
            "einwilligung_talentpool": a.consentTalentPool,
            # Freiwillige Angabe nach § 164 SGB IX: ob sie vorliegt, gehört in
            # die Auskunft – über disability_value_disclosed, damit nicht
            # entschlüsselbarer Altbestand faelschlich als "ja" gilt.
            "angabe_schwerbehinderung": (
                "ja, freiwillig angegeben"
                if disability_value_disclosed(a.severeDisability) else "keine Angabe"),
            "datenschutzhinweis_fassung": (
                a.privacyNoticeVersion.version if a.privacyNoticeVersion
                else "nicht dokumentiert"),
        }
        if a.withdrawReason:
            entry["absage_oder_ruecknahme"] = a.withdrawReason
        if a.hiredAt:
            entry["eingestellt_am"] = a.hiredAt.isoformat()
        applications.append(entry)

    app_ids = [str(a.id) for a in apps]
    audit = [
        {**row, "createdAt": row["createdAt"].isoformat()}
        for row in AuditLog.objects
        .filter(applicationId__in=app_ids)
        .order_by("createdAt")
        .values("action", "userId", "applicationId", "createdAt")
    ]

    return {
        "betroffene_person": {
            "id": str(applicant.id),
            "vorname": applicant.firstName,
            "nachname": applicant.lastName,
            "email": applicant.email,
            "telefon": applicant.phone or "",
            # Wird nur beim Import aus Bestandslisten befüllt und war bis U4
            # in keiner Ansicht sichtbar – gespeichert, aber unauffindbar.
            "anschrift": applicant.address or "",
            "erfasst_am": applicant.createdAt.isoformat(),
        },
        "bewerbungen": applications,
        "talentpool_einwilligung": _talent_pool(applicant),
        "zugriffsprotokoll": audit,
        "nicht_enthalten": EXCLUDED_WITH_REASON,
        "ihre_rechte": {
            "berichtigung": "Art. 16 DSGVO",
            "loeschung": "Art. 17 DSGVO",
            "einschraenkung": "Art. 18 DSGVO",
            "widerspruch": "Art. 21 DSGVO",
            "beschwerde": "Art. 77 DSGVO – bei der zuständigen Aufsichtsbehörde",
        },
        "hinweis": "Auskunft und Datenübertragbarkeit nach Art. 15 und 20 DSGVO.",
    }
