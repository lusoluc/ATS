"""L3: gelerntes, ERKLAERBARES A/B/C/D-Scoring (transparente erste Stufe).

Kein zweites Ranking neben dem Score - das bestehende A/B/C/D wird besser, aus
den TATSAECHLICHEN Entscheidungen des Teams. Diese Stufe ist bewusst
transparent (keine Black Box): pro Kontext wird gemessen, welche stellen-
relevanten Merkmale mit einer Einladung zusammenhaengen (Lift), das Score ist
eine gewichtete Summe erfuellter Kriterien, kalibriert auf die Baender - und
jede Note kommt mit ihrer Begruendung.

Leitplanken (EU AI Act, Hochrisiko):
- NUR stellenrelevante, NIE geschuetzte Merkmale als Eingabe. Datensparsamkeit.
- Label = reale Screening-Entscheidung (eingeladen/eingestellt vs. abgelehnt)
  aus dem STATUS_CHANGE-Verlauf - die Wahrheit, die das Team selbst schuf.
- Interview-Feedback fliesst NICHT als Vorfilter-Merkmal ein (liegt erst nach
  dem Gespraech vor).
- Pro Kontext gelernt (Jobfamilie/Standort/Abteilung, ueber die Leiter), nur
  wo genug Entscheidungen vorliegen. Kaltstart: kein gelerntes Score.
- Erklaerbar: grade_application liefert die Begruendung je Merkmal.

Ob dieses Score ANGEZEIGT/genutzt wird, entscheidet die Messstrecke
(scoring_eval: Ehrlichkeits-Schranke) plus das Opt-in - nicht dieses Modul.
"""
import re
from dataclasses import dataclass

from .insights import (
    POSITIVE_STATUSES,
    LearningScope,
    _reached,
    _status_events,
    resolve_learning_scope,
)
from .models import Application, JobPosting

# Generische, stellenrelevante Merkmale (ueber Stellen hinweg vergleichbar,
# damit je Kontext gelernt werden kann - unabhaengig davon, welche konkreten
# Fragen eine einzelne Stelle hatte). Bewusst keine geschuetzten Merkmale.
FEATURES = ["ko_all", "ko_ratio", "req_coverage", "has_cover"]

FEATURE_LABELS = {
    "ko_all": "Alle Pflichtkriterien erfüllt",
    "ko_ratio": "Anteil erfüllter Pflichtkriterien",
    "req_coverage": "Anschreiben deckt Anforderungen",
    "has_cover": "Anschreiben vorhanden",
}


@dataclass
class LearnedModel:
    weights: dict[str, float]          # Merkmal -> Gewicht (Lift, kann negativ)
    thresholds: list[float]            # [A>=, B>=, C>=] auf dem Rohscore
    context_label: str                 # z. B. "Jobfamilie Pflege"
    sample_size: int                   # gelernte Entscheidungen
    base_rate: float                   # Einladungsquote im Kontext


def _features_for_app(app: Application) -> dict[str, float]:
    """Merkmalsvektor NUR aus den eigenen Feldern der Bewerbung + der Stelle
    (kein N+1: keine Zusatzabfragen). Werte in [0, 1]."""
    job = app.jobPosting
    answers = app.screeningAnswersJson if isinstance(
        app.screeningAnswersJson, dict) else {}
    ko = [q for q in (job.screeningQuestionsJson or [])
          if q.get("isMandatory") and q.get("expectedAnswer")]
    ko_met = sum(1 for q in ko
                 if answers.get(q.get("question")) == q.get("expectedAnswer"))
    ko_ratio = (ko_met / len(ko)) if ko else 1.0
    ko_all = 1.0 if (not ko or ko_met == len(ko)) else 0.0

    reqs = [str(r) for r in (job.requirementsJson or []) if str(r).strip()]
    cover = (app.coverLetterTxt or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        cover = cover.replace(a, b)
    if reqs and cover:
        hits = 0
        for r in reqs:
            toks = [t for t in re.split(r"[^a-z0-9]+", r.lower()
                                        .replace("ä", "ae").replace("ö", "oe")
                                        .replace("ü", "ue").replace("ß", "ss"))
                    if len(t) >= 4]
            if toks and any(t in cover for t in toks):
                hits += 1
        req_coverage = hits / len(reqs)
    else:
        req_coverage = 0.0

    has_cover = 1.0 if (app.coverLetterTxt or "").strip() else 0.0
    return {"ko_all": ko_all, "ko_ratio": ko_ratio,
            "req_coverage": req_coverage, "has_cover": has_cover}


def _labelled_rows(apps: list[Application]) -> list[tuple[dict[str, float], bool]]:
    """(Merkmalsvektor, eingeladen?) je abgeschlossener Bewerbung. Der Verlauf
    wird EINMAL geladen (kein N+1). Eingeladen = erreichte je INVITED/HIRED."""
    events = _status_events([str(a.id) for a in apps])
    rows: list[tuple[dict[str, float], bool]] = []
    for a in apps:
        invited = bool(_reached(str(a.id), a.status, events) & POSITIVE_STATUSES)
        rows.append((_features_for_app(a), invited))
    return rows


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(q * (len(sorted_vals) - 1)))
    return sorted_vals[idx]


def _raw_score(feats: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights.get(f, 0.0) * feats.get(f, 0.0) for f in FEATURES)


def fit_model(rows: list[tuple[dict[str, float], bool]],
              context_label: str) -> "LearnedModel | None":
    """Lernt Gewichte per Lift und kalibriert die Baender auf die
    Score-Verteilung des Trainings. None bei leerer Datenlage."""
    if not rows:
        return None
    labels = [1.0 if inv else 0.0 for _, inv in rows]
    base_rate = _mean(labels)

    weights: dict[str, float] = {}
    for f in FEATURES:
        pos = [1.0 if inv else 0.0 for feats, inv in rows if feats[f] >= 0.5]
        neg = [1.0 if inv else 0.0 for feats, inv in rows if feats[f] < 0.5]
        # Lift = Einladungsquote MIT dem Merkmal minus OHNE (in [-1, 1]).
        weights[f] = (_mean(pos) - _mean(neg)) if (pos and neg) else 0.0

    scores = sorted(_raw_score(feats, weights) for feats, _ in rows)
    thresholds = [_quantile(scores, 0.75), _quantile(scores, 0.50),
                  _quantile(scores, 0.25)]
    return LearnedModel(weights=weights, thresholds=thresholds,
                        context_label=context_label, sample_size=len(rows),
                        base_rate=round(base_rate, 3))


def learn_context_model(scope: LearningScope) -> "LearnedModel | None":
    """Gelerntes Modell fuer eine Kontext-Ebene. Nur wenn die Ebene belastbar
    ist (>= Mindestmenge); sonst None (Kaltstart -> kein gelerntes Score)."""
    if not scope.sufficient:
        return None
    from .insights import DECIDED_STATUSES
    apps = list(scope.applications.filter(status__in=DECIDED_STATUSES)
                .select_related("jobPosting"))
    return fit_model(_labelled_rows(apps), scope.label)


def learn_for_job(job: JobPosting,
                  base: "object | None" = None) -> "LearnedModel | None":
    scope = resolve_learning_scope(job, base)  # type: ignore[arg-type]
    return learn_context_model(scope)


def grade_application(app: Application,
                      model: LearnedModel) -> tuple[str, list[str]]:
    """Note A/B/C/D + Begruendung. Die Begruendung nennt die Merkmale, die
    (mit positivem Gewicht) fuer die Note sprachen - erklaerbar, keine Black
    Box."""
    feats = _features_for_app(app)
    score = _raw_score(feats, model.weights)
    a, b, c = model.thresholds
    if score >= a:
        grade = "A"
    elif score >= b:
        grade = "B"
    elif score >= c:
        grade = "C"
    else:
        grade = "D"

    reasons: list[str] = []
    for f in FEATURES:
        w = model.weights.get(f, 0.0)
        if w > 0.02 and feats[f] >= 0.5:
            reasons.append(f"{FEATURE_LABELS[f]} (+)")
        elif w > 0.02 and feats[f] < 0.5:
            reasons.append(f"{FEATURE_LABELS[f]}: offen (−)")
    if not reasons:
        reasons.append("Keine trennscharfen Merkmale im Kontext gelernt.")
    return grade, reasons
