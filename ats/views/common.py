"""SecurATS Views — Gemeinsame Helfer (ohne Abhaengigkeit zu anderen View-Modulen).

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from ..audit import write_audit
from ..models import (
    Applicant,
    Application,
    ApplicationDocument,
    Benefit,
    ContactPerson,
    Department,
    Facility,
    FacilityProfile,
    Interview,
    InterviewSlot,
    JobFamily,
    JobPosting,
    JobTemplate,
    Location,
    Organization,
    Page,
    SystemSetting,
    WorkflowState,
)
from ..permissions import can_access_application, recruiter_required

logger = logging.getLogger(__name__)

__all__ = ["_safe_next_url", "seed_data_if_empty", "exclude_filled", "campaign_expired", "_remember_campaign_src", "download_document"]


def _safe_next_url(request):
    """Open-Redirect-Schutz (CWE-601): liefert das next-Ziel nur zurueck,
    wenn es intern/gleicher Host ist – sonst None. Verhindert
    next=//evil.com oder https://phishing.example."""
    nxt = request.POST.get('next') or request.GET.get('next')
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return nxt
    return None


def seed_data_if_empty():
    """Seeds the SQLite database with fully functional mock data if it is empty."""
    # Ensure all AI global settings exist (even if organization exists)
    ai_defaults = {
        "COMPANY_NAME": "SecurATS GmbH",
        "PRIMARY_COLOR": "#8b5cf6",
        "SUPPORT_EMAIL": "support@securats.de",
        "FOOTER_TEXT": "© 2026 SecurATS. Datensouveränes Recruiting.",
        "AI_TONE": "EMPATHETIC",
        "AI_LANGUAGE": "DE_DU",
        "AI_AUTO_REJECT_ENABLED": "false",
        "AI_THRESHOLD_D_REJECT": "15",
        "AI_THRESHOLD_C_WAITLIST": "50",
        "AI_THRESHOLD_A_INVITE": "80",
        "AI_CV_LEARNING_MODE": "true",
        "AI_AGG_CHECK_ENABLED": "true",
        "AI_AGG_PROMPT": "Prüfe den folgenden Text auf Diskriminierung (Alter, Geschlecht, Herkunft, Religion) nach dem deutschen AGG. Zeige kritische Stellen auf und mache neutrale Formulierungsvorschläge.",
        "AI_TRANSLATE_EASY_LANGUAGE": "true",
        "AI_EASY_LANGUAGE_PROMPT": "Übersetze den folgenden Text in leichte Sprache (A2/B1 Niveau). Nutze kurze Sätze, vermeide Fachwörter und verwende aktive Verben.",
        "AI_MODEL": "gemma:2b"
    }
    for k, v in ai_defaults.items():
        SystemSetting.objects.get_or_create(key=k, defaults={"value": v})

    if Organization.objects.exists():
        return  # Already seeded

    # SICHERHEITSRIEGEL (sonst füllt sich eine PRODUKTIV-Datenbank von selbst
    # mit erfundenen Bewerbern):
    # Diese Funktion wird im Dashboard UND auf der öffentlichen Startseite
    # aufgerufen. Ohne Riegel legte der erste Seitenaufruf einer frischen
    # Installation – auch der eines anonymen Besuchers – Phantasie-Stellen,
    # erfundene Bewerber:innen samt Anschreiben, fabrizierte KI-Bewertungen
    # und einen Fake-Meeting-Link an. Für ein DSGVO-Produkt in einem
    # regulierten Markt ist das inakzeptabel: erfundene Personendaten in der
    # Kundendatenbank, sichtbar auf der öffentlichen Stellenbörse.
    # Demo-Daten gibt es nur noch bewusst: DEMO_MODE=1 oder Entwicklung
    # (DEBUG=True) – bzw. explizit über `manage.py seed_demo`.
    if not (getattr(settings, 'DEMO_MODE', False)
            or getattr(settings, 'DEBUG', False)):
        return

    with transaction.atomic():
        # 1. Organization
        org = Organization.objects.create(name="SecurATS GmbH")

        # 2. Facilities
        fac_berlin = Facility.objects.create(
            name="Berlin Headquarters",
            description="Hauptverwaltung und Entwicklungszentrum im Herzen von Berlin.",
            organization=org
        )
        fac_munich = Facility.objects.create(
            name="München Office",
            description="Vertriebs- und Beratungsstandort im Süden Deutschlands.",
            organization=org
        )

        # 3. Facility Profiles
        FacilityProfile.objects.create(
            facility=fac_berlin,
            description="Modernes Loft-Büro mit exzellenter Anbindung und Dachterrasse.",
            images=json.dumps(["/static/images/berlin1.jpg"]),
            slug="berlin-headquarters"
        )
        FacilityProfile.objects.create(
            facility=fac_munich,
            description="Stilvolles Altbaubüro nahe dem Englischen Garten.",
            images=json.dumps(["/static/images/munich1.jpg"]),
            slug="muenchen-office"
        )

        # 4. Departments
        dept_eng = Department.objects.create(name="Engineering & IT", facility=fac_berlin, slug="engineering-it")
        Department.objects.create(name="Human Resources & Recruiting", facility=fac_berlin, slug="hr-recruiting")
        dept_sales = Department.objects.create(name="Sales & Consulting", facility=fac_munich, slug="sales-consulting")

        # 5. Locations
        loc_berlin = Location.objects.create(
            name="Berlin Hauptbahnhof", address="Europaplatz 1", city="Berlin", postalCode="10557", lat=52.525, lng=13.369
        )
        loc_munich = Location.objects.create(
            name="München Marienplatz", address="Marienplatz 1", city="München", postalCode="80331", lat=48.137, lng=11.575
        )

        # 6. Job Families
        jf_tech = JobFamily.objects.create(name="Technology & Development")
        jf_hr = JobFamily.objects.create(name="HR & Recruiting")
        JobFamily.objects.create(name="Sales & Accounts")

        # 7. Contact Persons
        contact_carla = ContactPerson.objects.create(
            firstName="Carla",
            lastName="Miller",
            email="carla.miller@securats.de",
            phone="+49 30 555 1234",
            photoUrl="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200",
            quote="Ich liebe es, neue Talente auf ihrem Weg in unser großartiges Team zu begleiten!",
            globalJobTitle="Lead Talent Acquisition Manager"
        )
        contact_marcus = ContactPerson.objects.create(
            firstName="Marcus",
            lastName="Smith",
            email="marcus.smith@securats.de",
            phone="+49 30 555 5678",
            photoUrl="https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&q=80&w=200",
            quote="Qualität, Clean Code und datensichere Systeme stehen bei uns an erster Stelle.",
            globalJobTitle="Head of Engineering"
        )

        # 8. Workflow States
        WorkflowState.objects.create(name="draft", description="Entwurf")
        WorkflowState.objects.create(name="in_review", description="In Freigabe")
        WorkflowState.objects.create(name="approved", description="Freigegeben")
        ws_published = WorkflowState.objects.create(name="published", description="Veröffentlicht")
        WorkflowState.objects.create(name="archived", description="Archiviert")

        # 9. Job Templates
        template_standard = JobTemplate.objects.create(
            title="Standard Template",
            content="<h1>Willkommen bei SecurATS</h1><p>Wir freuen uns auf Ihre Bewerbung!</p>"
        )

        # 10. Benefits
        benefits_list = [
            Benefit.objects.create(name="Flexibles Home-Office", icon="🏠", description="Arbeite bis zu 4 Tage pro Woche von zu Hause aus."),
            Benefit.objects.create(name="ÖPNV-Ticket", icon="🚇", description="Vollständig bezahltes Deutschlandticket."),
            Benefit.objects.create(name="Weiterbildung", icon="📚", description="Jährliches Weiterbildungsbudget von 2.000 €."),
            Benefit.objects.create(name="Hardware-Wahl", icon="💻", description="Freie Wahl zwischen MacBook Pro oder Lenovo ThinkPad."),
            Benefit.objects.create(name="Fitness & Gesundheit", icon="🏋️", description="Kostenlose Mitgliedschaft im Premium-Fitnessstudio."),
        ]

        # 11. Pages (CMS)
        Page.objects.create(
            title="SecurATS Karriereportal",
            slug="home",
            content="""# Machen Sie Karriere bei SecurATS
Wir verändern das Recruiting von morgen mit datensicheren, modernen und KI-gestützten Bewerberprozessen. Werden Sie Teil eines dynamischen Teams, das echten Mehrwert schafft.""",
            status="published",
            navEnabled=True,
            navLabel="Startseite",
            navOrder=1,
            metaDesc="Karriere bei SecurATS. Finden Sie Ihren Traumjob im Recruiting, Engineering oder Sales."
        )

        Page.objects.create(
            title="Über Uns",
            slug="ueber-uns",
            content="""# Über die SecurATS GmbH
Gegründet im Herzen von Berlin, ist SecurATS ein führender Anbieter von datensouveränen Bewerbermanagement-Systemen (ATS) im DACH-Raum. Unser Fokus liegt auf Barrierefreiheit, Datenschutz (DSGVO-Compliance) und nahtloser HR-Integration.""",
            status="published",
            navEnabled=True,
            navLabel="Über Uns",
            navOrder=2,
            metaDesc="Erfahren Sie mehr über die Vision, Werte und Geschichte der SecurATS GmbH."
        )

        # 12. Job Postings
        job_fullstack = JobPosting.objects.create(
            title="Full Stack Django Developer (m/w/d)",
            description="Wir suchen einen erfahrenen Web-Entwickler zur Skalierung unserer integrierten Recruiting-Plattform.",
            tasksJson=json.dumps([
                "Entwicklung von robusten Backend-Architekturen mit Python & Django",
                "Gestaltung von hochresponsiven UIs mittels modernem CSS und performantem Vanilla JS",
                "Anbindung und Optimierung von RESTful Schnittstellen und Integrations-Feeds",
                "Sicherstellung höchster Sicherheits- und Datenschutzstandards (DSGVO)"
            ]),
            requirementsJson=json.dumps([
                "Fundierte Erfahrung mit Python, Django und relationalen Datenbanken",
                "Exzellente Kenntnisse in HTML5, CSS3 und modernen Web-Technologien",
                "Verständnis von Sicherheitsaspekten wie CSRF, XSS und PII-At-Rest-Verschlüsselung",
                "Fließende Deutsch- und gute Englischkenntnisse in Wort und Schrift"
            ]),
            screeningQuestionsJson=json.dumps([
                {
                    "id": "q1",
                    "question": "Verfügen Sie über mindestens 3 Jahre Erfahrung mit dem Django Web-Framework?",
                    "type": "YES_NO",
                    "isMandatory": True,
                    "expectedAnswer": "YES"
                },
                {
                    "id": "q2",
                    "question": "Haben Sie bereits mit PII-Verschlüsselung (z.B. Fernet/AES) gearbeitet?",
                    "type": "YES_NO",
                    "isMandatory": False,
                    "expectedAnswer": "YES"
                }
            ]),
            contactPerson=contact_marcus,
            organization=org,
            facility=fac_berlin,
            department=dept_eng,
            location=loc_berlin,
            jobFamily=jf_tech,
            workflowState=ws_published,
            jobTemplate=template_standard
        )
        job_fullstack.benefits.set(benefits_list[:4])

        job_recruiter = JobPosting.objects.create(
            title="Junior Recruiting Manager (m/w/d)",
            description="Verstärke unser HR-Team bei der Suche und Betreuung der besten IT-Talente.",
            tasksJson=json.dumps([
                "Steuerung des gesamten Bewerbungsprozesses von der Ausschreibung bis zum Onboarding",
                "Führen von Erstgesprächen und Koordination von Fachinterviews",
                "Pflege und Ausbau unseres Talent Pools",
                "Mitgestaltung moderner Candidate Journeys"
            ]),
            requirementsJson=json.dumps([
                "Erste Berufserfahrung im Recruiting oder HR-Bereich",
                "Starke kommunikative Fähigkeiten und Empathie",
                "Strukturierte, selbstständige Arbeitsweise",
                "Fließende Deutschkenntnisse"
            ]),
            screeningQuestionsJson=json.dumps([
                {
                    "id": "q1",
                    "question": "Können Sie ab sofort in Vollzeit an unserem Standort München starten?",
                    "type": "YES_NO",
                    "isMandatory": True,
                    "expectedAnswer": "YES"
                }
            ]),
            contactPerson=contact_carla,
            organization=org,
            facility=fac_munich,
            department=dept_sales,
            location=loc_munich,
            jobFamily=jf_hr,
            workflowState=ws_published,
            jobTemplate=template_standard
        )
        job_recruiter.benefits.set([benefits_list[0], benefits_list[1], benefits_list[4]])

        # 13. Seed Applicants and Applications
        # Applicant 1 - New
        app1 = Applicant.objects.create(
            firstName="Max", lastName="Mustermann", email="max.mustermann@web.de", phone="+49 170 1111111"
        )
        Application.objects.create(
            applicant=app1,
            jobPosting=job_fullstack,
            coverLetterTxt="Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich auf Ihre Full-Stack-Entwicklerstelle. Ich bringe 5 Jahre Erfahrung mit Django mit und freue mich auf das Gespräch.",
            aiScore="A",
            aiRationale="Starkes Django-Profil. Übereinstimmende Kernkompetenzen. Sehr gutes Anschreiben.",
            status="NEW"
        )

        # Applicant 2 - In Review
        app2 = Applicant.objects.create(
            firstName="Julia", lastName="Schmidt", email="julia.schmidt@gmx.de", phone="+49 171 2222222"
        )
        Application.objects.create(
            applicant=app2,
            jobPosting=job_fullstack,
            coverLetterTxt="Hallo Marcus,\n\nich habe großes Interesse daran, SecurATS als Python-Entwicklerin zu unterstützen. Ich kenne mich exzellent mit Verschlüsselung aus.",
            aiScore="B",
            aiRationale="Gute technische Skills, aber etwas weniger Erfahrung im Frontend-Bereich.",
            status="IN_REVIEW"
        )

        # Applicant 3 - Invited
        app3 = Applicant.objects.create(
            firstName="Alexander", lastName="Kaiser", email="alexander.kaiser@gmail.com", phone="+49 172 3333333"
        )
        appl_invited = Application.objects.create(
            applicant=app3,
            jobPosting=job_recruiter,
            coverLetterTxt="Sehr geehrte Carla,\n\nIT-Recruiting ist meine Leidenschaft. Ich freue mich sehr darauf, Euer HR-Team in München tatkräftig zu unterstützen.",
            aiScore="A",
            aiRationale="Hervorragende HR-Vorerfahrung, sehr sympathischer Auftritt im Anschreiben.",
            status="INVITED"
        )

        # Schedule a mock interview
        Interview.objects.create(
            application=appl_invited,
            scheduledAt=timezone.now() + datetime.timedelta(days=2, hours=10),
            locationType="REMOTE",
            meetingLink="https://meet.google.com/abc-defg-hij"
        )

        # Applicant 4 - Rejected
        app4 = Applicant.objects.create(
            firstName="Sven", lastName="Müller", email="sven.mueller@t-online.de", phone="+49 173 4444444"
        )
        Application.objects.create(
            applicant=app4,
            jobPosting=job_fullstack,
            coverLetterTxt="Moin,\n\nich suche einen Job. Ich kann ein bisschen HTML.",
            aiScore="D",
            aiRationale="K.O.-Kriterien nicht erfüllt. Keine Django-Kenntnisse vorhanden.",
            status="REJECTED",
            withdrawReason="K.O. Kriterien ungenügend"
        )

        # 14. Seed Interview Slots
        InterviewSlot.objects.create(
            jobPosting=job_fullstack,
            startTime=timezone.now() + datetime.timedelta(days=3, hours=14),
            endTime=timezone.now() + datetime.timedelta(days=3, hours=15)
        )
        InterviewSlot.objects.create(
            jobPosting=job_recruiter,
            startTime=timezone.now() + datetime.timedelta(days=4, hours=11),
            endTime=timezone.now() + datetime.timedelta(days=4, hours=12)
        )

        # 15. Seed SystemSettings and EmailTemplates
        from ..models import EmailTemplate
        if not SystemSetting.objects.exists():
            SystemSetting.objects.create(key="COMPANY_NAME", value="SecurATS GmbH")
            SystemSetting.objects.create(key="PRIMARY_COLOR", value="#8b5cf6")
            SystemSetting.objects.create(key="SUPPORT_EMAIL", value="support@securats.de")
            SystemSetting.objects.create(key="FOOTER_TEXT", value="© 2026 SecurATS. Datensouveränes Recruiting.")

        if not EmailTemplate.objects.exists():
            EmailTemplate.objects.create(
                name="Eingangsbestätigung",
                subject="Bewerbungseingang bei [[COMPANY_NAME]]",
                htmlContent="<h3>Hallo [[FIRST_NAME]] [[LAST_NAME]],</h3><p>vielen Dank für deine Bewerbung für die Position als <strong>[[JOB_TITLE]]</strong>.</p><p>Wir haben deine Unterlagen erhalten und prüfen diese sorgfältig. Unsere KI analysiert die Übereinstimmung mit unseren Anforderungen unvoreingenommen.</p><p>Beste Grüße,<br/>Dein HR Team von [[COMPANY_NAME]]</p>"
            )
            EmailTemplate.objects.create(
                name="Einladung zum Interview",
                subject="Einladung zum Fachgespräch bei [[COMPANY_NAME]]",
                htmlContent="<h3>Hallo [[FIRST_NAME]] [[LAST_NAME]],</h3><p>wir sind von deiner Bewerbung beeindruckt! Gerne möchten wir dich zu einem persönlichen Fachgespräch einladen.</p><p>Bitte wähle im Portal einen passenden Termin aus.</p><p>Beste Grüße,<br/>[[COMPANY_NAME]] Recruiting Team</p>"
            )
            EmailTemplate.objects.create(
                name="Absage",
                subject="Deine Bewerbung bei [[COMPANY_NAME]]",
                htmlContent="<h3>Hallo [[FIRST_NAME]] [[LAST_NAME]],</h3><p>vielen Dank für das Interesse an einer Tätigkeit bei uns.</p><p>Leider müssen wir dir mitteilen, dass wir dich für diese Position nicht berücksichtigen können. Wir wünschen dir auf deinem weiteren Weg alles Gute.</p><p>Beste Grüße,<br/>[[COMPANY_NAME]] Recruiting Team</p>"
            )


def exclude_filled(jobs_qs):
    """Oeffentliche Listen: voll besetzte Stellen (HIRED >= headcount)
    ausblenden. Direktlinks bleiben erreichbar (Banner statt Blockade) –
    Initiativbewerbungen sind erwuenscht, irrefuehrende Werbung nicht."""
    from django.db.models import Count, F, Q
    return (jobs_qs
            .annotate(_hired=Count('applications',
                                   filter=Q(applications__status='HIRED')))
            .exclude(_hired__gte=F('headcount')))


def campaign_expired(obj) -> bool:
    """True, wenn eine Kampagne (Landingpage/Kanal) ihr Enddatum ueberschritten
    hat. Leeres Datum = laeuft unbegrenzt (Bestandsverhalten)."""
    return bool(getattr(obj, 'expiresAt', None)
                and obj.expiresAt < timezone.now())


def _remember_campaign_src(request, raw):
    """Kampagnen-Quelle fuer die Sitzung merken – ausser der Kanal ist
    abgelaufen. Freie Quellen (kein angelegter Kanal) bleiben unbeschraenkt,
    denn ihnen fehlt schlicht das Enddatum-Konzept."""
    src = (raw or '')[:50]
    if not src:
        return
    from ..models import SourceChannel
    channel = SourceChannel.objects.filter(slug__iexact=src).first()
    if channel and campaign_expired(channel):
        return  # Kampagne beendet: keine neue Zuordnung mehr
    request.session['application_src'] = src


# --- WP1: Sicherer Download eines Bewerbungsnachweises (BOLA + Audit) --------
@recruiter_required
def download_document(request, doc_id):
    doc = get_object_or_404(ApplicationDocument.objects.select_related('application__jobPosting'), id=doc_id)
    if not can_access_application(request.user, doc.application):
        raise Http404("Nicht im Zugriffsbereich.")
    if not doc.file or not default_storage.exists(doc.file.name):
        raise Http404("Datei nicht vorhanden.")
    write_audit("READ_DOCUMENT", user=request.user, application_id=doc.application_id,
                document=doc.name)
    return FileResponse(default_storage.open(doc.file.name, "rb"),
                        as_attachment=True, filename=doc.name)
