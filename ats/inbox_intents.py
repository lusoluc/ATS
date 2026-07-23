"""Anliegen-Erkennung fuer eingehende Bewerber-Nachrichten (Sammel-Postfach).

Zweck: aehnlich gelagerte Fragen buendeln, damit HR sie gesammelt statt
einzeln beantwortet. Regelbasiert (Schluesselwort-Scoring) - immer verfuegbar,
deterministisch, auditierbar; eine optionale lokale KI kann Grenzfaelle
nachschaerfen (per Dependency Injection, damit dieses Modul ohne Netz
testbar bleibt).

Zwei Sicherheits-Leitplanken sind hier fest verankert:

1. Ein Catch-all-Topf "Sonstiges / individuelle Pruefung" (OTHER). Er sammelt
   nicht nur Unerkanntes, sondern ist auch das Ziel fuer alles, was NICHT
   automatisch beantwortet werden darf.

2. Es wird die GANZE Nachricht bewertet, nicht ein einzelnes Stichwort. Wer
   eine Standard-Frage UND zusaetzlich etwas Besonderes schreibt, landet als
   "zusammengesetzt" in der individuellen Pruefung - eine Standard-Antwort
   darf das Besondere nie verschlucken, und automatisch beantwortet wird so
   eine Nachricht nie.
"""
from collections.abc import Callable
from dataclasses import dataclass, field

INTENT_STATUS = "STATUS"
INTENT_DOCUMENTS = "DOCUMENTS"
INTENT_SCHEDULING = "SCHEDULING"
INTENT_PROCESS = "PROCESS"
INTENT_WITHDRAWAL = "WITHDRAWAL"
INTENT_OTHER = "OTHER"

# Anzeige-Reihenfolge im Postfach. OTHER bewusst zuletzt, aber gleichwertig
# sichtbar - es ist der "braucht einen Menschen"-Topf.
INTENT_ORDER = [
    INTENT_STATUS, INTENT_SCHEDULING, INTENT_DOCUMENTS,
    INTENT_PROCESS, INTENT_WITHDRAWAL, INTENT_OTHER,
]

INTENT_LABELS = {
    INTENT_STATUS: "Stand des Verfahrens",
    INTENT_DOCUMENTS: "Unterlagen",
    INTENT_SCHEDULING: "Termin",
    INTENT_PROCESS: "Ablauf & nächste Schritte",
    INTENT_WITHDRAWAL: "Rückzug der Bewerbung",
    INTENT_OTHER: "Sonstiges / individuelle Prüfung",
}

INTENT_ICONS = {
    INTENT_STATUS: "fa-hourglass-half",
    INTENT_DOCUMENTS: "fa-folder-open",
    INTENT_SCHEDULING: "fa-calendar-day",
    INTENT_PROCESS: "fa-diagram-project",
    INTENT_WITHDRAWAL: "fa-person-walking-arrow-right",
    INTENT_OTHER: "fa-circle-question",
}

# Anliegen, die inhaltlich reine KOMMUNIKATION sind (keine Entscheidung) und
# daher grundsaetzlich fuer eine Auto-Antwort in Frage kommen - sofern der
# Betreiber sie freischaltet UND die Nachricht sauber (nicht zusammengesetzt)
# ist. Entscheidungen (Einladung/Absage/Zusage) sind NIE hier.
AUTO_SAFE_INTENTS = {INTENT_STATUS, INTENT_PROCESS}

# Tie-Break: spezifischere/aktionsbeduerftige Anliegen schlagen bei Gleichstand
# das sehr haeufige STATUS.
_PRIORITY = [
    INTENT_WITHDRAWAL, INTENT_SCHEDULING, INTENT_DOCUMENTS,
    INTENT_PROCESS, INTENT_STATUS,
]

# Schluesselwoerter in "gefalteter" Form (Umlaute -> ae/oe/ue, ss). Der
# Nachrichtentext wird gleich gefaltet, damit "Rueckmeldung" und
# "Rückmeldung" beide treffen.
_KEYWORDS: dict[str, list[str]] = {
    INTENT_STATUS: [
        "wann hoere ich", "bis wann", "wann bekomme ich", "wann kann ich",
        "wann rechnen", "wann melden", "wann erfahre ich", "stand",
        "rueckmeldung", "bescheid", "gehoert", "wie lange", "noch nichts",
        "immer noch nichts", "warte", "wie sieht es aus", "gibt es neuigkeiten",
    ],
    INTENT_DOCUMENTS: [
        "unterlagen", "dokument", "eingereicht", "hochgeladen", "hochladen",
        "zeugnis", "lebenslauf", "nachreichen", "fehlt noch", "vollstaendig",
        "anlage", "nachweis", "zertifikat", "bescheinigung", "angekommen",
    ],
    INTENT_SCHEDULING: [
        "termin", "verschieben", "verschoben", "umbuchen", "uhrzeit",
        "verhindert", "anderen tag", "spaeter", "frueher", "absagen",
        "verspaete", "gespraechstermin", "neuen termin", "zeitlich",
    ],
    INTENT_PROCESS: [
        "wie geht es weiter", "wie geht es nun weiter", "ablauf",
        "naechste schritte", "naechsten schritte", "verfahren", "wie laeuft",
        "wie ist der prozess", "was passiert dann", "wie sieht der ablauf",
    ],
    INTENT_WITHDRAWAL: [
        "zurueckziehen", "zurueckzuziehen", "bewerbung zurueck", "kein interesse",
        "nicht mehr interessiert", "moechte absagen", "zuruecknehmen",
        "ziehe zurueck", "ziehe meine bewerbung", "bewerbung annullieren",
    ],
}

# Marker, die auf eine zusammengesetzte Nachricht deuten (mehrere Anliegen).
_ADDITIONAL_MARKERS = [
    "ausserdem", "zusaetzlich", "noch eine frage", "noch eine weitere",
    "darueber hinaus", "und noch", "ferner", "weitere frage", "zwei fragen",
    "mehrere fragen", "nebenbei", "abgesehen davon", "und dann noch",
    "eine andere frage", "was mich noch",
]

# Ab hier gilt eine Nachricht als zu lang/komplex fuer eine sichere
# Auto-Einordnung - lange Texte tragen meist mehr als ein Anliegen.
_LONG_MESSAGE_CHARS = 600


@dataclass
class Analysis:
    """Ergebnis der Anliegen-Analyse einer ganzen Nachricht."""
    primary: str                       # bestes einzelnes Anliegen (oder OTHER)
    bucket: str                        # Topf im Postfach (OTHER bei Zusammensetzung)
    matched: list[str] = field(default_factory=list)  # alle getroffenen Intents
    compound: bool = False             # mehrere Anliegen / Zusatz / zu lang
    reason: str = ""                   # warum individuell (fuer die Anzeige)
    used_ai: bool = False

    @property
    def auto_safe(self) -> bool:
        """Darf diese Nachricht ueberhaupt automatisch beantwortet werden?

        Nur wenn sie sauber (nicht zusammengesetzt) ist UND das Anliegen ein
        reines Kommunikations-Anliegen ist. Die Freischaltung je Betrieb
        prueft der Aufrufer zusaetzlich.
        """
        return (not self.compound) and self.primary in AUTO_SAFE_INTENTS


def _normalize(text: str) -> str:
    lowered = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        lowered = lowered.replace(a, b)
    return lowered


def _scores(norm: str) -> dict[str, int]:
    return {
        intent: sum(1 for kw in kws if kw in norm)
        for intent, kws in _KEYWORDS.items()
    }


def classify_rule_based(text: str) -> str:
    """Bestes einzelnes Anliegen per Schluesselwort-Scoring (0 Treffer -> OTHER).

    Bewusst nur das primaere Anliegen; ob die Nachricht zusammengesetzt ist,
    beantwortet analyze().
    """
    norm = _normalize(text)
    scores = _scores(norm)
    best = max(scores.values(), default=0)
    if best == 0:
        return INTENT_OTHER
    winners = [i for i, s in scores.items() if s == best]
    if len(winners) == 1:
        return winners[0]
    for intent in _PRIORITY:            # Gleichstand -> Prioritaet
        if intent in winners:
            return intent
    return winners[0]


def analyze(text: str,
            ai_classifier: "Callable[[str], str | None] | None" = None) -> Analysis:
    """Bewertet die GANZE Nachricht und entscheidet den Postfach-Topf.

    Zusammengesetzte Nachrichten (mehrere Anliegen, Zusatz-Marker, mehrere
    Fragen, sehr lang) landen als OTHER = individuelle Pruefung und sind nie
    auto_safe - eine Standard-Antwort darf das Besondere nicht verschlucken.

    ai_classifier: optionaler Haken. Wird NUR befragt, wenn die Regel nichts
    erkennt (primary == OTHER, nicht zusammengesetzt). Gibt er ein gueltiges
    Anliegen zurueck, wird es uebernommen (used_ai=True).
    """
    norm = _normalize(text)
    scores = _scores(norm)
    matched = [i for i, s in scores.items() if s > 0]
    primary = classify_rule_based(text)

    multi = len(matched) > 1
    has_marker = any(m in norm for m in _ADDITIONAL_MARKERS)
    many_questions = (text or "").count("?") >= 2
    too_long = len((text or "").strip()) > _LONG_MESSAGE_CHARS
    compound = multi or has_marker or many_questions or too_long

    reason = ""
    if compound:
        if multi:
            reason = "mehrere Anliegen erkannt"
        elif has_marker:
            reason = "enthält einen Zusatz wie „außerdem“ oder „zusätzlich“"
        elif many_questions:
            reason = "mehrere Fragen in einer Nachricht"
        else:
            reason = "ungewöhnlich lange Nachricht"

    used_ai = False
    if primary == INTENT_OTHER and not compound and ai_classifier is not None:
        guess = ai_classifier(text)
        if guess in _KEYWORDS:
            primary = guess
            matched = [guess]
            used_ai = True

    # Zusammengesetzt ODER unerkannt -> Catch-all/individuelle Pruefung.
    bucket = INTENT_OTHER if (compound or primary == INTENT_OTHER) else primary
    if bucket == INTENT_OTHER and not reason and primary == INTENT_OTHER:
        reason = "kein Standard-Anliegen erkannt"

    return Analysis(primary=primary, bucket=bucket, matched=matched,
                    compound=compound, reason=reason, used_ai=used_ai)
