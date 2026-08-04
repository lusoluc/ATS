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
from .models import Application, JobPosting
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


# --- L5: Fruehwarnung statt Momentaufnahme -----------------------------------
# Der Backtest sagt "heute schlaegt es die Grundlinie" - aber nicht, ob es
# schlechter WIRD. Ein Modell, das vor drei Monaten passte, kann heute an der
# Realitaet vorbeilaufen (neue Stellenzuschnitte, anderer Bewerbermarkt).
# Deshalb zwei Frueh-Signale, beide aus denselben Daten, beide ehrlich
# getrennt: das Modell lernt NUR auf der aeltesten Haelfte und wird auf zwei
# spaeteren Fenstern geprueft.
MIN_DRIFT_TOTAL = 24   # darunter sind zwei Pruef-Fenster nicht sinnvoll
MIN_WINDOW = 5         # Faelle je Fenster
DRIFT_MARGIN = 0.10    # ab 10 Punkten Abfall sprechen wir von Drift


@dataclass
class DriftResult:
    """Zeitverlauf + Mensch-ueber-Modell-Quote. Jede Zahl kommt mit einer
    Handlung - eine Kennzahl ohne naechsten Schritt waere Deko."""

    scope_label: str
    early_precision: "float | None" = None   # aelteres Pruef-Fenster
    late_precision: "float | None" = None    # neueres Pruef-Fenster
    trend: str = "unbekannt"                 # steigend | stabil | fallend | unbekannt
    override_rate: "float | None" = None     # Anteil Entscheidungen GEGEN die Note
    override_n: int = 0
    too_optimistic: int = 0    # Note A, aber abgesagt
    too_pessimistic: int = 0   # Note D, aber eingeladen
    verdict: str = ""
    action: str = ""


def drift_report(scope: LearningScope) -> DriftResult:
    """Wird das gelernte Score mit der Zeit schlechter - und wie oft
    entscheidet der Mensch dagegen?

    Aufbau: aelteste 50 % = Trainingsdaten, danach zwei gleich grosse
    Pruef-Fenster (frueher / zuletzt). Beide werden mit DEMSELBEN Modell
    bewertet; faellt die Treffsicherheit im neueren Fenster deutlich ab,
    ist das ein Drift-Signal. Die Mensch-ueber-Modell-Quote zaehlt im
    neueren Fenster, wie oft die Entscheidung der Note widersprach - das
    frueheste Signal ueberhaupt, weil es kommt, bevor die Trefferquote
    kippt."""
    rows = _rows_sorted(scope)
    total = len(rows)
    if total < MIN_DRIFT_TOTAL:
        return DriftResult(
            scope_label=scope.label,
            verdict=f"Zu wenig Verlauf ({total} von {MIN_DRIFT_TOTAL} Entscheidungen).",
            action="Weiter arbeiten – die Messung startet automatisch, sobald genug Entscheidungen vorliegen.")

    half = total // 2
    rest = rows[half:]
    cut = len(rest) // 2
    train, early, late = rows[:half], rest[:cut], rest[cut:]
    if min(len(early), len(late)) < MIN_WINDOW:
        return DriftResult(
            scope_label=scope.label,
            verdict="Prüf-Fenster noch zu klein für einen Zeitvergleich.",
            action="Weiter arbeiten – kein Handlungsbedarf.")

    model = fit_model(train, scope.label)
    if model is None:
        return DriftResult(
            scope_label=scope.label,
            verdict="Kein Modell auf den älteren Daten lernbar.",
            action="Weiter arbeiten – kein Handlungsbedarf.")

    def _precision(window: list[tuple[dict, bool]]) -> "float | None":
        top = [inv for feats, inv in window
               if grade_features(feats, model)[0] == "A"]
        return _rate(sum(1 for v in top if v), len(top)) if top else None

    early_p, late_p = _precision(early), _precision(late)

    # Mensch ueber Modell im neuesten Fenster: Note A -> trotzdem abgesagt,
    # Note D -> trotzdem eingeladen. Beides heisst: die Note trug nicht.
    too_opt = too_pes = 0
    for feats, invited in late:
        grade = grade_features(feats, model)[0]
        if grade == "A" and not invited:
            too_opt += 1
        elif grade == "D" and invited:
            too_pes += 1
    override_n = too_opt + too_pes
    override_rate = _rate(override_n, len(late))

    if early_p is None or late_p is None:
        trend = "unbekannt"
    elif late_p + DRIFT_MARGIN < early_p:
        trend = "fallend"
    elif late_p > early_p + DRIFT_MARGIN:
        trend = "steigend"
    else:
        trend = "stabil"

    # Verdikt + HANDLUNG (nie eine Zahl ohne naechsten Schritt).
    if trend == "fallend":
        verdict = (f"Treffsicherheit fällt: {int((early_p or 0) * 100)} % → "
                   f"{int((late_p or 0) * 100)} % im neueren Zeitraum.")
        action = ("Anforderungen und Pflichtkriterien dieser Jobfamilie prüfen – "
                  "hat sich der Zuschnitt geändert? Bis dahin die gelernte Note "
                  "als schwächeres Signal behandeln.")
    elif override_rate >= 0.30:
        verdict = (f"Das Team entscheidet in {int(override_rate * 100)} % der "
                   "Fälle gegen die gelernte Note.")
        action = ("Stichprobe dieser Fälle im Aktionsverlauf ansehen: Fehlt dem "
                  "Modell ein Kriterium, das im Gespräch offensichtlich ist?")
    elif trend == "steigend":
        verdict = (f"Treffsicherheit steigt: {int((early_p or 0) * 100)} % → "
                   f"{int((late_p or 0) * 100)} %.")
        action = "Kein Handlungsbedarf – Kurs beibehalten."
    else:
        verdict = "Stabil im Zeitverlauf, keine auffälligen Gegenentscheidungen."
        action = "Kein Handlungsbedarf – nächste Prüfung läuft automatisch mit."

    return DriftResult(
        scope_label=scope.label, early_precision=early_p, late_precision=late_p,
        trend=trend, override_rate=override_rate, override_n=override_n,
        too_optimistic=too_opt, too_pessimistic=too_pes,
        verdict=verdict, action=action)


def is_trustworthy(scope: LearningScope) -> tuple[bool, str]:
    """Ehrlichkeits-Schranke: darf das gelernte Score angezeigt/genutzt werden?
    Nur wenn der Backtest die Grundlinie schlaegt."""
    bt = backtest(scope)
    return bt.beats_baseline, bt.reason


def evaluate_job(job: JobPosting) -> BacktestResult:
    return backtest(resolve_learning_scope(job))


# --- Governance: standardmaessig AUS, Opt-in je Betrieb -----------------------
LEARNED_SCORING_ENABLED_KEY = "LEARNED_SCORING_ENABLED"


def is_scoring_enabled() -> bool:
    """Ist das gelernte Scoring freigeschaltet? Default AUS (Opt-in; EU AI Act
    Hochrisiko - Aktivierung ist eine bewusste, dokumentierte Entscheidung)."""
    from .models import SystemSetting
    return SystemSetting.objects.filter(
        key=LEARNED_SCORING_ENABLED_KEY, value="1").exists()


def learned_grade(app: Application) -> "tuple[str, list[str], str] | None":
    """Gelernte Einordnung (Note, Begruendung, Kontext-Ebene) fuer eine
    Bewerbung - ODER None. Drei Tore, alle muessen offen sein:
    freigeschaltet, Kontext belastbar UND vertrauenswuerdig (Backtest schlaegt
    Grundlinie). Sonst bleibt das bestehende Score unveraendert."""
    if not is_scoring_enabled():
        return None
    from .scoring import grade_application, learn_context_model
    scope = resolve_learning_scope(app.jobPosting)
    ok, _ = is_trustworthy(scope)
    if not ok:
        return None
    model = learn_context_model(scope)
    if model is None:
        return None
    grade, reasons = grade_application(app, model)
    return grade, reasons, scope.label
