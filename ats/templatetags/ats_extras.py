"""Kleine Template-Filter fuer SecurATS."""
from django import template

register = template.Library()


@register.filter
def dictkey(d, key):
    """Wert aus einem Dict per dynamischem Schluessel (Templates koennen
    keine variablen Dict-Zugriffe). Leerer String, wenn nicht vorhanden."""
    try:
        return d.get(key, "")
    except (AttributeError, TypeError):
        return ""
