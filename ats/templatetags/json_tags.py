"""Template-Filter fuer JSONField-Werte.

Seit der Umstellung auf models.JSONField liefern die *Json-Felder direkt
list/dict. Wo Templates den Wert als JSON-Text brauchen (JS-Aufrufe mit
JSON.parse, data-Attribute), rendert `as_json` echtes JSON statt des
Python-reprs (einfache Anfuehrungszeichen wuerden JSON.parse brechen).
"""
import json

from django import template

register = template.Library()


@register.filter
def as_json(value):
    """Wert als JSON-String (fuer JSON.parse im Frontend)."""
    return json.dumps(value, ensure_ascii=False)
