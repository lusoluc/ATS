"""Kleine globale Template-Flags."""
from django.conf import settings


def demo_flags(request):
    return {"DEMO_MODE": getattr(settings, "DEMO_MODE", False)}


def rollen_flags(request):
    """`darf_aendern` fuer jedes Template.

    Ohne das haette die Rolle `Viewer` weiterhin Knoepfe vor sich, die beim
    Druecken in eine Fehlerseite laufen. Ein Knopf, der nichts tut, ist eine
    Zumutung - und aus Sicht der Bedienung schlimmer als gar keiner: Er
    behauptet eine Moeglichkeit, die es nicht gibt.
    """
    from .permissions import may_modify
    nutzer = getattr(request, "user", None)
    return {"darf_aendern": bool(nutzer is not None and may_modify(nutzer))}
