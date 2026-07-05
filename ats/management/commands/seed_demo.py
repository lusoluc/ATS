"""P0.4: Demo-Instanz – realistische, fiktive Daten fuer Discovery-Gespraeche.

Betrieb (siehe INSTALL.md):
  DEMO_MODE=1 in der Umgebung setzen, dann
    python manage.py seed_demo            # fuellt eine leere Demo einmalig
    python manage.py seed_demo --reset    # naechtlicher Cron: wipe + neu

Sicherheit: --reset loescht Daten und ist deshalb NUR mit DEMO_MODE=1 erlaubt –
eine Produktions-DB kann damit nicht versehentlich geleert werden.
Alle Personen/Einrichtungen sind frei erfunden.
"""
import json
import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ats.models import (Applicant, Application, ApprovalTicket, ApprovalStep,
                        AuditLog, Benefit, ContactPerson, Department, Facility,
                        FacilityContactPerson, FacilityProfile, JobAlertSubscription,
                        JobFamily, JobPosting, JobTemplate, Location, Organization,
                        TextSnippet, UserScope, WorkflowState, RoleDelegation, StaffingRequest, TalentPoolSubscription, TalentPoolContact, EmailTemplate, ApplicationVote)

MARKER_ORG = "Elbtal Gesundheitsgruppe (DEMO)"
rng = random.Random(2026)  # deterministisch: jede Demo sieht gleich aus


class Command(BaseCommand):
    help = "Befuellt die Demo-Instanz mit fiktiven Daten (--reset: wipe + neu, nur mit DEMO_MODE=1)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Vorher ALLE Bewegungsdaten loeschen (nur DEMO_MODE=1).")

    # ------------------------------------------------------------------ wipe
    def _wipe(self):
        # Reihenfolge beachtet FK-Abhaengigkeiten; die Governance-Objekte
        # (Gremium-Stimmen, Vertretungen, Bedarf, Pool) gehoeren MIT zum
        # Demo-Reset – sonst kollidieren unique-Felder beim Neuaufbau.
        from ats.models import (SourceChannel as _SC, LandingPage as _LP,
                                RequisitionRule as _RQ, RequisitionStep as _RS)
        for model in (_SC, _LP, _RS, _RQ,
                      ApplicationVote, RoleDelegation, StaffingRequest,
                      TalentPoolContact, TalentPoolSubscription,
                      Application, Applicant, ApprovalStep, ApprovalTicket,
                      JobAlertSubscription, JobPosting, TextSnippet, JobTemplate,
                      FacilityContactPerson, ContactPerson, FacilityProfile,
                      Department, Facility, JobFamily, Location, Benefit,
                      AuditLog, Organization):
            model.objects.all().delete()

    # ------------------------------------------------------------------ seed
    def handle(self, *args, **options):
        # Sicherheit: Dieser Befehl legt Demo-Staff-Accounts mit bekanntem
        # Passwort an. Er darf NUR auf einer Demo-Instanz laufen (DEMO_MODE=1),
        # damit auf Produktion niemals Backdoor-Logins entstehen.
        if not getattr(settings, "DEMO_MODE", False):
            raise CommandError(
                "seed_demo* legt Demo-Konten mit bekanntem Passwort an "
                "und ist nur mit DEMO_MODE=1 erlaubt (Schutz vor "
                "Backdoor-Accounts auf Produktion).")
        if options["reset"]:
            if not getattr(settings, "DEMO_MODE", False):
                raise CommandError(
                    "--reset loescht Daten und ist nur mit DEMO_MODE=1 erlaubt "
                    "(Schutz vor versehentlichem Leeren einer Produktions-DB).")
            self._wipe()
        elif Organization.objects.filter(name=MARKER_ORG).exists():
            self.stdout.write("Demo-Daten existieren bereits – nichts zu tun "
                              "(Neuaufbau: --reset mit DEMO_MODE=1).")
            return

        now = timezone.now()
        org = Organization.objects.create(name=MARKER_ORG)

        # Standorte mit Koordinaten (Umkreis-Alerts demonstrierbar)
        hh = Location.objects.create(name="Hamburg-Altona", city="Hamburg",
                                     lat=53.5511, lng=9.9937)
        lg = Location.objects.create(name="Lüneburg", city="Lüneburg",
                                     lat=53.2464, lng=10.4115)
        be = Location.objects.create(name="Berlin-Pankow", city="Berlin",
                                     lat=52.5200, lng=13.4050)

        fac_klinik = Facility.objects.create(
            name="Klinik Elbblick", organization=org)
        fac_pflege = Facility.objects.create(
            name="Seniorenzentrum Ilmenaupark", organization=org,
            requiresApproval=True)  # Demo: Freigabe-Gate live zeigen
        FacilityProfile.objects.create(
            facility=fac_klinik, slug="klinik-elbblick",
            description=("Haus der Grund- und Regelversorgung mit 320 Betten. "
                         "Wir glauben, dass gute Pflege Zeit braucht – und "
                         "organisieren uns so, dass sie da ist."))

        fam_pflege = JobFamily.objects.create(name="Pflege")
        fam_verwaltung = JobFamily.objects.create(name="Verwaltung")
        fam_it = JobFamily.objects.create(name="IT & Technik")
        dep_station3 = Department.objects.create(name="Station 3 – Innere",
                                                 slug="station-3", facility=fac_klinik)
        dep_it = Department.objects.create(name="IT-Abteilung", slug="it",
                                           facility=fac_klinik)

        for name, icon in [("30 Tage Urlaub", "fa-umbrella-beach"),
                           ("Deutschlandticket", "fa-train"),
                           ("Betriebliche Altersvorsorge", "fa-piggy-bank"),
                           ("Verlässliche Dienstplanung", "fa-calendar-check")]:
            Benefit.objects.get_or_create(name=name, defaults={"icon": icon})

        cp_pw = ContactPerson.objects.create(
            firstName="Petra", lastName="Wolf", email="p.wolf@demo.example",
            phone="040 555 1234", globalJobTitle="Pflegedienstleitung",
            quote="Melden Sie sich gern direkt bei mir – auch ohne fertige Unterlagen.")
        cp_tk = ContactPerson.objects.create(
            firstName="Tobias", lastName="Klein", email="t.klein@demo.example",
            phone="04131 555 88", globalJobTitle="Recruiting")
        FacilityContactPerson.objects.create(facility=fac_klinik, contactPerson=cp_pw)
        FacilityContactPerson.objects.create(facility=fac_pflege, contactPerson=cp_tk)

        TextSnippet.objects.create(category="BENEFITS", content=(
            "Bei uns erwarten Sie 30 Tage Urlaub, das Deutschlandticket und eine "
            "verlässliche Dienstplanung mit echter Ausfallregelung."))
        TextSnippet.objects.create(category="INTRO", jobFamily=fam_pflege, content=(
            "Sie pflegen gern – wir kümmern uns um den Rest. Station 3 arbeitet im "
            "festen Bezugspflege-System mit stabilen Teams."))
        JobTemplate.objects.create(
            title="Pflegefachkraft (Vorlage)", version=1,
            content="Standardvorlage Pflegefachkraft – Aufgaben, Anforderungen, Benefits.")

        published, _ = WorkflowState.objects.get_or_create(
            name="published", defaults={"description": "Öffentlich sichtbar"})
        draft, _ = WorkflowState.objects.get_or_create(
            name="draft", defaults={"description": "Deaktiviert / Entwurf"})

        def job(title, fac, loc, fam, dep=None, cp=None, easy=None, screening=None,
                state=published, days_old=30):
            j = JobPosting.objects.create(
                title=title, organization=org, facility=fac, location=loc,
                jobFamily=fam, department=dep, contactPerson=cp,
                workflowState=state,
                description=(f"{title} in {loc.city}: unbefristet, faire Vergütung "
                             "nach Tarif, strukturierte Einarbeitung."),
                descriptionEasy=easy or "",
                screeningQuestionsJson=json.dumps(screening or []),
            )
            JobPosting.objects.filter(id=j.id).update(
                createdAt=now - timedelta(days=days_old))
            j.refresh_from_db()
            return j

        j1 = job("Pflegefachkraft Station 3 (m/w/d)", fac_klinik, hh, fam_pflege,
                 dep=dep_station3, cp=cp_pw, days_old=45,
                 easy=("Sie arbeiten als Pflege-Fachkraft. Sie helfen kranken "
                       "Menschen. Das Team hilft Ihnen. Sie bekommen gutes Geld."),
                 screening=[{"id": "exam", "question":
                             "Haben Sie ein Examen als Pflegefachkraft?",
                             "isMandatory": True, "expectedAnswer": "Ja"}])
        j2 = job("Pflegehilfskraft Nachtdienst (m/w/d)", fac_pflege, lg,
                 fam_pflege, cp=cp_tk, days_old=60)
        j3 = job("Medizinische Fachangestellte (m/w/d)", fac_klinik, hh,
                 fam_verwaltung, cp=cp_pw, days_old=25)
        j4 = job("IT-Systemadministrator (m/w/d)", fac_klinik, be, fam_it,
                 dep=dep_it, days_old=80)
        job("Empfang & Patientenaufnahme (m/w/d)", fac_klinik, hh,
            fam_verwaltung, days_old=10)
        # Anzeige im Freigabe-Gate (Approvals-Postfach demonstrierbar)
        j_gate = job("Stationsleitung Geriatrie (m/w/d)", fac_pflege, lg,
                     fam_pflege, state=draft, days_old=3)
        ticket = ApprovalTicket.objects.create(jobPosting=j_gate, status="PENDING")
        ApprovalStep.objects.create(approvalTicket=ticket, stepOrder=1,
                                    assignedRoleId="HR-Admin")

        # --- Bewerbungen: realistische Verteilung ueber 90 Tage ---------------
        first = ["Anna", "Mehmet", "Julia", "Piotr", "Fatima", "Lars", "Sofia",
                 "Jonas", "Elif", "Marta", "David", "Aylin", "Tom", "Ewa", "Nina"]
        last = ["Krüger", "Yilmaz", "Schneider", "Kowalski", "Haddad", "Petersen",
                "Ricci", "Brandt", "Demir", "Nowak", "Fischer", "Kaya", "Weber",
                "Lis", "Hoffmann"]
        jobs_weighted = [j1, j1, j1, j2, j2, j3, j3, j4]
        sources = ["DIRECT", "DIRECT", "STEPSTONE", "STEPSTONE", "BA", "IMPORT"]
        statuses = ["NEW", "NEW", "NEW", "IN_REVIEW", "IN_REVIEW",
                    "INVITED", "INVITED", "REJECTED"]
        # Historische KI-Scores (Scoring war in der fiktiven Vergangenheit aktiv;
        # Default der Demo bleibt AUS – neue Bewerbungen erhalten keinen Score)
        scores = ["A", "B", "B", "C", "C", "C", "D", None, None]

        for i in range(32):
            fn, ln = rng.choice(first), rng.choice(last)
            email = f"{fn}.{ln}{i}@bewerber-demo.example".lower()
            applicant = Applicant.objects.create(
                firstName=fn, lastName=ln, email=email,
                phone=f"01{rng.randint(50, 79)} {rng.randint(1000000, 9999999)}")
            target = rng.choice(jobs_weighted)
            status = rng.choice(statuses)
            days = rng.randint(1, 85)
            a = Application.objects.create(
                applicant=applicant, jobPosting=target, status=status,
                source=rng.choice(sources), aiScore=rng.choice(scores),
                consentTalentPool=rng.random() < 0.3,
                internalNotes="Demo-Datensatz (fiktiv)." if rng.random() < 0.2 else "")
            upd = days - rng.randint(0, min(days, 21)) if status != "NEW" else days
            Application.objects.filter(id=a.id).update(
                createdAt=now - timedelta(days=days),
                updatedAt=now - timedelta(days=max(upd, 0)))
        # Anomalie-Demo: drei bewusst liegengebliebene Erstsichtungen
        for a in Application.objects.filter(status="NEW")[:3]:
            Application.objects.filter(id=a.id).update(
                createdAt=now - timedelta(days=28))

        # Freie Timeslots (Kalender- & Selbstbuchungs-Demo): naechste 2 Wochen
        from ats.models import InterviewSlot
        kinds = ["PHONE", "VIDEO", "ON_SITE", "TRIAL_WORK", "VIDEO"]
        for i, day_offset in enumerate((2, 4, 7, 9, 11)):
            start = (now + timedelta(days=day_offset)).replace(
                hour=10, minute=0, second=0, microsecond=0)
            InterviewSlot.objects.create(jobPosting=j1, startTime=start, kind=kinds[i],
                                         endTime=start + timedelta(
                                             hours=4 if kinds[i] == "TRIAL_WORK" else 0,
                                             minutes=0 if kinds[i] == "TRIAL_WORK" else 45))
            start2 = start.replace(hour=14, minute=30)
            InterviewSlot.objects.create(jobPosting=j2, startTime=start2, kind="ON_SITE",
                                         endTime=start2 + timedelta(minutes=45))

        # Job-Alerts (Scope-Demo: Stichwort + Umkreis)
        JobAlertSubscription.objects.create(
            email="alert-pflege@demo.example", status="ACTIVE", keyword="Pflege",
            confirmationToken="demo-c1", managementToken="demo-m1",
            lastConfirmedAt=now)
        JobAlertSubscription.objects.create(
            email="alert-umkreis@demo.example", status="ACTIVE",
            locations=json.dumps([str(hh.id)]), radiusKm=60,
            confirmationToken="demo-c2", managementToken="demo-m2",
            lastConfirmedAt=now)

        # Demo-Kanal: die Jobmesse-Frage live beantwortbar
        from ats.models import SourceChannel
        SourceChannel.objects.get_or_create(
            slug="JOBMESSE_HH_2026", defaults=dict(
                name="Jobmesse Hamburg 06/2026",
                note="Stand B4, Standkosten 1.200 €"))
        for i, st in enumerate(["NEW", "IN_REVIEW", "INVITED", "HIRED"]):
            a = Applicant.objects.create(
                firstName=["Timo", "Sara", "Nils", "Grete"][i],
                lastName="Messe", email=f"messe{i}@beispiel-demo.de")
            _app = Application.objects.create(
                applicant=a, jobPosting=j1, status=st,
                source="JOBMESSE_HH_2026",
                hiredAt=(now - timedelta(days=1)) if st == "HIRED" else None)
            if st == "HIRED":
                Application.objects.filter(id=_app.id).update(
                    createdAt=now - timedelta(days=19))

        # Demo-Landingpage: Messe-Trichter live zeigbar (/k/jobmesse-hh/)
        from ats.models import LandingPage
        LandingPage.objects.get_or_create(
            slug="jobmesse-hh", defaults=dict(
                name="Jobmesse Hamburg 06/2026 (Landingpage)",
                headline="Pflege mit Elbblick – lernen Sie uns kennen",
                introText=("Sie waren an unserem Messestand? Schön, dass Sie "
                           "reinschauen. Hier finden Sie die Stellen, über "
                           "die wir gesprochen haben – kurze Wege, feste "
                           "Teams, echte Zeit für Menschen."),
                views=24))

        # Demo-CI: Elbtal-Blau auf hellem Grund (Muster der CI-Analyse) –
        # im Gespraech live umschaltbar unter /recruiter/branding/.
        org.brandEnabled = True
        org.brandMode = "LIGHT"
        org.brandPrimary = "#0065bd"
        org.save(update_fields=["brandEnabled", "brandMode", "brandPrimary"])

        # ---------- Governance-Demo: Gremium, Vertretung, Standards, Pool ----
        # Erzaehlbare Geschichte fuer Discovery-Gespraeche mit komplexen
        # Traegern: hoehere Position mit Sichtungs-Gremium (bewusst NUR auf
        # Stellen-Ebene, damit die uebrigen Demo-Flows frei bleiben),
        # aktive Urlaubsvertretung, Vorstands-Mindeststandard, offene
        # Bedarfsmeldung und ein Talent-Pool mit Treffer.
        User = get_user_model()
        pwd_gov = getattr(settings, "DEMO_PASSWORD", None) or \
            __import__("os").environ.get("DEMO_PASSWORD", "securats-demo-2026")

        def demo_user(username, role, first, last):
            u, _ = User.objects.get_or_create(username=username)
            u.first_name, u.last_name = first, last
            u.email = f"{username}@elbtal-demo.example"
            u.set_password(pwd_gov)
            u.save()
            g, _ = Group.objects.get_or_create(name=role)
            u.groups.set([g])
            UserScope.objects.get_or_create(user=u)
            return u

        hm_hoefer = demo_user("demo-hm", "Hiring-Manager", "Martin", "Höfer")
        vertretung = demo_user("demo-vertretung", "Viewer", "Volkan", "Tas")
        leitung = demo_user("demo-leitung", "Hiring-Manager", "Melanie", "Dorn")

        # Vorstands-Mindeststandard: Pflege braucht IMMER die Examensfrage
        fam_pflege.minimumQuestionsJson = json.dumps([{
            "id": "min-examen",
            "question": "Liegt ein Pflege-Examen (3-jährig) vor?",
            "type": "YES_NO", "isMandatory": True, "expectedAnswer": "YES"}])
        fam_pflege.save(update_fields=["minimumQuestionsJson"])

        # Hoehere Position mit Sichtungs-Gremium (2 von 3 noetig)
        j_pdl = job("Pflegedienstleitung Haus Elbblick (m/w/d)", fac_pflege, lg,
                    fam_pflege, days_old=12)
        j_pdl.panelUserIdsJson = json.dumps([str(hm_hoefer.id),
                                             str(leitung.id),
                                             str(User.objects.get_or_create(
                                                 username="demo-admin")[0].id)])
        j_pdl.save(update_fields=["panelUserIdsJson"])
        pdl_bewerberin = Applicant.objects.create(
            firstName="Sabine", lastName="Krüger",
            email="sabine.krueger@beispiel-demo.de", phone="0171 5550101")
        app_pdl = Application.objects.create(
            applicant=pdl_bewerberin, jobPosting=j_pdl, status="IN_REVIEW",
            source="Empfehlung",
            internalNotes="[Demo] 12 Jahre Leitungserfahrung, WBL Haus Nord.")
        ApplicationVote.objects.create(application=app_pdl, user=leitung,
                                       vote="FOR")
        app_pdl.internalNotes += ("\n[Demo] Gremium Melanie Dorn: Sehr "
                                  "überzeugendes Konzept für Dienstplanung – dafür.")
        app_pdl.save(update_fields=["internalNotes"])

        # Aktive Urlaubsvertretung: Höfer 3 Wochen weg, Tas uebernimmt
        RoleDelegation.objects.create(
            delegator=hm_hoefer, delegatee=vertretung, scopeType="ALL",
            validFrom=now - timedelta(days=2),
            validUntil=now + timedelta(days=19))

        # Offene Bedarfsmeldung (Fachbereich -> "Heute wichtig" der Entscheider)
        StaffingRequest.objects.create(
            title="Pflegefachkraft Nachtdienst, Station 2 (2×)",
            facility=fac_klinik, jobFamily=fam_pflege, headcount=2,
            desiredStart=(now + timedelta(days=45)).date(),
            justification="Nachtdienste seit März nur mit Leasingkräften "
                          "abgedeckt – Mehrkosten ca. 8 T€/Monat, Team am Limit.",
            requestedBy=hm_hoefer)

        # Talent-Pool: aktiver Treffer + kuerzlich abgelaufener Eintrag
        TalentPoolSubscription.objects.get_or_create(
            email="jonas.weber@beispiel-demo.de", defaults=dict(
                consentId="demo-consent-1",
                criteria=json.dumps({"job_families": [str(fam_pflege.id)],
                                     "locations": [str(hh.id)]}),
                expiresAt=now + timedelta(days=200)))
        TalentPoolSubscription.objects.get_or_create(
            email="lea.fischer@beispiel-demo.de", defaults=dict(
                consentId="demo-consent-2",
                criteria=json.dumps({"job_families": [str(fam_pflege.id)]}),
                expiresAt=now - timedelta(days=10)))  # Kulanzfenster sichtbar

        # Absage-Vorlage (Platzhalter-Demo fuer wuerdevolle Kommunikation)
        EmailTemplate.objects.get_or_create(
            name="Absage", defaults=dict(
                subject="Ihre Bewerbung: {stelle}",
                htmlContent="",
                textContent=("Guten Tag {name},\n\nvielen Dank für Ihre "
                             "Bewerbung als {stelle} bei {firma} und die Zeit, "
                             "die Sie investiert haben. Wir haben uns diesmal "
                             "für eine andere Person entschieden – das ist "
                             "keine Aussage über Ihre Qualifikation.\n\n"
                             "Gerne bleiben wir in Kontakt.")))

        # Demo-Logins (Passwort per Env DEMO_PASSWORD, Default fuer Gespraeche)
        User = get_user_model()
        pwd = getattr(settings, "DEMO_PASSWORD", None) or \
            __import__("os").environ.get("DEMO_PASSWORD", "securats-demo-2026")
        for username, role, scope_all in [("demo-admin", "HR-Admin", True),
                                          ("demo-recruiter", "Recruiter", False)]:
            user, _ = User.objects.get_or_create(username=username)
            user.set_password(pwd)
            user.is_staff = False
            user.save()
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.set([group])
            scope, _ = UserScope.objects.get_or_create(user=user)
            scope.full_access = scope_all
            scope.save()
            if not scope_all:
                scope.locations.set([hh])  # BOLA live zeigen: sieht nur Hamburg

        self.stdout.write(self.style.SUCCESS(
            f"Demo befuellt: {JobPosting.objects.count()} Stellen, "
            f"{Application.objects.count()} Bewerbungen, "
            f"{Applicant.objects.count()} Bewerber, 2 Job-Alerts, "
            f"1 offenes Freigabe-Gate, 1 Gremium-Fall (PDL, 1/3 Stimmen), "
            f"1 aktive Vertretung, 1 offene Bedarfsmeldung, Talent-Pool mit "
            f"Treffer. Logins: demo-admin / demo-recruiter / demo-hm / "
            f"demo-vertretung / demo-leitung."))
