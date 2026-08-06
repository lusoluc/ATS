"""Test-Runner: schneller Passwort-Hash, damit die Suite in Minuten läuft.

WAS GEMESSEN WURDE: 970 Tests in 1.374 Sekunden — im Schnitt 1,4 Sekunden je
Test. Genau so lange braucht auf dieser Maschine EIN Passwort-Hash. Django
hängt an jedes `create_user()` den Produktions-Hasher (PBKDF2, 1,2 Mio.
Iterationen), und die Testhilfe `make_user()` steht an über 300 Stellen, die
meisten davon in `setUp` — also einmal pro Testmethode. Die langsamsten Fälle
waren folgerichtig die Gremien-Tests mit vier bis sechs Beteiligten: rund
sieben Sekunden, davon fast alles Hashen.

Das ist keine Schwäche der Tests, sondern eine Voreinstellung, die für den
Betrieb richtig und für einen Testlauf sinnlos ist: Kein Test prüft die Stärke
des Hashers, und niemand greift die Testdatenbank an.

WARUM HIER UND NICHT IN settings.py: Ein `if 'test' in sys.argv` in den
Einstellungen wäre ein schwacher Hasher, der nur an einer Zeichenkette hängt —
ein falsch gesetztes Argument, ein Aufruf über eine andere Einstiegsstelle, und
er gilt im Betrieb. Der Runner dagegen existiert ausschließlich während eines
Testlaufs. In die Produktion kann diese Einstellung nicht geraten, weil dort
nichts sie lädt.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.test.runner import DiscoverRunner


class SecurATSTestRunner(DiscoverRunner):
    """DiscoverRunner mit MD5-Hasher — nur innerhalb des Testlaufs."""

    def setup_test_environment(self, **kwargs: Any) -> None:
        super().setup_test_environment(**kwargs)
        settings.PASSWORD_HASHERS = [
            "django.contrib.auth.hashers.MD5PasswordHasher",
        ]
