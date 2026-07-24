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

# Woerter, die einen Satzteil als Frage/Bitte kennzeichnen. Dient dazu, einen
# NICHT adressierten Anliegen-Teil zu erkennen (Frage ohne erkanntes Thema) -
# nicht, um Fragezeichen zu zaehlen. Eine reine Mehrfachfrage zum SELBEN Thema
# ist kein zusammengesetzter Fall.
_REQUEST_WORDS = [
    "wie", "was", "wann", "wo", "warum", "wieso", "welche", "welchen",
    "koennen sie", "koennt ihr", "haben sie", "bieten sie", "gibt es",
    "ist es moeglich", "waere es moeglich", "wuerde", "duerfte", "bitte",
    "frage", "moechte ich wissen", "wollte ich fragen",
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


Keywords = "dict[str, list[str]] | None"


def _scores(norm: str, extra: "dict[str, list[str]] | None" = None) -> dict[str, int]:
    out: dict[str, int] = {}
    for intent, kws in _KEYWORDS.items():
        hits = sum(1 for kw in kws if kw in norm)
        if extra and extra.get(intent):
            hits += sum(1 for kw in extra[intent] if kw and kw in norm)
        out[intent] = hits
    return out


def _total_hits(norm: str, extra: "dict[str, list[str]] | None" = None) -> int:
    base = sum(1 for kws in _KEYWORDS.values() for kw in kws if kw in norm)
    if extra:
        base += sum(1 for kws in extra.values() for kw in kws
                    if kw and kw in norm)
    return base


def _has_unaddressed_request(text: str,
                             extra: "dict[str, list[str]] | None" = None) -> bool:
    """Enthaelt die Nachricht einen Frage-/Bitte-Teil OHNE erkennbares Anliegen?

    Das ist der Kern der Ganze-Nachricht-Analyse: eine Standard-Frage plus
    etwas Unerkanntes ("... und bieten Sie eine Betriebswohnung an?") muss
    auffallen. Eine Mehrfachfrage zum SELBEN Thema loest NICHT aus, weil jeder
    Teil ein Anliegen-Stichwort traegt.
    """
    import re
    for raw in re.split(r"[?!.\n]+", text or ""):
        seg = raw.strip()
        if not seg:
            continue
        norm = _normalize(seg)
        is_request = any(
            norm.startswith(w) or f" {w}" in f" {norm}"
            for w in _REQUEST_WORDS)
        if is_request and _total_hits(norm, extra) == 0:
            return True
    return False


def classify_rule_based(text: str,
                        extra: "dict[str, list[str]] | None" = None) -> str:
    """Bestes einzelnes Anliegen per Schluesselwort-Scoring (0 Treffer -> OTHER).

    `extra`: gelernte Zusatz-Stichwoerter je Anliegen (Stufe 5), gleichwertig
    zu den Regeln gewichtet. Bewusst nur das primaere Anliegen; ob die
    Nachricht zusammengesetzt ist, beantwortet analyze().
    """
    norm = _normalize(text)
    scores = _scores(norm, extra)
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
            ai_classifier: "Callable[[str], str | None] | None" = None,
            extra_keywords: "dict[str, list[str]] | None" = None) -> Analysis:
    """Bewertet die GANZE Nachricht und entscheidet den Postfach-Topf.

    Zusammengesetzte Nachrichten (mehrere Anliegen, Zusatz-Marker, mehrere
    Fragen, sehr lang) landen als OTHER = individuelle Pruefung und sind nie
    auto_safe - eine Standard-Antwort darf das Besondere nicht verschlucken.

    ai_classifier: optionaler Haken. Wird NUR fuer eine VOLLSTAENDIG unerkannte
    Einzelnachricht befragt (kein Stichwort getroffen, kein Zusatz-Marker, nicht
    zu lang). Loest er sie in EIN Anliegen auf, gilt sie als adressiert. Steht
    dagegen ein erkannter Teil NEBEN etwas Unklarem, bleibt es beim Menschen -
    die KI hebt diese Grenze nicht auf.
    """
    norm = _normalize(text)
    scores = _scores(norm, extra_keywords)
    matched = [i for i, s in scores.items() if s > 0]
    primary = classify_rule_based(text, extra_keywords)

    multi = len(matched) > 1
    has_marker = any(m in norm for m in _ADDITIONAL_MARKERS)
    unaddressed = _has_unaddressed_request(text, extra_keywords)
    too_long = len((text or "").strip()) > _LONG_MESSAGE_CHARS

    # KI-Rettung nur fuer den voellig unbekannten Einzelfall: nichts erkannt,
    # kein Mehrfach-/Zusatz-Signal, nicht zu lang. Erfolg macht die Nachricht
    # "adressiert" - der unaddressed-Verdacht ist damit ausgeraeumt.
    used_ai = False
    if (primary == INTENT_OTHER and not matched and not has_marker
            and not too_long and ai_classifier is not None):
        guess = ai_classifier(text)
        if guess in _KEYWORDS:
            primary = guess
            matched = [guess]
            unaddressed = False
            used_ai = True

    compound = multi or has_marker or unaddressed or too_long
    reason = ""
    if compound:
        if multi:
            reason = "mehrere Anliegen erkannt"
        elif has_marker:
            reason = "enthält einen Zusatz wie „außerdem“ oder „zusätzlich“"
        elif unaddressed:
            reason = "enthält eine zusätzliche, unklare Frage"
        else:
            reason = "ungewöhnlich lange Nachricht"

    # Zusammengesetzt ODER unerkannt -> Catch-all/individuelle Pruefung.
    bucket = INTENT_OTHER if (compound or primary == INTENT_OTHER) else primary
    if bucket == INTENT_OTHER and not reason and primary == INTENT_OTHER:
        reason = "kein Standard-Anliegen erkannt"

    return Analysis(primary=primary, bucket=bucket, matched=matched,
                    compound=compound, reason=reason, used_ai=used_ai)
