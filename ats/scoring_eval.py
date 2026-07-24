"""L3-2: Messstrecke fuers gelernte Scoring - ohne Messung kein gelerntes Score.

Die Ehrlichkeits-Schranke, angewandt auf ML: ein gelerntes Score wird nur
verwendet, wenn es im BACKTEST die naive Grundlinie (rein regelbasiert)
schlaegt. Schlaegt es sie nicht, bleibt es aus. Anti-Blender-Prinzip.

Zwei Messungen:
- Backtest (aus der Stichprobe heraus, ehrlich getrennt): auf aelteren
  Entscheidungen lernen, auf neueren pruefen. Wie treffsicher ist die
  A/B-Empfehlung auf „eingeladen" - im Vergleich zur regelbasierten Grundlinie
  (alle Pflichtkriterien erfuellt)?
- Kalibrierung: Einladungsquote je Band. A soll haeufiger eingeladen werden
  als C - sonst hat das Modell nichts gelernt, und das wird ehrlich gezeigt.

Fairness-Drift und Mensch-ueber-Modell-Quote liegen bewusst im bestehenden
Fairness-Cockpit / bei den Gremien-Overrides und werden hier nicht dupliziert.
"""
from dataclasses import dataclass, field

from .insights import (
    DECIDED_STATUSES,
    POSITIVE_STATUSES,
    LearningScope,
    _reached,
    _status_events,
    resolve_learning_scope,
)
from .models import JobPosting
from .scoring import _features_for_app, fit_model, grade_features

# Mindestgroessen fuer eine belastbare Messung.
MIN_TOTAL = 20         # Entscheidungen im Kontext
MIN_TEST = 6           # Pruef-Faelle (neuere Haelfte)
MIN_TEST_POSITIVE = 3  # als A empfohlene Pruef-Faelle (sonst keine Praezision)
# Das gelernte Score muss die Grundlinie DEUTLICH schlagen, nicht nur gleich-
# ziehen - sonst oeffnet die Schranke schon bei einem nutzlosen Modell, das
# einfach alle in A steckt.
BEAT_MARGIN = 0.05


@dataclass
class BandStat:
    grade: str
    count: int
    invited: int
    invite_rate: float


@dataclass
class BacktestResult:
    scope_label: str
    total: int
    train_n: int
    test_n: int
    learned_precision: "float | None"    # P(eingeladen | Empfehlung A/B)
    baseline_precision: "float | None"   # P(eingeladen | alle Pflicht erfuellt)
    beats_baseline: bool
    calibration: list[BandStat] = field(default_factory=list)
    reason: str = ""


def _rows_sorted(scope: LearningScope) -> list[tuple[dict, bool]]:
    """(Merkmale, eingeladen?) je Entscheidung, AELTESTE zuerst (fuer den
    zeitlichen Split). Verlauf einmal geladen."""
    apps = list(scope.applications.filter(status__in=DECIDED_STATUSES)
                .select_related("jobPosting").order_by("createdAt"))
    events = _status_events([str(a.id) for a in apps])
    return [(_features_for_app(a),
             bool(_reached(str(a.id), a.status, events) & POSITIVE_STATUSES))
            for a in apps]


def _rate(pos: int, n: int) -> float:
    return round(pos / n, 3) if n else 0.0


def backtest(scope: LearningScope) -> BacktestResult:
    """Zeitlicher Backtest: auf 70 % aelteren lernen, auf 30 % neueren pruefen.
    Vergleicht die Treffsicherheit der A/B-Empfehlung mit der regelbasierten
    Grundlinie (alle Pflichtkriterien erfuellt)."""
    rows = _rows_sorted(scope)
    total = len(rows)
    if total < MIN_TOTAL:
        return BacktestResult(
            scope_label=scope.label, total=total, train_n=0, test_n=0,
            learned_precision=None, baseline_precision=None,
            beats_baseline=False,
            reason=f"Zu wenig Entscheidungen ({total} von {MIN_TOTAL}).")

    split = int(total * 0.7)
    train, test = rows[:split], rows[split:]
    if len(test) < MIN_TEST:
        return BacktestResult(
            scope_label=scope.label, total=total, train_n=len(train),
            test_n=len(test), learned_precision=None, baseline_precision=None,
            beats_baseline=False, reason="Zu wenig Prüf-Fälle für den Backtest.")

    model = fit_model(train, scope.label)
    if model is None:
        return BacktestResult(
            scope_label=scope.label, total=total, train_n=len(train),
            test_n=len(test), learned_precision=None, baseline_precision=None,
            beats_baseline=False, reason="Kein Modell gelernt.")

    # Gelernt: Praezision der starken Empfehlung (Band A) auf den Pruef-Faellen.
    top = [(feats, inv) for feats, inv in test
           if grade_features(feats, model)[0] == "A"]
    learned_prec = (_rate(sum(1 for _, inv in top if inv), len(top))
                    if len(top) >= MIN_TEST_POSITIVE else None)

    # Grundlinie: regelbasiert = alle Pflichtkriterien erfuellt (ko_all).
    base_pos = [(feats, inv) for feats, inv in test if feats["ko_all"] >= 0.5]
    baseline_prec = (_rate(sum(1 for _, inv in base_pos if inv), len(base_pos))
                     if len(base_pos) >= MIN_TEST_POSITIVE else None)

    # Nur wenn das gelernte Score die Grundlinie DEUTLICH schlaegt (Margin).
    beats = (learned_prec is not None and baseline_prec is not None
             and learned_prec > baseline_prec + BEAT_MARGIN)

    if learned_prec is None or baseline_prec is None:
        reason = "Zu wenige vergleichbare Fälle im Prüf-Satz."
    elif beats:
        reason = "Gelerntes Score schlägt die regelbasierte Grundlinie."
    else:
        reason = "Gelerntes Score schlägt die Grundlinie (noch) nicht."

    return BacktestResult(
        scope_label=scope.label, total=total, train_n=len(train),
        test_n=len(test), learned_precision=learned_prec,
        baseline_precision=baseline_prec, beats_baseline=beats,
        calibration=_calibration(scope), reason=reason)


def _calibration(scope: LearningScope) -> list[BandStat]:
    """Einladungsquote je Band (auf dem vollen Kontext-Modell). Zeigt, ob A
    tatsaechlich haeufiger eingeladen wird als C/D."""
    from .scoring import learn_context_model
    model = learn_context_model(scope)
    if model is None:
        return []
    rows = _rows_sorted(scope)
    buckets: dict[str, list[bool]] = {g: [] for g in "ABCD"}
    for feats, inv in rows:
        buckets[grade_features(feats, model)[0]].append(inv)
    out: list[BandStat] = []
    for g in "ABCD":
        vals = buckets[g]
        out.append(BandStat(grade=g, count=len(vals),
                            invited=sum(1 for v in vals if v),
                            invite_rate=_rate(sum(1 for v in vals if v),
                                              len(vals))))
    return out


def is_trustworthy(scope: LearningScope) -> tuple[bool, str]:
    """Ehrlichkeits-Schranke: darf das gelernte Score angezeigt/genutzt werden?
    Nur wenn der Backtest die Grundlinie schlaegt."""
    bt = backtest(scope)
    return bt.beats_baseline, bt.reason


def evaluate_job(job: JobPosting) -> BacktestResult:
    return backtest(resolve_learning_scope(job))
