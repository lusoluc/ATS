"""SecurATS Views — Login inkl. Brute-Force-Sperre.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import logging

from django.contrib.auth.views import LoginView as AuthLoginView
from django.core.cache import cache

logger = logging.getLogger(__name__)

__all__ = ["SafeLoginView"]


class SafeLoginView(AuthLoginView):
    """Zuverlässiger Schutz gegen Login-Brute-Force-Angriffe (Fund 5).
    Sperrt IP-Adresse und Benutzername nach 5 Fehlversuchen für 10 Minuten."""
    MAX_ATTEMPTS = 5
    LOCKOUT_TIMEOUT = 600  # 10 Minuten (in Sekunden)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            ip = self.get_client_ip()
            username = request.POST.get('username', '').strip()

            # Schlüssel für Cache-Abfragen
            ip_key = f"lockout_ip_{ip}"
            user_key = f"lockout_user_{username}"

            ip_attempts = cache.get(ip_key, 0)
            user_attempts = cache.get(user_key, 0)

            if ip_attempts >= self.MAX_ATTEMPTS or user_attempts >= self.MAX_ATTEMPTS:
                form = self.get_form()
                form.add_error(None, "Zu viele fehlerhafte Anmeldeversuche. Dieses Konto oder diese IP ist vorübergehend gesperrt. Bitte versuchen Sie es in 10 Minuten erneut.")
                return self.render_to_response(self.get_context_data(form=form))

        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        ip = self.get_client_ip()
        username = self.request.POST.get('username', '').strip()

        ip_key = f"lockout_ip_{ip}"
        user_key = f"lockout_user_{username}"

        # Fehlversuche hochzählen und im Cache speichern
        try:
            val_ip = cache.get(ip_key, 0) + 1
            val_user = cache.get(user_key, 0) + 1
            cache.set(ip_key, val_ip, self.LOCKOUT_TIMEOUT)
            if username:
                cache.set(user_key, val_user, self.LOCKOUT_TIMEOUT)
        except Exception:
            pass

        return super().form_invalid(form)

    def form_valid(self, form):
        ip = self.get_client_ip()
        username = self.request.POST.get('username', '').strip()

        ip_key = f"lockout_ip_{ip}"
        user_key = f"lockout_user_{username}"

        # Nach erfolgreichem Login Zähler zurücksetzen
        try:
            cache.delete(ip_key)
            if username:
                cache.delete(user_key)
        except Exception:
            pass

        return super().form_valid(form)
