"""Fragen-Registry: EINE Wahrheit fuer Screening- und Mindeststandard-Fragen.

Speist den formularbasierten Editor (kein JSON-Vorwissen noetig) UND die
serverseitige Normalisierung. Speicherformat bleibt die bestehende
JSON-Liste – kein Migrationsbedarf, ensure_minimum_standards & Co. arbeiten
unveraendert weiter.

Typen:
- YES_NO: Ja/Nein; optional K.O. (erwartete Antwort)
- SELECT: eigene Optionen; optional K.O. (eine Option als erwartet)
- TEXT:   Freitext; Pflicht = ausfuellen (nie K.O.)
- FILE:   Pflicht-Dokument (z. B. "Fuehrerschein Klasse B") – Upload am
          Bewerbungsformular, gleiche Whitelist/Limits wie alle Uploads;
          Pflicht = Datei dabei (nie K.O.)
"""
import uuid

QUESTION_TYPES = {
    "YES_NO": "Ja/Nein-Frage",
    "SELECT": "Auswahl",
    "TEXT": "Freitext",
    "FILE": "Pflicht-Dokument (Upload)",
}


def normalize_question(raw):
    """Ein Frage-Dict pruefen/stutzen; None wenn unbrauchbar."""
    qtype = (raw or {}).get("type", "YES_NO")
    if qtype not in QUESTION_TYPES:
        return None
    question = str(raw.get("question") or "").strip()[:300]
    if not question:
        return None
    out = {
        "id": str(raw.get("id") or f"q-{uuid.uuid4().hex[:8]}"),
        "type": qtype,
        "question": question,
        "isMandatory": bool(raw.get("isMandatory")),
    }
    if qtype == "SELECT":
        opts = raw.get("options") or []
        if isinstance(opts, str):
            opts = opts.splitlines()
        out["options"] = [str(o).strip()[:120] for o in opts
                          if str(o).strip()][:12]
        expected = str(raw.get("expectedAnswer") or "").strip()
        if expected and expected in out["options"]:
            out["expectedAnswer"] = expected     # K.O. auf eine Option
    elif qtype == "YES_NO":
        expected = str(raw.get("expectedAnswer") or "").strip().upper()
        if expected in ("YES", "NO"):
            out["expectedAnswer"] = expected
    # TEXT/FILE: bewusst kein expectedAnswer – Pflicht heisst ausfuellen/
    # hochladen, nie automatische Absage.
    return out


def normalize_questions(raw_list):
    out = []
    for raw in (raw_list or [])[:30]:
        q = normalize_question(raw)
        if q:
            out.append(q)
    return out


# --- N2: Objektive Gruende fuer K.O.-Absagen ---------------------------------
# WICHTIG (AGG): Automatisch benannt werden duerfen AUSSCHLIESSLICH nicht
# erfuellte K.O.-Kriterien, die VOR der Bewerbung in der Ausschreibung
# standen und die die Person selbst beantwortet hat. Ermessens-Absagen
# (HR entscheidet sich fuer jemand anderen) bekommen NIE automatisch
# formulierte Gruende - jede erfundene Begruendung waere ein Klagerisiko
# und unehrlich gegenueber der Person.

KO_REASON_PREFIX = "Automatische Ablehnung: K.O.-Kriterium nicht erfüllt: "


def format_ko_reason(failed_questions):
    """Ablehnungsgrund-Snapshot bei Einreichung (Fragen koennen sich spaeter
    aendern - massgeblich ist, was die Person tatsaechlich gefragt wurde)."""
    return KO_REASON_PREFIX + "; ".join(failed_questions)


def ko_grounds(withdraw_reason):
    """Objektive Gruende aus dem gespeicherten Ablehnungsgrund zurueckholen.

    Nur K.O.-Absagen tragen welche; alles andere liefert [] - siehe
    AGG-Hinweis oben.
    """
    text = withdraw_reason or ""
    if not text.startswith(KO_REASON_PREFIX):
        return []
    return [g.strip() for g in text[len(KO_REASON_PREFIX):].split(";")
            if g.strip()]
