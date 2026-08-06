"""Das Audit-Log als Nachweis — nicht als Fenster in die letzten 500 Zeilen.

Vorher schnitt die Ansicht bei `logs[:500]` ab und schrieb die eigene Grenze
als Merkmal auf die Seite. Wer zu einem Vorgang von vor drei Monaten befragt
wurde — Betriebsrat nach § 99 BetrVG, Auskunftsersuchen nach Art. 15 DSGVO —
fand den Eintrag nicht. Dazu kannte die Ansicht nur den Aktions-Filter, der
Export zusätzlich Zeitraum: Der Knopf versprach „aktuelle Auswahl als CSV"
und lieferte etwas anderes als der Bildschirm zeigte.
"""
import csv
import io

from django.test import TestCase
from django.urls import reverse

from ..audit import write_audit
from ..models import AuditLog
from .utils import make_user


def _entries(count, action="READ_CV", user_id="mara", app_id=None):
    """Rohe Einträge ohne Kette — für Mengen-Tests reicht das."""
    AuditLog.objects.bulk_create([
        AuditLog(action=action, userId=user_id, applicationId=app_id,
                 metadataJson=f'{{"i": {i}}}') for i in range(count)])


class NoSilentCapTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("audit-admin", role="HR-Admin"))

    def test_all_entries_are_reachable_not_just_the_newest_500(self):
        _entries(205)
        resp = self.client.get(reverse('ats:audit_log'))
        self.assertEqual(resp.context['gesamt'], 205)
        self.assertEqual(len(resp.context['logs']), 100)
        letzte = self.client.get(reverse('ats:audit_log'), {'seite': 3})
        self.assertEqual(len(letzte.context['logs']), 5)

    def test_page_states_the_range_not_a_limit(self):
        _entries(205)
        resp = self.client.get(reverse('ats:audit_log'), {'seite': 2})
        self.assertContains(resp, "101–200 von 205")
        self.assertNotContains(resp, "max. 500")

    def test_an_absurd_page_number_does_not_crash(self):
        _entries(5)
        self.assertEqual(self.client.get(reverse('ats:audit_log'),
                                         {'seite': 'zwoelf'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('ats:audit_log'),
                                         {'seite': 9999}).status_code, 200)


class SelectionTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("audit-admin", role="HR-Admin"))
        _entries(3, action="READ_CV", user_id="mara")
        _entries(2, action="STATUS_CHANGE", user_id="jonas",
                 app_id="b88ae34d-e254-4ed7-976c-8cb6397a6bfa")

    def test_filter_by_action(self):
        resp = self.client.get(reverse('ats:audit_log'), {'action': 'READ_CV'})
        self.assertEqual(resp.context['gesamt'], 3)

    def test_filter_by_person(self):
        resp = self.client.get(reverse('ats:audit_log'), {'person': 'jonas'})
        self.assertEqual(resp.context['gesamt'], 2)

    def test_filter_by_application_accepts_the_shortened_id(self):
        """Die Tabelle zeigt die ID gekürzt — wer sie abschreibt, hat einen
        Präfix. Exakte Eingabe zu verlangen hiesse: Filter unbenutzbar."""
        resp = self.client.get(reverse('ats:audit_log'), {'bewerbung': 'b88ae34d'})
        self.assertEqual(resp.context['gesamt'], 2)

    def test_a_wrong_date_explains_itself_instead_of_breaking(self):
        resp = self.client.get(reverse('ats:audit_log'), {'von': '32.13.2026'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "JJJJ-MM-TT")

    def test_reversed_range_is_named_not_silently_empty(self):
        """Null Treffer und „Zeitraum verdreht" sehen sonst gleich aus."""
        resp = self.client.get(reverse('ats:audit_log'),
                               {'von': '2026-08-01', 'bis': '2026-07-01'})
        self.assertContains(resp, "Bis-Datum liegt vor dem Von-Datum")


class ExportMatchesTheScreenTestCase(TestCase):
    """Der Kern des Pakets: eine Auswahl-Logik für Ansicht UND Export."""

    def setUp(self):
        self.client.force_login(make_user("audit-admin", role="HR-Admin"))
        _entries(4, action="READ_CV", user_id="mara")
        _entries(6, action="STATUS_CHANGE", user_id="jonas")

    def _csv_rows(self, params):
        resp = self.client.get(reverse('ats:audit_export'), params)
        self.assertEqual(resp.status_code, 200)
        text = resp.content.decode('utf-8-sig')
        rows = list(csv.reader(io.StringIO(text), delimiter=';'))
        return rows[0][0], rows[2:]      # Kopfzeile, Datenzeilen

    def test_person_filter_reaches_the_export(self):
        kopf, rows = self._csv_rows({'person': 'jonas'})
        self.assertEqual(len(rows), 6)
        self.assertIn("Person jonas", kopf)

    def test_application_filter_reaches_the_export(self):
        _entries(1, action="READ_CV", user_id="mara", app_id="abc-123")
        _, rows = self._csv_rows({'bewerbung': 'abc-'})
        self.assertEqual(len(rows), 1)

    def test_export_and_view_count_the_same_entries(self):
        params = {'action': 'READ_CV'}
        sicht = self.client.get(reverse('ats:audit_log'), params)
        _, rows = self._csv_rows(params)
        self.assertEqual(len(rows), sicht.context['gesamt'])

    def test_bad_date_is_refused_not_exported_wholesale(self):
        """Ein Nachweis, der bei ungültigem Filter still ALLES ausliefert,
        wäre die gefährlichere Variante."""
        resp = self.client.get(reverse('ats:audit_export'), {'bis': 'gestern'})
        self.assertEqual(resp.status_code, 400)


class PersonFilterIsItselfLoggedTestCase(TestCase):
    """§ 87 Abs. 1 Nr. 6 BetrVG — Verhaltenskontrolle braucht ein Gegengewicht."""

    def setUp(self):
        self.client.force_login(make_user("audit-admin", role="HR-Admin"))
        _entries(2, user_id="jonas")

    def _notes(self):
        return AuditLog.objects.filter(action='AUDIT_PERSON_FILTER')

    def test_searching_for_a_person_leaves_a_trace(self):
        self.client.get(reverse('ats:audit_log'), {'person': 'jonas'})
        note = self._notes().get()
        self.assertEqual(note.userId, 'audit-admin')
        self.assertIn('jonas', note.metadataJson)

    def test_browsing_the_same_search_is_one_event_not_twenty(self):
        """Sonst ist die Kette zwar vollständig, aber unlesbar — und ein
        Protokoll, das niemand mehr liest, schützt niemanden."""
        for seite in (1, 2, 1):
            self.client.get(reverse('ats:audit_log'),
                            {'person': 'jonas', 'seite': seite})
        self.assertEqual(self._notes().count(), 1)

    def test_a_different_person_is_a_new_event(self):
        self.client.get(reverse('ats:audit_log'), {'person': 'jonas'})
        self.client.get(reverse('ats:audit_log'), {'person': 'mara'})
        self.assertEqual(self._notes().count(), 2)

    def test_browsing_without_a_person_filter_is_not_logged(self):
        self.client.get(reverse('ats:audit_log'))
        self.assertFalse(self._notes().exists())

    def test_the_export_by_person_is_logged_too(self):
        self.client.get(reverse('ats:audit_export'), {'person': 'jonas'})
        self.assertEqual(self._notes().count(), 1)


class ChainCheckTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("audit-admin", role="HR-Admin"))

    def test_the_check_runs_only_when_asked(self):
        """Sie liest und hasht jeden Eintrag — bei jedem Seitenaufruf
        mitzulaufen wäre derselbe Fehler wie die KI-Abfrage, die früher das
        Dashboard blockiert hat."""
        resp = self.client.get(reverse('ats:audit_log'))
        self.assertIsNone(resp.context['chain'])
        self.assertContains(resp, "Integrität jetzt prüfen")
        self.assertFalse(
            AuditLog.objects.filter(action='AUDIT_CHAIN_VERIFIED').exists())

    def test_an_intact_chain_says_so(self):
        write_audit('READ_CV', application_id='x')
        resp = self.client.get(reverse('ats:audit_log'), {'pruefen': '1'})
        self.assertTrue(resp.context['chain']['ok'])
        self.assertContains(resp, "Kette intakt")

    def test_a_broken_chain_names_the_entry_and_the_consequence(self):
        write_audit('READ_CV', application_id='x')
        manipuliert = write_audit('READ_CV', application_id='y')
        AuditLog.objects.filter(id=manipuliert.id).update(action='HARMLOS')
        resp = self.client.get(reverse('ats:audit_log'), {'pruefen': '1'})
        self.assertFalse(resp.context['chain']['ok'])
        self.assertContains(resp, "Kette verletzt")
        self.assertContains(resp, "nicht mehr belastbar")

    def test_the_check_itself_is_recorded(self):
        self.client.get(reverse('ats:audit_log'), {'pruefen': '1'})
        self.assertTrue(
            AuditLog.objects.filter(action='AUDIT_CHAIN_VERIFIED').exists())


class AccessTestCase(TestCase):
    def test_only_hr_admin_reaches_the_log(self):
        self.client.force_login(make_user("nur-viewer", role="Viewer"))
        for name in ('ats:audit_log', 'ats:audit_export'):
            resp = self.client.get(reverse(name))
            self.assertIn(resp.status_code, (302, 403), name)
