"""Koordinaten aus der Postleitzahl — offline, ohne fremden Dienst.

Ohne Koordinaten fällt die Umkreissuche des Job-Alerts still auf „exakt
derselbe Standort" zurück: Man stellt 50 km ein und bekommt einen Ort.
Eintragen konnte man sie seit U6, kennen tut sie trotzdem niemand auswendig.

Die Tabelle liegt bewusst im Repo statt hinter einem Geocoding-Dienst — sonst
ginge bei jeder Standortanlage eine Trägeradresse nach außen.
"""
from django.test import TestCase
from django.urls import reverse

from ..geo import lookup_plz, table_size
from ..models import Location
from .utils import make_user


class PlzLookupTestCase(TestCase):
    def test_known_postal_codes_resolve_plausibly(self):
        hh = lookup_plz("20095")
        self.assertIsNotNone(hh)
        # Hamburg liegt bei 53,55 N / 10,00 O - grosszuegige Schranken, der
        # Test soll die Tabelle pruefen, nicht die vierte Nachkommastelle.
        self.assertAlmostEqual(hh[0], 53.55, delta=0.1)
        self.assertAlmostEqual(hh[1], 10.00, delta=0.1)

    def test_common_spellings_are_accepted(self):
        self.assertEqual(lookup_plz(" 21335 "), lookup_plz("21335"))
        self.assertEqual(lookup_plz("D-21335"), lookup_plz("21335"))

    def test_unknown_or_malformed_gives_none(self):
        for value in (None, "", "abcde", "1234", "123456", "99999"):
            self.assertIsNone(lookup_plz(value), value)

    def test_table_is_actually_bundled(self):
        """Ein leeres Ergebnis waere hier kein Fehlschlag, sondern ein
        stillschweigender Funktionsverlust - deshalb gepruefte Untergrenze."""
        self.assertGreater(table_size(), 8000)


class LocationCoordinateFillTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("plz-admin", role="HR-Admin"))
        self.url = reverse('ats:locations')

    def test_new_location_gets_coordinates_from_its_postal_code(self):
        self.client.post(self.url, {'name': 'Klinik Nord', 'city': 'Hamburg',
                                    'postalCode': '20095'})
        loc = Location.objects.get(name='Klinik Nord')
        self.assertAlmostEqual(loc.lat, 53.55, delta=0.1)
        self.assertAlmostEqual(loc.lng, 10.00, delta=0.1)

    def test_typed_coordinates_win_over_the_table(self):
        """Wer sie kennt, kennt sie genauer als den Mittelpunkt einer PLZ."""
        self.client.post(self.url, {'name': 'Haus Elbblick', 'postalCode': '20095',
                                    'lat': '53.1234', 'lng': '9.8765'})
        loc = Location.objects.get(name='Haus Elbblick')
        self.assertAlmostEqual(loc.lat, 53.1234)
        self.assertAlmostEqual(loc.lng, 9.8765)

    def test_unknown_postal_code_leaves_coordinates_empty(self):
        self.client.post(self.url, {'name': 'Irgendwo', 'postalCode': '99999'})
        loc = Location.objects.get(name='Irgendwo')
        self.assertIsNone(loc.lat)

    def test_existing_locations_can_be_filled_afterwards(self):
        Location.objects.create(name='Alt-Standort', postalCode='21335')
        self.client.post(self.url, {'action': 'fill_coordinates'})
        loc = Location.objects.get(name='Alt-Standort')
        self.assertAlmostEqual(loc.lat, 53.23, delta=0.1)

    def test_filling_never_overwrites_existing_coordinates(self):
        Location.objects.create(name='Gepflegt', postalCode='20095',
                                lat=1.0, lng=2.0)
        self.client.post(self.url, {'action': 'fill_coordinates'})
        loc = Location.objects.get(name='Gepflegt')
        self.assertEqual(loc.lat, 1.0)
        self.assertEqual(loc.lng, 2.0)

    def test_button_appears_only_when_there_is_work(self):
        Location.objects.create(name='Ohne PLZ')
        self.assertNotContains(self.client.get(self.url),
                               "Fehlende Koordinaten aus der Postleitzahl")
        Location.objects.create(name='Mit PLZ', postalCode='20095')
        self.assertContains(self.client.get(self.url),
                            "Fehlende Koordinaten aus der Postleitzahl")

    def test_radius_search_actually_works_with_filled_coordinates(self):
        """Der eigentliche Zweck: der Job-Alert trifft jetzt den Umkreis."""
        from ..job_alerts import haversine_km
        hh, lg = lookup_plz("20095"), lookup_plz("21335")
        distance = haversine_km(hh[0], hh[1], lg[0], lg[1])
        # Hamburg-Lueneburg sind rund 45 km Luftlinie.
        self.assertGreater(distance, 30)
        self.assertLess(distance, 60)
