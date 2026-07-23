"""Stufe 2+3: Antwort-Bausteine je Anliegen + Auto-Vorschlag.

Deckt ab: Speichern legt einen REPLY_<Intent>-Baustein an, OTHER/leer wird
abgelehnt, und der juengste gespeicherte Baustein wird zum Auto-Vorschlag im
Postfach (statt der eingebauten Default-Vorlage).
"""
from django.test import TestCase
from django.urls import reverse

from ..models import Message, TextSnippet
from .factories import make_application, make_job, make_world
from .utils import make_user


class SaveReplySnippetTestCase(TestCase):
    def setUp(self):
        self.rec = make_user("rs-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:save_reply_snippet')

    def test_saves_snippet_for_intent(self):
        r = self.client.post(self.url, data={
            'intent': 'STATUS', 'content': 'Danke für Ihre Geduld [[Vorname]].'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        self.assertEqual(
            TextSnippet.objects.filter(category='REPLY_STATUS').count(), 1)

    def test_rejects_other(self):
        r = self.client.post(self.url, data={
            'intent': 'OTHER', 'content': 'irgendwas'})
        self.assertEqual(r.status_code, 400)

    def test_rejects_empty(self):
        r = self.client.post(self.url, data={'intent': 'STATUS', 'content': ' '})
        self.assertEqual(r.status_code, 400)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class AutoSuggestTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflege Station 1")
        self.rec = make_user("as-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.app = make_application(self.job, first_name="Anna", last_name="Berg",
                                    status="IN_REVIEW")
        Message.objects.create(application=self.app, direction='INBOUND',
                               content="Wie ist der Stand?")

    def test_default_template_when_no_snippet(self):
        r = self.client.get(reverse('ats:inbox'))
        # Default-STATUS-Vorlage enthält diese Wendung.
        self.assertContains(r, "sorgfaeltig geprueft")

    def test_saved_snippet_becomes_suggestion(self):
        TextSnippet.objects.create(
            category='REPLY_STATUS',
            content='MEINE HAUSVORLAGE fuer [[Vorname]].')
        r = self.client.get(reverse('ats:inbox'))
        self.assertContains(r, "MEINE HAUSVORLAGE")
        # Der Default weicht dem gespeicherten Baustein.
        self.assertNotContains(r, "sorgfaeltig geprueft")
