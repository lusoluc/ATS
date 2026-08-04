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
