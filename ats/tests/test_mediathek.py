"""Die Mediathek als Bestand — nicht als Fenster in die letzten 200 Dateien.

Vorher schnitt die Ansicht bei `MediaAsset.objects...[:200]` ab, ohne dass die
Seite das erwähnte. Wer ein Bild aus dem letzten Jahr in eine Inhaltsseite
einbinden wollte, fand es nicht — und hatte keinen Grund anzunehmen, dass es
noch existiert. Also wurde dieselbe Datei ein zweites Mal hochgeladen, unter
neuem Namen, mit neuem Alt-Text. Dieselbe Fehlerklasse wie früher im Audit-Log
(`logs[:500]`), nur mit einem Bestand, der ausschliesslich wächst.
"""
import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import MediaAsset
from .utils import make_user


def _assets(count, prefix="bild", content_type="image/jpeg"):
    """Datensätze ohne echte Dateien — für Mengen-Tests reicht das.

    Die Zeitstempel werden gesetzt statt der Uhr überlassen: unter Windows
    tickt sie grob, `timezone.now()`-Gleichstände sind hier der Normalfall.
    Index 0 ist die älteste Datei, der höchste Index die neueste.
    """
    jetzt = timezone.now()
    MediaAsset.objects.bulk_create([
        MediaAsset(name=f"{prefix}-{i}", altText=f"Motiv {i}",
                   file=f"uploads/{prefix}-{i}.jpg", contentType=content_type,
                   createdAt=jetzt - datetime.timedelta(minutes=count - i))
        for i in range(count)])


class NoSilentCapTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("medien-admin", role="HR-Admin"))

    def test_all_files_are_reachable_not_just_the_newest_200(self):
        _assets(205)
        resp = self.client.get(reverse('ats:media_manage'))
        self.assertEqual(resp.context['gesamt'], 205)
        self.assertEqual(len(resp.context['assets']), 50)
        letzte = self.client.get(reverse('ats:media_manage'), {'seite': 5})
        self.assertEqual(len(letzte.context['assets']), 5)

    def test_the_oldest_file_is_actually_on_the_last_page(self):
        """Die eigentliche Frage: komme ich an die Datei von damals?"""
        _assets(205)
        letzte = self.client.get(reverse('ats:media_manage'), {'seite': 5})
        self.assertContains(letzte, "bild-0")

    def test_page_states_the_range_not_a_limit(self):
        _assets(205)
        resp = self.client.get(reverse('ats:media_manage'), {'seite': 2})
        self.assertContains(resp, "51–100 von 205")

    def test_an_absurd_page_number_does_not_crash(self):
        _assets(5)
        self.assertEqual(self.client.get(reverse('ats:media_manage'),
                                         {'seite': 'zwoelf'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('ats:media_manage'),
                                         {'seite': 9999}).status_code, 200)

    def test_one_page_shows_no_pagination(self):
        _assets(3)
        resp = self.client.get(reverse('ats:media_manage'))
        self.assertNotContains(resp, "Seiten der Mediathek")
        self.assertContains(resp, "1–3 von 3 Dateien")

    def test_identical_timestamps_lose_no_file_while_paging(self):
        """Die Windows-Uhr tickt grob — gleiche `createdAt` sind hier der
        Normalfall. Bei Gleichständen ist die Reihenfolge über LIMIT/OFFSET
        nicht garantiert: dieselbe Datei erscheint auf zwei Seiten, eine
        andere auf keiner. Das wäre wieder eine stille Lücke, nur schwerer zu
        bemerken als die alte Kappung.

        Der Durchlauf allein beweist das nicht — SQLite gibt Gleichstände
        stabil zurück, PostgreSQL (Produktion) nicht. Deshalb prüft der Test
        zusätzlich, dass überhaupt nach etwas Eindeutigem sortiert wird.
        """
        jetzt = timezone.now()
        MediaAsset.objects.bulk_create([
            MediaAsset(name=f"gleich-{i}", altText="Motiv",
                       file=f"uploads/gleich-{i}.jpg", createdAt=jetzt)
            for i in range(120)])
        gesehen = []
        for seite in (1, 2, 3):
            resp = self.client.get(reverse('ats:media_manage'), {'seite': seite})
            gesehen += [a.id for a in resp.context['assets']]
        self.assertEqual(len(gesehen), 120)
        self.assertEqual(len(set(gesehen)), 120)
        sortierung = resp.context['page'].paginator.object_list.query.order_by
        self.assertTrue(
            any(s.lstrip('-') == 'id' for s in sortierung),
            "Blätterung ohne eindeutige Zweitsortierung: bei gleichem "
            f"createdAt verliert LIMIT/OFFSET Zeilen (sortiert nach {sortierung}).")


class SucheTestCase(TestCase):
    """Blättern allein reicht nicht: bei 300 Dateien ist die gesuchte auf
    Seite 4, und niemand blättert danach."""

    def setUp(self):
        self.client.force_login(make_user("medien-admin", role="HR-Admin"))
        _assets(3, prefix="teamfoto")
        _assets(2, prefix="logo")

    def test_search_finds_by_display_name(self):
        resp = self.client.get(reverse('ats:media_manage'), {'suche': 'logo'})
        self.assertEqual(resp.context['gesamt'], 2)

    def test_search_finds_by_file_name(self):
        """Anzeigename und Dateiname fallen auseinander, sobald jemand den
        Anzeigenamen pflegt — gesucht wird trotzdem oft nach der Datei."""
        MediaAsset.objects.create(name="Pflegeteam Station 3",
                                  altText="Das Pflegeteam im Gruppenbild",
                                  file="uploads/IMG_2831.jpg")
        resp = self.client.get(reverse('ats:media_manage'), {'suche': 'IMG_2831'})
        self.assertEqual(resp.context['gesamt'], 1)

    def test_search_ignores_upper_and_lower_case(self):
        resp = self.client.get(reverse('ats:media_manage'), {'suche': 'TEAMFOTO'})
        self.assertEqual(resp.context['gesamt'], 3)

    def test_no_hits_names_the_stock_instead_of_looking_empty(self):
        """Sonst sehen „nichts gefunden" und „Mediathek ist leer" gleich aus."""
        resp = self.client.get(reverse('ats:media_manage'), {'suche': 'roentgen'})
        self.assertEqual(resp.context['gesamt'], 0)
        self.assertContains(resp, "im Bestand liegen 5 Dateien")

    def test_search_survives_paging(self):
        _assets(60, prefix="logo-serie")
        resp = self.client.get(reverse('ats:media_manage'),
                               {'suche': 'logo-serie', 'seite': 2})
        self.assertEqual(resp.context['gesamt'], 60)
        self.assertEqual(len(resp.context['assets']), 10)
        self.assertContains(resp, "suche=logo-serie&amp;seite=1")


class DeleteKeepsTheViewTestCase(TestCase):
    """Wer auf Seite 3 aufräumt, will nicht nach jedem Löschen wieder oben
    anfangen — sonst ist die Blätterung unbenutzbar."""

    def setUp(self):
        self.client.force_login(make_user("medien-admin", role="HR-Admin"))
        _assets(120, prefix="alt")

    def test_delete_returns_to_the_same_page_and_search(self):
        opfer = MediaAsset.objects.order_by('-createdAt')[60]
        resp = self.client.post(reverse('ats:delete_media', args=[opfer.id]),
                                {'suche': 'alt', 'seite': '2'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('suche=alt', resp['Location'])
        self.assertIn('seite=2', resp['Location'])
        self.assertFalse(MediaAsset.objects.filter(id=opfer.id).exists())

    def test_delete_without_view_params_still_works(self):
        opfer = MediaAsset.objects.first()
        resp = self.client.post(reverse('ats:delete_media', args=[opfer.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('ats:media_manage'))

    def test_delete_cannot_be_redirected_off_site(self):
        """Die Ziel-Adresse wird aus `reverse` plus zwei bekannten Parametern
        gebaut, nie aus einer mitgeschickten URL."""
        opfer = MediaAsset.objects.first()
        resp = self.client.post(reverse('ats:delete_media', args=[opfer.id]),
                                {'next': 'https://beispiel.invalid/',
                                 'suche': 'alt'})
        self.assertTrue(resp['Location'].startswith(reverse('ats:media_manage')))


class AccessTestCase(TestCase):
    def test_only_hr_admin_reaches_the_library(self):
        self.client.force_login(make_user("nur-viewer", role="Viewer"))
        resp = self.client.get(reverse('ats:media_manage'))
        self.assertIn(resp.status_code, (302, 403))
