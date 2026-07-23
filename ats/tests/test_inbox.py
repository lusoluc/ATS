"""Sammel-Postfach: offene Bewerber-Fragen nach Anliegen gebuendelt.

Deckt ab: nur Bewerbungen mit LETZTER Nachricht INBOUND erscheinen,
Buendelung nach Anliegen, zusammengesetzte Nachricht -> Sonstiges, BOLA
(fremder Standort nicht sichtbar), leerer Zustand.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import Message
from .factories import make_application, make_job, make_world
from .utils import make_user


def _inbound(app, text, minutes_ago=0):
    m = Message.objects.create(application=app, direction='INBOUND', content=text)
    if minutes_ago:
        Message.objects.filter(id=m.id).update(
            createdAt=timezone.now() - timezone.timedelta(minutes=minutes_ago))
    return m


class InboxViewTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflege Station 1")
        self.rec = make_user("ib-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:inbox')

    def test_empty_when_no_open_questions(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Keine offenen Fragen")

    def test_groups_questions_by_intent(self):
        a1 = make_application(self.job, first_name="Anna", last_name="Berg")
        a2 = make_application(self.job, first_name="Ben", last_name="Krause")
        _inbound(a1, "Bis wann bekomme ich eine Rückmeldung?")
        _inbound(a2, "Sind meine Unterlagen vollständig angekommen?")
        r = self.client.get(self.url)
        self.assertContains(r, "Stand des Verfahrens")
        self.assertContains(r, "Unterlagen")
        self.assertContains(r, "Anna Berg")
        self.assertContains(r, "Ben Krause")

    def test_answered_thread_not_shown(self):
        """Letzte Nachricht OUTBOUND = beantwortet -> nicht im Postfach."""
        a = make_application(self.job, first_name="Cara", last_name="Doll")
        _inbound(a, "Wie ist der Stand?", minutes_ago=10)
        Message.objects.create(application=a, direction='OUTBOUND',
                               content="Wir prüfen gerade.")
        r = self.client.get(self.url)
        self.assertNotContains(r, "Cara Doll")

    def test_compound_message_lands_in_other(self):
        a = make_application(self.job, first_name="Dana", last_name="Erle")
        _inbound(a, "Bis wann höre ich von Ihnen? Außerdem: gibt es eine "
                    "Betriebswohnung?")
        r = self.client.get(self.url)
        self.assertContains(r, "Sonstiges / individuelle Prüfung")
        self.assertContains(r, "Dana Erle")

    def test_bola_foreign_location_hidden(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        fa = make_application(foreign_job, first_name="Zoe", last_name="Fremd")
        _inbound(fa, "Wie ist der Stand meiner Bewerbung?")
        mine = make_application(self.job, first_name="Mia", last_name="Meins")
        _inbound(mine, "Wie ist der Stand meiner Bewerbung?")
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(self.url)
        self.assertContains(r, "Mia Meins")
        self.assertNotContains(r, "Zoe Fremd")
