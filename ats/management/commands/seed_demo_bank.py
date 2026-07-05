"""Banken-Demo-Welt im BAWAG-Stil (fiktionalisiert: "BAWAG Group (Demo)").

Zeigt, dass SecurATS auch Grossunternehmen ausserhalb der Pflege traegt:
seriöses Dunkelrot auf hellem Grund, Kategorien-Hierarchie (Bereich >
Jobfamilie), je Kategorie eigene Prozesse (Screening-Fragen, K.O.-Logik,
Sichtungs-Gremium, Mindeststandards) und die komplette Kampagnen-Strecke
(Kanaele, Landingpage, Trichter).

Nutzung (ALTERNATIV zur Pflege-Demo, gleiche Instanz = ein Mandant):
  DEMO_MODE=1 python manage.py seed_demo_bank --reset

Bewusst OHNE geschuetzte Assets (kein Logo, keine Bilder der BAWAG) –
nur Farbwelt und Struktur der Referenz.
"""
import json
from datetime import timedelta

from django.conf import settings
from django.core.management.base import CommandError
from django.utils import timezone

from ats.management.commands.seed_demo import Command as PflegeSeed
from ats.models import (Organization, Location, Facility, Department,
                        JobFamily, WorkflowState, JobPosting, ContactPerson,
                        Applicant, Application, ApplicationVote,
                        SourceChannel, LandingPage)


class Command(PflegeSeed):
    help = ("Befuellt die Demo-Instanz mit der Banken-Welt "
            "(--reset: wipe + neu, nur mit DEMO_MODE=1).")

    def handle(self, *args, **options):
        # Sicherheit: Dieser Befehl legt Demo-Staff-Accounts mit bekanntem
        # Passwort an. Er darf NUR auf einer Demo-Instanz laufen (DEMO_MODE=1),
        # damit auf Produktion niemals Backdoor-Logins entstehen.
        if not getattr(settings, "DEMO_MODE", False):
            raise CommandError(
                "seed_demo* legt Demo-Konten mit bekanntem Passwort an "
                "und ist nur mit DEMO_MODE=1 erlaubt (Schutz vor "
                "Backdoor-Accounts auf Produktion).")
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        AuthUser = get_user_model()
        now = timezone.now()

        if options.get("reset"):
            if not getattr(settings, "DEMO_MODE", False):
                self.stderr.write(
                    "--reset loescht Daten und ist nur mit DEMO_MODE=1 "
                    "erlaubt (Schutz vor Produktivdaten).")
                return
            self._wipe()

        # ---------- Mandant & Branding (CI-Muster: EINE Farbe, heller Grund)
        org = Organization.objects.create(
            name="BAWAG Group (Demo)",
            brandEnabled=True, brandMode="LIGHT",
            brandPrimary="#a0132f",          # seriöses Banken-Dunkelrot
            brandAccent="#2d3239")           # Anthrazit als Zweitton

        # ---------- Standorte (DACH + Remote)
        wien = Location.objects.create(name="Wien", city="Wien")
        hamburg = Location.objects.create(name="Hamburg", city="Hamburg")
        linz = Location.objects.create(name="Linz", city="Linz")
        remote = Location.objects.create(name="Remote (DACH)", city="Remote")

        # ---------- Hierarchie: Einrichtung > Bereich (Dept) > Jobfamilie
        zentrale = Facility.objects.create(name="Group Headquarter Wien",
                                           organization=org)
        filialnetz = Facility.objects.create(name="Filialnetz Österreich",
                                             organization=org)
        dep_it = Department.objects.create(name="IT & Digital Banking",
                                           facility=zentrale)
        dep_risk = Department.objects.create(name="Risikomanagement",
                                             facility=zentrale)
        dep_central = Department.objects.create(name="Central Functions",
                                                facility=zentrale)
        dep_vertrieb = Department.objects.create(name="Filialnetz & Vertrieb",
                                                 facility=filialnetz)

        fam_ba = JobFamily.objects.create(name="IT Business Analysis")
        fam_agile = JobFamily.objects.create(name="Agile & Product Ownership")
        fam_beratung = JobFamily.objects.create(name="Kundenberatung Filiale")
        fam_exec = JobFamily.objects.create(name="Executive & Leadership")

        # ---------- Prozess-Governance je Kategorie -----------------------
        # Tech-Familien: Mindeststandard "reguliertes Umfeld" (K.O.)
        min_reg = [{"id": "min-reg", "type": "YES_NO", "isMandatory": True,
                    "expectedAnswer": "YES",
                    "question": "Haben Sie bereits im regulierten Umfeld "
                                "(Bank/Versicherung/KRITIS) gearbeitet?"}]
        for fam in (fam_ba, fam_agile):
            fam.minimumQuestionsJson = json.dumps(min_reg)
            fam.save(update_fields=["minimumQuestionsJson"])
        # Filiale: Bankausbildung als Mindeststandard (K.O.)
        fam_beratung.minimumQuestionsJson = json.dumps([{
            "id": "min-bank", "type": "YES_NO", "isMandatory": True,
            "expectedAnswer": "YES",
            "question": "Liegt eine abgeschlossene Bankausbildung oder "
                        "vergleichbare Qualifikation vor?"}])
        fam_beratung.save(update_fields=["minimumQuestionsJson"])

        # ---------- Menschen ----------------------------------------------
        def demo_user(username, role, first, last):
            u, _ = AuthUser.objects.get_or_create(
                username=username,
                defaults=dict(first_name=first, last_name=last,
                              email=f"{username}@demo.example"))
            u.first_name, u.last_name = first, last
            u.set_password("securats-demo-2026")
            u.save()
            g, _ = Group.objects.get_or_create(name=role)
            u.groups.add(g)
            return u

        rec = demo_user("demo-bank-recruiter", "Recruiter", "Julia", "Steiner")
        hm_it = demo_user("demo-bank-hm", "Hiring-Manager", "Thomas", "Berger")
        lead_it = demo_user("demo-bank-lead", "Hiring-Manager", "Petra",
                            "Novak")
        demo_user("demo-bank-admin", "HR-Admin", "Sandra", "Wolf")

        # Executive-Prozess als KONFIGURATION: Familien-Default-Gremium
        fam_exec.panelUserIdsJson = json.dumps([str(hm_it.id),
                                                str(lead_it.id),
                                                str(rec.id)])
        fam_exec.minimumQuestionsJson = json.dumps([{
            "id": "min-exec", "type": "TEXT", "isMandatory": True,
            "question": "Beschreiben Sie Ihre P&L- bzw. "
                        "Führungsverantwortung der letzten 5 Jahre."}])
        fam_exec.save(update_fields=["panelUserIdsJson",
                                     "minimumQuestionsJson"])

        # Routing-Matrix: die drei Regel-Typen aus dem Anforderungs-Prompt
        from ats.models import RequisitionRule
        for role in ("Bereichsleitung IT", "Risikomanagement",
                     "Geschäftsführung", "Filialleitung"):
            Group.objects.get_or_create(name=role)
        RequisitionRule.objects.create(
            name="Tech-Prozess Core Banking", facility=zentrale,
            department=dep_it, jobFamily=fam_ba,
            chain="Bereichsleitung IT, Risikomanagement, Geschäftsführung",
            mandatory=True,
            formQuestionsJson=json.dumps([
                {"id": "stack", "type": "TEXT", "isMandatory": True,
                 "question": "Welcher Tech-Stack / welche Systeme werden "
                             "betreut (z. B. T24, SWIFT-Gateway)?"},
                {"id": "budget", "type": "SELECT", "isMandatory": True,
                 "question": "Ist das Budget im Stellenplan hinterlegt?",
                 "options": ["Ja, Stellenplan", "Ja, Sonderbudget",
                             "Noch offen"]}]))
        RequisitionRule.objects.create(
            name="Standard Filialvertrieb", facility=filialnetz,
            chain="Filialleitung, Geschäftsführung", mandatory=False)
        RequisitionRule.objects.create(
            name="Fallback Gesamtbank", chain="Geschäftsführung",
            mandatory=False)

        cp = ContactPerson.objects.create(
            firstName="Julia", lastName="Steiner",
            email="julia.steiner@demo.example", phone="+43 1 546 12-0",
            globalJobTitle="Talent Acquisition Partnerin",
            quote="Wir melden uns innerhalb von 5 Werktagen – versprochen.")

        published, _ = WorkflowState.objects.get_or_create(name="published")

        def job(title, dep, loc, fam, description, tasks, requirements,
                screening, days_old=14):
            j = JobPosting.objects.create(
                title=title, organization=org, facility=dep.facility,
                department=dep, location=loc, jobFamily=fam,
                contactPerson=cp, workflowState=published,
                description=description,
                tasksJson=json.dumps(tasks),
                requirementsJson=json.dumps(requirements),
                screeningQuestionsJson=json.dumps(screening))
            JobPosting.objects.filter(id=j.id).update(
                createdAt=now - timedelta(days=days_old))
            return j

        # ---------- Stelle 1: Senior IT Business Analyst -------------------
        j_ba = job(
            "Senior IT Business Analyst – Core Banking & Zahlungsverkehr (m/w/d)",
            dep_it, wien, fam_ba,
            description=(
                "Sie übersetzen zwischen Fachbereich, Regulatorik und "
                "Entwicklung: In unserem Core-Banking-Team verantworten Sie "
                "Anforderungen rund um den Zahlungsverkehr (SEPA, SWIFT, "
                "ISO 20022) – von der Analyse über das Fachkonzept bis zur "
                "Testbegleitung. Vollzeit (38,5 h), unbefristet, "
                "Eintritt ab sofort. Jahresbruttogehalt ab 70.000 € mit "
                "klarer Bereitschaft zur Überzahlung je nach Erfahrung."),
            tasks=[
                "Anforderungsanalyse und Fachkonzeption im Core Banking "
                "(Konten, Zahlungsverkehr, Clearing)",
                "Begleitung der ISO-20022-Migration und der "
                "SEPA-/SWIFT-Schnittstellen",
                "Umsetzung regulatorischer Vorgaben (DORA, MaRisk, PSD2) "
                "gemeinsam mit Compliance und IT-Security",
                "Testfälle, Abnahmen und Go-Live-Begleitung mit den "
                "Entwicklungsteams",
            ],
            requirements=[
                "Mehrjährige Erfahrung als Business Analyst im Banken- "
                "oder Zahlungsverkehrsumfeld",
                "Sichere Kenntnis mindestens eines Standards: SEPA, "
                "SWIFT MT oder ISO 20022",
                "Erfahrung mit regulatorischen Projekten im "
                "Finanzsektor",
                "Sehr gutes Deutsch (C1) und gutes Englisch",
            ],
            screening=[
                {"id": "pay-std", "type": "SELECT", "isMandatory": True,
                 "question": "Mit welchem Payment-Standard haben Sie am "
                             "intensivsten gearbeitet?",
                 "options": ["SEPA", "SWIFT MT", "ISO 20022",
                             "Noch keine Berührung"]},
                {"id": "reg-proj", "type": "TEXT", "isMandatory": True,
                 "question": "Beschreiben Sie in 2–3 Sätzen ein "
                             "regulatorisches Projekt (z. B. DORA, MaRisk, "
                             "PSD2), das Sie begleitet haben."},
                {"id": "exp-core", "type": "YES_NO", "isMandatory": True,
                 "expectedAnswer": "YES",
                 "question": "Haben Sie mindestens 3 Jahre Erfahrung im "
                             "Core-Banking-Umfeld?"},
            ] + min_reg, days_old=18)
        # Tech-Prozess: Fachinterview + Team-Fit als 2er-Sichtungs-Gremium
        j_ba.panelUserIdsJson = json.dumps([str(hm_it.id), str(lead_it.id)])
        j_ba.save(update_fields=["panelUserIdsJson"])

        # ---------- Stelle 2: Scrum Product Owner --------------------------
        j_po = job(
            "Certified Scrum Product Owner / Agile Coach – "
            "Digitale Transformation (m/w/d)",
            dep_it, remote, fam_agile,
            description=(
                "Sie treiben die digitale Transformation unseres Bankings: "
                "Als Product Owner priorisieren Sie das Backlog unserer "
                "Kunden-Apps, als Agile Coach entwickeln Sie Teams und "
                "Führungskräfte weiter. Remote innerhalb DACH mit "
                "regelmäßigen Team-Tagen in Wien. Vollzeit, unbefristet."),
            tasks=[
                "Produktvision, Roadmap und Backlog für digitale "
                "Banking-Produkte verantworten",
                "Stakeholder von Vorstand bis Entwicklungsteam "
                "orchestrieren",
                "Agile Arbeitsweisen (Scrum, Kanban, OKR) coachen und "
                "skalieren",
                "Discovery mit echten Kundendaten: Hypothesen, Experimente, "
                "Messung",
            ],
            requirements=[
                "Zertifizierung als Product Owner (CSPO/PSPO) oder "
                "vergleichbar",
                "Erfahrung in der Produktentwicklung regulierter "
                "digitaler Services",
                "Moderations- und Coaching-Kompetenz auf allen Ebenen",
            ],
            screening=[
                {"id": "cert", "type": "SELECT", "isMandatory": True,
                 "question": "Welche Product-Owner-Zertifizierung bringen "
                             "Sie mit?",
                 "options": ["CSPO", "PSPO I", "PSPO II/III",
                             "Keine, aber Praxiserfahrung"]},
                {"id": "impact", "type": "TEXT", "isMandatory": False,
                 "question": "Ihr größter Produkterfolg in einem Satz?"},
                {"id": "exp-agile", "type": "YES_NO", "isMandatory": True,
                 "expectedAnswer": "YES",
                 "question": "Haben Sie mindestens 2 Jahre als PO/Agile "
                             "Coach mit Entwicklungsteams gearbeitet?"},
            ] + min_reg, days_old=9)
        j_po.panelUserIdsJson = json.dumps([str(hm_it.id), str(lead_it.id)])
        j_po.save(update_fields=["panelUserIdsJson"])

        # ---------- Stelle 3: Customer Relationship Manager ---------------
        job("Customer Relationship Manager – Filialvertrieb (m/w/d)",
            dep_vertrieb, linz, fam_beratung,
            description=(
                "Sie sind das Gesicht unserer Filiale: Sie beraten "
                "Privatkundinnen und -kunden zu Konto, Karte, Vorsorge und "
                "Finanzierung – persönlich, digital unterstützt und auf "
                "Augenhöhe. Vollzeit oder Teilzeit ab 30 h, Eintritt nach "
                "Vereinbarung."),
            tasks=[
                "Ganzheitliche Beratung im Privatkundengeschäft",
                "Aktive Kundenansprache und Terminvereinbarung – digital "
                "und in der Filiale",
                "Zusammenarbeit mit Spezialistinnen für Wertpapier und "
                "Finanzierung",
            ],
            requirements=[
                "Abgeschlossene Bankausbildung oder kaufmännische "
                "Ausbildung mit Finanzbezug",
                "Freude am direkten Kundenkontakt",
                "Verlässlichkeit und Teamgeist",
            ],
            screening=[
                {"id": "standort", "type": "SELECT", "isMandatory": True,
                 "question": "Welcher Einsatzort passt für Sie?",
                 "options": ["Linz Zentrum", "Linz Süd",
                             "Flexibel im Raum Linz"]},
            ], days_old=25)

        # ---------- Kampagnen-Strecke: Kanaele + Landingpage --------------
        SourceChannel.objects.create(name="LinkedIn Kampagne Q3/2026",
                                     slug="LINKEDIN",
                                     note="Paid Ads, Budget 4.500 €")
        SourceChannel.objects.create(name="Jobmesse Wien 2026",
                                     slug="JOBMESSE_WIEN_2026",
                                     note="Stand C12, WU Career Day")
        LandingPage.objects.create(
            name="Karriere-Hub Banking", slug="karriere-banking",
            headline="Arbeiten bei der BAWAG Group (Demo)",
            introText=(
                "Wir verbinden die Stabilität einer führenden Bank mit dem "
                "Tempo eines Tech-Unternehmens.\n"
                "✓ Flexible Arbeitsmodelle inkl. Remote (DACH)\n"
                "✓ 13. und 14. Gehalt, Erfolgsbeteiligung\n"
                "✓ Gesundheitsangebote, Betriebsrestaurant, Öffi-Ticket\n"
                "✓ Strukturierte Entwicklung: von der Fachkarriere bis zur "
                "Führung"),
            contactPerson=cp, views=57,
            blocksJson=json.dumps([
                {"type": "stats",
                 "items": ["2,1 Mio|Kundinnen & Kunden",
                           "3.600+|Kolleginnen & Kollegen",
                           "4,2 ★|Arbeitgeber-Bewertung",
                           "1883|gegründet"]},
                {"type": "quote",
                 "text": "Ich bin für die ISO-20022-Migration gekommen und "
                         "wegen des Teams geblieben.",
                 "author": "Miriam A.", "role": "IT Business Analystin"},
                {"type": "faq", "heading": "Häufige Fragen",
                 "items": [
                     "Wie schnell bekomme ich Rückmeldung?|Innerhalb von 5 "
                     "Werktagen – dafür steht Julia persönlich ein.",
                     "Ist Remote wirklich möglich?|Ja, in vielen Rollen "
                     "innerhalb der DACH-Region mit Team-Tagen in Wien.",
                     "Wie läuft der Tech-Prozess ab?|Screening, technisches "
                     "Gespräch, Team-Fit – transparent im Bewerberportal."]},
                {"type": "cta", "text": "Nichts Passendes dabei?",
                 "buttonLabel": "Alle offenen Stellen ansehen",
                 "url": "/jobs/"}]))

        # ---------- Lebendige Bewerbungen ----------------------------------
        def applicant(first, last, mail):
            return Applicant.objects.create(firstName=first, lastName=last,
                                            email=mail)

        answers_ba = {
            "Mit welchem Payment-Standard haben Sie am intensivsten "
            "gearbeitet?": "ISO 20022",
            "Beschreiben Sie in 2–3 Sätzen ein regulatorisches Projekt "
            "(z. B. DORA, MaRisk, PSD2), das Sie begleitet haben.":
                "DORA-Umsetzung: Auslagerungsregister und "
                "Resilienz-Testkonzept für den Zahlungsverkehr aufgebaut.",
            "Haben Sie mindestens 3 Jahre Erfahrung im Core-Banking-Umfeld?":
                "YES",
        }
        a1 = applicant("Miriam", "Aigner", "miriam.aigner@demo-mail.at")
        app1 = Application.objects.create(
            applicant=a1, jobPosting=j_ba, status="IN_REVIEW",
            source="LINKEDIN",
            screeningAnswersJson=json.dumps(answers_ba))
        ApplicationVote.objects.create(application=app1, user=hm_it,
                                       vote="FOR")  # 1/2 – Demo-Moment
        a2 = applicant("Daniel", "Kraus", "daniel.kraus@demo-mail.at")
        Application.objects.create(applicant=a2, jobPosting=j_ba,
                                   status="NEW", source="KARRIERE-BANKING")
        a3 = applicant("Selin", "Yildiz", "selin.yildiz@demo-mail.at")
        Application.objects.create(applicant=a3, jobPosting=j_po,
                                   status="INVITED",
                                   source="JOBMESSE_WIEN_2026")
        a4 = applicant("Georg", "Pichler", "georg.pichler@demo-mail.at")
        Application.objects.create(applicant=a4, jobPosting=j_po,
                                   status="NEW", source="KARRIERE-BANKING")
        # Die Koenigskennzahl live: eine echte Einstellung ueber die Messe
        a5 = applicant("Katrin", "Moser", "katrin.moser@demo-mail.at")
        app5 = Application.objects.create(
            applicant=a5, jobPosting=j_po, status="HIRED",
            source="JOBMESSE_WIEN_2026",
            hiredAt=now - timedelta(days=2))
        Application.objects.filter(id=app5.id).update(
            createdAt=now - timedelta(days=23))  # 21 Tage bis Einstellung

        self.stdout.write(self.style.SUCCESS(
            "Banken-Demo befuellt: 3 Stellen (BA/PO/CRM), 5 Bewerbungen (1 EINGESTELLT via Messe, 21 Tage), "
            "Gremium 1/2 auf der BA-Stelle, Kanaele LINKEDIN + "
            "JOBMESSE_WIEN_2026, 3 Routing-Regeln, Landingpage /k/karriere-banking/ (57 "
            "Aufrufe), Branding Dunkelrot #a0132f hell. Logins: "
            "demo-bank-recruiter / demo-bank-hm / demo-bank-lead / "
            "demo-bank-admin (Passwort securats-demo-2026)."))
