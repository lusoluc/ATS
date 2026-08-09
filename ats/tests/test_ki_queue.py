"""Die KI-Queue muss Ausfälle überstehen — nicht nur den Normalfall können.

Dieselbe Frage wie an die Zustell-Jobs: Was passiert, wenn der Worker stirbt,
die KI nicht erreichbar ist, ein Task endgültig scheitert? Vorher: Der Task
blieb ewig RUNNING, die Versuche verbrannten in Sekunden, FAILED war eine
unsichtbare Endstation, und der Platzhalter „KI-Analyse läuft im
Hintergrund …" log für immer.
"""
import datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import AiTask, Applicant, Application, SystemSetting
from ..queue import (
    FAILURE_RATIONALE,
    PLACEHOLDER_RATIONALE,
    enqueue,
    reclaim_stale,
    requeue_failed,
    run_pending,
    trim_finished,
)
from .factories import make_job, make_world
from .utils import make_user


def _app_mit_platzhalter():
    world = make_world()
    job = make_job(world, title="Pflegefachkraft")
    person = Applicant.objects.create(firstName="Queue", lastName="T",
                                      email="queue@example.invalid")
    return Application.objects.create(
        applicant=person, jobPosting=job, status="NEW",
        coverLetterTxt="Ich pflege gern.",
        aiRationale=PLACEHOLDER_RATIONALE)


class WorkerAbsturzTestCase(TestCase):
    """Ein Task, dessen Worker starb, darf nicht für immer RUNNING bleiben."""

    def test_a_stale_running_task_is_reclaimed_and_finished(self):
        app = _app_mit_platzhalter()
        task = enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})
        task.status = "RUNNING"
        task.attempts = 1
        task.startedAt = timezone.now() - datetime.timedelta(minutes=45)
        task.save()
        with patch("ats.views.evaluate_with_local_gemma",
                   return_value=("B", "Passt gut.")):
            verarbeitet = run_pending()
        self.assertEqual(verarbeitet, 1, "Der verwaiste Task wurde nicht "
                                         "wieder aufgenommen.")
        task.refresh_from_db()
        self.assertEqual(task.status, "DONE")
        app.refresh_from_db()
        self.assertEqual(app.aiScore, "B")

    def test_a_fresh_running_task_is_left_alone(self):
        """Ein Task, der erst seit Minuten läuft, ist Arbeit — kein Waisenkind."""
        app = _app_mit_platzhalter()
        task = enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})
        task.status = "RUNNING"
        task.attempts = 1
        task.startedAt = timezone.now() - datetime.timedelta(minutes=5)
        task.save()
        self.assertEqual(reclaim_stale(), 0)
        task.refresh_from_db()
        self.assertEqual(task.status, "RUNNING")

    def test_a_stale_task_without_remaining_attempts_fails_honestly(self):
        app = _app_mit_platzhalter()
        task = enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})
        task.status = "RUNNING"
        task.attempts = 3
        task.startedAt = timezone.now() - datetime.timedelta(minutes=45)
        task.save()
        reclaim_stale()
        task.refresh_from_db()
        self.assertEqual(task.status, "FAILED")
        self.assertIn("Worker-Abbruch", task.error)
        app.refresh_from_db()
        self.assertEqual(app.aiRationale, FAILURE_RATIONALE,
                         "Der Platzhalter muss auch bei einem verwaisten "
                         "Task ohne Restversuche ersetzt werden.")


class EhrlicherPlatzhalterTestCase(TestCase):
    """„KI-Analyse läuft im Hintergrund …" darf keine ewige Zusage sein."""

    def _endgueltig_scheitern(self, app):
        task = enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})
        task.attempts = 2                   # naechster Versuch ist der letzte
        task.save(update_fields=["attempts"])
        with patch("ats.views.evaluate_with_local_gemma",
                   side_effect=OSError("KI nicht erreichbar")):
            run_pending()
        task.refresh_from_db()
        self.assertEqual(task.status, "FAILED")
        return task

    def test_final_failure_replaces_the_placeholder(self):
        app = _app_mit_platzhalter()
        self._endgueltig_scheitern(app)
        app.refresh_from_db()
        self.assertEqual(app.aiRationale, FAILURE_RATIONALE)
        self.assertFalse(app.aiScore, "Ein erfundener Score waere schlimmer "
                                      "als keiner.")

    def test_a_hand_written_rationale_is_not_overwritten(self):
        app = _app_mit_platzhalter()
        app.aiRationale = "Von Hand gesichtet: passt."
        app.save(update_fields=["aiRationale"])
        self._endgueltig_scheitern(app)
        app.refresh_from_db()
        self.assertEqual(app.aiRationale, "Von Hand gesichtet: passt.")

    def test_the_placeholder_constant_is_what_the_form_writes(self):
        """public.py schreibt DIESELBE Konstante, die der Worker ersetzt —
        ein abweichendes Literal liesse die Zusage ewig stehen."""
        import inspect

        from ..views import public
        quelle = inspect.getsource(public)
        self.assertIn("PLACEHOLDER_RATIONALE", quelle)
        self.assertNotIn("'KI-Analyse läuft", quelle,
                         "Platzhalter-Literal statt der Konstante aus "
                         "ats/queue.py.")


class RequeueTestCase(TestCase):
    """FAILED ist keine Endstation mehr: Jobs-Seite zeigt es, ein Knopf heilt es."""

    def setUp(self):
        self.admin = make_user("queueadmin", role="HR-Admin")
        self.client.force_login(self.admin)

    def _failed_task(self):
        task = enqueue("SCORE_APPLICATION",
                       {"application_id": "00000000-0000-0000-0000-000000000000"})
        task.status = "FAILED"
        task.attempts = 3
        task.error = "KI nicht erreichbar"
        task.finishedAt = timezone.now()
        task.save()
        return task

    def test_requeue_gives_full_attempts_again(self):
        task = self._failed_task()
        self.assertEqual(requeue_failed(), 1)
        task.refresh_from_db()
        self.assertEqual(task.status, "PENDING")
        self.assertEqual(task.attempts, 0)
        self.assertIsNone(task.nextAttemptAt)

    def test_the_jobs_page_shows_the_queue_and_the_button(self):
        self._failed_task()
        r = self.client.get(reverse('ats:scheduled_jobs'))
        self.assertContains(r, "KI-Warteschlange")
        self.assertContains(r, "Fehlgeschlagene erneut einreihen")
        self.assertContains(r, "KI nicht erreichbar")

    def test_the_requeue_endpoint_requeues_and_writes_audit(self):
        from ..models import AuditLog
        self._failed_task()
        r = self.client.post(reverse('ats:requeue_failed_ai_tasks'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(AiTask.objects.filter(status="PENDING").count(), 1)
        self.assertTrue(AuditLog.objects.filter(
            action="AI_QUEUE_REQUEUED").exists())

    def test_without_any_queue_activity_the_block_stays_away(self):
        """Context-Aware: Installationen ohne KI sehen keinen Queue-Block."""
        r = self.client.get(reverse('ats:scheduled_jobs'))
        self.assertNotContains(r, "KI-Warteschlange")

    def test_with_ai_async_on_the_block_appears_even_when_empty(self):
        SystemSetting.objects.create(key="AI_ASYNC", value="1")
        r = self.client.get(reverse('ats:scheduled_jobs'))
        self.assertContains(r, "KI-Warteschlange")

    def test_an_old_pending_task_raises_the_alarm(self):
        """Wartet ein Task laenger, als der Worker-Takt erklaeren kann,
        laeuft kein Worker - das muss die Seite sagen, nicht verstecken."""
        task = enqueue("SCORE_APPLICATION", {"application_id": "x"})
        AiTask.objects.filter(id=task.id).update(
            createdAt=timezone.now() - datetime.timedelta(hours=2))
        r = self.client.get(reverse('ats:scheduled_jobs'))
        self.assertContains(r, "bei laufendem Worker unmöglich")


class TrimTestCase(TestCase):
    """Erledigte Tasks sind Historie, keine Ewigkeitslast."""

    def _task(self, status, tage):
        task = enqueue("SCORE_APPLICATION", {"application_id": "x"})
        task.status = status
        task.finishedAt = timezone.now() - datetime.timedelta(days=tage)
        task.save()
        return task

    def test_old_done_and_failed_rows_go_young_ones_stay(self):
        self._task("DONE", 31)
        junge_done = self._task("DONE", 5)
        self._task("FAILED", 91)
        junge_failed = self._task("FAILED", 60)
        done, failed = trim_finished()
        self.assertEqual((done, failed), (1, 1))
        uebrig = set(AiTask.objects.values_list("id", flat=True))
        self.assertEqual(uebrig, {junge_done.id, junge_failed.id})

    def test_data_retention_runs_the_trim(self):
        from django.core import management
        self._task("DONE", 31)
        management.call_command("data_retention")
        self.assertEqual(AiTask.objects.count(), 0)

    def test_the_dry_run_deletes_nothing(self):
        from django.core import management
        self._task("DONE", 31)
        management.call_command("data_retention", "--dry-run")
        self.assertEqual(AiTask.objects.count(), 1)


class AiAsyncSchalterTestCase(TestCase):
    """AI_ASYNC ist eine Produktentscheidung - sie muss im Produkt treffbar sein."""

    def setUp(self):
        self.admin = make_user("kiadmin", role="HR-Admin")
        self.client.force_login(self.admin)

    def test_the_switch_is_saved_and_cleared(self):
        self.client.post(reverse('ats:save_ai_settings'),
                         data={"AI_ASYNC": "1"})
        self.assertEqual(SystemSetting.objects.get(key="AI_ASYNC").value, "1")
        self.client.post(reverse('ats:save_ai_settings'), data={})
        self.assertEqual(SystemSetting.objects.get(key="AI_ASYNC").value, "0")

    def test_the_ki_page_shows_the_switch(self):
        r = self.client.get(reverse('ats:ki_page'))
        self.assertContains(r, 'name="AI_ASYNC"')
