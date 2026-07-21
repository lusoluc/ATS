"""Entgelttransparenz (EU-RL 2023/970) — zentrale Durchsetzungslogik.

Phase E1: Publish-Gate nach Art. 5 Abs. 1 — Bewerbende müssen das
Einstiegsentgelt bzw. dessen Spanne VOR dem Gespräch erfahren (bei uns:
direkt in der veröffentlichten Anzeige). Ohne Entgeltband geht deshalb
keine Stelle online — durchgesetzt in create_job und toggle_job_active.

Phase E2: Frageverbots-Wächter nach Art. 5 Abs. 2 — Arbeitgeber dürfen
Bewerbende NICHT nach ihrer Gehaltshistorie (aktuelles oder früheres
Entgelt) fragen. Durchgesetzt an allen Wegen, auf denen Fragen ins System
kommen: Stellen-Editor, zentrale Fragen-Registry, Jobfamilien-
Mindeststandards und KI-Zusatzfragen. WICHTIG: Die Frage nach der
GEHALTSVORSTELLUNG (Wunschgehalt) bleibt rechtlich zulässig und wird
bewusst nicht blockiert — die Muster verlangen Historie-Bezug.

Bewusst als eigenes Modul: die Wächter der Folgephasen (Art.-4-
Tätigkeitsbewertung, Spannen-Konsistenz) docken hier an, ohne Views
oder Modelle zu verstreuen.
"""
import re
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


PAY_HISTORY_MESSAGE = (
    "Entgelttransparenz: Fragen nach dem aktuellen oder früheren Gehalt sind "
    "unzulässig (EU-RL 2023/970, Art. 5 Abs. 2) und wurden entfernt. "
    "Zulässig bleibt die Frage nach der Gehaltsvorstellung."
)

# Historie-spezifische Muster (deutsch + englisch). Bewusst KEIN generisches
# "Gehalt": Gehaltsvorstellung/Wunschgehalt ist zulässig und darf nicht anschlagen.
_SALARY_HISTORY_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in (
        # "Ihr letztes/bisheriges/aktuelles/derzeitiges Gehalt/Verdienst/…"
        r"(letzt|bisherig|aktuell|derzeitig|momentan|früher|frueher|vorherig)\w*\s+"
        r"(brutto-?|netto-?)?(jahres-?|monats-?)?"
        r"(gehalt|vergütung|verguetung|verdienst|einkommen|entgelt|bezüge|bezuege|lohn)",
        # Gehaltshistorie / Gehaltsnachweis / Gehalts-/Lohnabrechnung
        r"(gehalt|verdienst|entgelt|lohn)s?-?\s?(historie|nachweis|abrechnung)",
        # "Was verdienen Sie derzeit?" / "Wie viel verdienst du?" / "Was haben Sie verdient?"
        r"was\s+verdien(en\s+sie|st\s+du)",
        r"wie\s*viel\s+(haben\s+sie|hast\s+du)?\s*verdien",
        r"was\s+(haben\s+sie|hast\s+du)\s+[^?]{0,40}verdient",
        # Englisch
        r"(current|previous|last|prior)\s+(salary|pay|compensation|remuneration|income)",
        r"(salary|pay|compensation)\s+history",
    )
]


def salary_history_violation(text: str) -> str | None:
    """Gefundener Gehaltshistorie-Bezug (Textausschnitt) — oder None.

    Art. 5 Abs. 2: Das Verbot betrifft die Frage nach BESTEHENDEN oder
    FRÜHEREN Entgelten. Die Gehaltsvorstellung bleibt zulässig."""
    for pattern in _SALARY_HISTORY_PATTERNS:
        match = pattern.search(text or "")
        if match:
            return match.group(0)
    return None


def transparency_overview() -> dict:
    """Kennzahlen für die Analytics-Seite (Phase E4).

    - coverage: veröffentlichte Stellen mit/ohne Entgeltband. Ohne Band
      sollte durch das Publish-Gate nichts mehr online sein; Altbestand
      aus der Zeit vor E1 wird hier sichtbar statt vergessen.
    - unevaluated_bands: aktive Bänder ohne vollständige Art.-4-Bewertung.
    - family_conflicts: Jobfamilien, deren veröffentlichte Stellen mehr als
      ein Band nutzen. Das ist eine AMPEL, kein Fehler — unterschiedliche
      Qualifikationsstufen in einer Familie sind legitim. Aber genau diese
      Fälle muss ein Träger begründen können (Art. 4), darum stehen sie hier.
    """
    from .models import JobPosting, PayBand

    published = JobPosting.objects.filter(workflowState__name="published")
    with_band = published.filter(payBand__isnull=False).count()
    total = published.count()

    unevaluated = [b for b in PayBand.objects.filter(archived=False)
                   if not b.has_evaluation]

    by_family: dict[str, dict] = {}
    for job in (published.filter(payBand__isnull=False)
                .select_related("jobFamily", "payBand")):
        band = job.payBand
        if band is None:  # per Filter ausgeschlossen — nur für die Typprüfung
            continue
        fam = by_family.setdefault(
            job.jobFamily.name, {"family": job.jobFamily.name, "bands": {}})
        fam["bands"].setdefault(band.name, []).append(job.title)
    conflicts = [
        {"family": f["family"],
         "bands": [{"band": name, "jobs": jobs}
                   for name, jobs in sorted(f["bands"].items())]}
        for f in by_family.values() if len(f["bands"]) > 1
    ]

    return {
        "published": total,
        "with_band": with_band,
        "without_band": total - with_band,
        "unevaluated_bands": [b.name for b in unevaluated],
        "family_conflicts": sorted(conflicts, key=lambda c: c["family"]),
    }


def strip_salary_history_questions(job: "JobPosting") -> list[str]:
    """Entfernt Gehaltshistorie-Fragen aus job.screeningQuestionsJson.

    Liefert die entfernten Fragetexte (leer = nichts zu tun). Der Aufrufer
    speichert und auditiert — Muster wie ensure_minimum_standards."""
    questions = job.screeningQuestionsJson or []
    if not isinstance(questions, list):
        return []
    kept, removed = [], []
    for q in questions:
        text = str(q.get("question", "")) if isinstance(q, dict) else str(q)
        if salary_history_violation(text):
            removed.append(text)
        else:
            kept.append(q)
    if removed:
        job.screeningQuestionsJson = kept
    return removed
