"""Auf einer Seite dürfen nicht die Hälfte der Zahlen den Bereich meinen und die andere Hälfte alles.

Die Auswertungs-Seite heißt im Code „BOLA-gescopt", und ihre Funnel-Zahlen
waren es auch. Zwei Blöcke nicht: die Kampagnen-/Landingpage-Quoten und
„Einstellungen gesamt". Eine Standortleitung las damit ihre eigenen
Bewerbungszahlen neben Kennzahlen der ganzen Organisation — ohne dass die
Seite den Unterschied markiert hätte.

Das ist schlimmer als eine durchgehende Entscheidung in die eine oder andere
Richtung: Wer eine Quote liest, muss wissen, worauf sie sich bezieht.
"""
import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import (
    Applicant,
    Application,
    Facility,
    JobFamily,
    JobPosting,
    LandingPage,
    Location,
    Organization,
    WorkflowState,
)
from .utils import make_user


class ScopedAnalyticsTestCase(TestCase):
    """Eine Recruiterin sieht Hamburg, nicht das Haus in München."""

    def setUp(self):
        org = Organization.objects.create(name="Träger")
        self.hh = Location.objects.create(name="Hamburg")
        self.muc = Location.objects.create(name="München")
        self.fac_hh = Facility.objects.create(name="Klinik HH", organization=org)
        self.fac_muc = Facility.objects.create(name="Klinik M", organization=org)
        fam = JobFamily.objects.create(name="Pflege")
        wf = WorkflowState.objects.create(name="published")

        def stelle(titel, fac, loc):
            return JobPosting.objects.create(
                title=titel, organization=org, facility=fac, location=loc,
                jobFamily=fam, workflowState=wf)

        self.job_hh = stelle("Pflegefachkraft HH", self.fac_hh, self.hh)
        self.job_muc = stelle("Pflegefachkraft M", self.fac_muc, self.muc)

        # Kampagne, ueber die BEIDE Haeuser Bewerbungen bekommen.
        self.lp = LandingPage.objects.create(name="Herbstkampagne",
                                             slug="herbst", active=True)
        vor = timezone.now() - datetime.timedelta(days=3)
        LandingPage.objects.filter(id=self.lp.id).update(createdAt=vor)
        self.lp.refresh_from_db()

        def bewerbung(job, name, status, quelle):
            person = Applicant.objects.create(
                firstName=name, lastName="X",
                email=f"{name.lower()}@example.invalid")
            app = Application.objects.create(applicant=person, jobPosting=job,
                                             status=status, source=quelle)
            if status == 'HIRED':
                Application.objects.filter(id=app.id).update(
                    hiredAt=timezone.now())
            return app

        bewerbung(self.job_hh, "Hamburgerin", "HIRED", "HERBST")
        bewerbung(self.job_muc, "Muenchnerin", "HIRED", "HERBST")
        bewerbung(self.job_muc, "Zweite", "INVITED", "HERBST")

        from ..models import UserScope
        self.rec = make_user("rec-hamburg", role="Recruiter")
        scope = UserScope.objects.create(user=self.rec, full_access=False)
        scope.facilities.add(self.fac_hh)

    def test_campaign_numbers_count_only_my_area(self):
        self.client.force_login(self.rec)
        resp = self.client.get(reverse('ats:analytics'))
        zeilen = {z['name']: z for z in resp.context['landing_rows']}
        self.assertIn("Herbstkampagne", zeilen)
        self.assertEqual(zeilen["Herbstkampagne"]['apps'], 1,
                         "Die Kampagnen-Quote zaehlte Bewerbungen aus fremden "
                         "Einrichtungen mit.")
        self.assertEqual(zeilen["Herbstkampagne"]['hired'], 1)

    def test_total_hires_counts_only_my_area(self):
        self.client.force_login(self.rec)
        resp = self.client.get(reverse('ats:analytics'))
        self.assertEqual(resp.context['hiring_summary']['count'], 1,
                         "Einstellungen gesamt meinte die ganze Organisation.")

    def test_full_access_still_sees_everything(self):
        """Die Einschränkung darf nur greifen, wo sie soll."""
        admin = make_user("analytics-admin", role="HR-Admin")
        self.client.force_login(admin)
        resp = self.client.get(reverse('ats:analytics'))
        zeilen = {z['name']: z for z in resp.context['landing_rows']}
        self.assertEqual(zeilen["Herbstkampagne"]['apps'], 3)
        self.assertEqual(resp.context['hiring_summary']['count'], 2)


class GuardrailAnalyticsIsScopedTestCase(TestCase):
    """Wo die Seite Scoping zusagt, muss jede Zahl daraus stammen.

    `analytics_views.py` trägt im Kopf „BOLA-gescopt". Zwei Blöcke griffen
    trotzdem direkt auf `Application.objects` zu — mitten zwischen gescopten
    Zahlen und direkt neben einem Block, der das Scoping ausdrücklich
    kommentiert. Ein Versehen also, kein Entwurf.

    Der Wächter arbeitet über den Syntaxbaum: Jeder Zugriff auf
    `Application.objects` in diesem Modul muss Argument von
    `scope_applications(...)` sein.
    """

    def test_no_unscoped_application_query_in_the_analytics_module(self):
        import ast
        import os

        pfad = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "views", "analytics_views.py")
        with open(pfad, encoding="utf-8") as fh:
            baum = ast.parse(fh.read())

        # Alle Knoten einsammeln, die INNERHALB eines scope_applications-Aufrufs
        # stehen - die sind in Ordnung.
        erlaubt = set()
        for knoten in ast.walk(baum):
            if (isinstance(knoten, ast.Call)
                    and getattr(knoten.func, "id", None) == "scope_applications"):
                for kind in ast.walk(knoten):
                    erlaubt.add(id(kind))

        offen = []
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.Attribute) or knoten.attr != "objects":
                continue
            if getattr(knoten.value, "id", None) != "Application":
                continue
            if id(knoten) not in erlaubt:
                offen.append(knoten.lineno)

        self.assertEqual(
            offen, [],
            "Ungescopter Zugriff auf Application.objects in analytics_views.py "
            f"(Zeilen {offen}). Auf dieser Seite muss jede Zahl aus "
            "`scope_applications` stammen - sonst stehen Bereichs- und "
            "Gesamtzahlen ununterscheidbar nebeneinander.")
