from django.apps import AppConfig


class AtsConfig(AppConfig):
    name = 'ats'

    def ready(self):
        # Entgelttransparenz E3: Signal-Verankerung veröffentlichter Spannen
        from . import signals  # noqa: F401
