"""Die Suite darf nicht an einer Voreinstellung hängen, die niemand prüft.

GEMESSEN, NICHT VERMUTET: 970 Tests brauchten 1.374 Sekunden — im Schnitt
1,4 Sekunden je Test, exakt die Dauer EINES PBKDF2-Hashes mit 1,2 Mio.
Iterationen auf dieser Maschine. Die Testhilfe `make_user()` steht an über 300
Stellen, die meisten in `setUp`. Die langsamsten Fälle waren die Gremien-Tests
mit vier bis sechs Beteiligten (rund sieben Sekunden je Test); nach der
Umstellung läuft dieselbe Klasse in 0,36 Sekunden.

Eine Suite, die eine halbe Stunde braucht, wird vor dem Commit übersprungen —
und dann nützt sie niemandem mehr.
"""
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from .utils import make_user


class FastHasherTestCase(TestCase):
    def test_the_test_run_uses_a_cheap_hasher(self):
        self.assertTrue(settings.PASSWORD_HASHERS[0].endswith("MD5PasswordHasher"),
                        f"Unerwarteter Hasher: {settings.PASSWORD_HASHERS[0]}")

    def test_users_are_still_usable_after_the_switch(self):
        """Ein schneller Hasher darf nichts am Verhalten ändern."""
        user = make_user("laufzeit-probe")
        self.assertTrue(user.check_password("pw12345!"))
        self.assertFalse(user.check_password("falsch"))
        self.assertNotIn("pw12345!", user.password)
        self.assertTrue(self.client.login(username="laufzeit-probe",
                                          password="pw12345!"))

    def test_creating_users_does_not_cost_a_production_hash(self):
        """Die eigentliche Aussage in Zahlen.

        Mit dem Produktions-Hasher bräuchten 20 Benutzer hier über 20 Sekunden;
        mit dem Test-Hasher sind es Millisekunden. Die Grenze liegt bewusst
        weit dazwischen, damit ein langsamer CI-Läufer nicht rot wird — sie
        trennt die beiden Größenordnungen, nicht zwei ähnliche Werte.
        """
        User = get_user_model()
        start = time.perf_counter()
        for i in range(20):
            User.objects.create_user(username=f"tempo-{i}", password="pw12345!")
        dauer = time.perf_counter() - start
        self.assertLess(dauer, 5.0,
                        f"20 Benutzer brauchten {dauer:.1f}s – läuft hier der "
                        f"Produktions-Hasher? ({settings.PASSWORD_HASHERS[0]})")


class GuardrailNoWeakHasherInSettingsTestCase(TestCase):
    """Der schwache Hasher gehört in den Runner, nicht in die Einstellungen.

    Die naheliegende Abkürzung wäre `if 'test' in sys.argv: PASSWORD_HASHERS =
    [...]` in `securats/settings.py`. Dann hinge die Passwortsicherheit der
    Produktion an einer Zeichenkette in der Kommandozeile — ein Aufruf über
    einen anderen Einstiegspunkt, und MD5 gilt im Betrieb. Der Runner wird
    dort nie geladen.
    """

    def test_settings_do_not_assign_password_hashers(self):
        from pathlib import Path
        basis = Path(settings.BASE_DIR) / "securats"
        for pfad in basis.glob("*.py"):
            text = pfad.read_text(encoding="utf-8")
            self.assertNotIn(
                "PASSWORD_HASHERS =", text,
                f"{pfad.name} setzt PASSWORD_HASHERS. Ein schwacher Hasher "
                f"gehört ausschließlich in ats/test_runner.py – dort kann er "
                f"nicht in den Betrieb geraten.")
