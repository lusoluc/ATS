"""CMS-Baukasten: typisierte Inhalts-Bloecke fuer Seiten und Landingpages.

Ziel: schoene, funktionsfaehige Seiten OHNE HTML-Kenntnisse in Minuten –
Block waehlen, Felder ausfuellen, sortieren, fertig. Bewusst server-
gerendert (keine JS-Abhaengigkeit), Ausgabe ausschliesslich ueber Django-
Autoescape (Waechter-Test) und Design-Tokens (Traeger-Branding wirkt
automatisch).

BLOCK_TYPES ist die eine Wahrheit: sie speist den Editor (Felder, Labels,
Hilfetexte) UND die serverseitige Validierung. Neue Bloecke = ein Eintrag
hier + ein Zweig im Render-Include.
"""
from typing import Any

# field-Typen: text, textarea, lines (eine Angabe je Zeile), int, url
# (heterogene Editor-Spezifikation: label ist str, fields eine Tupel-Liste)
BLOCK_TYPES: dict[str, dict[str, Any]] = {
    "hero": {
        "label": "Hero (Bild + Botschaft)",
        "fields": [
            ("heading", "text", "Überschrift"),
            ("text", "textarea", "Unterzeile / Botschaft"),
            ("imageUrl", "url", "Bild-URL (optional)"),
        ]},
    "text": {
        "label": "Textabschnitt",
        "fields": [
            ("heading", "text", "Zwischenüberschrift (optional)"),
            ("text", "textarea", "Text"),
        ]},
    "checklist": {
        "label": "Checkliste / Benefits",
        "fields": [
            ("heading", "text", "Überschrift (optional)"),
            ("items", "lines", "Ein Punkt je Zeile"),
        ]},
    "stats": {
        "label": "Kennzahlen-Reihe",
        "fields": [
            ("items", "lines", "Je Zeile: Zahl|Beschriftung – z. B. 21|Standorte"),
        ]},
    "quote": {
        "label": "Zitat / Stimme aus dem Team",
        "fields": [
            ("text", "textarea", "Zitat"),
            ("author", "text", "Name"),
            ("role", "text", "Rolle (optional)"),
        ]},
    "faq": {
        "label": "Fragen & Antworten",
        "fields": [
            ("heading", "text", "Überschrift (optional)"),
            ("items", "lines", "Je Zeile: Frage|Antwort"),
        ]},
    "image": {
        "label": "Bild",
        "fields": [
            ("url", "url", "Bild-URL"),
            ("caption", "text", "Bildunterschrift (optional)"),
        ]},
    "contact": {
        "label": "Ansprechperson",
        "fields": [
            ("contactPersonId", "text", "Wird im Editor als Auswahl angeboten"),
        ]},
    "jobs": {
        "label": "Aktuelle Stellen",
        "fields": [
            ("heading", "text", "Überschrift (optional)"),
            ("limit", "int", "Anzahl (1–12)"),
        ]},
    "cta": {
        "label": "Handlungsaufruf (Button)",
        "fields": [
            ("text", "text", "Kurzer Satz davor (optional)"),
            ("buttonLabel", "text", "Button-Beschriftung"),
            ("url", "url", "Ziel-Link, z. B. /jobs/"),
        ]},
}

MAX_BLOCKS = 30
MAX_TEXT = 4000


def normalize_block(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Einzelnen Block pruefen/stutzen; None wenn Typ unbekannt."""
    raw = raw or {}
    btype = str(raw.get("type") or "")
    spec = BLOCK_TYPES.get(btype)
    if not spec:
        return None
    out: dict[str, Any] = {"type": btype}
    for name, ftype, _label in spec["fields"]:
        val = raw.get(name)
        if ftype == "int":
            try:
                # fehlender Wert faellt wie bisher auf den Default 5
                out[name] = max(1, min(12, int(val) if val is not None else 5))
            except (TypeError, ValueError):
                out[name] = 5
        elif ftype == "lines":
            lines = [line.strip() for line in str(val or "").splitlines() if line.strip()]
            out[name] = lines[:20]
        else:
            out[name] = str(val or "").strip()[:MAX_TEXT]
    return out


def normalize_blocks(raw_list: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in (raw_list or [])[:MAX_BLOCKS]:
        b = normalize_block(raw)
        if b:
            out.append(b)
    return out


def load_blocks(obj: Any) -> list[dict[str, Any]]:
    # obj: jedes Modell mit blocksJson (Page, Landingpage) — Union unnoetig eng
    try:
        return normalize_blocks(obj.blocksJson or [])
    except (ValueError, TypeError):
        return []


def enrich_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Datenbedarf aufloesen: Ansprechpersonen-Objekt, Stellen-Liste.
    Mutiert Kopien – Templates rendern nur, holen nichts selbst."""
    from .models import ContactPerson, JobPosting
    enriched: list[dict[str, Any]] = []
    for b in blocks:
        b = dict(b)
        if b["type"] == "contact" and b.get("contactPersonId"):
            b["person"] = ContactPerson.objects.filter(
                id=b["contactPersonId"]).first()
        if b["type"] == "jobs":
            b["job_list"] = (JobPosting.objects
                             .filter(workflowState__name="published")
                             .select_related("location", "facility")
                             .order_by("-createdAt")[:b.get("limit", 5)])
        # Pipe-Listen fuer stats/faq vorzerlegen (Template bleibt dumm)
        if b["type"] in ("stats", "faq"):
            pairs: list[dict[str, str]] = []
            for line in b.get("items", []):
                left, _, right = line.partition("|")
                pairs.append({"a": left.strip(), "b": right.strip()})
            b["pairs"] = pairs
        enriched.append(b)
    return enriched
