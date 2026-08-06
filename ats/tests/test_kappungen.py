"""Listen, die still abschneiden — die Fehlerklasse, nicht der Einzelfall.

An einem Tag zweimal gefunden: `logs[:500]` im Audit-Log und `assets[:200]` in
der Mediathek. Beide Male stand keine Zahl auf der Seite, beide Male fehlte
etwas, das jemand gesucht hätte. Der Durchgang danach fand vier weitere
Stellen, an denen eine feste Zahl entscheidet, was jemand zu sehen bekommt:

* die Nachweise einer Bewerbung im Steckbrief (20) — ausgerechnet dort, wo der
  Kommentar daneben erklärt, dass sie vorher gar niemand zu Gesicht bekam,
* der eigene Schriftwechsel im Bewerberportal (20),
* Jobfamilien in der Messstrecke (40) und Textbausteine im Antwort-Modal (50),
  beides Stammdaten.

Alle vier sind aufgehoben. Wo ein Deckel bleibt, weil die Menge über Jahre
wächst — die eigenen entschiedenen Personalbedarfe — nennt die Seite ihn.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import (
    Applicant,
    ApplicantToken,
    Application,
    ApplicationDocument,
    Message,
)
from .factories import make_job, make_world
from .utils import make_user


class DocumentsAreCompleteTestCase(TestCase):
    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        applicant = Applicant.objects.create(firstName="Mira", lastName="S",
                                             email="mira@example.invalid")
        self.app = Application.objects.create(applicant=applicant, jobPosting=job,
                                              status="IN_REVIEW")
        ApplicationDocument.objects.bulk_create([
            ApplicationDocument(application=self.app, name=f"Nachweis {i:02d}",
                                file=f"application_docs/n{i}.pdf")
            for i in range(25)])
        self.client.force_login(make_user("kappung-admin", role="HR-Admin"))

    def test_all_25_documents_reach_the_profile_card(self):
        resp = self.client.get(reverse('ats:application_summary', args=[self.app.id]))
        self.assertEqual(resp.status_code, 200)
        namen = [d['name'] for d in resp.json()['documents']]
        self.assertEqual(len(namen), 25)
        self.assertIn("Nachweis 24", namen, "Der 25. Nachweis fehlte – "
                                            "genau die stille Kappung von vorher.")


class PortalMessagesAreCompleteTestCase(TestCase):
    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        self.applicant = Applicant.objects.create(firstName="Jonas", lastName="B",
                                                  email="jonas@example.invalid")
        app = Application.objects.create(applicant=self.applicant, jobPosting=job,
                                         status="IN_REVIEW")
        Message.objects.bulk_create([
            Message(application=app, direction="OUTBOUND", content=f"Nachricht {i:02d}")
            for i in range(25)])
        self.token = ApplicantToken.objects.create(
            applicant=self.applicant, token="kappung-probe-token",
            expiresAt=timezone.now() + timezone.timedelta(days=7))

    def test_the_oldest_message_is_still_there(self):
        """Es ist der eigene Schriftwechsel – die ältesten wegzulassen hiesse,
        jemandem den Anfang der eigenen Unterhaltung vorzuenthalten."""
        resp = self.client.get(reverse('ats:candidate_portal',
                                       args=[self.token.token]))
        self.assertEqual(resp.status_code, 200)
        inhalt = resp.content.decode()
        self.assertIn("Nachricht 00", inhalt)
        self.assertIn("Nachricht 24", inhalt)


class MasterDataIsNotCappedTestCase(TestCase):
    """Stammdaten, die jemand anlegt und dann nicht wiederfindet, sind
    schlimmer als gar keine: Man sucht den Fehler bei sich."""

    def setUp(self):
        self.client.force_login(make_user("kappung-recruiter", role="Recruiter"))

    def test_all_text_snippets_are_offered(self):
        from ..models import TextSnippet
        TextSnippet.objects.bulk_create([
            TextSnippet(category="INTRO", content=f"Baustein {i:02d}")
            for i in range(55)])
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(len(list(resp.context['text_snippets'])), 55)
