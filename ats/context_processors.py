"""Kleine globale Template-Flags."""
from django.conf import settings


def demo_flags(request):
    return {"DEMO_MODE": getattr(settings, "DEMO_MODE", False)}
