"""Wiederkehrende Jobs: laufen sie, und sagt das Produkt die Wahrheit darüber?

WAS SCHIEFLIEF: `OPERATIONS.md` schlug für neun Kommandos einen Cron-Eintrag
vor. Der ausgelieferte `docker-compose.yml` enthielt **keinen Zeitplan** — wer
der Installationsanleitung folgt und `docker compose up -d` fährt, bekam
`db`, `web`, KI und KI-Worker, aber keinen einzigen dieser Jobs.

Gleichzeitig sagte die Seite „Datenaufbewahrung" zu HR-Admins, Bewerbungen
würden „nach Ablauf der Frist automatisch anonymisiert
(DSGVO-Datenminimierung)". Ein Satz, den die Auslieferung nicht einlöste — bei
einer Pflicht aus Art. 5 Abs. 1 lit. e DSGVO, für die die Leitung geradesteht.
"""
import datetime
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..jobs import (
    JOBS,
    JobSpec,
    is_due,
    job_overview,
    last_run,
    open_problems,
    record_job_run,
    run_job,
)
from .utils import make_user


class DueLogicTestCase(TestCase):
    def setUp(self):
        self.spec = JobSpec("data_retention", "Fristen", 2, 15)

    def test_a_job_that_never_ran_is_due(self):
        self.assertTrue(is_due(self.spec))

    def test_a_job_that_ran_after_its_time_is_not_due_again_today(self):
        """Ein Lauf je Fälligkeit — nicht je Aufruf des Zeitplans."""
        heute = timezone.localtime().replace(hour=2, minute=30)
        with mock.patch('ats.jobs.timezone.now',
                        return_value=heute.astimezone(datetime.UTC)):
            record_job_run("data_retention", True)
            self.assertFalse(is_due(self.spec, heute))

    def test_a_job_whose_last_run_predates_the_due_time_is_due(self):
        gestern = timezone.now() - datetime.timedelta(days=2)
        with mock.patch('ats.jobs.timezone.now', return_value=gestern):
            record_job_run("data_retention", True)
        self.assertTrue(is_due(self.spec))


class RunRecordingTestCase(TestCase):
    def test_a_successful_run_is_recorded(self):
        spec = JobSpec("verify_audit", "Audit", 2, 30)
        self.assertTrue(run_job(spec))
        eintrag = last_run("verify_audit")
        self.assertIsNotNone(eintrag)
        self.assertTrue(eintrag["ok"])

    def test_a_failing_job_is_recorded_and_does_not_stop_the_schedule(self):
        """Sonst haette ein kaputter Wochenbericht die Fristen mit lahmgelegt."""
        spec = JobSpec("data_retention", "Fristen", 2, 15)
        with mock.patch('ats.jobs.management.call_command',
                        side_effect=RuntimeError("kaputt")):
            self.assertFalse(run_job(spec))
        eintrag = last_run("data_retention")
        self.assertFalse(eintrag["ok"])
        self.assertIn("kaputt", eintrag["detail"])

    def test_overdue_jobs_are_listed(self):
        offen = {z["name"] for z in open_problems()}
        self.assertIn("data_retention", offen,
                      "Ein nie gelaufener Pflicht-Job muss als offen gelten.")
        run_job(JobSpec("data_retention", "Fristen", 2, 15))
        self.assertNotIn("data_retention",
                         {z["name"] for z in open_problems()})


class RetentionPageIsHonestTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("jobs-admin", role="HR-Admin"))

    def test_the_page_says_when_nothing_was_ever_anonymised(self):
        resp = self.client.get(reverse('ats:retention'))
        self.assertContains(resp, "noch nie anonymisiert")
        self.assertNotContains(resp, "automatisch anonymisiert",
                               msg_prefix="Die Seite darf nicht behaupten, was "
                                          "niemand ausfuehrt")

    def test_after_a_run_the_page_shows_it(self):
        record_job_run("data_retention", True)
        resp = self.client.get(reverse('ats:retention'))
        self.assertContains(resp, "Zuletzt anonymisiert")

    def test_the_hub_names_overdue_jobs(self):
        resp = self.client.get(reverse('ats:settings_hub'))
        self.assertContains(resp, "überfällig")

    def test_the_job_page_lists_every_scheduled_job(self):
        resp = self.client.get(reverse('ats:scheduled_jobs'))
        for spec in JOBS:
            self.assertContains(resp, spec.name)


class AccessTestCase(TestCase):
    def test_only_hr_admin_sees_the_job_page(self):
        self.client.force_login(make_user("jobs-viewer", role="Viewer"))
        resp = self.client.get(reverse('ats:scheduled_jobs'))
        self.assertIn(resp.status_code, (302, 403))


class GuardrailScheduleIsRealTestCase(TestCase):
    """Ein Zeitplan taugt nur, wenn seine Jobs existieren und jemand ihn ausführt."""

    def test_every_scheduled_job_exists_as_a_command(self):
        befehle = {p.stem for p in
                   (Path(settings.BASE_DIR) / "ats" / "management" / "commands")
                   .glob("*.py")}
        # Selbstnachweis: Es gibt ueber ein Dutzend Kommandos. Sieht der Scan
        # fast keine, zeigt der Pfad ins Leere - und die Pruefung darunter
        # waere gruen und wertlos.
        self.assertGreaterEqual(len(befehle), 10,
                                f"Nur {len(befehle)} Kommandos gefunden")
        fehlend = [s.name for s in JOBS if s.name not in befehle]
        self.assertEqual(fehlend, [],
                         f"Zeitplan-Eintrag ohne Kommando: {fehlend}")

    def test_the_delivered_stack_actually_runs_the_schedule(self):
        """Der Kern des Fundes: Es gab neun Jobs und keinen, der sie startet.

        Ohne diesen Dienst ist die Zusage der Oberfläche („wird anonymisiert")
        wieder ungedeckt — deshalb hängt sie hier an einem Test, nicht an
        einem Absatz in der Betriebsdoku.
        """
        compose = (Path(settings.BASE_DIR) / "docker-compose.yml").read_text(
            encoding="utf-8")
        self.assertIn("scheduler:", compose,
                      "docker-compose.yml enthaelt keinen Zeitplan-Dienst")
        self.assertIn('"scheduler"', compose,
                      "Der Dienst ruft das scheduler-Kommando nicht auf")
        block = compose.split("scheduler:", 1)[1].split("\n\n", 1)[0]
        self.assertNotIn("profiles:", block,
                         "Ein Zeitplan, den man erst einschalten muss, ist "
                         "derselbe Fehler noch einmal.")

    def test_the_overview_is_complete(self):
        self.assertEqual(len(job_overview()), len(JOBS))
