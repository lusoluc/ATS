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
import json

# field-Typen: text, textarea, lines (eine Angabe je Zeile), int, url
BLOCK_TYPES = {
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


def normalize_block(raw):
    """Einzelnen Block pruefen/stutzen; None wenn Typ unbekannt."""
    btype = (raw or {}).get("type")
    spec = BLOCK_TYPES.get(btype)
    if not spec:
        return None
    out = {"type": btype}
    for name, ftype, _label in spec["fields"]:
        val = raw.get(name)
        if ftype == "int":
            try:
                out[name] = max(1, min(12, int(val)))
            except (TypeError, ValueError):
                out[name] = 5
        elif ftype == "lines":
            lines = [l.strip() for l in str(val or "").splitlines() if l.strip()]
            out[name] = lines[:20]
        else:
            out[name] = str(val or "").strip()[:MAX_TEXT]
    return out


def normalize_blocks(raw_list):
    out = []
    for raw in (raw_list or [])[:MAX_BLOCKS]:
        b = normalize_block(raw)
        if b:
            out.append(b)
    return out


def load_blocks(obj):
    try:
        return normalize_blocks(json.loads(obj.blocksJson or "[]"))
    except (ValueError, TypeError):
        return []


def enrich_blocks(blocks):
    """Datenbedarf aufloesen: Ansprechpersonen-Objekt, Stellen-Liste.
    Mutiert Kopien – Templates rendern nur, holen nichts selbst."""
    from .models import ContactPerson, JobPosting
    enriched = []
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
            pairs = []
            for line in b.get("items", []):
                left, _, right = line.partition("|")
                pairs.append({"a": left.strip(), "b": right.strip()})
            b["pairs"] = pairs
        enriched.append(b)
    return enriched
