"""L2: Bewerber-Steckbrief - ein schnelles, faktentreues Bild beim Öffnen.

Keine Rangliste, kein Bewerber gegen Bewerber. Beim Öffnen einer Karte eine
kurze Zusammenfassung, damit der Prüfer in Sekunden ein Bild hat - drei
Sekunden statt drei Minuten Lesen.

Streng faktentreu: der Steckbrief wird deterministisch aus vorhandenen Feldern
gebaut (Screening-Antworten gegen die K.O.-Kriterien der Stelle, Erwähnungen
der Anforderungen im Anschreiben, Vollständigkeit, Quelle, Zeit). Eine lokale
KI darf diesen Text spaeter nur UMFORMULIEREN - erfinden, hinzufügen oder
weglassen ist ausgeschlossen (das macht die View, fail-safe). Die gelernte
Einordnung (A/B/C/D) steckt in L3, nicht hier.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime

from django.utils import timezone

from .models import Application
from .models.applications import disability_value_disclosed

# Fuellwoerter, die beim Anforderungs-Abgleich nichts kennzeichnen.
_STOP = {
    "und", "oder", "mit", "von", "der", "die", "das", "den", "dem", "ein",
    "eine", "einen", "einer", "fuer", "sowie", "sehr", "gute", "guter",
    "gutes", "jahre", "jahren", "mind", "mindestens", "idealerweise", "bzw",
    "z.b", "zum", "zur", "sind", "ist", "wird", "werden", "kenntnisse",
    "erfahrung", "erfahrungen", "abgeschlossene", "abgeschlossenes",
}


def _fold(text: str) -> str:
    t = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return t


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", _fold(text))
            if len(t) >= 4 and t not in _STOP]


@dataclass
class SteckbriefFacts:
    name: str
    job_title: str
    ko_total: int
    ko_met: int
    ko_missing: list[str] = field(default_factory=list)   # Frage-Texte offen
    req_total: int = 0
    req_hits: list[str] = field(default_factory=list)      # erwaehnte Anforderungen
    has_cv: bool = False
    has_cover: bool = False
    doc_count: int = 0
    source: str = "DIRECT"
    days_since: int = 0
    repeat_count: int = 1                                    # Bewerbungen dieser Person
    ai_score: "str | None" = None
    # § 164 SGB IX: freiwillige Angabe - nur Anzeige/SBV-Einbindung,
    # NIE Bewertungs-Eingabe.
    disability_disclosed: bool = False


def build_facts(app: Application, now: "datetime | None" = None) -> SteckbriefFacts:
    """Sammelt die harten Fakten zu einer Bewerbung - deterministisch."""
    now = now or timezone.now()
    job = app.jobPosting

    # K.O.-Kriterien: Pflichtfragen mit erwarteter Antwort (Antworten sind
    # nach Frage-TEXT verschluesselt gespeichert).
    answers: dict[str, str] = app.screeningAnswersJson if isinstance(
        app.screeningAnswersJson, dict) else {}
    ko = [q for q in (job.screeningQuestionsJson or [])
          if q.get("isMandatory") and q.get("expectedAnswer")]
    ko_met = 0
    ko_missing: list[str] = []
    for q in ko:
        if answers.get(q.get("question")) == q.get("expectedAnswer"):
            ko_met += 1
        else:
            ko_missing.append(q.get("question", ""))

    # Anforderungs-Erwaehnungen im Anschreiben (Text-Signal, keine gepruefte
    # Qualifikation - entsprechend vorsichtig formuliert).
    cover = _fold(app.coverLetterTxt or "")
    reqs = [r for r in (job.requirementsJson or []) if str(r).strip()]
    req_hits: list[str] = []
    if cover:
        for r in reqs:
            toks = _tokens(str(r))
            if toks and any(t in cover for t in toks):
                req_hits.append(str(r).strip())

    repeat_count = Application.objects.filter(
        applicant_id=app.applicant_id).count()

    return SteckbriefFacts(
        name=f"{app.applicant.firstName} {app.applicant.lastName}".strip(),
        job_title=job.title,
        ko_total=len(ko), ko_met=ko_met, ko_missing=ko_missing,
        req_total=len(reqs), req_hits=req_hits,
        has_cv=bool(app.cvStorageId),
        has_cover=bool((app.coverLetterTxt or "").strip()),
        doc_count=app.documents.count(),
        source=app.source or "DIRECT",
        days_since=max(0, (now - app.createdAt).days),
        repeat_count=repeat_count,
        ai_score=app.aiScore or None,
        disability_disclosed=disability_value_disclosed(app.severeDisability))


def facts_to_bullets(facts: SteckbriefFacts) -> list[str]:
    """Die Fakten als kurze, einzelne Aussagen (fuer die Chip-Anzeige)."""
    out: list[str] = []
    if facts.ko_total:
        if facts.ko_met == facts.ko_total:
            out.append(f"Erfüllt alle {facts.ko_total} Pflichtkriterien")
        else:
            miss = ", ".join(m for m in facts.ko_missing if m)[:120]
            out.append(f"Erfüllt {facts.ko_met} von {facts.ko_total} "
                       f"Pflichtkriterien" + (f" (offen: {miss})" if miss else ""))
    if facts.req_total:
        out.append(f"Anschreiben greift {len(facts.req_hits)} von "
                   f"{facts.req_total} Anforderungen auf")
    if not facts.has_cover:
        out.append("Kein Anschreiben")
    if facts.doc_count:
        out.append(f"{facts.doc_count} zusätzliche Nachweise")
    if facts.repeat_count >= 2:
        out.append(f"Bewirbt sich erneut ({facts.repeat_count} Bewerbungen)")
    if facts.disability_disclosed:
        # § 164 SGB IX: Hinweis fuer das Verfahren (SBV ist einbezogen) -
        # bewusst neutral formuliert, keine Bewertungs-Aussage.
        out.append("Schwerbehinderung angegeben – SBV einbezogen (§ 164 SGB IX)")
    return out


def facts_to_text(facts: SteckbriefFacts) -> str:
    """Ein knapper, faktentreuer Fließtext (immer verfügbar, ohne KI)."""
    parts: list[str] = []
    if facts.ko_total:
        if facts.ko_met == facts.ko_total:
            parts.append(f"Erfüllt alle {facts.ko_total} Pflichtkriterien der Stelle.")
        else:
            miss = ", ".join(m for m in facts.ko_missing if m)
            parts.append(
                f"Erfüllt {facts.ko_met} von {facts.ko_total} Pflichtkriterien"
                + (f" (offen: {miss})." if miss else "."))
    if facts.req_total:
        if facts.req_hits:
            hits = "; ".join(facts.req_hits[:3])
            parts.append(f"Das Anschreiben greift {len(facts.req_hits)} von "
                         f"{facts.req_total} Anforderungen auf ({hits}).")
        else:
            parts.append("Das Anschreiben nennt keine der Anforderungen ausdrücklich.")
    elif not facts.has_cover:
        parts.append("Kein Anschreiben übermittelt.")
    if facts.repeat_count >= 2:
        parts.append(f"Hat sich bereits früher beworben "
                     f"({facts.repeat_count} Bewerbungen insgesamt).")
    parts.append(f"Eingegangen vor {facts.days_since} Tag"
                 f"{'en' if facts.days_since != 1 else ''} über {facts.source}.")
    return " ".join(parts)
