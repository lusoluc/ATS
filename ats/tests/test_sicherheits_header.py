"""Die Air-Gap-Zusage als Browser-Regel statt als Vorsatz.

`System_Architektur_und_Feature_Katalog.md` wirbt mit „Air-Gapped Architektur
(keine Cloud-APIs, keine Tracker, keine Google Fonts)". Genau diese Zusage war
schon einmal gebrochen: `base.html` lud Schriften und Symbole von cdnjs und
Google — jahrelang, unbemerkt. Behoben wurde es von Hand, und damit galt sie
seither wieder nur, solange alle daran denken.

Gemessen wurde außerdem, was Django von sich aus setzt: Referrer-Policy,
X-Frame-Options, nosniff und COOP sind da. Content-Security-Policy und
Permissions-Policy fehlten.
"""
from django.test import TestCase
from django.urls import reverse

from ..security_headers import CSP_DIREKTIVEN, PERMISSIONS_POLICY, csp_wert
from .factories import make_job, make_world
from .utils import make_user


class KopfzeilenSindDaTestCase(TestCase):
    def test_public_pages_carry_the_policy(self):
        for name in ('ats:home', 'ats:job_list', 'ats:accessibility_statement'):
            resp = self.client.get(reverse(name))
            self.assertIn('Content-Security-Policy', resp.headers, name)
            self.assertIn('Permissions-Policy', resp.headers, name)

    def test_internal_pages_carry_it_too(self):
        """Auch dort werden Bewerberdaten angezeigt."""
        self.client.force_login(make_user("csp-rec", role="Recruiter"))
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertIn('Content-Security-Policy', resp.headers)

    def test_django_still_sets_what_it_always_set(self):
        """Die neue Middleware darf nichts verdrängen."""
        resp = self.client.get(reverse('ats:job_list'))
        for kopf in ('Referrer-Policy', 'X-Frame-Options',
                     'X-Content-Type-Options'):
            self.assertIn(kopf, resp.headers, kopf)

    def test_the_django_admin_is_left_alone(self):
        """Djangos eigene Oberfläche bringt eigene Skripte mit und ist kein
        Teil des Produkts — sie mit einer Politik zu brechen, die für die
        Bewerberstrecke gedacht ist, hilft niemandem."""
        self.client.force_login(make_user("csp-su", superuser=True))
        resp = self.client.get('/admin/')
        self.assertNotIn('Content-Security-Policy', resp.headers)


class DiePolitikSchliesstFremdeQuellenAusTestCase(TestCase):
    """Der Kern: Was nicht von diesem Server kommt, wird nicht geladen."""

    def test_no_directive_allows_a_foreign_host(self):
        for name, wert in CSP_DIREKTIVEN.items():
            for teil in wert.split():
                self.assertNotIn(
                    "://", teil,
                    f"{name} erlaubt eine fremde Herkunft: {teil}")
                self.assertNotIn(
                    "*", teil,
                    f"{name} erlaubt beliebige Quellen: {teil}")

    def test_the_directives_that_carry_the_promise_are_present(self):
        """Fällt eine davon weg, ist die Zusage wieder nur ein Vorsatz."""
        for name in ("default-src", "script-src", "style-src", "img-src",
                     "font-src", "connect-src", "frame-ancestors",
                     "form-action", "base-uri", "object-src"):
            self.assertIn(name, CSP_DIREKTIVEN, name)

    def test_data_exfiltration_and_framing_are_closed(self):
        self.assertEqual(CSP_DIREKTIVEN["connect-src"], "'self'")
        self.assertEqual(CSP_DIREKTIVEN["frame-ancestors"], "'none'")
        self.assertEqual(CSP_DIREKTIVEN["form-action"], "'self'")

    def test_the_header_value_is_well_formed(self):
        wert = csp_wert()
        self.assertIn("default-src 'self'", wert)
        self.assertEqual(wert.count(";"), len(CSP_DIREKTIVEN) - 1)

    def test_an_applicant_system_asks_for_no_camera_or_location(self):
        for merkmal in ("camera=()", "microphone=()", "geolocation=()"):
            self.assertIn(merkmal, PERMISSIONS_POLICY)


class KeineFremdenAdressenInDenVorlagenTestCase(TestCase):
    """Der Wächter zur Politik: Was die CSP blockt, soll gar nicht erst im
    Markup stehen — sonst bleibt ein Bild leer und niemand weiß, warum.

    Genau so ist es passiert: cdnjs und Google Fonts standen in `base.html`,
    und auf einer abgeschotteten Installation fehlten damit ALLE Symbole."""

    def test_no_template_loads_from_a_foreign_host(self):
        import pathlib
        import re
        wurzel = (pathlib.Path(__file__).resolve().parent.parent.parent
                  / "templates")
        dateien = list(wurzel.rglob("*.html"))
        self.assertGreater(len(dateien), 20,
                           "Der Scan sieht ins Leere — dann prüft er nichts.")
        treffer = []
        muster = re.compile(r'(?:src|href)\s*=\s*"(https?:)?//([^"/]+)')
        for pfad in dateien:
            inhalt = pfad.read_text(encoding="utf-8", errors="ignore")
            for m in muster.finditer(inhalt):
                host = m.group(2)
                # schema.org/w3.org stehen in Metadaten (JSON-LD, xmlns) und
                # werden nie geladen - sie sind Bezeichner, keine Adressen.
                if host in ("schema.org", "www.w3.org"):
                    continue
                zeile = inhalt[:m.start()].count("\n") + 1
                treffer.append(f"{pfad.name}:{zeile} -> {host}")
        self.assertEqual(
            treffer, [],
            "Vorlage laedt von einem fremden Server. Die CSP blockt das, und "
            "die Air-Gap-Zusage waere gebrochen: " + ", ".join(treffer))


class FremdeBildAdressenWerdenAbgelehntTestCase(TestCase):
    """Zwei Felder darf der Betrieb frei füllen — Logo und Startbild. Eine
    fremde Adresse dort meldet die IP-Adresse JEDER bewerbenden Person an
    diesen Server. Die CSP blockt sie ohnehin; ohne diese Prüfung bliebe das
    Bild leer und niemand wüsste, warum."""

    def setUp(self):
        self.welt = make_world()
        make_job(self.welt)
        self.client.force_login(make_user("brand-admin", role="HR-Admin"))

    def _speichern(self, logo):
        return self.client.post(reverse('ats:branding'),
                                {'enabled': '1', 'mode': 'LIGHT',
                                 'primary': '#0065bd', 'logo_url': logo},
                                follow=True)

    def test_a_local_path_is_accepted(self):
        self._speichern('/media/uploads/logo.png')
        self.welt.org.refresh_from_db()
        self.assertEqual(self.welt.org.brandLogoUrl, '/media/uploads/logo.png')

    def test_a_foreign_url_is_refused_and_explained(self):
        resp = self._speichern('https://cdn.beispiel.example/logo.png')
        self.welt.org.refresh_from_db()
        self.assertEqual(self.welt.org.brandLogoUrl, '')
        self.assertContains(resp, "IP-Adresse")
        self.assertContains(resp, "Medien")

    def test_a_protocol_relative_url_is_refused_too(self):
        """`//host/bild.png` sieht relativ aus und ist es nicht."""
        self._speichern('//cdn.beispiel.example/logo.png')
        self.welt.org.refresh_from_db()
        self.assertEqual(self.welt.org.brandLogoUrl, '')

    def test_the_refusal_is_recorded(self):
        from ..models import AuditLog
        self._speichern('https://cdn.beispiel.example/logo.png')
        self.assertTrue(AuditLog.objects.filter(
            action='BRANDING_EXTERNAL_URL_BLOCKED').exists())

    def test_an_existing_logo_survives_a_refused_change(self):
        """Sonst löscht ein Fehlversuch das funktionierende Logo."""
        self._speichern('/media/uploads/logo.png')
        self._speichern('https://cdn.beispiel.example/neu.png')
        self.welt.org.refresh_from_db()
        self.assertEqual(self.welt.org.brandLogoUrl, '/media/uploads/logo.png')
