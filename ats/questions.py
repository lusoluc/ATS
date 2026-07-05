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
