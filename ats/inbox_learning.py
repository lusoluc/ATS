"""Stufe 5: lernende Optimierung der Einsortierung aus HR-Korrekturen.

Lernt aus natuerlichem Verhalten, nicht aus Extra-Klicks: Wenn HR eine
Nachricht in ein anderes Anliegen verschiebt (weil die Regel danebenlag),
ist das eine Korrektur. Aus den unterscheidenden Woertern solcher Korrekturen
werden gelernte Zusatz-Stichwoerter - sie ERGAENZEN die Regeln, ersetzen sie
nicht.

Drei feste Prinzipien:

1. Ehrlichkeits-Gate: ein Wort wird nur gelernt, wenn es in mindestens
   MIN_EVIDENCE Korrekturen auftauchte, die ALLE auf dasselbe Anliegen zeigen
   (kein Wort, das mal hierhin, mal dorthin korrigiert wurde). Konservativ und
   nachvollziehbar statt Blackbox.

2. Nie Selbst-Ausweitung: Gelerntes verbessert die SORTIERUNG. Es kann kein
   Anliegen zur Auto-Antwort freischalten - der auto-sichere Kreis
   (AUTO_SAFE_INTENTS) ist eine Konstante, die dieses Modul nicht anfasst.

3. Sofort-Korrektur getrennt vom Lernen: eine einzelne Korrektur wirkt sofort
   fuer GENAU diese Nachricht (message_overrides); ins gelernte Regelwerk geht
   sie erst, wenn genug gleichlautende Evidenz zusammenkommt.

Bewusst global (nicht je Standort/Abteilung): Nachrichten-THEMEN wie
"Stand/Unterlagen/Termin" sind abteilungsuebergreifend aehnlich. Die
Kontext-Dimension bleibt der Kandidaten-Bewertung vorbehalten (LEARNING_ROADMAP,
L3), wo Kriterien wirklich je Abteilung verschieden sind.
"""
import json
import re

from .inbox_intents import _KEYWORDS
from .models import AuditLog

RECLASSIFY_ACTION = "INBOX_RECLASSIFIED"

# So viele gleichlautende Korrekturen braucht ein Wort, um gelernt zu werden.
MIN_EVIDENCE = 3

# Haeufige Fuellwoerter, die nie ein Anliegen kennzeichnen.
_STOPWORDS = {
    "bitte", "danke", "vielen", "guten", "hallo", "sehr", "geehrte",
    "geehrter", "freundliche", "gruesse", "koennen", "koennten", "wuerde",
    "haben", "hätte", "haette", "meine", "meiner", "meinen", "einen", "eine",
    "einer", "ihre", "ihren", "ihrem", "noch", "auch", "schon", "dass",
    "nach", "fuer", "mich", "mir", "wann", "wieso", "warum", "wie", "was",
    "welche", "ueber", "unsere", "diese", "dieser", "damit", "wollte",
    "moechte", "moechten", "gerne", "gern", "nochmal", "bereits", "leider",
}


def _tokens(text: str) -> set[str]:
    norm = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        norm = norm.replace(a, b)
    return {t for t in re.split(r"[^a-z]+", norm)
            if len(t) >= 4 and t not in _STOPWORDS}


def _is_base_keyword(token: str) -> bool:
    """Schon durch die Regeln abgedeckt? (Wort steckt in einem Regel-Stichwort)"""
    for kws in _KEYWORDS.values():
        for kw in kws:
            if token in kw:
                return True
    return False


def _reclassify_rows() -> list[dict]:
    out: list[dict] = []
    for a in AuditLog.objects.filter(action=RECLASSIFY_ACTION).order_by("seq"):
        try:
            meta = json.loads(a.metadataJson or "{}")
        except (ValueError, TypeError):
            continue
        if isinstance(meta, dict) and meta.get("to_intent"):
            out.append(meta)
    return out


def learned_keywords() -> dict[str, list[str]]:
    """Aus den Korrekturen abgeleitete Zusatz-Stichwoerter je Anliegen.

    Ehrlichkeits-Gate: ein Wort muss in >= MIN_EVIDENCE Korrekturen vorkommen,
    die ALLE dasselbe Anliegen meinen. Ein Wort, das je einmal in Korrekturen
    zu verschiedenen Anliegen auftaucht, wird verworfen (mehrdeutig).
    """
    # token -> {intent: count}
    counts: dict[str, dict[str, int]] = {}
    for meta in _reclassify_rows():
        intent = str(meta["to_intent"])
        if intent not in _KEYWORDS:      # nur echte Regel-Anliegen lernen
            continue
        for tok in _tokens(str(meta.get("excerpt", ""))):
            if _is_base_keyword(tok):
                continue
            counts.setdefault(tok, {})
            counts[tok][intent] = counts[tok].get(intent, 0) + 1

    learned: dict[str, list[str]] = {}
    for tok, per_intent in counts.items():
        if len(per_intent) != 1:         # mehrdeutig -> verworfen
            continue
        intent, n = next(iter(per_intent.items()))
        if n >= MIN_EVIDENCE:
            learned.setdefault(intent, []).append(tok)
    return learned


def message_overrides(message_ids: list[str]) -> dict[str, str]:
    """Sofort-Korrektur: je Nachricht das zuletzt von HR gesetzte Anliegen.

    Wirkt unabhaengig vom Lern-Gate - eine einzige Korrektur verschiebt GENAU
    diese Nachricht sofort in den richtigen Topf.
    """
    if not message_ids:
        return {}
    wanted = {str(m) for m in message_ids}
    override: dict[str, str] = {}
    for a in (AuditLog.objects.filter(action=RECLASSIFY_ACTION)
              .order_by("seq")):
        try:
            meta = json.loads(a.metadataJson or "{}")
        except (ValueError, TypeError):
            continue
        mid = str(meta.get("message_id", ""))
        if mid in wanted and meta.get("to_intent"):
            override[mid] = str(meta["to_intent"])   # spaeter gewinnt
    return override
