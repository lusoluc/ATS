"""Die Rolle heißt Viewer — dann darf sie auch nur sehen.

Bis hierher war `Viewer` technisch mit `Hiring-Manager` identisch: Beide
liefen nur über `any_staff_required`. Ein „Viewer" konnte damit das Board
umsortieren, Aufgaben abhaken, Seiteninhalte bearbeiten und Personalbedarf
melden. Ein Rollenname, der etwas anderes verspricht als er hält, ist in
einer Rechteverwaltung besonders teuer: Danach werden Zugänge vergeben —
„der schaut ja nur" — und niemand prüft nach.

Die Ausnahme ist bewusst und wird hier mitgeprüft: Wer namentlich in ein
Auswahlgremium oder eine Freigabestufe berufen wurde, entscheidet genau
dort. Diese Befugnis kommt aus der Benennung, nicht aus der Basisrolle —
sonst könnte ein Betriebsratsmitglied mit Basisrolle `Viewer` seine eigene
Freigabe nicht mehr erteilen.
"""
import ast
import pathlib

from django.test import TestCase
from django.urls import reverse

from .utils import make_user


class ViewerDarfNichtsAendernTestCase(TestCase):
    """Lesen ja, ändern nein — an den Stellen des täglichen Bearbeitens."""

    def setUp(self):
        self.client.force_login(make_user("nur-schauer", role="Viewer"))

    def test_the_board_may_be_seen(self):
        r = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_the_board_order_may_not_be_changed(self):
        r = self.client.post(reverse('ats:reorder_board'), data={})
        self.assertEqual(r.status_code, 403)

    def test_tasks_may_be_seen_but_not_ticked_off(self):
        self.assertEqual(self.client.get(reverse('ats:tasks')).status_code, 200)
        self.assertEqual(self.client.post(reverse('ats:tasks'), data={}).status_code,
                         403)

    def test_staffing_requests_may_be_seen_but_not_filed(self):
        self.assertEqual(
            self.client.get(reverse('ats:staffing_requests')).status_code, 200)
        self.assertEqual(
            self.client.post(reverse('ats:staffing_requests'), data={}).status_code,
            403)

    def test_landing_pages_may_be_seen_but_not_edited(self):
        self.assertEqual(
            self.client.get(reverse('ats:landing_pages')).status_code, 200)
        self.assertEqual(
            self.client.post(reverse('ats:landing_pages'), data={}).status_code,
            403)


class OberflaecheZeigtKeineWirkungslosenKnoepfeTestCase(TestCase):
    """Ein Knopf, der ins 403 läuft, ist schlimmer als kein Knopf.

    Er behauptet eine Möglichkeit, die es nicht gibt — und die Person sucht
    den Fehler bei sich.
    """

    def setUp(self):
        # Ohne offene Aufgabe zeigt die Seite auch einer Recruiterin keinen
        # Knopf - der Gegentest unten wuerde dann nichts beweisen.
        from ..models import Applicant, Application, WorkflowTask
        from .factories import make_job, make_world
        job = make_job(make_world(), title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Aufgaben", lastName="T",
                                          email="task@example.invalid")
        app = Application.objects.create(applicant=person, jobPosting=job,
                                         status="IN_REVIEW")
        WorkflowTask.objects.create(application=app,
                                    title="Referenzen einholen")
        self.client.force_login(make_user("schauer-ui", role="Viewer"))

    #: Seite -> ein Feld, das es NUR im Aktions-Formular dieser Seite gibt.
    #: Bewusst nicht auf `method="post"` pruefen: Das Abmelden-Formular in der
    #: Navigation ist auf JEDER Seite eins - der Test waere immer rot.
    AKTIONSFELD = {
        'ats:tasks': 'name="task_id"',
        'ats:staffing_requests': 'name="department"',
        'ats:landing_pages': 'name="expires"',
    }

    def test_the_viewer_sees_the_reason_instead_of_buttons(self):
        for name, feld in self.AKTIONSFELD.items():
            with self.subTest(seite=name):
                inhalt = self.client.get(reverse(name)).content.decode()
                self.assertIn("Nur Einsicht", inhalt,
                              "Ohne Hinweis wirkt die Seite kaputt.")
                self.assertNotIn(feld, inhalt,
                                 "Formular sichtbar, das der Viewer nicht "
                                 "absenden darf.")

    def test_a_writing_role_still_gets_the_buttons(self):
        self.client.force_login(make_user("rec-ui", role="Recruiter"))
        inhalt = self.client.get(reverse('ats:tasks')).content.decode()
        self.assertNotIn("Nur Einsicht", inhalt)
        self.assertIn('name="task_id"', inhalt,
                      "Die Verschaerfung hat der Recruiterin die Knoepfe "
                      "genommen.")


class SchreibendeRollenBleibenUnberuehrtTestCase(TestCase):
    """Die Verschärfung darf niemandem die Arbeit nehmen, der sie braucht."""

    def test_the_hiring_manager_may_still_file_a_staffing_request(self):
        self.client.force_login(make_user("hm-schreibt", role="Hiring-Manager"))
        r = self.client.post(reverse('ats:staffing_requests'), data={})
        self.assertNotEqual(r.status_code, 403,
                            "Hiring-Manager wurde mit dem Viewer zusammen "
                            "ausgesperrt - die Bedarfsmeldung ist genau seine "
                            "Aufgabe.")

    def test_the_recruiter_may_still_reorder_the_board(self):
        self.client.force_login(make_user("rec-sortiert", role="Recruiter"))
        r = self.client.post(reverse('ats:reorder_board'), data={})
        self.assertNotEqual(r.status_code, 403)


class GuardrailWritingViewsAreClosedForViewerTestCase(TestCase):
    """Die Fehlerklasse, nicht die fünf gefundenen Fälle.

    Jede interne View, die etwas per POST verändert, muss den Viewer
    aussperren — oder hier mit Begründung stehen. Sonst öffnet die nächste
    neue Seite die Lücke wieder, und niemand merkt es.
    """

    #: View -> warum sie den Viewer NICHT ueber die Basisrolle aussperrt.
    AUSNAHMEN = {
        'approvals_inbox':
            'Freigabe-Entscheidung: Die Befugnis kommt aus der Kettenrolle '
            '(may_decide_requisition_step), nicht aus der Basisrolle. Ein '
            'Betriebsratsmitglied mit Basisrolle Viewer koennte sonst seine '
            'eigene Freigabe nicht mehr erteilen.',
        'application_vote':
            'Gremiums-Stimme: Nur namentlich berufene Mitglieder duerfen '
            'abstimmen (sits_on_panel), sonst 403. Ausdrueckliche '
            'Einzelbenennung schlaegt die Basisrolle.',
        'delegations_view':
            'Eigene Vertretung: Wer in einer Freigabekette sitzt, muss sich '
            'vertreten lassen koennen - unabhaengig von der Basisrolle. Fuer '
            'FREMDE Vertretungen prueft die View ohnehin auf HR-Admin.',
        'analytics_ask':
            'POST ist hier eine Frage an die Auswertung, keine Aenderung an '
            'Daten - lesen im Sinne dieser Regel.',
    }

    #: Views, die zwar POST entgegennehmen, aber ohnehin einer strengeren
    #: Rolle unterliegen - `recruiter_required`/`hr_admin_required` schliessen
    #: den Viewer bereits aus.
    STRENGERE_DECORATOR = {'recruiter_required', 'hr_admin_required'}

    def _views_mit_dekoratoren(self):
        wurzel = pathlib.Path(__file__).resolve().parent.parent / "views"
        dateien = sorted(wurzel.glob("*.py"))
        self.assertGreaterEqual(
            len(dateien), 5,
            "Der Scan findet fast keine View-Dateien - er prueft ins Leere.")
        for pfad in dateien:
            quelle = pfad.read_text(encoding="utf-8")
            baum = ast.parse(quelle)
            for knoten in ast.walk(baum):
                if not isinstance(knoten, ast.FunctionDef):
                    continue
                namen = {d.id for d in knoten.decorator_list
                         if isinstance(d, ast.Name)}
                if not namen:
                    continue
                rumpf = ast.get_source_segment(quelle, knoten) or ""
                yield knoten.name, namen, rumpf

    def test_every_writing_staff_view_blocks_the_viewer(self):
        offen = []
        gesehen = 0
        for name, dekoratoren, rumpf in self._views_mit_dekoratoren():
            if 'any_staff_required' not in dekoratoren:
                continue
            if dekoratoren & self.STRENGERE_DECORATOR:
                continue
            schreibt = ('request.POST' in rumpf
                        or 'method == "POST"' in rumpf
                        or "method == 'POST'" in rumpf)
            if not schreibt:
                continue
            gesehen += 1
            if 'denies_viewer_writes' in dekoratoren:
                continue
            if name in self.AUSNAHMEN:
                continue
            offen.append(name)
        self.assertGreaterEqual(
            gesehen, 5,
            "Der Scan findet kaum schreibende Staff-Views - vermutlich greift "
            "die Erkennung nicht mehr, und der Waechter waere ein Nichtstuer.")
        self.assertEqual(
            offen, [],
            "Interne View veraendert per POST etwas, sperrt aber den Viewer "
            "nicht aus. Bitte @denies_viewer_writes ergaenzen ODER mit "
            "Begruendung in AUSNAHMEN eintragen: " + ", ".join(offen))

    def test_the_exception_list_has_no_dead_entries(self):
        """Eine Begruendung fuer eine View, die es nicht mehr gibt, ist eine
        stehen gebliebene Erlaubnis fuer den naechsten gleichnamigen Fall."""
        vorhanden = {name for name, _, _ in self._views_mit_dekoratoren()}
        tot = sorted(set(self.AUSNAHMEN) - vorhanden)
        self.assertEqual(tot, [], f"Begruendung ohne zugehoerige View: {tot}")

    def test_the_scan_would_notice_a_new_gap(self):
        """Funktionsprobe: Erkennt der Scan eine kuenstlich geoeffnete Luecke?

        Ohne diesen Nachweis koennte die Erkennung stillschweigend kaputtgehen
        (z.B. weil ein Decorator umbenannt wurde) und der Waechter waere ab
        dann gruen, ohne etwas zu pruefen."""
        quelle = ("@any_staff_required\n"
                  "def neue_seite(request):\n"
                  "    if request.method == 'POST':\n"
                  "        pass\n")
        baum = ast.parse(quelle)
        funktion = baum.body[0]
        namen = {d.id for d in funktion.decorator_list if isinstance(d, ast.Name)}
        self.assertIn('any_staff_required', namen)
        self.assertNotIn('denies_viewer_writes', namen)
        self.assertIn('request.method', ast.get_source_segment(quelle, funktion))
