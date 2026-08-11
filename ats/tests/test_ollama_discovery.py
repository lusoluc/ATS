"""Die Suche nach der Ollama-Adresse darf nicht bei jedem Aufruf laufen.

Sie probiert zwei TCP-Verbindungen mit je zwei Sekunden Zeitlimit und danach
eine Namensaufloesung – und lief bisher vor JEDEM KI-Aufruf erneut, auch
mitten in einer Schleife ueber dutzende Bewerbungen und selbst dann, wenn die
vorherige Antwort eine Sekunde alt war.
"""
import os
from unittest import mock

from django.test import TestCase

from ..views import ai as ai_views


class OllamaDiscoveryCacheTestCase(TestCase):
    def setUp(self):
        ai_views.reset_ollama_url_cache()
        self.addCleanup(ai_views.reset_ollama_url_cache)

    def _no_env(self):
        return mock.patch.dict(os.environ, {"OLLAMA_HOST": "", "OLLAMA_PORT": ""},
                               clear=False)

    def test_repeated_calls_probe_only_once(self):
        with self._no_env(), \
             mock.patch("socket.create_connection") as conn, \
             mock.patch("socket.gethostbyname", side_effect=OSError):
            conn.side_effect = OSError("kein Dienst")
            for _ in range(10):
                ai_views.get_ollama_url("api/generate")
            # Zwei Kandidaten-Hosts einmal probiert, nicht zehnmal
            self.assertEqual(conn.call_count, 2)

    def test_result_is_stable_across_calls(self):
        with self._no_env(), \
             mock.patch("socket.create_connection") as conn:
            conn.return_value = mock.MagicMock()
            first = ai_views.get_ollama_url("api/tags")
            second = ai_views.get_ollama_url("api/tags")
            self.assertEqual(first, second)

    def test_expired_cache_probes_again(self):
        """Wer Ollama nachtraeglich startet, soll nicht neu starten muessen."""
        with self._no_env(), \
             mock.patch("socket.create_connection") as conn, \
             mock.patch("socket.gethostbyname", side_effect=OSError):
            conn.side_effect = OSError("kein Dienst")
            ai_views.get_ollama_url()
            # Suchergebnis kuenstlich altern lassen
            stamp, base = ai_views._OLLAMA_BASE_CACHE
            ai_views._OLLAMA_BASE_CACHE = (
                stamp - ai_views.OLLAMA_DISCOVERY_TTL - 1, base)
            ai_views.get_ollama_url()
            self.assertEqual(conn.call_count, 4)

    def test_env_override_never_probes(self):
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "10.0.0.9"}, clear=False), \
             mock.patch("socket.create_connection") as conn:
            url = ai_views.get_ollama_url("api/tags")
            self.assertEqual(url, "http://10.0.0.9:11434/api/tags")
            conn.assert_not_called()

    def test_changed_port_is_not_served_from_cache(self):
        with self._no_env(), \
             mock.patch("socket.create_connection") as conn:
            conn.return_value = mock.MagicMock()
            self.assertIn(":11434/", ai_views.get_ollama_url())
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "", "OLLAMA_PORT": "11500"},
                             clear=False), \
             mock.patch("socket.create_connection") as conn:
            conn.return_value = mock.MagicMock()
            self.assertIn(":11500/", ai_views.get_ollama_url())

    def test_reset_forces_a_fresh_search(self):
        """`ai_doctor` muss den jetzigen Zustand sehen, nicht den gepufferten."""
        with self._no_env(), \
             mock.patch("socket.create_connection") as conn:
            conn.return_value = mock.MagicMock()
            ai_views.get_ollama_url()
            ai_views.reset_ollama_url_cache()
            ai_views.get_ollama_url()
            self.assertEqual(conn.call_count, 2)


class OllamaStatusBadgeTestCase(TestCase):
    """Das Dashboard-Abzeichen darf die meistgeoeffnete Seite nicht bremsen -
    und es muss dieselbe Adresse pruefen, die die KI-Aufrufe benutzen."""

    def setUp(self):
        ai_views.reset_ollama_url_cache()
        ai_views.reset_ollama_status_cache()
        self.addCleanup(ai_views.reset_ollama_url_cache)
        self.addCleanup(ai_views.reset_ollama_status_cache)
        # Diese Klasse prueft die MECHANIK der Erreichbarkeitspruefung. Die
        # laeuft nur, wenn die KI-Assistenz freigeschaltet ist - ohne
        # Freischaltung wird bewusst gar nicht gesucht (eigene Testklasse
        # unten). Also hier einschalten, sonst prueft niemand mehr den Puffer.
        from ..models import SystemSetting
        SystemSetting.objects.create(key='AI_SCORING_ENABLED', value='1')

    def test_status_is_not_probed_on_every_page_view(self):
        from ..views.admin_pages import gemma_status
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "10.0.0.7"}, clear=False), \
             mock.patch("socket.create_connection") as conn:
            conn.side_effect = OSError("kein Dienst")
            for _ in range(8):
                self.assertEqual(gemma_status(), 'OFFLINE')
            self.assertEqual(conn.call_count, 1)

    def test_custom_port_is_respected(self):
        """Vorher stand hier fest 11434: Wer OLLAMA_PORT setzte, sah OFFLINE
        ueber einer laufenden KI."""
        from ..views.admin_pages import gemma_status
        with mock.patch.dict(os.environ,
                             {"OLLAMA_HOST": "10.0.0.7", "OLLAMA_PORT": "11500"},
                             clear=False), \
             mock.patch("socket.create_connection") as conn:
            conn.return_value = mock.MagicMock()
            self.assertEqual(gemma_status(), 'ONLINE')
            self.assertEqual(conn.call_args[0][0], ("10.0.0.7", 11500))

    def test_reset_forces_fresh_probe(self):
        from ..views.admin_pages import gemma_status
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "10.0.0.7"}, clear=False), \
             mock.patch("socket.create_connection") as conn:
            conn.side_effect = OSError("weg")
            gemma_status()
            ai_views.reset_ollama_status_cache()
            gemma_status()
            self.assertEqual(conn.call_count, 2)


class AbgeschalteteKiWirdNichtGesuchtTestCase(TestCase):
    """Der Kern des Pakets: Ohne Freischaltung kein Netzwerk-Versuch.

    GEMESSEN gegen die Demo-Daten, ohne installierte KI: Das Dashboard
    brauchte 6.299 ms — davon 6.161 ms allein für diese Suche. Der Puffer
    hält 20 Sekunden, also wartete alle 20 Sekunden die nächste Person wieder
    sechs Sekunden. Für eine Funktion, die per Default AUS ist und auf der
    Seite nur ein Abzeichen zeichnet.

    Dasselbe Muster gilt im Steckbrief schon länger (`application_summary`
    kehrt ohne Opt-in sofort zurück, „kein Ollama-Verbindungsversuch") — es
    war nur an dieser Tür nicht durchgesetzt.
    """

    def setUp(self):
        ai_views.reset_ollama_url_cache()
        ai_views.reset_ollama_status_cache()
        self.addCleanup(ai_views.reset_ollama_url_cache)
        self.addCleanup(ai_views.reset_ollama_status_cache)

    def test_no_socket_is_opened_when_the_assistance_is_off(self):
        from ..views.admin_pages import gemma_status
        with mock.patch("socket.create_connection") as conn, \
             mock.patch("socket.gethostbyname") as dns:
            self.assertEqual(gemma_status(), 'AUS')
        conn.assert_not_called()
        dns.assert_not_called()

    def test_off_is_reported_as_off_not_as_offline(self):
        """„OFFLINE" liest sich wie ein Defekt. Es ist aber schlicht nichts
        eingeschaltet — und der Unterschied entscheidet, ob jemand die IT
        ruft."""
        from ..views.admin_pages import gemma_status
        self.assertEqual(gemma_status(), 'AUS')

    def test_the_ai_page_probes_anyway(self):
        """Wer die Vorbewertung einschalten will, muss vorher sehen, ob
        überhaupt etwas antwortet — dort ist die Erreichbarkeit die Frage."""
        from ..views.admin_pages import gemma_status
        with mock.patch("socket.create_connection") as conn:
            conn.side_effect = OSError("nichts da")
            self.assertEqual(gemma_status(force=True), 'OFFLINE')
        self.assertTrue(conn.called)

    def test_once_switched_on_the_probe_runs_again(self):
        from ..models import SystemSetting
        from ..views.admin_pages import gemma_status
        SystemSetting.objects.create(key='AI_SCORING_ENABLED', value='1')
        with mock.patch("socket.create_connection") as conn:
            conn.side_effect = OSError("nichts da")
            self.assertEqual(gemma_status(), 'OFFLINE')
        self.assertTrue(conn.called)

    def test_the_dashboard_does_not_wait_for_a_disabled_ai(self):
        """Die Seite selbst, nicht nur die Hilfsfunktion."""
        from django.urls import reverse

        from .utils import make_user
        self.client.force_login(make_user("kein-warten", role="HR-Admin"))
        with mock.patch("socket.create_connection") as conn:
            resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(resp.status_code, 200)
        conn.assert_not_called()
        self.assertEqual(resp.context['gemma_status'], 'AUS')

    def test_the_settings_hub_does_not_wait_either(self):
        from django.urls import reverse

        from .utils import make_user
        self.client.force_login(make_user("hub-kein-warten", role="HR-Admin"))
        with mock.patch("socket.create_connection") as conn:
            resp = self.client.get(reverse('ats:settings_hub'))
        self.assertEqual(resp.status_code, 200)
        conn.assert_not_called()
        self.assertContains(resp, "KI-Assistenz ist aus")


class VerbindungsZeitlimitTestCase(TestCase):
    """Auch mit eingeschalteter KI darf ein toter Dienst nicht sechs Sekunden
    kosten. Ollama läuft lokal oder im LAN: Dort steht eine TCP-Verbindung in
    Millisekunden oder wird sofort abgelehnt. Die zwei Sekunden wirkten nur,
    wenn Pakete ins Leere laufen — und dann dreimal hintereinander."""

    def test_the_timeout_is_short_enough_to_stay_usable(self):
        self.assertLessEqual(
            ai_views.OLLAMA_CONNECT_TIMEOUT, 1.0,
            "Drei Verbindungsversuche hintereinander: Bei mehr als einer "
            "Sekunde je Versuch wartet die Seite wieder mehrere Sekunden.")

    def test_every_probe_uses_the_shared_timeout(self):
        """Sonst senkt jemand die Konstante und ein Versuch bleibt langsam."""
        import pathlib
        import re
        quelle = pathlib.Path(ai_views.__file__).read_text(encoding='utf-8')
        harte_werte = re.findall(r'create_connection\([^)]*timeout=([\d.]+)',
                                 quelle, re.S)
        self.assertEqual(
            harte_werte, [],
            f"Verbindungsversuch mit fest verdrahtetem Zeitlimit: {harte_werte}")
