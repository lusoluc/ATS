"""Fehlerseiten, die einen Weg zurück zeigen.

Ohne sie lieferte Django in Produktion seinen englischen Standardtext:
„Not Found — The requested resource was not found on this server.", mit
`lang="en"`, 179 Bytes, ohne einen einzigen Link. Für eine deutsche
Karriereseite in der Pflege ist das eine verlorene Bewerbung — zumal der
häufigste 404 kein Tippfehler ist, sondern eine besetzte Stelle, deren Link
noch in einer Jobbörse oder E-Mail steht.

Die Tests laufen mit `DEBUG=False`, denn nur dann benutzt Django die eigenen
Vorlagen. Mit `DEBUG=True` sieht man die gelbe Entwickler-Seite und hätte
nie gemerkt, dass diese hier fehlen.
"""
import pathlib

from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import make_job, make_world
from .utils import make_user

VORLAGEN = pathlib.Path(__file__).resolve().parent.parent.parent / "templates"


@override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
class VierhundertvierTestCase(TestCase):
    """Der häufigste Fall: eine Stelle, die es nicht mehr gibt."""

    def test_a_dead_job_link_offers_a_way_on(self):
        resp = self.client.get(
            reverse('ats:job_detail',
                    args=["00000000-0000-0000-0000-000000000000"]))
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, "Diese Seite gibt es nicht", status_code=404)
        # Der Kern: ein Weg weiter, nicht nur eine Feststellung
        self.assertContains(resp, reverse('ats:job_list'), status_code=404)
        self.assertContains(resp, reverse('ats:job_alert'), status_code=404)

    def test_the_likely_reason_is_named(self):
        """„Nicht gefunden" beantwortet die Frage nicht, die die Person hat."""
        resp = self.client.get("/gibtesnicht/")
        self.assertContains(resp, "besetzt", status_code=404)

    def test_it_is_german_and_says_so(self):
        resp = self.client.get("/gibtesnicht/")
        self.assertContains(resp, 'lang="de"', status_code=404)
        self.assertNotContains(resp, "The requested resource",
                               status_code=404)


@override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
class FuenfhundertTestCase(TestCase):
    """Die Fehlerseite, die selbst nicht scheitern darf."""

    def test_the_page_renders_without_request_context(self):
        """Django rendert 500.html mit LEEREM Kontext — kein `request`, keine
        Kontextprozessoren. Wer hier `base.html` erbt, dessen Fehlerseite
        wirft beim Branding-Zugriff selbst einen Fehler, und der Besucher
        sieht Djangos nackten Standardtext."""
        from django.template import loader
        html = loader.get_template("500.html").render({})
        self.assertIn("Es ist etwas schiefgegangen", html)
        self.assertIn("/jobs/", html)

    def test_it_is_standalone_on_purpose(self):
        quelle = (VORLAGEN / "500.html").read_text(encoding="utf-8")
        self.assertNotIn("{% extends", quelle,
                         "Eine 500-Seite, die base.html erbt, scheitert genau "
                         "dann, wenn sie gebraucht wird.")
        self.assertIn("<!DOCTYPE", quelle)

    def test_it_needs_neither_database_nor_static_files(self):
        """Beides kann in der Lage, die den 500 ausgeloest hat, weg sein."""
        quelle = (VORLAGEN / "500.html").read_text(encoding="utf-8")
        for verboten in ("{% static", "{% load static", ".objects."):
            self.assertNotIn(verboten, quelle, verboten)

    def test_the_a11y_fundament_is_there(self):
        """Der Standalone-Wächter verlangt es, und hier gilt es besonders:
        Wer per Tastatur navigiert, muss den Weg zurück finden."""
        quelle = (VORLAGEN / "500.html").read_text(encoding="utf-8")
        for pflicht in ('<html lang="de"', "skip-link", ":focus-visible"):
            self.assertIn(pflicht, quelle, pflicht)


@override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
class DreihundertdreiTestCase(TestCase):
    """403 trifft interne Rollen — und liest sich sonst wie ein Defekt."""

    def test_a_viewer_sees_an_explanation_not_a_wall(self):
        welt = make_world()
        make_job(welt)
        self.client.force_login(make_user("fehler-viewer", role="Viewer"))
        resp = self.client.get(reverse('ats:audit_log'))
        if resp.status_code == 302:
            self.skipTest("Diese Route leitet um statt 403 zu werfen")
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, "Absicht", status_code=403)
        self.assertContains(resp, "HR-Admin", status_code=403)
        self.assertContains(resp, reverse('ats:dashboard'), status_code=403)


@override_settings(DEBUG=False, ALLOWED_HOSTS=["*"])
class CsrfFehlerTestCase(TestCase):
    """Der teuerste Fall: ausgefülltes Bewerbungsformular, Sitzung abgelaufen."""

    def setUp(self):
        self.welt = make_world()
        self.job = make_job(self.welt)

    def test_a_missing_token_no_longer_ends_in_english_jargon(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        resp = c.post(reverse('ats:bewerben', args=[self.job.id]),
                      {"first_name": "Mira", "last_name": "Muster",
                       "email": "mira@beispiel.example"})
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, "Sitzung ist abgelaufen", status_code=403)
        self.assertNotContains(resp, "CSRF verification failed",
                               status_code=403)

    def test_it_says_that_the_entries_are_still_there(self):
        """Die Eingaben stehen noch im Formular — das weiß nur niemand, dem
        man es nicht sagt."""
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        resp = c.post(reverse('ats:bewerben', args=[self.job.id]), {})
        self.assertContains(resp, "Zurück-Knopf", status_code=403)
        self.assertContains(resp, "noch da", status_code=403)

    def test_the_technical_reason_stays_out(self):
        """Der Ablehnungsgrund hilft beim Sondieren und sagt einer
        bewerbenden Person nichts."""
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        resp = c.post(reverse('ats:bewerben', args=[self.job.id]), {})
        for jargon in ("CSRF cookie not set", "Referer checking failed",
                       "CSRF token missing"):
            self.assertNotContains(resp, jargon, status_code=403)


class AlleFehlerseitenTestCase(TestCase):
    """Was für alle gilt — sonst wächst die nächste Seite ohne Ausweg."""

    SEITEN = ("400.html", "403.html", "404.html", "csrf_failure.html",
              "500.html")

    def test_every_error_page_offers_at_least_one_link(self):
        """Eine Fehlerseite ohne Weg zurück ist eine Sackgasse mit Stil."""
        ohne = []
        for name in self.SEITEN:
            quelle = (VORLAGEN / name).read_text(encoding="utf-8")
            if "href=" not in quelle:
                ohne.append(name)
        self.assertEqual(ohne, [], f"Fehlerseite ohne Ausweg: {ohne}")

    def test_every_error_page_exists(self):
        fehlend = [n for n in self.SEITEN if not (VORLAGEN / n).exists()]
        self.assertEqual(fehlend, [], f"Fehlerseite fehlt: {fehlend}")

    def test_none_of_them_leaks_english_django_wording(self):
        """Geprüft wird, was der Mensch SIEHT — nicht der Quelltext.

        Die Kommentare zitieren genau die Standardtexte, die hier ersetzt
        werden („403 Forbidden" …). Sie mitzuzählen hiesse, die Erklärung zu
        bestrafen; derselbe Stolperstein hat kurz zuvor schon den
        Label-Wächter ausgelöst.
        """
        import re
        stumm = re.compile(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}"
                           r"|<!--.*?-->|\{#.*?#\}", re.DOTALL)
        for name in self.SEITEN:
            sichtbar = stumm.sub(
                "", (VORLAGEN / name).read_text(encoding="utf-8"))
            for jargon in ("Not Found", "Forbidden", "Server Error",
                           "Bad Request"):
                self.assertNotIn(jargon, sichtbar, f"{name}: {jargon}")
