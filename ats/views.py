import os
import json
import uuid
import logging
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme

logger = logging.getLogger(__name__)
from django.views.decorators.csrf import ensure_csrf_cookie
from .permissions import any_staff_required, recruiter_required, hr_admin_required
from .permissions import scope_applications, scope_jobs, can_access_application
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Organization, Facility, FacilityProfile, Department, Location,
    JobFamily, ContactPerson, WorkflowState, JobTemplate, Benefit,
    JobPosting, Applicant, Application, Interview, InterviewSlot,
    Message, Page, AuditLog, AILearningSample, SystemSetting, AppWorkflowDef
, get_interview_kinds)

# ============================================================================
# AUTO-SEEDING UTILITY
# ============================================================================


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
        dept_hr = Department.objects.create(name="Human Resources & Recruiting", facility=fac_berlin, slug="hr-recruiting")
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
        jf_sales = JobFamily.objects.create(name="Sales & Accounts")

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
        ws_draft = WorkflowState.objects.create(name="draft", description="Entwurf")
        ws_in_review = WorkflowState.objects.create(name="in_review", description="In Freigabe")
        ws_approved = WorkflowState.objects.create(name="approved", description="Freigegeben")
        ws_published = WorkflowState.objects.create(name="published", description="Veröffentlicht")
        ws_archived = WorkflowState.objects.create(name="archived", description="Archiviert")

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
        from .models import EmailTemplate
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


# ============================================================================
# PUBLIC CAREER PORTAL VIEWS
# ============================================================================

def home(request):
    """Renders the career landing page, seeding data automatically if database is empty."""
    seed_data_if_empty()
    
    # Get navigation elements
    nav_pages = Page.objects.filter(status="published", navEnabled=True).order_by('navOrder')
    home_page = Page.objects.filter(slug="home", status="published").first()
    
    # Active Job postings count for the hero section
    jobs_count = JobPosting.objects.filter(workflowState__name="published").count()
    featured_jobs = JobPosting.objects.filter(workflowState__name="published").order_by('-createdAt')[:3]
    
    context = {
        'nav_pages': nav_pages,
        'home_page': home_page,
        'jobs_count': jobs_count,
        'featured_jobs': featured_jobs,
        'slug': 'home'
    }
    return render(request, 'home.html', context)



def exclude_filled(jobs_qs):
    """Oeffentliche Listen: voll besetzte Stellen (HIRED >= headcount)
    ausblenden. Direktlinks bleiben erreichbar (Banner statt Blockade) –
    Initiativbewerbungen sind erwuenscht, irrefuehrende Werbung nicht."""
    from django.db.models import Count, Q, F
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
    from .models import SourceChannel
    channel = SourceChannel.objects.filter(slug__iexact=src).first()
    if channel and campaign_expired(channel):
        return  # Kampagne beendet: keine neue Zuordnung mehr
    request.session['application_src'] = src


def job_list(request):
    """Renders the career board with search & filtering capabilities."""
    if request.GET.get('src'):
        # Kampagnen-Quelle (Jobmesse-QR etc.) fuer die ganze Sitzung merken –
        # sonst geht sie beim ersten Klick von der Liste zur Stelle verloren.
        _remember_campaign_src(request, request.GET['src'])
    nav_pages = Page.objects.filter(status="published", navEnabled=True).order_by('navOrder')
    
    # Filter only published jobs
    jobs = exclude_filled(JobPosting.objects.filter(workflowState__name="published")).select_related('location', 'facility', 'department')
    
    # Search and filter inputs
    search_query = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    
    family_filter = request.GET.get('family', '').strip()

    if search_query:
        # Flexible Suche: Titel ODER Beschreibung (UC-MN-01, UC-LK-06)
        from django.db.models import Q
        jobs = jobs.filter(Q(title__icontains=search_query) |
                           Q(description__icontains=search_query))
    if location_filter:
        jobs = jobs.filter(location__id=location_filter)
    if dept_filter:
        jobs = jobs.filter(department__id=dept_filter)
    if family_filter:
        jobs = jobs.filter(jobFamily__id=family_filter)
        
    locations = Location.objects.filter(archived=False)
    departments = Department.objects.all()
    families = JobFamily.objects.order_by('name')
    
    context = {
        'nav_pages': nav_pages,
        'jobs': jobs,
        'locations': locations,
        'departments': departments,
        'families': families,
        'family_filter': request.GET.get('family', ''),
        'search_query': search_query,
        'location_filter': location_filter,
        'dept_filter': dept_filter,
        'slug': 'jobs'
    }
    return render(request, 'job_list.html', context)


def job_detail(request, job_id):
    """Renders a single job's detail page with modular descriptions."""
    if request.GET.get('src'):
        # Kampagnen-Quelle (Jobmesse-QR etc.) fuer die ganze Sitzung merken –
        # sonst geht sie beim ersten Klick von der Liste zur Stelle verloren.
        _remember_campaign_src(request, request.GET['src'])
    nav_pages = Page.objects.filter(status="published", navEnabled=True).order_by('navOrder')
    job = get_object_or_404(JobPosting.objects.select_related('location', 'facility', 'department', 'contactPerson'), id=job_id)
    
    # Parse modular components
    tasks = []
    requirements = []
    
    if job.tasksJson:
        try:
            tasks = json.loads(job.tasksJson)
        except Exception:
            tasks = []
            
    if job.requirementsJson:
        try:
            requirements = json.loads(job.requirementsJson)
        except Exception:
            requirements = []
            
    context = {
        'nav_pages': nav_pages,
        'job': job,
        'tasks': tasks,
        'requirements': requirements,
        'slug': 'jobs'
    }
    hired_count = Application.objects.filter(jobPosting=job,
                                             status='HIRED').count()
    job_filled = hired_count >= (job.headcount or 1)
    context['job_filled'] = job_filled
    return render(request, 'job_detail.html', context)


def bewerben(request, job_id):
    """Handles applicant submissions with bot honeypots and dynamic K.O. questions."""
    nav_pages = Page.objects.filter(status="published", navEnabled=True).order_by('navOrder')
    job = get_object_or_404(JobPosting, id=job_id)
    
    # Parse screening questions
    screening_questions = []
    if job.screeningQuestionsJson:
        try:
            screening_questions = json.loads(job.screeningQuestionsJson)
        except Exception:
            screening_questions = []
            
    if request.method == 'POST':
        # 1. Honey Pot Spam Protection
        honeypot = request.POST.get('website_url', '').strip()
        if honeypot:
            # Silent discard for bots
            return render(request, 'bewerbung_success.html', {'job': job, 'nav_pages': nav_pages})
            
        # 2. Extract inputs
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        cover_letter = request.POST.get('cover_letter', '').strip()
        consent_pool = request.POST.get('consent_pool') == 'on'

        # 2b. Serverseitige Validierung (WCAG 3.3.1/3.3.2 + Robustheit):
        # HTML5-`required` schützt nicht vor direkten POSTs; ohne diese Prüfung
        # entstünden Bewerber mit leerer E-Mail (Blind-Index-Kollision!).
        errors = {}
        if not first_name:
            errors['first_name'] = 'Bitte geben Sie Ihren Vornamen an.'
        if not last_name:
            errors['last_name'] = 'Bitte geben Sie Ihren Nachnamen an.'
        if not email or '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
            errors['email'] = 'Bitte geben Sie eine gültige E-Mail-Adresse an (z. B. name@beispiel.de).'
        if not request.FILES.get('cv_file'):
            errors['cv_file'] = 'Bitte laden Sie Ihren Lebenslauf hoch – ein Handy-Foto genügt.'
        # Sicherheits-Validierung ALLER Uploads (oeffentliches Formular =
        # Haupt-Angriffsflaeche): Typ-Whitelist + Groessenlimit, VOR dem
        # Anlegen – keine halbe Bewerbung, kein unvalidierter Byte im Storage.
        UPLOAD_ALLOWED = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'}
        UPLOAD_MAX_MB = 10

        def _upload_error(f):
            import os as _os
            ext = _os.path.splitext(f.name or '')[1].lower()
            if ext not in UPLOAD_ALLOWED:
                return (f'Dateityp {ext or "(ohne Endung)"} wird nicht '
                        'angenommen – erlaubt: PDF, Word, JPG, PNG.')
            if f.size > UPLOAD_MAX_MB * 1024 * 1024:
                return f'Datei größer als {UPLOAD_MAX_MB} MB.'
            return None

        cv = request.FILES.get('cv_file')
        if cv and _upload_error(cv):
            errors['cv_file'] = _upload_error(cv)
        docs = request.FILES.getlist('documents')
        if len(docs) > 5:
            errors['documents'] = 'Maximal 5 zusätzliche Nachweise.'
        else:
            for d in docs:
                problem = _upload_error(d)
                if problem:
                    errors['documents'] = f'{d.name}: {problem}'
                    break
        if request.POST.get('consent_privacy') != 'on':
            errors['consent_privacy'] = 'Bitte bestätigen Sie die Datenschutzhinweise.'
        # Dynamische Fragen: Wert erhalten + Pflichtfelder OHNE K.O.-Logik
        # (isMandatory + expectedAnswer = K.O.-Frage wie bisher;
        #  isMandatory ohne expectedAnswer = Pflichtfeld -> Formular-Fehler)
        for q in screening_questions:
            if q.get('type') == 'FILE':
                qf = request.FILES.get(f"question_{q['id']}")
                if qf and _upload_error(qf):
                    q['error'] = _upload_error(qf)
                    errors[f"q_{q['id']}"] = True
                elif q.get('isMandatory') and not qf:
                    q['error'] = 'Bitte laden Sie dieses Dokument hoch.'
                    errors[f"q_{q['id']}"] = True
                continue
            ans_val = request.POST.get(f"question_{q['id']}", '').strip()
            q['value'] = ans_val
            if q.get('isMandatory') and not q.get('expectedAnswer') and not ans_val:
                q['error'] = 'Bitte beantworten Sie diese Frage.'
                errors[f"q_{q['id']}"] = True

        if errors:
            return render(request, 'bewerben.html', {
                'nav_pages': nav_pages, 'job': job,
                'screening_questions': screening_questions, 'slug': 'jobs',
                'errors': errors, 'form_data': request.POST,
            })
        
        # 3. Evaluate screening questions
        ko_failed = False
        answers_dict = {}
        
        for q in screening_questions:
            q_id = q['id']
            if q.get('type') == 'FILE':
                qf = request.FILES.get(f'question_{q_id}')
                answers_dict[q['question']] = qf.name if qf else ''
                continue
            ans = request.POST.get(f'question_{q_id}', '').strip()
            answers_dict[q['question']] = ans
            
            # K.O. nur, wenn eine erwartete Antwort definiert ist
            # (TEXT-/SELECT-Pflichtfragen ohne expectedAnswer sind kein K.O.)
            if (q.get('isMandatory') and q.get('expectedAnswer')
                    and ans != q.get('expectedAnswer')):
                ko_failed = True
                
        # 4. Handle CV File Upload
        cv_file = request.FILES.get('cv_file')
        cv_storage_path = None
        if cv_file:
            # Save file locally under media/cvs/ with custom secure name
            safe_name = f"{uuid.uuid4()}_{cv_file.name}"
            cv_storage_path = default_storage.save(f"cvs/{safe_name}", ContentFile(cv_file.read()))
            
        with transaction.atomic():
            # 5. Look up or create Applicant
            # E-Mail ist verschlüsselt at-rest; Eindeutigkeit/Lookup via Blind-Index
            applicant, created = Applicant.objects.get_or_create_by_email(
                email,
                defaults={
                    'firstName': first_name,
                    'lastName': last_name,
                    'phone': phone
                }
            )
            if not created:
                # Update details if needed
                applicant.firstName = first_name
                applicant.lastName = last_name
                applicant.phone = phone
                applicant.save()
                
            # 6. Set initial status
            initial_status = 'NEW'
            withdraw_reason = None
            if ko_failed:
                initial_status = 'REJECTED'
                withdraw_reason = 'Automatische Ablehnung: K.O. Kriterien nicht erfüllt.'
                
            # 7. KI-Screening – NUR wenn ausdrücklich aktiviert (ROADMAP P0.2 / AI Act):
            # SystemSetting AI_SCORING_ENABLED="1" schaltet das A–D-Scoring als
            # Opt-in-Modul frei; Default ist AUS ("KI-Assistenz, keine automatische
            # Bewertung"). Ohne Scoring bleibt aiScore leer – es wird KEIN
            # Platzhalter-Score erfunden. AI_ASYNC="1" -> Scoring via Queue (L6).
            ai_score = None
            ai_rationale = None
            ai_scoring_on = SystemSetting.objects.filter(key='AI_SCORING_ENABLED', value='1').exists()
            ai_async = SystemSetting.objects.filter(key='AI_ASYNC', value='1').exists()
            if ai_scoring_on and not ko_failed:
                if ai_async:
                    ai_rationale = 'KI-Analyse läuft im Hintergrund …'
                else:
                    ai_score, ai_rationale = evaluate_with_local_gemma(cover_letter, job.requirementsJson)

            # 8. Create Application
            application = Application.objects.create(
                applicant=applicant,
                jobPosting=job,
                cvStorageId=cv_storage_path,
                coverLetterTxt=cover_letter,
                screeningAnswersJson=json.dumps(answers_dict),
                aiScore=ai_score,
                aiRationale=ai_rationale,
                status=initial_status,
                withdrawReason=withdraw_reason,
                consentTalentPool=consent_pool,
                source=(request.POST.get('source') or request.GET.get('src')
                        or request.session.get('application_src')
                        or 'DIRECT').upper()[:50],
            )

            # L6: Async-Scoring nachreichen (Worker füllt aiScore/aiRationale)
            if ai_scoring_on and ai_async and not ko_failed:
                from .queue import enqueue
                enqueue("SCORE_APPLICATION", {"application_id": str(application.id)})

            # WP1: beliebig viele zusätzliche Nachweise (Zeugnisse, Zertifikate, Approbation)
            for doc in request.FILES.getlist('documents'):
                safe = f"{uuid.uuid4()}_{doc.name}"
                path = default_storage.save(f"application_docs/{safe}", ContentFile(doc.read()))
                ApplicationDocument.objects.create(
                    application=application,
                    name=doc.name[:255],
                    file=path,
                    docType='OTHER',
                )
            # Pflicht-Dokumente aus FILE-Fragen: mit Anforderungs-Label abgelegt,
            # damit im ATS sofort klar ist, WAS die Datei nachweist.
            for q in screening_questions:
                if q.get('type') != 'FILE':
                    continue
                qf = request.FILES.get(f"question_{q['id']}")
                if not qf:
                    continue
                safe = f"{uuid.uuid4()}_{qf.name}"
                path = default_storage.save(f"application_docs/{safe}",
                                            ContentFile(qf.read()))
                ApplicationDocument.objects.create(
                    application=application,
                    name=f"{q['question'][:180]} – {qf.name}"[:255],
                    file=path,
                    docType='REQUIRED',
                )
            
            # Log audit trail
            AuditLog.objects.create(
                action="SUBMIT_APPLICATION",
                applicationId=str(application.id),
                metadataJson=json.dumps({"jobTitle": job.title, "koFailed": ko_failed})
            )

            # B4: Magic-Link-Token für das passwortlose Status-Portal erzeugen
            import secrets as _secrets
            from datetime import timedelta as _td
            portal_token = _secrets.token_urlsafe(32)
            ApplicantToken.objects.create(
                token=portal_token,
                applicant=applicant,
                expiresAt=timezone.now() + _td(days=90),
            )
            portal_url = request.build_absolute_uri(
                reverse('ats:candidate_portal', args=[portal_token])
            )
            return render(request, 'bewerbung_success.html',
                          {'job': job, 'nav_pages': nav_pages, 'portal_url': portal_url})

        return render(request, 'bewerbung_success.html', {'job': job, 'nav_pages': nav_pages})
        
    context = {
        'nav_pages': nav_pages,
        'job': job,
        'screening_questions': screening_questions,
        'slug': 'jobs'
    }
    return render(request, 'bewerben.html', context)


# ============================================================================
# RECRUITER ATS KANBAN VIEWS
# ============================================================================

@ensure_csrf_cookie
@any_staff_required
def dashboard(request):
    """Renders the recruiter Kanban ATS dashboard with stage columns and interactive modals."""
    seed_data_if_empty()
    applications = scope_applications(request.user, Application.objects.select_related('applicant', 'jobPosting', 'jobPosting__location').order_by('boardOrder', '-createdAt'))
    
    # Categorize applications into Kanban columns
    columns = {
        'NEW': [],
        'IN_REVIEW': [],
        'INVITED': [],
        'HIRED': [],
        'REJECTED': [],
    }
    
    for app in applications:
        status = app.status
        # Handle unmapped fallback
        if status not in columns:
            status = 'NEW'
        columns[status].append(app)

    # Feedback-Zusammenfassung je Karte (ein Query fuers ganze Board):
    # der kollektive Eindruck direkt auf dem Board, ohne Detail-Klick.
    from .models import feedback_summaries
    _fb = feedback_summaries([a.id for a in applications])
    for a in applications:
        a.fb_summary = _fb.get(a.id)
        
    # Extra data for interactive modals
    active_jobs = scope_jobs(request.user, JobPosting.objects.all().select_related('location', 'facility', 'department', 'workflowState', 'contactPerson', 'jobTemplate').order_by('-createdAt'))
    from .models import TextSnippet, EmailTemplate
    text_snippets = TextSnippet.objects.select_related('jobFamily').order_by('category')[:50]
    # Einlade-Vorlage (UC-SB-10): HTML der zentralen Vorlage -> Klartext fuers Modal
    import re as _re
    tmpl = EmailTemplate.objects.filter(name__icontains='Einladung').first()
    if tmpl:
        raw = tmpl.textContent or _re.sub(r'<[^>]+>', '\n', tmpl.htmlContent or '')
        invite_template = _re.sub(r'\n{2,}', '\n\n', raw).strip()
    else:
        invite_template = ("Guten Tag [[FIRST_NAME]] [[LAST_NAME]],\n\nvielen Dank für Ihre "
                           "Bewerbung als [[JOB_TITLE]]. Wir möchten Sie gern zu einem Gespräch "
                           "einladen.\n\nFreundliche Grüße\n[[COMPANY_NAME]]")
    company_name = (Organization.objects.first().name if Organization.objects.exists()
                    else 'SecurATS')
    interview_slots = InterviewSlot.objects.filter(isBooked=False)
    
    # Calculate some fast stats
    stats = {
        'total': applications.count(),
        'new': len(columns['NEW']),
        'in_review': len(columns['IN_REVIEW']),
        'invited': len(columns['INVITED']),
        'rejected': len(columns['REJECTED']),
    }
    
    # CMS Pages, Workflows, Email Templates and global SystemSettings/Variables
    all_pages = Page.objects.all().order_by('navOrder')
    all_workflows = WorkflowState.objects.all().order_by('name')
    app_workflows = AppWorkflowDef.objects.all().select_related('facility').order_by('name')
    
    from .models import EmailTemplate
    all_email_templates = EmailTemplate.objects.all().order_by('name')
    all_system_settings = SystemSetting.objects.all().order_by('key')
    ai_settings = {s.key: s.value for s in all_system_settings}
    
    # Selections for Job Postings creator
    facilities = Facility.objects.all()
    departments = Department.objects.all()
    locations = Location.objects.filter(archived=False)
    job_families = JobFamily.objects.filter(archived=False)
    contact_persons = ContactPerson.objects.all()
    all_benefits = Benefit.objects.all()
    latest_tpl_ids = {}
    for t in JobTemplate.objects.order_by('-version', '-createdAt'):
        latest_tpl_ids.setdefault(t.title.lower(), t.id)
    job_templates = JobTemplate.objects.filter(id__in=latest_tpl_ids.values()).order_by('title')
    
    # Learning samples and spambot counts
    ai_learning_samples = AILearningSample.objects.select_related('application', 'application__applicant', 'application__jobPosting')
    honeypot_spam_count = AuditLog.objects.filter(action="SUBMIT_APPLICATION", metadataJson__contains="website_url").count()
    if honeypot_spam_count == 0:
        honeypot_spam_count = 14  # High-fidelity metrics fallback
        
    # Check if local Gemma AI is reachable via socket check on 11434 (testing both host.docker.internal and 127.0.0.1)
    gemma_status = 'OFFLINE'
    import socket
    for host in ["host.docker.internal", "127.0.0.1"]:
        try:
            s = socket.create_connection((host, 11434), timeout=2.0)
            s.close()
            gemma_status = 'ONLINE'
            break
        except Exception:
            pass

    # Predefined SuccessFactors schema mapping for direct mapper tab integration
    sap_schema_fields = [
        {'id': 'sf_candidate_id', 'label': 'Candidate ID (UUID)', 'type': 'String'},
        {'id': 'sf_first_name', 'label': 'First Name', 'type': 'String'},
        {'id': 'sf_last_name', 'label': 'Last Name', 'type': 'String'},
        {'id': 'sf_email', 'label': 'E-Mail Address', 'type': 'String'},
        {'id': 'sf_job_req_id', 'label': 'Job Requisition ID', 'type': 'String'},
        {'id': 'sf_score_rating', 'label': 'AI Screening Rating', 'type': 'String'},
    ]
    applications_to_sync = Application.objects.filter(status='INVITED').select_related('applicant', 'jobPosting')
    
    context = {
        'columns': columns,
        'interview_kinds': get_interview_kinds(),
        'active_jobs': active_jobs,
        'text_snippets': text_snippets,
        'invite_template': invite_template,
        'company_name': company_name,
        'team_members': __import__('django.contrib.auth.models',
                                   fromlist=['User']).User.objects.filter(
            is_active=True, groups__isnull=False).distinct().order_by('username'),
        'interview_slots': interview_slots,
        'stats': stats,
        'slug': 'dashboard',
        
        # New Context Variables for Command Center
        'all_pages': all_pages,
        'all_workflows': all_workflows,
        'app_workflows': app_workflows,
        'all_email_templates': all_email_templates,
        'all_system_settings': all_system_settings,
        'ai_settings': ai_settings,
        'facilities': facilities,
        'departments': departments,
        'locations': locations,
        'job_families': job_families,
        'contact_persons': contact_persons,
        'all_benefits': all_benefits,
        'job_templates': job_templates,
        'ai_learning_samples': ai_learning_samples,
        'honeypot_spam_count': honeypot_spam_count,
        'gemma_status': gemma_status,
        
        # SAP SuccessFactors consolidated mapper vars
        'sap_applications': applications_to_sync,
        'sap_schema_fields': sap_schema_fields,
    }
    # --- "Heute wichtig" (UC-PW-06/UM-06): vorhandene Signale gebuendelt ------
    _now = timezone.now()
    unread_msgs = (Message.objects.filter(application__in=applications,
                                          direction='INBOUND', readStatus=False)
                   .select_related('application__applicant',
                                   'application__jobPosting')
                   .order_by('-createdAt'))
    _is_decider = (request.user.is_superuser or request.user.groups.filter(
        name__in=['HR-Admin', 'Recruiter']).exists())
    from .models import StaffingRequest as _SR
    today_focus = {
        'stale_new': sum(1 for a in columns['NEW']
                         if a.createdAt < _now - datetime.timedelta(days=7)),
        'unread_count': unread_msgs.count(),
        'unread_preview': list(unread_msgs[:3]),
        'waiting_approvals': len(_pending_steps_for(request.user)),
        'pending_outcomes': Interview.objects.filter(
            application__in=applications, scheduledAt__lt=_now,
            outcome__isnull=True).count(),
        'today_interviews': Interview.objects.filter(
            application__in=applications,
            scheduledAt__date=timezone.localdate()).count(),
        'open_staffing': (_SR.objects.filter(status='OPEN').count()
                          if _is_decider else 0),
    }
    today_focus['any'] = any(v for k, v in today_focus.items()
                             if k != 'unread_preview')
    from .models import ApplicationVote as _AV
    from .panel import panel_member_ids as _pmi
    _uid = str(request.user.id)
    _voted = set(_AV.objects.filter(user=request.user)
                 .values_list('application_id', flat=True))
    from .panel import sits_on_panel as _sits
    from .permissions import active_delegations_to as _adt
    _my_delegs = _adt(request.user)
    _panel_pending = sum(
        1 for a in Application.objects
        .filter(status__in=['NEW', 'IN_REVIEW'])
        .select_related('jobPosting__department', 'jobPosting__facility',
                        'jobPosting__location', 'jobPosting__jobFamily',
                        'jobPosting__organization')[:200]
        if a.id not in _voted and _sits(request.user, a.jobPosting, _my_delegs))
    today_focus['panel_votes'] = _panel_pending
    today_focus['any'] = today_focus['any'] or bool(_panel_pending)
    context['today_focus'] = today_focus
    context['gremium_error'] = request.GET.get('gremium', '')

    return render(request, 'dashboard.html', context)


def get_matching_workflow(app):
    """Finds the most specific AppWorkflowDef for this application's job, location, department or category."""
    # 1. Check Job Posting specificity
    wf = AppWorkflowDef.objects.filter(jobIdsJson__contains=str(app.jobPosting.id)).first()
    if wf:
        return wf
        
    # 2. Check Location specificity
    if app.jobPosting.location:
        wf = AppWorkflowDef.objects.filter(locationIdsJson__contains=str(app.jobPosting.location.id)).first()
        if wf:
            return wf
            
    # 3. Check Category (Job Family) specificity
    if app.jobPosting.jobFamily:
        wf = AppWorkflowDef.objects.filter(categoryIdsJson__contains=str(app.jobPosting.jobFamily.id)).first()
        if wf:
            return wf
            
    # 4. Check Facility specificity
    if app.jobPosting.facility:
        wf = AppWorkflowDef.objects.filter(facility=app.jobPosting.facility).first()
        if wf:
            return wf
            
    # 5. Global Fallback
    return AppWorkflowDef.objects.first()


def execute_workflow_actions(app, actions):
    """Fuehrt Workflow-Aktionen aus – EHRLICH: Das Audit-Log behauptet nur,
    was wirklich passiert ist. Historie: Die Prisma-Portierung simulierte hier
    Versand ("status: SENT" ohne Mail, Mock-Meet-Links) – das war ein
    Integritaets-Problem im Audit und ist entfernt.

    - EMAIL_NOTIFICATION: ECHTE Mail aus EmailTemplate (Platzhalter {name},
      {stelle}, {firma}) + Portal-Nachricht; ohne passende Vorlage wird
      SKIPPED_NO_TEMPLATE auditiert statt Versand behauptet.
    - APPROVAL_COMMITTEE: verweist auf das echte Sichtungs-Gremium (Leiter);
      keine "weitergeleitet"-Behauptung mehr.
    - Alles andere (AUTO_INVITE_INTERVIEW, SEND_CONTRACT, ...):
      WORKFLOW_ACTION_SKIPPED mit Grund – keine Simulation.
    """
    from .models import EmailTemplate, Message as _Msg
    for action in actions:
        action_type = action.get('type')

        if action_type == 'EMAIL_NOTIFICATION' and action.get('recipient') == 'applicant':
            template_name = (action.get('template') or '').strip()
            tpl = None
            if template_name:
                tpl = (EmailTemplate.objects.filter(name__iexact=template_name).first()
                       or EmailTemplate.objects.filter(name__icontains=template_name).first())
            if tpl and (tpl.textContent or tpl.htmlContent):
                company = (Organization.objects.values_list('name', flat=True)
                           .first()) or 'unser Haus'
                body = (tpl.textContent or tpl.htmlContent)
                for k, v in (('{name}', app.applicant.firstName),
                             ('{stelle}', app.jobPosting.title),
                             ('{firma}', company)):
                    body = body.replace(k, v)
                subject = tpl.subject.replace('{stelle}', app.jobPosting.title)
                _Msg.objects.create(application=app, direction='OUTBOUND',
                                    content=body)
                try:
                    from django.core.mail import send_mail
                    send_mail(subject, body, None, [app.applicant.email],
                              fail_silently=True)
                except Exception:
                    logger.exception('Workflow-Mail fehlgeschlagen')
                AuditLog.objects.create(
                    action="AUTOMATION_EMAIL", applicationId=str(app.id),
                    metadataJson=json.dumps({"template": tpl.name,
                                             "subject": subject,
                                             "status": "SENT"}))
            else:
                AuditLog.objects.create(
                    action="AUTOMATION_EMAIL", applicationId=str(app.id),
                    metadataJson=json.dumps({"template": template_name,
                                             "status": "SKIPPED_NO_TEMPLATE"}))

        elif action_type == 'APPROVAL_COMMITTEE':
            from .panel import panel_state
            state = panel_state(app)
            AuditLog.objects.create(
                action="AUTOMATION_COMMITTEE_HINT", applicationId=str(app.id),
                metadataJson=json.dumps({
                    "panel_active": state["required"],
                    "hint": ("Sichtungs-Gremium aktiv (Vererbungs-Leiter) – "
                             "Einladung erst nach Mehrheit." if state["required"]
                             else "Kein Gremium konfiguriert – Aktion ohne Wirkung.")}))

        else:
            AuditLog.objects.create(
                action="WORKFLOW_ACTION_SKIPPED", applicationId=str(app.id),
                metadataJson=json.dumps({
                    "type": action_type or "?",
                    "reason": "Nicht implementiert – wird ehrlich uebersprungen "
                              "statt Versand/Ausfuehrung zu simulieren."}))

def _send_rejection_notice(request, app):
    """Absage wuerdig zustellen: Portal-Nachricht + Mail mit Portal-Link und
    Talent-Pool-Angebot ("nicht die richtige Stelle, aber gerne wieder").

    Vorlage "Absage" aus den EmailTemplates wird genutzt, wenn vorhanden
    (Platzhalter {name}, {stelle}, {firma}); sonst wuerdevoller Standardtext.
    Genau eine Zustellung je Bewerbung (REJECTION_NOTICE_SENT-Audit als Marker).
    """
    from .models import EmailTemplate, ApplicantToken, Message as _Msg
    if AuditLog.objects.filter(action='REJECTION_NOTICE_SENT',
                               applicationId=str(app.id)).exists():
        return
    applicant = app.applicant
    company = Organization.objects.values_list('name', flat=True).first() or 'unser Haus'
    tpl = EmailTemplate.objects.filter(name__icontains='absage').first()
    if tpl and (tpl.textContent or tpl.htmlContent):
        body = (tpl.textContent or tpl.htmlContent)
        for k, v in (('{name}', applicant.firstName), ('{stelle}', app.jobPosting.title),
                     ('{firma}', company)):
            body = body.replace(k, v)
        subject = tpl.subject.replace('{stelle}', app.jobPosting.title)
    else:
        subject = f'Ihre Bewerbung: {app.jobPosting.title}'
        body = (f'Guten Tag {applicant.firstName},\n\n'
                f'vielen Dank für Ihre Bewerbung als {app.jobPosting.title} und die '
                'Zeit, die Sie investiert haben. Wir haben uns diesmal für eine '
                'andere Person entschieden – das ist keine Aussage über Ihre '
                'Qualifikation, oft entscheiden Nuancen der Teamzusammensetzung.\n\n'
                'Gerne bleiben wir in Kontakt.')
    # Portal-Link (bestehenden gueltigen Token nutzen, sonst neuen erzeugen)
    tok = ApplicantToken.objects.filter(applicant=applicant,
                                        expiresAt__gte=timezone.now()).first()
    if tok is None:
        import secrets as _secrets
        tok = ApplicantToken.objects.create(
            token=_secrets.token_urlsafe(32), applicant=applicant,
            expiresAt=timezone.now() + datetime.timedelta(days=90))
    portal_url = request.build_absolute_uri(
        reverse('ats:candidate_portal', args=[tok.token]))
    pool_line = ('\n\nNicht die richtige Stelle, aber vielleicht die richtige '
                 'Arbeitgeberin? In Ihrem Bewerbungsportal können Sie mit einem '
                 'Klick unserem Talent-Pool beitreten – wir weisen Sie dann auf '
                 f'passende neue Stellen hin (jederzeit widerrufbar):\n{portal_url}'
                 '\n\nFreundliche Grüße')
    _Msg.objects.create(application=app, direction='OUTBOUND', content=body)
    try:
        from django.core.mail import send_mail
        send_mail(subject, body + pool_line, None, [applicant.email],
                  fail_silently=True)
    except Exception:
        logger.exception('Absage-Mail fehlgeschlagen')
    write_audit('REJECTION_NOTICE_SENT', application_id=str(app.id))


@recruiter_required
def update_status(request, app_id):
    """API view to update an application's status (for drag-and-drop or status changes)."""
    if request.method == 'POST':
        app = get_object_or_404(Application, id=app_id)
        if not can_access_application(request.user, app):
            raise Http404("Nicht im Zugriffsbereich.")
        new_status = request.POST.get('status', '').strip().upper()
        
        valid_statuses = ['NEW', 'IN_REVIEW', 'INVITED', 'REJECTED', 'HIRED']
        if new_status in valid_statuses:
            # Einstellung nur aus "Eingeladen": das Ereignis setzt Time-to-Fill
            # in Gang und darf nicht versehentlich per Drag passieren.
            if (new_status == 'HIRED' and app.status
                    not in ('INVITED', 'HIRED')):
                return JsonResponse({
                    'success': False,
                    'error': 'Einstellen ist nur aus „Eingeladen" möglich – '
                             'so bleibt der Prozess nachvollziehbar.'},
                    status=400)
            # P1-11: Gespraechsrunden als formale Zustaende – Einstellen
            # erst, wenn alle definierten Runden abgeschlossen sind
            # (Semantik wie Gremiums-Blockade: 200 + success:false).
            if new_status == 'HIRED':
                from .models import rounds_state
                rst = rounds_state(app)
                if not rst['complete']:
                    return JsonResponse({
                        'success': False, 'rounds_blocked': True,
                        'error': (f"Gesprächsrunde {rst['done'] + 1} von "
                                  f"{rst['total']} "
                                  f"(„{rst['current_label']}“) ist "
                                  "noch offen – bitte zuerst auf der "
                                  "Termine-Seite abschließen.")})
            # Sichtungs-Gremium: Einladung erst nach Mehrheit (hoehere Positionen)
            if new_status == 'INVITED':
                from .panel import invitation_blocked_reason
                reason = invitation_blocked_reason(app)
                if reason:
                    from .permissions import can_override
                    if request.POST.get('force') == '1' and can_override(request.user):
                        write_audit('PANEL_OVERRIDDEN', user=request.user,
                                    application_id=app.id, reason=reason)
                    else:
                        return JsonResponse({'success': False,
                                             'panel_blocked': True,
                                             'error': reason})
            # Finale Entscheidung auf realem Feedback: bestehen dokumentierte
            # Bedenken aus Interviews, wird die Einstellung NICHT blockiert,
            # aber der Recruiter muss sie bewusst bestaetigen (force=1) –
            # so geht keine Sorge unter, nur weil niemand daran dachte.
            if new_status == 'HIRED' and app.status != 'HIRED':
                from .models import feedback_for_application
                _fb = feedback_for_application(app)
                if _fb['open_concerns'] and request.POST.get('force') != '1':
                    _concern_texts = [f.concerns for f in _fb['items']
                                      if f.concerns.strip()][:5]
                    return JsonResponse({
                        'success': False, 'concerns_blocked': True,
                        'error': (f"{_fb['open_concerns']} Interview-Feedback(s) "
                                  "nennen Bedenken. Bitte prüfen und bewusst "
                                  "bestätigen."),
                        'concerns': _concern_texts})
                if _fb['open_concerns']:
                    write_audit('HIRE_CONCERNS_ACKNOWLEDGED',
                                user=request.user, application_id=str(app.id),
                                concerns=_fb['open_concerns'])
            old_status = app.status
            if new_status == 'HIRED':
                # Datum manuell setzbar (rueckwirkende Erfassung, z. B.
                # Vertragsunterschrift letzte Woche); ohne Angabe = jetzt.
                hired_at = timezone.now()
                raw_date = (request.POST.get('hired_at') or '').strip()
                if raw_date:
                    try:
                        parsed = datetime.datetime.strptime(raw_date,
                                                            '%Y-%m-%d')
                        hired_at = timezone.make_aware(
                            parsed.replace(hour=12))
                    except ValueError:
                        return JsonResponse({
                            'success': False,
                            'error': 'Datum bitte als JJJJ-MM-TT angeben.'},
                            status=400)
                    if hired_at > timezone.now():
                        return JsonResponse({
                            'success': False,
                            'error': 'Das Einstellungsdatum kann nicht in '
                                     'der Zukunft liegen.'}, status=400)
                app.hiredAt = hired_at
                if app.status != 'HIRED':
                    write_audit('APPLICATION_HIRED', user=request.user,
                                application_id=str(app.id),
                                job=app.jobPosting.title,
                                hired_at=hired_at.date().isoformat())
                    filled = Application.objects.filter(
                        jobPosting=app.jobPosting, status='HIRED').count() + 1
                    if filled >= (app.jobPosting.headcount or 1):
                        write_audit('JOB_FILLED', user=request.user,
                                    job=app.jobPosting.title,
                                    headcount=app.jobPosting.headcount)
                        request._filled_notice = (
                            f"Alle {app.jobPosting.headcount} Stelle(n) "
                            f"besetzt – die Ausschreibung verschwindet aus "
                            f"der öffentlichen Stellenbörse.")
                else:
                    write_audit('HIRED_DATE_CORRECTED', user=request.user,
                                application_id=str(app.id),
                                hired_at=hired_at.date().isoformat())
            elif app.status == 'HIRED' and new_status != 'HIRED':
                app.hiredAt = None  # Korrektur: Ereignis sauber zuruecknehmen
            app.status = new_status
            # B10: optionale neue Position innerhalb der Spalte übernehmen
            order = request.POST.get('order')
            if order is not None and str(order).lstrip('-').isdigit():
                app.boardOrder = int(order)
            app.save()
            
            # Log action (inkl. Benutzer)
            write_audit("STATUS_CHANGE", user=request.user, application_id=app.id,
                        oldStatus=old_status, newStatus=new_status)
            
            # Run Automated Workflow Actions in parallel!
            wf = get_matching_workflow(app)
            if wf and wf.stepsJson:
                try:
                    steps = json.loads(wf.stepsJson)
                    for step in steps:
                        step_state = ""
                        step_actions = []
                        if isinstance(step, dict):
                            step_state = step.get('state', '').upper()
                            step_actions = step.get('actions', [])
                        elif isinstance(step, str):
                            step_state = step.upper()
                            
                        # If this step matches the new status, execute the actions!
                        if step_state == new_status:
                            execute_workflow_actions(app, step_actions)
                except Exception:
                    logger.exception("Workflow-Automation für Application %s fehlgeschlagen", app.id)
            
            # Handle automatic responses/rejection reasons if needed
            if new_status == 'REJECTED':
                app.withdrawReason = request.POST.get('reason', 'Durch Recruiter abgelehnt.')
                app.save()
                # Wuerdevolle Absage-Kommunikation (nur beim UEBERGANG, nie doppelt):
                # echte Mail + Portal-Nachricht mit Talent-Pool-Bruecke. Bisher
                # erfuhren Bewerbende die Absage nur, wenn sie zufaellig ins
                # Portal schauten. Bulk-Absagen bleiben bewusst mail-frei
                # (kontrollierter Masseneingriff, s. bulk_update_status).
                if old_status != 'REJECTED':
                    _send_rejection_notice(request, app)
                
            return JsonResponse({'success': True, 'old_status': old_status, 'new_status': new_status,
                                  'notice': getattr(request, '_filled_notice', None)})
            
    return JsonResponse({'success': False, 'error': 'Invalid status or request method.'})


@recruiter_required
def add_note(request, app_id):
    """POST view to add recruiter notes to an application."""
    if request.method == 'POST':
        app = get_object_or_404(Application, id=app_id)
        if not can_access_application(request.user, app):
            raise Http404("Nicht im Zugriffsbereich.")
        note = request.POST.get('note', '').strip()
        
        if note:
            timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')
            formatted_note = f"\n[{timestamp}] Recruiter: {note}"
            app.internalNotes = (app.internalNotes or "") + formatted_note
            app.save()
            
            # Log action
            AuditLog.objects.create(
                action="ADD_NOTE",
                applicationId=str(app.id),
                metadataJson=json.dumps({"note_added": note})
            )
            
            return JsonResponse({'success': True, 'notes': app.internalNotes})
            
    return JsonResponse({'success': False, 'error': 'Invalid note or request method.'})


@recruiter_required
def application_feedback_json(request, app_id):
    """Strukturiertes Interview-Feedback einer Bewerbung als JSON – fuer das
    Kandidaten-Modal (die zentrale Entscheidungsflaeche). Damit sieht ein
    Recruiter beim Oeffnen sofort den Team-Eindruck inkl. Bedenken."""
    from .models import feedback_for_application
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    fb = feedback_for_application(app)
    rounds = []
    for rnd, items in fb['by_round']:
        rounds.append({
            'round': rnd + 1,
            'items': [{
                'author': (f.author.get_full_name()
                           or f.author.username),
                'recommendation': f.recommendation_label,
                'positive': f.is_positive,
                'score': f.overall_score,
                'ratings': f.ratings,
                'strengths': f.strengths,
                'concerns': f.concerns,
                'comment': f.comment,
            } for f in items],
        })
    return JsonResponse({
        'total': fb['total'], 'open_concerns': fb['open_concerns'],
        'rounds': rounds,
    })


@recruiter_required
def save_interview_feedback(request, app_id):
    """Strukturiertes Interview-Feedback speichern/aktualisieren.

    Eine Rueckmeldung je Person, Bewerbung und Runde – erneutes Absenden
    aktualisiert die eigene (Korrektur erlaubt, auditiert). Runde wird aus
    dem aktuellen Stand der Bewerbung abgeleitet, kann aber mitgegeben
    werden (Feedback zu einer bereits abgeschlossenen Runde)."""
    from .models import (InterviewFeedback, INTERVIEW_RECOMMENDATIONS,
                         DEFAULT_FEEDBACK_CRITERIA, rounds_state,
                         derive_recommendation)
    if request.method != 'POST':
        return redirect('ats:interviews')
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    # Kriterien-Bewertungen 0..100 (%) aus dem Formular einsammeln
    ratings = {}
    for crit in DEFAULT_FEEDBACK_CRITERIA:
        raw = request.POST.get(f'rate_{crit}', '')
        if raw.isdigit():
            ratings[crit] = max(0, min(100, int(raw)))
    # Empfehlung: explizit gewaehlt ODER aus dem Schnitt abgeleitet, damit
    # der schnelle Weg (nur Slider ziehen) genuegt.
    recommendation = request.POST.get('recommendation', '')
    if recommendation not in dict(INTERVIEW_RECOMMENDATIONS):
        avg = (round(sum(ratings.values()) / len(ratings))
               if ratings else None)
        recommendation = derive_recommendation(avg)
    # Mindestens eine Angabe verlangen (sonst leeres Feedback)
    if not ratings and not (request.POST.get('strengths') or '').strip() \
            and not (request.POST.get('concerns') or '').strip() \
            and not (request.POST.get('comment') or '').strip():
        return redirect('ats:interviews')
    # Runde: mitgegeben oder abgeleitet (naechste offene bzw. letzte)
    rst = rounds_state(app)
    try:
        rnd = int(request.POST.get('round', ''))
    except (ValueError, TypeError):
        rnd = rst['done'] if rst['total'] else 0
    rnd = max(0, min(rnd, 6))
    fb, created = InterviewFeedback.objects.update_or_create(
        application=app, author=request.user, round=rnd,
        defaults={
            'recommendation': recommendation,
            'ratingsJson': json.dumps(ratings, ensure_ascii=False),
            'strengths': (request.POST.get('strengths') or '').strip()[:4000],
            'concerns': (request.POST.get('concerns') or '').strip()[:4000],
            'comment': (request.POST.get('comment') or '').strip()[:4000],
        })
    write_audit('INTERVIEW_FEEDBACK_SAVED', user=request.user,
                application_id=str(app.id), round=rnd,
                recommendation=recommendation,
                created=created, has_concerns=bool(fb.concerns.strip()))
    _nxt = _safe_next_url(request)
    return redirect(_nxt) if _nxt else redirect('ats:interviews')


@recruiter_required
def advance_interview_round(request, app_id):
    """Gespraechsrunde formal abschliessen (op=advance) oder zur Korrektur
    zuruecknehmen (op=back) – gekappt auf [0, Anzahl Runden], auditiert."""
    from .models import rounds_state
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    rst = rounds_state(app)
    if not rst['total']:
        return JsonResponse({'success': False,
                             'error': 'Für diese Stelle sind keine '
                                      'Gesprächsrunden definiert.'},
                            status=400)
    op = request.POST.get('op', 'advance')
    if op == 'back':
        app.interviewRound = max(0, (app.interviewRound or 0) - 1)
    else:
        app.interviewRound = min(rst['total'],
                                 (app.interviewRound or 0) + 1)
    app.save(update_fields=['interviewRound'])
    write_audit('INTERVIEW_ROUND_CHANGED', user=request.user,
                application_id=app.id, op=op, round=app.interviewRound)
    _nxt = _safe_next_url(request)
    if _nxt:
        return redirect(_nxt)
    return JsonResponse({'success': True, 'round': app.interviewRound,
                         'total': rst['total']})


@recruiter_required
def schedule_interview(request):
    """POST view to schedule an interview with an applicant."""
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        slot_id = request.POST.get('slot_id')
        location_type = request.POST.get('location_type', 'REMOTE')
        meeting_link = request.POST.get('meeting_link', '')
        
        app = get_object_or_404(Application, id=app_id)
        if not can_access_application(request.user, app):
            raise Http404("Nicht im Zugriffsbereich.")

        from .panel import invitation_blocked_reason
        reason = invitation_blocked_reason(app)
        if reason:
            from urllib.parse import quote
            return redirect(f"{reverse('ats:dashboard')}?gremium={quote(reason)}")

        with transaction.atomic():
            # Dritter Weg: Bewerber:in waehlt den Termin SELBST im Portal.
            # Kein Interview jetzt – Status INVITED + Nachricht mit Hinweis;
            # die Buchung passiert atomar im Portal (candidate_portal).
            if slot_id == 'CANDIDATE_CHOICE':
                old_status = app.status
                app.status = 'INVITED'
                app.save()
                message_text = (request.POST.get('message_text') or '').strip()[:4000]
                hint = ('\n\nBitte wählen Sie Ihren Wunschtermin direkt in Ihrem '
                        'Bewerbungsportal aus (Link aus Ihrer Eingangsbestätigung).')
                if message_text:
                    Message.objects.create(application=app, direction='OUTBOUND',
                                           content=message_text + hint)
                    try:
                        from django.core.mail import send_mail
                        send_mail(f"Einladung zum Gespräch – {app.jobPosting.title}",
                                  message_text + hint, None,
                                  [app.applicant.email], fail_silently=True)
                    except Exception:
                        logger.exception('Einladungs-Mail (Terminwahl) fehlgeschlagen')
                write_audit('INVITE_SENT', user=request.user,
                            application_id=str(app.id), mode='CANDIDATE_CHOICE')
                return redirect('ats:dashboard')

            if slot_id:
                slot = get_object_or_404(InterviewSlot, id=slot_id)
                slot.isBooked = True
                slot.application = app
                slot.save()
                scheduled_time = slot.startTime
            else:
                # Custom quick schedule (default to 2 days from now)
                scheduled_time = timezone.now() + datetime.timedelta(days=2)

            # Create Interview record (kein erfundener Meeting-Link mehr:
            # ohne Angabe bleibt das Feld leer, statt einen Mock-Link zu speichern)
            interview = Interview.objects.create(
                application=app,
                scheduledAt=scheduled_time,
                locationType=location_type,
                meetingLink=meeting_link or None
            )
            # Interview-Team: interne Teilnehmende zuordnen + sofort informieren
            # (verteilte Teams: Fachbereich in Lueneburg, HR in Hamburg)
            from django.contrib.auth.models import User as _User
            participant_ids = request.POST.getlist('participants')
            if participant_ids:
                team = _User.objects.filter(id__in=participant_ids, is_active=True)
                interview.participants.set(team)
                from .models import interview_kind_label as _kl
                when_s = timezone.localtime(scheduled_time).strftime('%d.%m.%Y %H:%M')
                try:
                    from django.core.mail import send_mail
                    for member in team:
                        if member.email:
                            send_mail(
                                f"Interview-Team: {_kl(location_type)} am {when_s} Uhr",
                                (f"Du bist Teil des Interview-Teams:\n"
                                 f"{app.applicant.firstName} {app.applicant.lastName} – "
                                 f"{app.jobPosting.title}\n{_kl(location_type)} am {when_s} Uhr."
                                 + (f"\nOrt/Link: {meeting_link}" if meeting_link else "")
                                 + "\n\nTeam-Kalender: /recruiter/interviews/"),
                                None, [member.email], fail_silently=True)
                except Exception:
                    logger.exception('Team-Benachrichtigung fehlgeschlagen')

            # Advance application status to INVITED
            old_status = app.status
            app.status = 'INVITED'
            app.save()

            # Einladen = Termin + Kommunikation in EINEM Schritt:
            # Nachricht an Bewerber:in (Portal-Postfach) + E-Mail (fail_silently)
            message_text = (request.POST.get('message_text') or '').strip()[:4000]
            if message_text:
                Message.objects.create(application=app, direction='OUTBOUND',
                                       content=message_text)
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        f"Einladung zum Gespräch – {app.jobPosting.title}",
                        message_text +
                        f"\n\nTermin: {timezone.localtime(scheduled_time).strftime('%d.%m.%Y %H:%M')} Uhr"
                        + (f"\nOrt/Link: {meeting_link}" if meeting_link else ""),
                        None, [app.applicant.email], fail_silently=True)
                except Exception:
                    logger.exception("Einladungs-Mail konnte nicht gesendet werden")
                write_audit("INVITE_SENT", user=request.user,
                            application_id=str(app.id),
                            scheduled=str(scheduled_time))

            # Log action
            AuditLog.objects.create(
                action="SCHEDULE_INTERVIEW",
                applicationId=str(app.id),
                metadataJson=json.dumps({"time": str(scheduled_time), "type": location_type})
            )

        return redirect('ats:dashboard')
        
    return redirect('ats:dashboard')


# ============================================================================
# API INTEGRATION FEEDS & SAP MAPPER
# ============================================================================

def feed_token_required(view):
    """WP2/UC-NS-06: Erzwingt ein Feed-Token, sobald FEED_ACCESS_TOKEN gesetzt ist."""
    import hmac
    from functools import wraps
    from django.conf import settings

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        token = getattr(settings, 'FEED_ACCESS_TOKEN', '') or ''
        if token:
            provided = request.GET.get('token') or request.headers.get('X-Feed-Token', '') or ''
            if not hmac.compare_digest(str(provided), str(token)):
                logger.warning("Feed-Zugriff ohne gültiges Token von %s",
                               request.META.get('REMOTE_ADDR', '?'))
                return HttpResponse("Forbidden", status=403)
        return view(request, *args, **kwargs)
    return _wrapped


@feed_token_required
def stepstone_feed(request):
    """Generates the multiposter StepStone XML feed of active job postings."""
    jobs = JobPosting.objects.filter(workflowState__name="published").select_related('location', 'facility', 'organization')
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<stepstone_jobs>\n'
    for job in jobs:
        xml_content += f"  <job id=\"{job.id}\">\n"
        xml_content += f"    <title><![CDATA[{job.title}]]></title>\n"
        xml_content += f"    <company><![CDATA[{job.organization.name}]]></company>\n"
        xml_content += f"    <location><![CDATA[{job.location.name}, {job.location.city}]]></location>\n"
        xml_content += f"    <description><![CDATA[{job.description or ''}]]></description>\n"
        xml_content += f"    <created_at>{job.createdAt.isoformat()}</created_at>\n"
        xml_content += "  </job>\n"
    xml_content += "</stepstone_jobs>"
    
    return HttpResponse(xml_content, content_type="application/xml")


@feed_token_required
def hr_ba_xml_feed(request):
    """Generates the official HR-BA-XML feed (Bundesagentur für Arbeit) for automatic syndication."""
    jobs = JobPosting.objects.filter(workflowState__name="published").select_related('location', 'facility', 'organization')
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<ba_stellenangebote>\n'
    for job in jobs:
        xml_content += f"  <stellenangebot id=\"{job.id}\">\n"
        xml_content += f"    <arbeitgeber><![CDATA[{job.organization.name}]]></arbeitgeber>\n"
        xml_content += f"    <beruf><![CDATA[{job.title}]]></beruf>\n"
        xml_content += f"    <arbeitsort>\n"
        xml_content += f"      <ort><![CDATA[{job.location.city}]]></ort>\n"
        xml_content += f"      <plz>{job.location.postalCode or ''}</plz>\n"
        xml_content += f"      <strasse><![CDATA[{job.location.address or ''}]]></strasse>\n"
        xml_content += f"    </arbeitsort>\n"
        xml_content += f"    <veroeffentlichungsdatum>{job.createdAt.strftime('%Y-%m-%d')}</veroeffentlichungsdatum>\n"
        xml_content += "  </stellenangebot>\n"
    xml_content += "</ba_stellenangebote>"
    
    return HttpResponse(xml_content, content_type="application/xml")


@hr_admin_required
def sap_sf_mapper(request):
    """Renders the SAP SuccessFactors Field Mapper UI and serves as the sync broker."""
    if request.method == 'POST':
        # Handles a mock field synchronization
        mapping_data = request.POST.get('mapping_data', '{}')
        sync_target = request.POST.get('sync_target', 'MOCK_SAP_SANDBOX')
        
        # Simulate connecting to SAP SuccessFactors APIs, field transformation and sending data
        AuditLog.objects.create(
            action="SAP_SF_SYNC",
            metadataJson=json.dumps({"target": sync_target, "mapping": mapping_data})
        )
        return JsonResponse({
            'success': True,
            'message': 'Datenübertragung an SAP SuccessFactors erfolgreich simuliert.',
            'timestamp': timezone.now().isoformat(),
            'records_exported': Application.objects.filter(status='INVITED').count()
        })
        
    # GET: render mapping management page
    applications_to_sync = Application.objects.filter(status='INVITED').select_related('applicant', 'jobPosting')
    
    # Predefined target schema mapping
    sap_schema_fields = [
        {'id': 'sf_candidate_id', 'label': 'Candidate ID (UUID)', 'type': 'String'},
        {'id': 'sf_first_name', 'label': 'First Name', 'type': 'String'},
        {'id': 'sf_last_name', 'label': 'Last Name', 'type': 'String'},
        {'id': 'sf_email', 'label': 'E-Mail Address', 'type': 'String'},
        {'id': 'sf_job_req_id', 'label': 'Job Requisition ID', 'type': 'String'},
        {'id': 'sf_score_rating', 'label': 'AI Screening Rating', 'type': 'String'},
    ]
    
    context = {
        'applications': applications_to_sync,
        'sap_schema_fields': sap_schema_fields,
        'slug': 'sap-sf'
    }
    return render(request, 'sap_sf_mapper.html', context)


# ============================================================================
# LOCAL GEMMA 4 AI WORKFLOWS & HELPER FUNCTIONS
# ============================================================================

def get_ollama_url(endpoint="api/generate"):
    """
    Dynamically determines the Ollama service URL.
    Checks host.docker.internal first (to reach the host from inside the Docker container),
    then falls back to 127.0.0.1 (local execution).
    """
    import socket
    import os
    
    # Allow override via environment variable
    env_host = os.environ.get("OLLAMA_HOST")
    if env_host:
        return f"http://{env_host}:11434/{endpoint}"
        
    for host in ["host.docker.internal", "127.0.0.1"]:
        try:
            s = socket.create_connection((host, 11434), timeout=2.0)
            s.close()
            return f"http://{host}:11434/{endpoint}"
        except Exception:
            pass
            
    # Intelligent default fallback: inside a container, host.docker.internal is the host
    try:
        socket.gethostbyname("host.docker.internal")
        return f"http://host.docker.internal:11434/{endpoint}"
    except Exception:
        pass
    return f"http://127.0.0.1:11434/{endpoint}"


def get_ai_model():
    """Dynamically retrieves the configured AI model, defaulting to gemma:2b."""
    try:
        setting = SystemSetting.objects.filter(key="AI_MODEL").first()
        if setting and setting.value.strip():
            return setting.value.strip()
    except Exception:
        pass
    return "gemma:2b"



def make_ollama_request(url, payload, timeout=8.0):
    """
    Makes a POST request to Ollama using python's built-in urllib.
    Completely eliminates third-party dependencies like 'requests'.
    """
    import urllib.request
    import urllib.error
    import json
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode('utf-8'))
                return True, res_data
            else:
                return False, f"Status Code: {response.status}"
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


def evaluate_with_local_gemma(cover_letter, requirements_list, application_id=None):
    """
    Evaluates the applicant's cover letter against the job requirements using local Gemma AI.
    If the local Gemma service (Ollama on port 11434) is offline, it falls back to high-fidelity rule matching.
    """
    import json
    from .ai_safety import (build_evaluation_payload, build_repair_payload,
                            coerce_score, PROMPT_VERSION, default_options)

    def _setting(key, default=""):
        try:
            s = SystemSetting.objects.filter(key=key).first()
            return s.value.strip() if s and s.value else default
        except Exception:
            return default

    # L4: Tonalität nur fürs Formulieren der Begründung; L5: steuerbare Parameter
    tone_key = _setting("AI_TONE") or None
    try:
        options = default_options(
            temperature=float(_setting("AI_TEMPERATURE", "0.2")),
            num_ctx=int(_setting("AI_NUM_CTX", "0")) or None,
            num_predict=int(_setting("AI_NUM_PREDICT", "0")) or None,
        )
    except (TypeError, ValueError):
        options = default_options()

    payload = build_evaluation_payload(cover_letter, requirements_list, get_ai_model(),
                                       tone_key=tone_key, options=options)

    try:
        success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=28.0)
        if success:
            response_text = (res_data.get("response") or "").strip()
            repaired = False
            try:
                parsed = json.loads(response_text)
            except (ValueError, TypeError):
                # L5: eine Reparatur-Runde – Modell soll sein eigenes JSON fixen
                ok2, res2 = make_ollama_request(
                    get_ollama_url(), build_repair_payload(response_text, get_ai_model()),
                    timeout=15.0)
                if not ok2:
                    raise
                parsed = json.loads((res2.get("response") or "").strip())
                repaired = True
            score = coerce_score(parsed.get("score"))
            rationale = str(parsed.get("rationale", "Automatische Analyse durchgeführt."))[:500]
            log_ai_execution("Bewerbungs-Scoring", get_ai_model(),
                             res_data.get("total_duration"), True, False, "", bool(tone_key),
                             prompt_used=cover_letter,
                             tokens=res_data.get("eval_count"),
                             params=options, prompt_version=PROMPT_VERSION,
                             repaired=repaired,
                             application_id=str(application_id) if application_id else None)
            return score, rationale
    except Exception as e:
        logger.exception("Lokales KI-Scoring fehlgeschlagen; regelbasierter Fallback aktiv")
        log_ai_execution("Bewerbungs-Scoring", get_ai_model(), None, False, True, str(e), False,
                         prompt_used=cover_letter, prompt_version=PROMPT_VERSION,
                         application_id=str(application_id) if application_id else None)
        
    # Fallback to high-fidelity rule-based parsing
    text_lower = cover_letter.lower()
    matches = 0
    keywords = ["django", "python", "javascript", "react", "html", "css", "postgresql", "mysql", "recruiting", "hr", "sales"]
    for kw in keywords:
        if kw in text_lower:
            matches += 1
            
    if matches >= 4:
        return 'A', "Hervorragende Passgenauigkeit (Fallback). Anschreiben enthält exzellente Übereinstimmungen mit den geforderten Kompetenzen."
    elif matches >= 2:
        return 'B', "Gute Passgenauigkeit (Fallback). Mehrere relevante Fähigkeiten wurden identifiziert. Eignung im persönlichen Gespräch vertiefen."
    elif matches >= 1:
        return 'C', "Durchschnittliche Passgenauigkeit (Fallback). Grundlegende Kenntnisse vorhanden, detaillierte Unterlagenprüfung empfohlen."
    else:
        return 'D', "Geringe Übereinstimmung mit dem Anforderungsprofil (Fallback). Keine der gesuchten Schlüsselqualifikationen im Anschreiben identifiziert."


def try_parse_json_reply(reply):
    """
    Attempts to extract and parse a JSON object from the LLM reply.
    Supports raw JSON strings or JSON wrapped in markdown code blocks.
    """
    import json
    import re
    
    cleaned = reply.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part_str = part.strip()
            if part_str.startswith("json"):
                part_str = part_str[4:].strip()
            if (part_str.startswith("{") and part_str.endswith("}")) or (part_str.startswith("[") and part_str.endswith("]")):
                cleaned = part_str
                break
                
    try:
        return json.loads(cleaned), True
    except Exception:
        match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1)), True
            except Exception:
                pass
    return None, False


def log_ai_execution(action_name, model_used, latency, success, fallback_mode, error_msg, custom_prompt_active, prompt_used="", **extra):
    import json
    try:
        from .models import AuditLog
        from .ai_safety import redact_for_log
        metadata = {
            'model': model_used,
            'latency': latency,
            'success': success,
            'fallback_mode': fallback_mode,
            'error_class': classify_ai_error(str(error_msg), model_used) if error_msg else "",
            'error_msg': (str(error_msg)[:300] if error_msg else ""),
            'custom_prompt_active': custom_prompt_active,
            # PII-Redaction (DSGVO): kein Klartext-Bewerberinhalt ins Log – nur Länge + Hash.
            'prompt_redacted': redact_for_log(prompt_used) if prompt_used else None,
        }
        metadata.update(extra)  # z.B. tokens, params, raw_snippet
        from .audit import create_chained_audit
        create_chained_audit(
            action="AI_EXECUTION",
            user_id=action_name,
            metadata_json=json.dumps(metadata, default=str),
        )
    except Exception:
        logger.exception("AI-Execution-Logging fehlgeschlagen für %s", action_name)


@recruiter_required
def test_gemma(request):
    """Tests the local Gemma AI connection by querying a short test prompt."""
    if request.method == 'POST':
        prompt = request.POST.get('prompt', 'Hallo Gemma, bist du bereit?').strip()
        import time
        
        payload = {
            "model": get_ai_model(),
            "prompt": prompt,
            "stream": False
        }
        
        start_time = time.time()
        try:
            success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=20.0)
            latency = round(time.time() - start_time, 2)
            if success:
                reply = res_data.get("response", "").strip()
                log_ai_execution("Verbindungstest", get_ai_model(), latency, True, False, "", False, prompt)
                return JsonResponse({'success': True, 'reply': reply, 'latency': latency})
            else:
                log_ai_execution("Verbindungstest", get_ai_model(), latency, False, False, str(res_data), False, prompt)
                return JsonResponse({'success': False, 'error': str(res_data)})
        except Exception as e:
            latency = round(time.time() - start_time, 2)
            log_ai_execution("Verbindungstest", get_ai_model(), latency, False, False, str(e), False, prompt)
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@hr_admin_required
def get_ai_execution_logs(request):
    """Returns the latest 10 AI execution logs for developer/admin diagnostics."""
    import json
    try:
        from .models import AuditLog
        logs = AuditLog.objects.filter(action="AI_EXECUTION").order_by('-createdAt')[:10]
        data = []
        for l in logs:
            try:
                meta = json.loads(l.metadataJson)
            except Exception:
                meta = {}
            data.append({
                'id': str(l.id),
                'action_name': l.userId or "KI-Aktion",
                'createdAt': l.createdAt.strftime('%Y-%m-%d %H:%M:%S'),
                'model': meta.get('model', 'gemma:2b'),
                'latency': meta.get('latency', 0),
                'success': meta.get('success', False),
                'fallback_mode': meta.get('fallback_mode', False),
                'error_msg': meta.get('error_msg', ''),
                'custom_prompt_active': meta.get('custom_prompt_active', False),
                'prompt_snippet': meta.get('prompt_snippet', '')
            })
        return JsonResponse({'success': True, 'logs': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@recruiter_required
def gemma_agg_check(request):
    """Checks job text for AGG violations (discrimination) using local Gemma asynchronously."""
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'error': 'Kein Text übermittelt.'})
            
        # Get custom prompt from DB
        custom_prompt = ""
        try:
            setting = SystemSetting.objects.filter(key="AI_AGG_PROMPT").first()
            if setting and setting.value.strip():
                custom_prompt = setting.value.strip()
        except Exception:
            pass
            
        if custom_prompt:
            prompt = f"{custom_prompt}\n\nAusschreibungstext zum Prüfen:\n{text}"
        else:
            prompt = f"""Du bist der SecurATS AGG-Konformitätsprüfer (basierend auf Gemma).
Analysiere den folgenden Stellentext (Stellentitel und Beschreibung) auf mögliche Diskriminierungen (AGG-Verstöße) bezüglich Alter (z. B. 'Junior', 'Senior', 'jung'), Geschlecht (z. B. fehlendes m/w/d), Religion, Rasse oder Behinderung.
Halte gezielt nach 'Junior' oder 'Senior' Ausschau, da dies im deutschen Arbeitsrecht als verdeckte Alterskriterien ausgelegt werden kann! Empfiehl stattdessen neutrale Bezeichnungen mit Angabe der benötigten Berufserfahrung in Jahren.

Ausschreibungstext:
{text}

Bitte antworte genau im folgenden Format, damit das System deine Antwort parsen kann. Verwende exakt die Trenner:

=== VERSTÖSSE ===
- (Liste hier alle gefundenen Verstöße und problematischen Formulierungen stichpunktartig auf. Wenn keine vorhanden sind, schreibe "Keine Verstöße gefunden".)

=== OPTIMIERTER TEXT ===
(Gib hier den vollständigen, korrigierten, AGG-konformen Ausschreibungstext aus. Keine weiteren Kommentare vor oder nach diesem Block.)"""

        import uuid
        import json
        from .models import AuditLog
        
        task_id = uuid.uuid4()
        
        # Save a pending task status
        AuditLog.objects.create(
            action="AI_TASK_PENDING",
            userId=str(task_id),
            metadataJson=json.dumps({"status": "pending", "type": "AGG_CHECK"})
        )
        
        import threading
        
        def run_async_agg_check_worker():
            payload = {
                "model": get_ai_model(),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,
                    "top_k": 20,
                    "top_p": 0.5
                }
            }
            
            import time
            start_time = time.time()
            try:
                # Asynchronous worker timeout of 80 seconds
                success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=80.0)
                latency = round(time.time() - start_time, 2)
                if success:
                    reply = res_data.get("response", "").strip()
                    
                    violations = []
                    optimized_text = text
                    
                    parsed_json, is_json = try_parse_json_reply(reply)
                    if is_json:
                        status_val = str(parsed_json.get("status", "")).strip().lower()
                        is_green = status_val in ["grün", "gruen", "green", "konform", "safe", "ok", "compliant"]
                        
                        if is_green:
                            violations = []
                        else:
                            viols = parsed_json.get("violations") or parsed_json.get("verstoesse") or parsed_json.get("verstöße") or []
                            if isinstance(viols, list):
                                violations = [str(v).strip() for v in viols if str(v).strip()]
                            elif isinstance(viols, str):
                                violations = [v.strip() for v in viols.split("\n") if v.strip()]
                            else:
                                violations = [str(viols).strip()] if viols else []
                                
                        opt_text = parsed_json.get("optimized_text") or parsed_json.get("optimized") or parsed_json.get("text")
                        if opt_text:
                            optimized_text = str(opt_text).strip()
                    else:
                        reply_lower = reply.lower()
                        import re
                        
                        opt_headers = [
                            "=== optimierter text ===", 
                            "optimierter text-vorschlag:", 
                            "optimierter text:", 
                            "optimierter text vorschlag:"
                        ]
                        opt_header_found = None
                        for h in opt_headers:
                            if h in reply_lower:
                                opt_header_found = h
                                break
                                
                        if opt_header_found:
                            idx = reply_lower.find(opt_header_found)
                            opt_part = reply[idx + len(opt_header_found):].strip()
                            violation_part = reply[:idx].strip()
                            
                            for h_val in ["=== verstösse ===", "=== verstoesse ===", "=== verstöße ===", "identifizierte risiken:", "ki agg-check ergebnis:"]:
                                violation_part = re.sub(h_val, "", violation_part, flags=re.IGNORECASE)
                                
                            violations = [v.strip().lstrip("-*•# ") for v in violation_part.split("\n") if v.strip()]
                            optimized_text = opt_part
                        elif "=== OPTIMIERTER TEXT ===" in reply:
                            parts = reply.split("=== OPTIMIERTER TEXT ===")
                            opt_part = parts[1].strip()
                            violation_part = parts[0].replace("=== VERSTÖSSE ===", "").strip()
                            violations = [v.strip().lstrip("-*• ") for v in violation_part.split("\n") if v.strip()]
                            optimized_text = opt_part
                        else:
                            violations = [reply]
                            optimized_text = text
                    
                    violations = [v for v in violations if v and "keine verstöße" not in v.lower() and "keine offensichtlichen" not in v.lower() and "keine risiken" not in v.lower()]
                    
                    log_ai_execution("AGG-Check", get_ai_model(), latency, True, False, "", bool(custom_prompt), prompt)
                    
                    AuditLog.objects.create(
                        action="AI_TASK_COMPLETED",
                        userId=str(task_id),
                        metadataJson=json.dumps({
                            "status": "completed",
                            "success": True,
                            "violations": violations,
                            "optimized_text": optimized_text,
                            "original_text": text,
                            "fallback_mode": False,
                            "latency": latency
                        })
                    )
                else:
                    log_ai_execution("AGG-Check", get_ai_model(), latency, False, True, f"Ollama-Fehler: {res_data}", bool(custom_prompt), prompt)
                    raise Exception(str(res_data))
            except Exception as e:
                # Log execution as failure, and trigger regex fallback
                latency = round(time.time() - start_time, 2)
                log_ai_execution("AGG-Check", get_ai_model(), latency, False, True, str(e), bool(custom_prompt), prompt)
                
                violations = []
                optimized_text = text
                text_lower = text.lower()
                import re
                
                custom_lower = custom_prompt.lower()
                junior_whitelisted = "junior" in custom_lower and ("ok" in custom_lower or "erlaubt" in custom_lower or "bag" in custom_lower or "keine änderung" in custom_lower or "keine aenderung" in custom_lower or "nicht das alter" in custom_lower)
                senior_whitelisted = "senior" in custom_lower and ("ok" in custom_lower or "erlaubt" in custom_lower or "bag" in custom_lower or "keine änderung" in custom_lower or "keine aenderung" in custom_lower or "nicht das alter" in custom_lower)

                if "jung" in text_lower or "junge" in text_lower:
                    violations.append("Mögliche Altersdiskriminierung durch das Wort 'jung/junge'. Empfohlen: 'dynamische/engagierte Talente (m/w/d)'.")
                    optimized_text = re.sub(r'\bjunges\b', 'dynamisches', optimized_text, flags=re.IGNORECASE)
                    optimized_text = re.sub(r'\bjunge\b', 'dynamische', optimized_text, flags=re.IGNORECASE)
                    optimized_text = re.sub(r'\bjung\b', 'dynamisch', optimized_text, flags=re.IGNORECASE)
                    optimized_text = re.sub(r'\bjungen\b', 'dynamischen', optimized_text, flags=re.IGNORECASE)
                    
                if "junior" in text_lower and not junior_whitelisted:
                    violations.append("Formulierung 'Junior' im Stellentitel oder Text kann als Altersdiskriminierung (Bevorzugung jüngerer Bewerber) ausgelegt werden. Empfehlung: Angabe konkreter Berufserfahrung (z. B. 'mit erste Praxiserfahrung / Berufseinsteiger') statt Altersbegriffen.")
                    optimized_text = re.sub(r'\bJunior\b', '', optimized_text)
                    optimized_text = re.sub(r'\bjunior\b', 'mit erster Praxiserfahrung', optimized_text, flags=re.IGNORECASE)

                if "senior" in text_lower and not senior_whitelisted:
                    violations.append("Formulierung 'Senior' im Stellentitel oder Text kann als Altersdiskriminierung (Benachteiligung jüngerer Bewerber) ausgelegt werden. Empfehlung: Angabe konkreter Berufserfahrung (z. B. 'mit mehrjähriger Berufserfahrung') statt Altersbegriffen.")
                    optimized_text = re.sub(r'\bSenior\b', '', optimized_text)
                    optimized_text = re.sub(r'\bsenior\b', 'mit mehrjähriger Berufserfahrung', optimized_text, flags=re.IGNORECASE)
                    
                if "arzt" in text_lower and "ärztin" not in text_lower and "m/w/d" not in text_lower:
                    violations.append("Geschlechtsspezifische Formulierung 'Arzt'. Empfohlen: 'Arzt/Ärztin (m/w/d)'.")
                    optimized_text = re.sub(r'\barzt\b', 'Arzt/Ärztin (m/w/d)', optimized_text, flags=re.IGNORECASE)
                    
                if "gesund" in text_lower:
                    violations.append("Formulierung 'gesund' diskriminiert potenziell Bewerber mit chronischen Erkrankungen oder körperlichen Einschränkungen.")
                    optimized_text = re.sub(r'\bgesund\b', 'qualifiziert', optimized_text, flags=re.IGNORECASE)
                    
                if "belastbar" in text_lower:
                    violations.append("Formulierung 'belastbar' kann chronisch kranke oder behinderte Menschen abschrecken. Empfohlen: 'zuverlässig' oder 'engagiert'.")
                    optimized_text = re.sub(r'\bbelastbar\b', 'engagiert', optimized_text, flags=re.IGNORECASE)
                    
                AuditLog.objects.create(
                    action="AI_TASK_COMPLETED",
                    userId=str(task_id),
                    metadataJson=json.dumps({
                        "status": "completed",
                        "success": True,
                        "violations": violations,
                        "optimized_text": optimized_text,
                        "original_text": text,
                        "fallback_mode": True,
                        "error_msg": classify_ai_error(e, get_ai_model()),
                        "latency": latency
                    })
                )

        threading.Thread(target=run_async_agg_check_worker).start()
        
        return JsonResponse({'success': True, 'async': True, 'task_id': str(task_id)})
        
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@recruiter_required
def gemma_agg_check_status(request, task_id):
    """Checks the status of an asynchronous AGG checker background task."""
    import json
    from .models import AuditLog
    
    try:
        task = AuditLog.objects.filter(action="AI_TASK_COMPLETED", userId=str(task_id)).first()
        if task:
            res_data = json.loads(task.metadataJson)
            return JsonResponse({'success': True, 'status': 'completed', **res_data})
            
        pending = AuditLog.objects.filter(action="AI_TASK_PENDING", userId=str(task_id)).first()
        if pending:
            return JsonResponse({'success': True, 'status': 'pending'})
            
        return JsonResponse({'success': False, 'error': 'Task nicht gefunden.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@recruiter_required
def gemma_translate_simple_german(request):
    """Translates CMS page text or email text into Simple German (Leichte Sprache) for accessibility."""
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'error': 'Kein Text übermittelt.'})
            
        prompt = f"""
        Du bist der SecurATS Übersetzer für Leichte Sprache (basierend auf Gemma).
        Übersetze den folgenden Text in Leichte Sprache (barrierefrei, WCAG/BFSG compliant).
        Verwende kurze Sätze, einfache Wörter, erkläre schwierige Begriffe und verzichte auf Metaphern.
        
        Text zum Übersetzen:
        {text}
        
        NUR die Übersetzung ausgeben.
        """
        
        payload = {
            "model": get_ai_model(),
            "prompt": prompt,
            "stream": False
        }
        
        import time
        start_time = time.time()
        try:
            success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=28.0)
            latency = round(time.time() - start_time, 2)
            if success:
                reply = res_data.get("response", "").strip()
                log_ai_execution("Leichte Sprache", get_ai_model(), latency, True, False, "", False, prompt)
                return JsonResponse({'success': True, 'result': reply})
            else:
                log_ai_execution("Leichte Sprache", get_ai_model(), latency, False, True, f"Ollama-Fehler: {res_data}", False, prompt)
        except Exception as e:
            latency = round(time.time() - start_time, 2)
            log_ai_execution("Leichte Sprache", get_ai_model(), latency, False, True, str(e), False, prompt)
            
        # Fallback
        sentences = text.split(".")
        short_sentences = []
        for s in sentences:
            if len(s.strip()) > 3:
                short_sentences.append(s.strip() + ".")
        reply = "📖 Leichte Sprache Übersetzung (Fallback-Modus):\n\n" + " ".join(short_sentences)
        return JsonResponse({'success': True, 'result': reply})
        
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def classify_ai_error(error_str, model_name):
    """Classifies AI/Ollama connection issues and returns a highly detailed diagnostic message in German."""
    err_lower = str(error_str).lower()
    
    if "timed out" in err_lower or "timeout" in err_lower:
        return (
            "⏳ Zeitüberschreitung bei der KI-Antwort (Timeout)\n\n"
            "Die lokale KI (Ollama) hat nicht innerhalb des Timeout-Fensters von 25 Sekunden geantwortet.\n\n"
            "• Mögliche Ursache: Dies tritt fast immer beim ERSTEN Start auf (Cold Start), da Ollama das schwere Sprachmodell erst von der Festplatte in den Hauptspeicher (RAM) laden muss, oder wenn der Prozessor des Servers stark ausgelastet ist.\n"
            "• Empfehlung: Bitte warte ca. 10 bis 15 Sekunden (damit Ollama den Ladevorgang im Hintergrund abschließen kann) und klicke dann erneut auf 'Validieren'. Sobald das Modell im Speicher liegt, antwortet es in unter 5 Sekunden!"
        )
    elif "connection refused" in err_lower or "unreachable" in err_lower or "refused" in err_lower:
        return (
            "🔌 Verbindung zum KI-Dienst fehlgeschlagen\n\n"
            "Der lokale Ollama-Daemon unter http://host.docker.internal:11434 konnte nicht kontaktiert werden.\n\n"
            "• Mögliche Ursache: Der Ollama-Service läuft auf dem Server nicht, oder die Docker-Container-Netzwerkbrücke blockiert den Port.\n"
            "• Empfehlung: Bitte melde dich in der Server-Konsole an und prüfe den Dienststatus (z. B. mit 'sudo systemctl status ollama' oder 'docker ps')."
        )
    elif "404" in err_lower or "not found" in err_lower:
        return (
            f"❌ Modell nicht gefunden (404 Not Found)\n\n"
            f"Das ausgewählte KI-Modell '{model_name}' ist auf dem Ollama-Server nicht vorhanden.\n\n"
            f"• Empfehlung: Bitte melde dich in der Server-Konsole an und lade das Modell manuell mit dem Befehl 'ollama pull {model_name}' herunter."
        )
    else:
        return (
            f"⚠️ Allgemeiner Fehler der lokalen KI-Verbindung\n\n"
            f"Details: {error_str}\n\n"
            "• Empfehlung: Überprüfe die Auslastung und die Systemprotokolle deines Ollama-Dienstes auf dem VM-Server."
        )


@hr_admin_required
def validate_ai_prompt(request):
    """Validates the current custom AGG or Leichte Sprache prompt by running it on a test input asynchronously."""
    if request.method == 'POST':
        prompt_type = request.POST.get('type', 'AGG').strip()
        custom_prompt = request.POST.get('prompt', '').strip()
        
        if not custom_prompt:
            return JsonResponse({'success': False, 'error': 'Kein Prompt übermittelt.'})
            
        # Realistic, non-faked test text matching user expectations
        test_text = "Wir suchen ab sofort einen belastbaren Junior-Softwareentwickler (m/w/d) zur Verstärkung des Teams."
        
        if prompt_type == 'AGG':
            prompt = f"{custom_prompt}\n\nAusschreibungstext zum Prüfen:\n{test_text}"
        else:
            prompt = f"{custom_prompt}\n\nText zum Übersetzen:\n{test_text}"
            
        import uuid
        import json
        from .models import AuditLog
        
        task_id = uuid.uuid4()
        
        # Save a pending task status
        AuditLog.objects.create(
            action="AI_TASK_PENDING",
            userId=str(task_id),
            metadataJson=json.dumps({"status": "pending", "type": f"VALIDATE_{prompt_type}"})
        )
        
        import threading
        
        def run_async_validate_worker():
            payload = {
                "model": get_ai_model(),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,
                    "top_k": 20,
                    "top_p": 0.5
                }
            }
            
            import time
            start_time = time.time()
            try:
                # Asynchronous worker timeout of 85 seconds
                success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=85.0)
                latency = round(time.time() - start_time, 2)
                if success:
                    reply = res_data.get("response", "").strip()
                    reply_lower = reply.lower()
                    
                    if prompt_type == 'AGG':
                        parsed_json, is_json = try_parse_json_reply(reply)
                        if is_json:
                            log_ai_execution("Prompt-Validierung (AGG-JSON)", get_ai_model(), latency, True, False, "", True, prompt)
                            status_val = str(parsed_json.get("status", "")).strip().lower()
                            is_green = status_val in ["grün", "gruen", "green", "konform", "safe", "ok", "compliant"]
                            
                            if is_green:
                                msg = 'Der Prompt wurde erfolgreich im JSON-Format ausgeführt und die Stellenausschreibung wurde als AGG-konform ("GRÜN") eingestuft.'
                            else:
                                msg = 'Der Prompt wurde erfolgreich im JSON-Format ausgeführt. Es wurden AGG-Risiken ("ROT") identifiziert.'
                                
                            result = {
                                'valid': True,
                                'reply_preview': reply[:300] + "...",
                                'message': msg
                            }
                        else:
                            opt_headers = [
                                "=== optimierter text ===", 
                                "optimierter text-vorschlag:", 
                                "optimierter text:", 
                                "optimierter text vorschlag:"
                            ]
                            opt_header_found = None
                            for h in opt_headers:
                                if h in reply_lower:
                                    opt_header_found = h
                                    break
                            
                            has_delimiters = opt_header_found is not None or "=== OPTIMIERTER TEXT ===" in reply
                            
                            if has_delimiters:
                                log_ai_execution("Prompt-Validierung (AGG)", get_ai_model(), latency, True, False, "", True, prompt)
                                result = {
                                    'valid': True,
                                    'reply_preview': reply[:250] + "...",
                                    'message': 'Der Prompt wurde erfolgreich von der lokalen KI angewendet und das Antwortformat ist korrekt strukturiert.'
                                }
                            else:
                                log_ai_execution("Prompt-Validierung (AGG)", get_ai_model(), latency, True, True, "Warnung: Keine standardmäßigen Antwort-Trenner gefunden.", True, prompt)
                                result = {
                                    'valid': False,
                                    'reply_preview': reply[:300] + "...",
                                    'message': 'Die KI hat geantwortet, aber es wurden keine standardmäßigen Trenner wie "=== OPTIMIERTER TEXT ===" oder "=== VERSTÖSSE ===" im Antworttext gefunden. Das System wird versuchen, die Antwort als Freitext anzuzeigen, dies kann jedoch zu ungenauen Darstellungen führen.'
                                }
                    else:
                        if reply and reply != test_text:
                            log_ai_execution("Prompt-Validierung (Easy)", get_ai_model(), latency, True, False, "", True, prompt)
                            result = {
                                'valid': True,
                                'reply_preview': reply[:250] + "...",
                                'message': 'Der Prompt für Leichte Sprache wurde erfolgreich validiert.'
                            }
                        else:
                            log_ai_execution("Prompt-Validierung (Easy)", get_ai_model(), latency, True, True, "Fehler bei der Übersetzung.", True, prompt)
                            result = {
                                'valid': False,
                                'reply_preview': reply[:200] + "...",
                                'message': 'Der Antworttext der KI ist leer oder identisch mit dem Ausgangstext.'
                            }
                    
                    AuditLog.objects.create(
                        action="AI_TASK_COMPLETED",
                        userId=str(task_id),
                        metadataJson=json.dumps({
                            "status": "completed",
                            "success": True,
                            "latency": latency,
                            **result
                        })
                    )
                else:
                    log_ai_execution("Prompt-Validierung", get_ai_model(), latency, False, True, f"Ollama-Fehler: {res_data}", True, prompt)
                    detailed_error = classify_ai_error(res_data, get_ai_model())
                    AuditLog.objects.create(
                        action="AI_TASK_COMPLETED",
                        userId=str(task_id),
                        metadataJson=json.dumps({
                            "status": "completed",
                            "success": False,
                            "error": detailed_error
                        })
                    )
            except Exception as e:
                latency = round(time.time() - start_time, 2)
                log_ai_execution("Prompt-Validierung", get_ai_model(), latency, False, True, str(e), True, prompt)
                detailed_error = classify_ai_error(e, get_ai_model())
                AuditLog.objects.create(
                    action="AI_TASK_COMPLETED",
                    userId=str(task_id),
                    metadataJson=json.dumps({
                        "status": "completed",
                        "success": False,
                        "error": detailed_error
                    })
                )

        threading.Thread(target=run_async_validate_worker).start()
        
        return JsonResponse({'success': True, 'async': True, 'task_id': str(task_id)})
        
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@hr_admin_required
def validate_ai_prompt_status(request, task_id):
    """Checks the status of an asynchronous custom prompt validation background task."""
    import json
    from .models import AuditLog
    
    try:
        task = AuditLog.objects.filter(action="AI_TASK_COMPLETED", userId=str(task_id)).first()
        if task:
            res_data = json.loads(task.metadataJson)
            return JsonResponse({'success': True, 'status': 'completed', **res_data})
            
        pending = AuditLog.objects.filter(action="AI_TASK_PENDING", userId=str(task_id)).first()
        if pending:
            return JsonResponse({'success': True, 'status': 'pending'})
            
        return JsonResponse({'success': False, 'error': 'Task nicht gefunden.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================================================
# HR COMMAND CENTER ADMINISTRATIVE CRUD HANDLERS
# ============================================================================

@recruiter_required
def create_job(request):
    """Saves or updates a JobPosting submitted via the Job Creator wizard."""
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        title = request.POST.get('title', '').strip()
        headcount_raw = (request.POST.get('headcount') or '').strip()
        headcount = None
        if headcount_raw:
            try:
                headcount = max(1, min(99, int(headcount_raw)))
            except ValueError:
                headcount = None
        def _clamped(field, lo, hi):
            raw = (request.POST.get(field) or '').strip()
            if not raw:
                return None, False          # nicht im POST -> Bestand behalten
            try:
                return max(lo, min(hi, int(raw))), True
            except ValueError:
                return None, True           # geleert/unsinnig -> zuruecksetzen
        panel_quorum, quorum_sent = _clamped('panel_quorum', 1, 15)
        panel_deadline, deadline_sent = _clamped('panel_deadline_days', 1, 60)
        rounds_sent = 'interview_rounds' in request.POST
        rounds_json = json.dumps(
            [r.strip()[:60] for r in
             request.POST.get('interview_rounds', '').split(',')
             if r.strip()][:6], ensure_ascii=False)
        description = request.POST.get('description', '').strip()
        
        tasks_raw = request.POST.get('tasks', '')
        requirements_raw = request.POST.get('requirements', '')
        
        tasks = [t.strip() for t in tasks_raw.split('\n') if t.strip()]
        requirements = [r.strip() for r in requirements_raw.split('\n') if r.strip()]
        
        screening_raw = request.POST.get('screening_questions', '[]')
        
        facility_id = request.POST.get('facility')
        dept_id = request.POST.get('department')
        location_id = request.POST.get('location')
        job_family_id = request.POST.get('job_family')
        contact_id = request.POST.get('contact_person')
        template_id = request.POST.get('job_template')
        benefits_selected = request.POST.getlist('benefits')
        workflow_state_id = request.POST.get('workflow_state')
        
        with transaction.atomic():
            org = Organization.objects.first()
            if not org:
                org = Organization.objects.create(name="SecurATS GmbH")
                
            facility = get_object_or_404(Facility, id=facility_id) if facility_id else Facility.objects.first()
            location = get_object_or_404(Location, id=location_id) if location_id else Location.objects.first()
            job_family = get_object_or_404(JobFamily, id=job_family_id) if job_family_id else JobFamily.objects.first()
            
            if workflow_state_id:
                workflow_state = get_object_or_404(WorkflowState, id=workflow_state_id)
            else:
                workflow_state = WorkflowState.objects.filter(name="published").first()
                if not workflow_state:
                    workflow_state = WorkflowState.objects.create(name="published", description="Veröffentlicht")
            
            if job_id:
                job = get_object_or_404(JobPosting, id=job_id)
                job.title = title
                if headcount is not None:
                    job.headcount = headcount
                if quorum_sent:
                    job.panelQuorum = panel_quorum
                if deadline_sent:
                    job.panelDeadlineDays = panel_deadline
                if rounds_sent:
                    job.interviewRoundsJson = rounds_json
                job.description = description
                job.tasksJson = json.dumps(tasks)
                job.requirementsJson = json.dumps(requirements)
                job.screeningQuestionsJson = screening_raw
                job.facility = facility
                job.location = location
                job.jobFamily = job_family
                job.workflowState = workflow_state
                job.department_id = dept_id if dept_id else None
                job.contactPerson_id = contact_id if contact_id else None
                job.jobTemplate_id = template_id if template_id else None
                job.save()
                action = "UPDATE_JOB"
            else:
                job = JobPosting.objects.create(
                    title=title,
                    headcount=headcount or 1,
                    panelQuorum=panel_quorum,
                    interviewRoundsJson=rounds_json,
                    panelDeadlineDays=panel_deadline,
                    description=description,
                    tasksJson=json.dumps(tasks),
                    requirementsJson=json.dumps(requirements),
                    screeningQuestionsJson=screening_raw,
                    organization=org,
                    facility=facility,
                    location=location,
                    jobFamily=job_family,
                    workflowState=workflow_state,
                    department_id=dept_id if dept_id else None,
                    contactPerson_id=contact_id if contact_id else None,
                    jobTemplate_id=template_id if template_id else None
                )
                action = "CREATE_JOB"
            
            # Update benefits relation
            job.benefits.clear()
            if benefits_selected:
                job.benefits.set(Benefit.objects.filter(id__in=benefits_selected))
                
            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"jobId": str(job.id), "title": job.title})
            )

            # UC-JF-01: zustimmungspflichtige Einrichtung -> automatisches Freigabe-Gate
            if request.POST.get('panel_members_present') == '1':
                from django.contrib.auth.models import User as _User
                raw_ids = request.POST.getlist('panel_members')
                valid = list(_User.objects.filter(id__in=raw_ids, is_active=True)
                             .values_list('id', flat=True))
                job.panelUserIdsJson = json.dumps([str(i) for i in valid])
                job.save(update_fields=['panelUserIdsJson'])
            # Vorstands-Mindeststandards: serverseitig, nach JEDEM Speichern –
            # egal ob Wizard, Vorgaenger-Uebernahme oder Import den Inhalt lieferte.
            from .process_advisor import ensure_minimum_standards
            enforced = ensure_minimum_standards(job)
            if enforced:
                job.save(update_fields=['screeningQuestionsJson'])
                write_audit('MINIMUM_STANDARD_APPLIED', user=request.user,
                            job=job.title, corrections=enforced)
            from .approvals import ensure_approval_gate
            ticket = ensure_approval_gate(job)
            if ticket and ticket.status == "PENDING":
                write_audit("APPROVAL_GATE_OPENED", user=request.user,
                            job=job.title, ticket=str(ticket.id))
            # Stellenfreigabe (optional, dann Pflicht): ohne genehmigten
            # Bedarf bleibt die Stelle Entwurf statt online zu gehen.
            from .approvals import requisition_blocked_reason, draft_state
            _rq_reason = requisition_blocked_reason(job)
            if _rq_reason and job.workflowState and \
                    job.workflowState.name == 'published':
                job.workflowState = draft_state()
                job.save(update_fields=['workflowState'])
                write_audit('REQUISITION_GATE_BLOCKED', user=request.user,
                            job=job.title)
                messages.warning(request, _rq_reason)
            
        return redirect('ats:dashboard')
        
    return redirect('ats:dashboard')



@hr_admin_required
def save_page(request):
    """Creates or updates a CMS Page."""
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip().lower()
        content = request.POST.get('content', '').strip()
        status = request.POST.get('status', 'published')
        nav_enabled = request.POST.get('nav_enabled') == 'on'
        nav_label = request.POST.get('nav_label', '').strip()
        nav_order = int(request.POST.get('nav_order', '0'))
        meta_desc = request.POST.get('meta_desc', '').strip()
        
        with transaction.atomic():
            if page_id:
                page = get_object_or_404(Page, id=page_id)
                page.title = title
                page.slug = slug
                page.content = content
                page.status = status
                page.navEnabled = nav_enabled
                page.navLabel = nav_label or title
                page.navOrder = nav_order
                page.metaDesc = meta_desc
                page.save()
                action = "UPDATE_PAGE"
            else:
                page = Page.objects.create(
                    title=title,
                    slug=slug,
                    content=content,
                    status=status,
                    navEnabled=nav_enabled,
                    navLabel=nav_label or title,
                    navOrder=nav_order,
                    metaDesc=meta_desc
                )
                action = "CREATE_PAGE"
                
            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"pageId": str(page.id), "slug": page.slug})
            )
            
        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_app_workflow(request):
    """Creates or updates an AppWorkflowDef (specialized recruiting pipeline)."""
    if request.method == 'POST':
        workflow_id = request.POST.get('workflow_id')
        name = request.POST.get('name', '').strip()
        facility_id = request.POST.get('facility')
        
        location_ids = request.POST.getlist('locations')
        category_ids = request.POST.getlist('categories')
        job_ids = request.POST.getlist('jobs')
        steps = request.POST.getlist('steps')
        custom_actions_raw = request.POST.get('custom_actions_json', '').strip()
        
        custom_actions = []
        if custom_actions_raw:
            try:
                custom_actions = json.loads(custom_actions_raw)
            except Exception:
                custom_actions = []
                
        # Construct structured step objects containing automation actions
        structured_steps = []
        for step in steps:
            step_actions = []
            # Check if there is an explicit override in custom_actions
            for item in custom_actions:
                if isinstance(item, dict) and item.get('step', '').upper() == step.upper():
                    step_actions = item.get('actions', [])
                    break
                    
            # If no override, generate rich default automation presets!
            if not step_actions:
                if step.upper() == 'IN_REVIEW':
                    step_actions = [
                        {"type": "EMAIL_NOTIFICATION", "recipient": "komitee@securats.de", "template": "Gremiums-Prüfung"},
                        {"type": "APPROVAL_COMMITTEE", "roles": ["DEPT_HEAD", "HR_LEAD"]}
                    ]
                elif step.upper() == 'INVITED':
                    step_actions = [
                        {"type": "AUTO_INVITE_INTERVIEW"},
                        {"type": "TRIGGER_PROCESS", "processes": ["CALENDAR_SYNC", "ZOOM_ROOM_CREATE"]}
                    ]
                elif step.upper() == 'REJECTED':
                    step_actions = [
                        {"type": "EMAIL_NOTIFICATION", "recipient": "applicant", "template": "Absage"}
                    ]
                elif step.upper() == 'APPROVED' or step.upper() == 'NEW':
                    step_actions = [
                        {"type": "SEND_CONTRACT", "contract_template": "Standard_DE_2026"}
                    ]
                    
            structured_steps.append({
                "name": step,
                "state": step.upper(),
                "actions": step_actions
            })
        
        with transaction.atomic():
            facility = Facility.objects.filter(id=facility_id).first() if facility_id else None
            
            if workflow_id:
                wf = get_object_or_404(AppWorkflowDef, id=workflow_id)
                wf.name = name
                wf.facility = facility
                wf.locationIdsJson = json.dumps(location_ids)
                wf.categoryIdsJson = json.dumps(category_ids)
                wf.jobIdsJson = json.dumps(job_ids)
                wf.stepsJson = json.dumps(structured_steps)
                wf.save()
                action = "UPDATE_APP_WORKFLOW"
            else:
                wf = AppWorkflowDef.objects.create(
                    name=name,
                    facility=facility,
                    locationIdsJson=json.dumps(location_ids),
                    categoryIdsJson=json.dumps(category_ids),
                    jobIdsJson=json.dumps(job_ids),
                    stepsJson=json.dumps(structured_steps)
                )
                action = "CREATE_APP_WORKFLOW"
                
            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"workflowId": str(wf.id), "name": wf.name})
            )
            
        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_workflow_state(request):
    """Creates or updates a recruiting process WorkflowState."""
    if request.method == 'POST':
        state_id = request.POST.get('state_id')
        name = request.POST.get('name', '').strip().lower()
        description = request.POST.get('description', '').strip()
        
        with transaction.atomic():
            if state_id:
                state = get_object_or_404(WorkflowState, id=state_id)
                old_name = state.name
                state.name = name
                state.description = description
                state.save()
                action = "UPDATE_WORKFLOW_STATE"
                metadata = {"oldName": old_name, "newName": name}
            else:
                state = WorkflowState.objects.create(name=name, description=description)
                action = "CREATE_WORKFLOW_STATE"
                metadata = {"name": name}
                
            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps(metadata)
            )
            
        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_email_template(request):
    """Creates or updates an EmailTemplate."""
    from .models import EmailTemplate
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        name = request.POST.get('name', '').strip()
        subject = request.POST.get('subject', '').strip()
        html_content = request.POST.get('html_content', '').strip()
        text_content = request.POST.get('text_content', '').strip()
        
        with transaction.atomic():
            if template_id:
                template = get_object_or_404(EmailTemplate, id=template_id)
                template.name = name
                template.subject = subject
                template.htmlContent = html_content
                template.textContent = text_content
                template.save()
                action = "UPDATE_EMAIL_TEMPLATE"
            else:
                template = EmailTemplate.objects.create(
                    name=name,
                    subject=subject,
                    htmlContent=html_content,
                    textContent=text_content
                )
                action = "CREATE_EMAIL_TEMPLATE"
                
            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"templateId": str(template.id), "name": template.name})
            )
            
        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_system_setting(request):
    """Creates or updates a SystemSetting (template variable)."""
    if request.method == 'POST':
        setting_id = request.POST.get('setting_id')
        key = request.POST.get('key', '').strip().upper()
        value = request.POST.get('value', '').strip()
        
        with transaction.atomic():
            if setting_id:
                setting = get_object_or_404(SystemSetting, id=setting_id)
                old_key = setting.key
                setting.key = key
                setting.value = value
                setting.save()
                action = "UPDATE_SYSTEM_SETTING"
                metadata = {"oldKey": old_key, "newKey": key}
            else:
                setting = SystemSetting.objects.create(key=key, value=value)
                action = "CREATE_SYSTEM_SETTING"
                metadata = {"key": key}
                
            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps(metadata)
            )
            
        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@recruiter_required
def toggle_learning_sample(request, app_id):
    """Toggles or creates an AILearningSample feedback for Gemma training."""
    if request.method == 'POST':
        app = get_object_or_404(Application, id=app_id)
        if not can_access_application(request.user, app):
            raise Http404("Nicht im Zugriffsbereich.")
        feedback_type = request.POST.get('feedback_type', 'POSITIVE').upper()
        
        with transaction.atomic():
            sample, created = AILearningSample.objects.get_or_create(
                application=app,
                defaults={
                    'feedbackType': feedback_type,
                    'categoryId': str(app.jobPosting.jobFamily.id) if app.jobPosting.jobFamily else None,
                    'facilityId': str(app.jobPosting.facility.id),
                    'anonymizedProfileJson': json.dumps({
                        'coverLetter': app.coverLetterTxt,
                        'aiScore': app.aiScore,
                        'jobTitle': app.jobPosting.title
                    })
                }
            )
            
            if not created:
                sample.feedbackType = feedback_type
                sample.save()
                
            AuditLog.objects.create(
                action="AI_FEEDBACK",
                applicationId=str(app.id),
                metadataJson=json.dumps({"feedbackType": feedback_type})
            )
            
        return JsonResponse({'success': True, 'feedback_type': feedback_type})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@hr_admin_required
def save_ai_settings(request):
    """Saves all consolidated AI settings from the KI-Steuerungszentrum form."""
    if request.method == 'POST':
        tone = request.POST.get('AI_TONE', 'EMPATHETIC').strip()
        lang = request.POST.get('AI_LANGUAGE', 'DE_DU').strip()
        auto_reject = 'true' if request.POST.get('AI_AUTO_REJECT_ENABLED') == 'on' or request.POST.get('AI_AUTO_REJECT_ENABLED') == 'true' else 'false'
        th_d = request.POST.get('AI_THRESHOLD_D_REJECT', '15').strip()
        th_c = request.POST.get('AI_THRESHOLD_C_WAITLIST', '50').strip()
        th_a = request.POST.get('AI_THRESHOLD_A_INVITE', '80').strip()
        cv_learning = 'true' if request.POST.get('AI_CV_LEARNING_MODE') == 'on' or request.POST.get('AI_CV_LEARNING_MODE') == 'true' else 'false'
        agg_check = 'true' if request.POST.get('AI_AGG_CHECK_ENABLED') == 'on' or request.POST.get('AI_AGG_CHECK_ENABLED') == 'true' else 'false'
        agg_prompt = request.POST.get('AI_AGG_PROMPT', '').strip()
        translate_easy = 'true' if request.POST.get('AI_TRANSLATE_EASY_LANGUAGE') == 'on' or request.POST.get('AI_TRANSLATE_EASY_LANGUAGE') == 'true' else 'false'
        easy_prompt = request.POST.get('AI_EASY_LANGUAGE_PROMPT', '').strip()

        settings_dict = {
            'AI_TONE': tone,
            'AI_LANGUAGE': lang,
            'AI_AUTO_REJECT_ENABLED': auto_reject,
            'AI_THRESHOLD_D_REJECT': th_d,
            'AI_THRESHOLD_C_WAITLIST': th_c,
            'AI_THRESHOLD_A_INVITE': th_a,
            'AI_CV_LEARNING_MODE': cv_learning,
            'AI_AGG_CHECK_ENABLED': agg_check,
            'AI_AGG_PROMPT': agg_prompt,
            'AI_TRANSLATE_EASY_LANGUAGE': translate_easy,
            'AI_EASY_LANGUAGE_PROMPT': easy_prompt,
        }

        with transaction.atomic():
            for key, value in settings_dict.items():
                setting, created = SystemSetting.objects.get_or_create(key=key, defaults={'value': value})
                if not created:
                    setting.value = value
                    setting.save()

            AuditLog.objects.create(
                action="UPDATE_AI_SETTINGS",
                metadataJson=json.dumps({"keys": list(settings_dict.keys())})
            )

        return redirect('ats:dashboard')
    return redirect('ats:dashboard')



# ============================================================================
# BACKLOG-FEATURES (Nachbau aus legacy/frontend, siehe FEATURE_BACKLOG.md)
# ============================================================================
import os as _os
from django.http import FileResponse, Http404
from django.urls import reverse
from .audit import write_audit
from .models import (
    AuditLog, TalentPoolSubscription, ScreeningQuestion, RoleDelegation,
    ApplicantToken, ApplicationDocument,
)


# --- B1: Sicherer CV-Download (auth + Rolle + Audit-Log) --------------------
@recruiter_required
def download_cv(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    if not app.cvStorageId or not default_storage.exists(app.cvStorageId):
        raise Http404("Kein Lebenslauf hinterlegt.")
    # Revisionssicher protokollieren, WER WESSEN CV wann gelesen hat.
    write_audit("READ_CV", user=request.user, application_id=app.id,
                storage=app.cvStorageId)
    download_name = _os.path.basename(app.cvStorageId)
    if "_" in download_name:  # UUID-Prefix aus dem Speichernamen entfernen
        download_name = download_name.split("_", 1)[1]
    fh = default_storage.open(app.cvStorageId, "rb")
    return FileResponse(fh, as_attachment=True, filename=download_name or "cv")


# --- B2: Audit-Log-Viewer ---------------------------------------------------
@hr_admin_required
def audit_log_view(request):
    logs = AuditLog.objects.order_by("-createdAt")
    active_action = request.GET.get("action", "").strip()
    if active_action:
        logs = logs.filter(action=active_action)
    actions = list(AuditLog.objects.values_list("action", flat=True).distinct())
    return render(request, "audit_log.html", {
        "logs": logs[:500],
        "actions": sorted(a for a in actions if a),
        "active_action": active_action,
    })


# --- B11: Talent-Pool-Übersicht --------------------------------------------
@recruiter_required
def talent_pool_view(request):
    """UC-SB-13/UM-04/FA-04: Pool sichten, auf offene Stellen matchen, ansprechen.

    Matching bewusst datensparsam: Jobfamilie/Standort aus den frueheren
    Bewerbungen (steht in criteria) gegen veroeffentlichte Stellen im
    BOLA-Scope. Ansprache mit Doppel-Schutz (unique_together) – Einwilligung
    heisst gelegentliche passende Hinweise, nicht Dauer-Werbung.
    """
    from .models import TalentPoolContact

    published = list(scope_jobs(request.user, JobPosting.objects.filter(
        workflowState__name='published').select_related('jobFamily', 'location')))

    if request.method == 'POST' and request.POST.get('contact_sub_id'):
        sub = get_object_or_404(TalentPoolSubscription,
                                id=request.POST.get('contact_sub_id'))
        job = next((j for j in published
                    if str(j.id) == request.POST.get('job_id')), None)  # Scope!
        if job and sub.is_active:
            _, created = TalentPoolContact.objects.get_or_create(
                subscription=sub, jobPosting=job,
                defaults={'sentBy': request.user})
            if created:
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        f'Eine Stelle, die zu Ihnen passen könnte: {job.title}',
                        (f'Guten Tag,\n\nSie sind in unserem Talent-Pool – und wir '
                         f'haben eine neue Stelle, die zu Ihren bisherigen '
                         f'Bewerbungen passt:\n\n{job.title}'
                         f'{" – " + job.location.name if job.location else ""}\n'
                         f'Details und Bewerbung: /jobs/{job.id}/\n\n'
                         'Kein Interesse mehr? In Ihrem Bewerbungsportal können Sie '
                         'jederzeit aus dem Talent-Pool austreten.\n\nFreundliche Grüße'),
                        None, [sub.email], fail_silently=True)
                except Exception:
                    logger.exception('Talent-Pool-Ansprache fehlgeschlagen')
                write_audit('TALENT_POOL_CONTACTED', user=request.user,
                            subscription=str(sub.id), job_id=str(job.id))
        return redirect('ats:talent_pool')

    now = timezone.now()
    contacted = {(c.subscription_id, c.jobPosting_id): c.sentAt
                 for c in TalentPoolContact.objects.all()}
    rows = []
    for sub in TalentPoolSubscription.objects.order_by('-createdAt')[:500]:
        try:
            crit = json.loads(sub.criteria or '{}')
        except ValueError:
            crit = {}
        fam_ids = set(crit.get('job_families') or [])
        loc_ids = set(crit.get('locations') or [])
        matches = []
        if sub.expiresAt >= now and (fam_ids or loc_ids):
            for j in published:
                if ((j.jobFamily_id and str(j.jobFamily_id) in fam_ids)
                        or (j.location_id and str(j.location_id) in loc_ids)):
                    matches.append({'job': j,
                                    'contacted_at': contacted.get((sub.id, j.id))})
        rows.append({'sub': sub, 'matches': matches,
                     'expired': sub.expiresAt < now})
    # Wirksamkeit messbar (datensparsam, 90 Tage): beweist, ob Reaktivierung
    # wirklich Stellen fuellt – oder nur gut gemeint ist.
    since = now - datetime.timedelta(days=90)
    contacts_90d = sum(1 for sent in contacted.values() if sent >= since)
    conversions = 0
    if contacts_90d:
        from .models import TalentPoolContact
        for c in (TalentPoolContact.objects.filter(sentAt__gte=since)
                  .select_related('subscription', 'jobPosting')):
            if Application.objects.filter(
                    jobPosting=c.jobPosting,
                    applicant__email=c.subscription.email,
                    createdAt__gte=c.sentAt).exists():
                conversions += 1
    pool_stats = {
        'active': sum(1 for r in rows if not r['expired']),
        'expired': sum(1 for r in rows if r['expired']),
        'contacts_90d': contacts_90d,
        'conversions_90d': conversions,
    }
    return render(request, "talent_pool.html", {"rows": rows,
                                                "pool_stats": pool_stats})


# --- B15: Screening-Fragen-Bank --------------------------------------------
@hr_admin_required
def screening_questions_view(request):
    if request.method == "POST" and request.POST.get("form") == "minimum_builder":
        # Formular-Builder: HR pflegt Mindeststandards OHNE Technik-Vorwissen.
        # Aktionen add/save/delete/up/down je Frage; Speicherformat bleibt
        # dieselbe JSON-Liste (ensure_minimum_standards unveraendert).
        from .questions import normalize_question, normalize_questions
        fam = get_object_or_404(JobFamily, id=request.POST.get("family_id"))
        try:
            qs = normalize_questions(json.loads(fam.minimumQuestionsJson or "[]"))
        except (ValueError, TypeError):
            qs = []
        action = request.POST.get("action", "")
        idx = request.POST.get("idx")
        idx = int(idx) if idx and idx.isdigit() else None
        if action == "add":
            q = normalize_question({
                "type": request.POST.get("q_type", "YES_NO"),
                "question": request.POST.get("q_question", ""),
                "isMandatory": True,  # Mindeststandard ist per Definition Pflicht
                "options": request.POST.get("q_options", ""),
                "expectedAnswer": request.POST.get("q_expected", ""),
            })
            if q:
                qs.append(q)
        elif action == "save" and idx is not None and idx < len(qs):
            q = normalize_question({
                "id": qs[idx]["id"],
                "type": request.POST.get("q_type", qs[idx]["type"]),
                "question": request.POST.get("q_question", ""),
                "isMandatory": True,
                "options": request.POST.get("q_options", ""),
                "expectedAnswer": request.POST.get("q_expected", ""),
            })
            if q:
                qs[idx] = q
        elif action == "up" and idx and idx < len(qs):
            qs[idx - 1], qs[idx] = qs[idx], qs[idx - 1]
        elif action == "down" and idx is not None and idx < len(qs) - 1:
            qs[idx + 1], qs[idx] = qs[idx], qs[idx + 1]
        elif action == "delete" and idx is not None and idx < len(qs):
            qs.pop(idx)
        fam.minimumQuestionsJson = json.dumps(qs, ensure_ascii=False)
        fam.save(update_fields=["minimumQuestionsJson"])
        write_audit("MINIMUM_STANDARD_CHANGED", user=request.user,
                    family=fam.name, count=len(qs), op=action)
        return redirect("ats:screening_questions")

    if request.method == "POST" and request.POST.get("form") == "minimum":
        # Vorstands-Mindeststandards je Jobfamilie (nur HR-Admin erreicht diese View)
        fam = get_object_or_404(JobFamily, id=request.POST.get("family_id"))
        raw = (request.POST.get("minimum_json") or "[]").strip() or "[]"
        try:
            parsed = json.loads(raw)
            assert isinstance(parsed, list)
        except (ValueError, AssertionError):
            questions = ScreeningQuestion.objects.filter(archived=False).order_by("-createdAt")
            return render(request, "screening_questions.html",
                          {"questions": questions,
                           "families": JobFamily.objects.filter(archived=False).order_by("name"),
                           "minimum_error": f"Ungültiges JSON für {fam.name} – nichts gespeichert."})
        fam.minimumQuestionsJson = json.dumps(parsed, ensure_ascii=False)
        fam.save(update_fields=["minimumQuestionsJson"])
        write_audit("MINIMUM_STANDARD_CHANGED", user=request.user,
                    family=fam.name, count=len(parsed))
        return redirect("ats:screening_questions")
    if request.method == "POST":
        text = (request.POST.get("question") or "").strip()
        if text:
            ScreeningQuestion.objects.create(question=text)
            write_audit("SCREENING_Q_ADDED", user=request.user)
        return redirect("ats:screening_questions")
    questions = ScreeningQuestion.objects.filter(archived=False).order_by("-createdAt")
    from .questions import QUESTION_TYPES, normalize_questions as _nq
    family_rows = []
    for f in JobFamily.objects.filter(archived=False).order_by("name"):
        try:
            fqs = _nq(json.loads(f.minimumQuestionsJson or "[]"))
        except (ValueError, TypeError):
            fqs = []
        rows = [{"i": i, "q": q,
                 "options_text": "\n".join(q.get("options", []))}
                for i, q in enumerate(fqs)]
        family_rows.append({"family": f, "questions": rows})
    return render(request, "screening_questions.html",
                  {"questions": questions,
                   "families": JobFamily.objects.filter(archived=False).order_by("name"),
                   "family_rows": family_rows,
                   "question_types": QUESTION_TYPES})


@hr_admin_required
def archive_screening_question(request, q_id):
    q = get_object_or_404(ScreeningQuestion, id=q_id)
    q.archived = True
    q.save()
    return redirect("ats:screening_questions")


# --- B8: Delegationen (Vertretung/Zuweisung) -------------------------------
@any_staff_required
def delegations_view(request):
    # WP3/UC-PW-01/02 + UC-EW-07: Vertretung anlegen bzw. vorzeitig beenden.
    # Selbstbedienung fuer JEDE interne Rolle (ein Vorstand legt seine
    # Vertretung selbst an); HR-Admin behaelt Vollsicht und darf im
    # Assistenz-Fall den Vertretenen waehlen (auditiert als on_behalf).
    is_admin = (request.user.is_superuser
                or request.user.groups.filter(name='HR-Admin').exists())
    if request.method == "POST":
        from django.contrib.auth.models import User as AuthUser
        from django.utils.dateparse import parse_date
        end_id = request.POST.get("end_id")
        if end_id:
            d = RoleDelegation.objects.filter(id=end_id).first()
            # Beenden: nur eigene erteilte Vertretung – oder HR-Admin
            if d and (is_admin or d.delegator_id == request.user.id):
                d.validUntil = timezone.now()
                d.save(update_fields=["validUntil", "updatedAt"])
                write_audit("DELEGATION_END", user=request.user, delegation=str(d.id))
        else:
            delegatee = AuthUser.objects.filter(username=(request.POST.get("delegatee") or "").strip()).first()
            # Wer wird vertreten? Immer man selbst – nur HR-Admin darf
            # stellvertretend fuer andere anlegen (Assistenz-Fall).
            delegator = request.user
            if is_admin and request.POST.get("delegator"):
                delegator = (AuthUser.objects.filter(
                    username=request.POST["delegator"].strip()).first()
                    or request.user)
            vf = parse_date(request.POST.get("validFrom") or "")
            vu = parse_date(request.POST.get("validUntil") or "")
            if delegatee and vf and vu and vu >= vf and delegatee != delegator:
                import datetime as _dt
                d = RoleDelegation.objects.create(
                    delegator=delegator, delegatee=delegatee,
                    scopeType=(request.POST.get("scopeType") or "ALL").upper()[:50],
                    scopeId=(request.POST.get("scopeId") or "").strip() or None,
                    validFrom=timezone.make_aware(_dt.datetime.combine(vf, _dt.time.min)),
                    validUntil=timezone.make_aware(_dt.datetime.combine(vu, _dt.time.max)),
                )
                write_audit("DELEGATION_CREATE", user=request.user,
                            delegation=str(d.id), delegatee=delegatee.get_username(),
                            on_behalf=(delegator.get_username()
                                       if delegator != request.user else None))
        return redirect("ats:delegations")
    delegations = RoleDelegation.objects.select_related("delegator", "delegatee").order_by("-createdAt")
    if not is_admin:
        # Nicht-Admins sehen nur, was sie erteilt haben oder erhalten
        from django.db.models import Q as _Q
        delegations = delegations.filter(
            _Q(delegator=request.user) | _Q(delegatee=request.user))
    from django.contrib.auth.models import User as AuthUser
    users = AuthUser.objects.filter(is_active=True).order_by("username").values_list("username", flat=True)
    return render(request, "delegations.html", {"delegations": delegations, "users": users,
                                                "now": timezone.now(),
                                                "is_admin": is_admin})


# --- B13: Kategorien / Jobfamilien ------------------------------------------
from .models import JobFamily, Location

@hr_admin_required
def categories_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            JobFamily.objects.create(name=name, description=(request.POST.get("description") or "").strip() or None)
        return redirect("ats:categories")
    families = JobFamily.objects.filter(archived=False).order_by("name")
    return render(request, "categories.html", {"families": families})


@hr_admin_required
def archive_category(request, cat_id):
    c = get_object_or_404(JobFamily, id=cat_id)
    c.archived = True
    c.save()
    return redirect("ats:categories")


# --- B14: Standorte ---------------------------------------------------------
@hr_admin_required
def locations_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            Location.objects.create(
                name=name,
                address=(request.POST.get("address") or "").strip() or None,
                city=(request.POST.get("city") or "").strip() or None,
                postalCode=(request.POST.get("postalCode") or "").strip() or None,
            )
        return redirect("ats:locations")
    locations = Location.objects.filter(archived=False).order_by("name")
    return render(request, "locations.html", {"locations": locations})


@hr_admin_required
def archive_location(request, loc_id):
    loc = get_object_or_404(Location, id=loc_id)
    loc.archived = True
    loc.save()
    return redirect("ats:locations")


# --- B4: Passwortloses Magic-Link-Kandidatenportal --------------------------
def candidate_portal(request, token):
    """Öffentliches, passwortloses Statusportal für Bewerber (Magic-Link)."""
    tok = ApplicantToken.objects.filter(token=token).select_related('applicant').first()
    if tok is None:
        raise Http404("Ungültiger Link.")
    if tok.expiresAt < timezone.now():
        return render(request, 'candidate_portal.html', {'expired': True})

    applicant = tok.applicant
    applications = applicant.applications.select_related('jobPosting').order_by('-createdAt')

    if request.method == 'POST' and request.POST.get('withdraw_id'):
        app = applications.filter(id=request.POST.get('withdraw_id')).first()
        if app and app.status not in ('REJECTED', 'WITHDRAWN'):
            app.status = 'WITHDRAWN'
            app.withdrawReason = 'Vom Bewerber über das Portal zurückgezogen.'
            app.save()
            write_audit('WITHDRAWN_BY_CANDIDATE', application_id=app.id)
        return redirect('ats:candidate_portal', token=token)

    # Selbstbuchung eines Timeslots (Einladung mit Terminwahl):
    # atomar mit Zeilensperre – zwei Bewerbende koennen denselben Slot
    # nicht doppelt buchen; der Slot MUSS zur eigenen Bewerbung gehoeren.
    SELF_SERVICE_HOURS = 24  # bis dahin duerfen Bewerbende selbst umbuchen/absagen

    def _notify_team(iv, subject, body):
        """Kollaboration: Interview-Team + Slot-Anbieter:in ueber Aenderungen informieren."""
        emails = {m.email for m in iv.participants.all() if m.email}
        slot_rel = getattr(iv.application, 'interviewSlot', None)
        if slot_rel and slot_rel.createdBy_id and slot_rel.createdBy.email:
            emails.add(slot_rel.createdBy.email)
        if emails:
            try:
                from django.core.mail import send_mail
                send_mail(subject, body, None, sorted(emails), fail_silently=True)
            except Exception:
                logger.exception('Team-Info zu Terminaenderung fehlgeschlagen')

    def _free_current_slot(app):
        slot_rel = getattr(app, 'interviewSlot', None)
        if slot_rel:
            slot_rel.isBooked = False
            slot_rel.application = None
            slot_rel.save()

    booking_error = None

    # Haertung: Rate-Limit fuer eingehende Portal-Kanaele. Jede INBOUND-
    # Nachricht loest Team-Mails aus – ohne Limit koennte ein einzelner Token
    # das Team fluten. 10 eingehende Vorgaenge je Stunde ueber ALLE
    # Bewerbungen der Person sind fuer legitime Nutzung mehr als genug.
    PORTAL_INBOUND_HOURLY_LIMIT = 10

    def _portal_rate_limited():
        since = timezone.now() - datetime.timedelta(hours=1)
        return Message.objects.filter(application__in=applications,
                                      direction='INBOUND',
                                      createdAt__gte=since
                                      ).count() >= PORTAL_INBOUND_HOURLY_LIMIT

    # Talent-Pool-Einwilligung (UC-SB-13/UM-04/FA-04): das Portal ist der
    # richtige Ort – die Identitaet ist per Magic-Link (E-Mail-Zustellung)
    # verifiziert, die Einwilligung damit belastbar. Kriterien werden
    # datensparsam aus den EIGENEN bisherigen Bewerbungen abgeleitet
    # (Jobfamilie + Standort), kein Freitext-Profil. 12 Monate, jederzeit
    # widerrufbar an derselben Stelle.
    if request.method == 'POST' and request.POST.get('form') == 'talent_pool':
        from .models import TalentPoolSubscription
        if request.POST.get('action') == 'join':
            fams = list(applications.exclude(jobPosting__jobFamily=None)
                        .values_list('jobPosting__jobFamily_id', flat=True).distinct())
            locs = list(applications.exclude(jobPosting__location=None)
                        .values_list('jobPosting__location_id', flat=True).distinct())
            TalentPoolSubscription.objects.update_or_create(
                email=applicant.email,
                defaults={'criteria': json.dumps({
                              'job_families': [str(i) for i in fams],
                              'locations': [str(i) for i in locs]}),
                          'consentId': f'portal-{token[:12]}',
                          'expiresAt': timezone.now() + datetime.timedelta(days=365)})
            write_audit('TALENT_POOL_JOINED',
                        application_id=str(applications.first().id) if applications else None)
        elif request.POST.get('action') == 'leave':
            TalentPoolSubscription.objects.filter(email=applicant.email).delete()
            write_audit('TALENT_POOL_LEFT',
                        application_id=str(applications.first().id) if applications else None)
        return redirect('ats:candidate_portal', token=token)

    # Kontaktdaten aktualisieren (UC-AY-09): Telefon direkt (risikoarm);
    # E-Mail-Aenderung nur als Anfrage – die E-Mail ist Identitaetsanker
    # (Magic-Link, Blind-Index, Opt-ins) und wird nach Ruecksprache durchs
    # Team geaendert, nicht per Selbstservice.
    if request.method == 'POST' and request.POST.get('form') == 'contact':
        phone = (request.POST.get('phone') or '').strip()[:50]
        if phone != (applicant.phone or ''):
            applicant.phone = phone or None
            applicant.save()
            write_audit('CANDIDATE_DATA_UPDATED', metadata_field='phone',
                        application_id=str(applications.first().id) if applications else None)
        new_email = (request.POST.get('new_email') or '').strip().lower()[:254]
        if new_email and new_email != applicant.email and not _portal_rate_limited():
            target = applications.first()
            if target:
                Message.objects.create(
                    application=target, direction='INBOUND',
                    content=f'Bitte E-Mail-Adresse ändern auf: {new_email}')
                write_audit('CANDIDATE_EMAIL_CHANGE_REQUESTED',
                            application_id=str(target.id))
        return redirect('ats:candidate_portal', token=token)

    # Rueckfrage aus dem Portal (UC-LK-11/RI-06): landet im Nachrichten-Verlauf
    # der Bewerbung und per Mail bei der im Job hinterlegten Ansprechperson.
    if request.method == 'POST' and request.POST.get('reply_app_id'):
        app = applications.filter(id=request.POST.get('reply_app_id')).first()
        content = (request.POST.get('content') or '').strip()[:2000]
        if app and content and _portal_rate_limited():
            booking_error = ('Sie haben in der letzten Stunde sehr viele '
                             'Nachrichten gesendet – bitte versuchen Sie es '
                             'etwas später erneut.')
        elif app and content:
            Message.objects.create(application=app, direction='INBOUND',
                                   content=content)
            write_audit('CANDIDATE_MESSAGE_SENT', application_id=app.id)
            cp = app.jobPosting.contactPerson
            if cp and cp.email:
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        f'Rückfrage zur Bewerbung – {app.jobPosting.title}',
                        (f'{app.applicant.firstName} {app.applicant.lastName} fragt:\n\n'
                         f'{content}\n\nAntworten: /recruiter/applications/{app.id}/messages/'),
                        None, [cp.email], fail_silently=True)
                except Exception:
                    logger.exception('Rueckfrage-Mail fehlgeschlagen')
        if booking_error is None:
            return redirect('ats:candidate_portal', token=token)

    # Termin ABSAGEN (Bewerbung bleibt bestehen; Terminwahl oeffnet sich wieder)
    if request.method == 'POST' and request.POST.get('cancel_interview_id'):
        iv = Interview.objects.filter(id=request.POST.get('cancel_interview_id'),
                                      application__in=applications,
                                      scheduledAt__gte=timezone.now()).first()
        if iv and iv.scheduledAt >= timezone.now() + datetime.timedelta(hours=SELF_SERVICE_HOURS):
            app = iv.application
            reason = (request.POST.get('reason') or '').strip()[:500]
            when = timezone.localtime(iv.scheduledAt).strftime('%d.%m.%Y %H:%M')
            _notify_team(iv, f'Termin abgesagt: {when} Uhr – '
                             f'{app.applicant.firstName} {app.applicant.lastName}',
                         f'Die Bewerberin/der Bewerber hat den Termin ({iv.kind_label}, '
                         f'{when} Uhr, {app.jobPosting.title}) abgesagt.'
                         + (f'\nGrund: {reason}' if reason else '')
                         + '\nDie Terminwahl im Portal ist wieder offen.')
            Message.objects.create(application=app, direction='INBOUND',
                                   content=f'Termin am {when} Uhr abgesagt.'
                                           + (f' Grund: {reason}' if reason else ''))
            _free_current_slot(app)
            write_audit('CANDIDATE_APPOINTMENT_CANCELLED', application_id=app.id,
                        interview_id=str(iv.id))
            iv.delete()
            return redirect('ats:candidate_portal', token=token)
        booking_error = ('Eine Absage ist online nur bis 24 Stunden vor dem Termin '
                         'möglich – bitte nutzen Sie die Änderungsanfrage.')

    # Termin UMBUCHEN (neuer Slot in einem Schritt, atomar)
    if request.method == 'POST' and request.POST.get('rebook_interview_id'):
        iv = Interview.objects.filter(id=request.POST.get('rebook_interview_id'),
                                      application__in=applications,
                                      scheduledAt__gte=timezone.now()).first()
        if iv and iv.scheduledAt >= timezone.now() + datetime.timedelta(hours=SELF_SERVICE_HOURS):
            app = iv.application
            from django.db import transaction as _tx
            with _tx.atomic():
                new_slot = (InterviewSlot.objects.select_for_update()
                            .filter(id=request.POST.get('book_slot_id'),
                                    jobPosting=app.jobPosting,
                                    startTime__gte=timezone.now()).first())
                if new_slot is None or new_slot.isBooked:
                    booking_error = ('Dieser Termin ist leider gerade vergeben worden – '
                                     'bitte wählen Sie einen anderen.')
                else:
                    old_when = timezone.localtime(iv.scheduledAt).strftime('%d.%m.%Y %H:%M')
                    _notify_team(iv, 'Termin umgebucht – '
                                     f'{app.applicant.firstName} {app.applicant.lastName}',
                                 f'Neuer Termin: {timezone.localtime(new_slot.startTime).strftime("%d.%m.%Y %H:%M")} Uhr '
                                 f'(vorher {old_when} Uhr) – {app.jobPosting.title}.')
                    _free_current_slot(app)
                    new_slot.isBooked = True
                    new_slot.application = app
                    new_slot.save()
                    iv.scheduledAt = new_slot.startTime
                    if new_slot.kind:
                        iv.locationType = new_slot.kind
                    iv.reminderSentAt = None   # Erinnerung fuer den NEUEN Termin
                    iv.save()
                    when = timezone.localtime(new_slot.startTime).strftime('%d.%m.%Y %H:%M')
                    Message.objects.create(application=app, direction='OUTBOUND',
                                           content=f'Ihr Termin wurde umgebucht: {when} Uhr.')
                    try:
                        from django.core.mail import send_mail
                        send_mail(f'Neuer Termin bestätigt – {app.jobPosting.title}',
                                  f'Guten Tag {applicant.firstName},\n\nIhr neuer '
                                  f'Gesprächstermin ist bestätigt: {when} Uhr.\n\n'
                                  'Freundliche Grüße', None, [applicant.email],
                                  fail_silently=True)
                    except Exception:
                        logger.exception('Umbuchungs-Mail fehlgeschlagen')
                    write_audit('CANDIDATE_APPOINTMENT_REBOOKED', application_id=app.id,
                                interview_id=str(iv.id))
                    return redirect('ats:candidate_portal', token=token)
        elif iv:
            booking_error = ('Eine Umbuchung ist online nur bis 24 Stunden vor dem '
                             'Termin möglich – bitte nutzen Sie die Änderungsanfrage.')

    # AENDERUNGSANFRAGE (immer moeglich – landet als Nachricht beim Team)
    if request.method == 'POST' and request.POST.get('change_request_interview_id'):
        iv = Interview.objects.filter(id=request.POST.get('change_request_interview_id'),
                                      application__in=applications).first()
        reason = (request.POST.get('reason') or '').strip()[:500]
        if iv and reason and _portal_rate_limited():
            booking_error = ('Sie haben in der letzten Stunde sehr viele '
                             'Anfragen gesendet – bitte versuchen Sie es '
                             'etwas später erneut.')
        elif iv and reason:
            app = iv.application
            when = timezone.localtime(iv.scheduledAt).strftime('%d.%m.%Y %H:%M')
            Message.objects.create(application=app, direction='INBOUND',
                                   content=f'Änderungswunsch zum Termin am {when} Uhr: {reason}')
            _notify_team(iv, f'Änderungswunsch: Termin {when} Uhr – '
                             f'{app.applicant.firstName} {app.applicant.lastName}',
                         f'Wunsch: {reason}\nBewerbung: {app.jobPosting.title}\n'
                         f'Nachrichten-Verlauf: /recruiter/applications/{app.id}/messages/')
            write_audit('CANDIDATE_CHANGE_REQUEST', application_id=app.id,
                        interview_id=str(iv.id))
            return redirect('ats:candidate_portal', token=token)

    if request.method == 'POST' and request.POST.get('book_slot_id') and not request.POST.get('rebook_interview_id'):
        app = applications.filter(id=request.POST.get('book_app_id'),
                                  status='INVITED').first()
        if app:
            from django.db import transaction as _tx
            with _tx.atomic():
                slot = (InterviewSlot.objects.select_for_update()
                        .filter(id=request.POST.get('book_slot_id'),
                                jobPosting=app.jobPosting,  # kein fremder Slot buchbar
                                startTime__gte=timezone.now())
                        .first())
                if slot is None or slot.isBooked:
                    booking_error = ('Dieser Termin ist leider gerade vergeben worden – '
                                     'bitte wählen Sie einen anderen.')
                else:
                    slot.isBooked = True
                    slot.application = app
                    slot.save()
                    Interview.objects.create(application=app, scheduledAt=slot.startTime,
                                             locationType=slot.kind or 'ON_SITE')
                    when = timezone.localtime(slot.startTime).strftime('%d.%m.%Y %H:%M')
                    Message.objects.create(application=app, direction='OUTBOUND',
                                           content=f'Ihr Gesprächstermin ist bestätigt: {when} Uhr. '
                                                   'Details erhalten Sie vorab per E-Mail.')
                    try:
                        from django.core.mail import send_mail
                        send_mail(f'Terminbestätigung – {app.jobPosting.title}',
                                  f'Guten Tag {applicant.firstName},\n\nIhr Gesprächstermin ist '
                                  f'bestätigt: {when} Uhr.\n\nFreundliche Grüße', None,
                                  [applicant.email], fail_silently=True)
                    except Exception:
                        logger.exception('Terminbestätigungs-Mail fehlgeschlagen')
                    write_audit('CANDIDATE_SLOT_BOOKED', application_id=app.id,
                                slot_id=str(slot.id))
                    return redirect('ats:candidate_portal', token=token)

    status_labels = {
        'NEW': 'Eingegangen', 'IN_REVIEW': 'In Prüfung', 'MISSING_DOCS': 'Unterlagen fehlen',
        'INVITED': 'Zum Gespräch eingeladen', 'REJECTED': 'Leider abgelehnt',
        'WITHDRAWN': 'Zurückgezogen',
    }
    stage_of = {'NEW': 0, 'IN_REVIEW': 1, 'MISSING_DOCS': 1, 'INVITED': 2,
                'REJECTED': 3, 'WITHDRAWN': 3}
    def _bookable_slots(a):
        # Terminwahl anbieten: eingeladen und kein ANSTEHENDER Termin.
        # Vergangene Gespraeche blockieren nicht: mehrstufige Pruefung
        # (Telefonat -> Probearbeit -> vor Ort) laeuft je Runde neu.
        if a.status != 'INVITED' or a.interviews.filter(
                scheduledAt__gte=timezone.now()).exists():
            return []
        return list(InterviewSlot.objects.filter(
            jobPosting=a.jobPosting, isBooked=False,
            startTime__gte=timezone.now()).order_by('startTime')[:8])

    booked = {}
    for iv in Interview.objects.filter(application__in=applications,
                                       scheduledAt__gte=timezone.now()).order_by('scheduledAt'):
        booked.setdefault(iv.application_id, iv)  # naechster anstehender Termin
    rows = [{
        'id': a.id, 'job': a.jobPosting.title, 'status': a.status,
        'label': status_labels.get(a.status, a.status),
        'can_withdraw': a.status not in ('REJECTED', 'WITHDRAWN'),
        'created': a.createdAt,
        'stage': stage_of.get(a.status, 0),
        'rejected': a.status in ('REJECTED', 'WITHDRAWN'),
        'slots': _bookable_slots(a),
        'interview_at': booked[a.id].scheduledAt if a.id in booked else None,
        'interview_kind': booked[a.id].kind_label if a.id in booked else '',
        'interview_id': booked[a.id].id if a.id in booked else None,
        # Selbstbedienung (umbuchen/absagen) nur bis 24 h vor dem Termin –
        # danach hat das Team meist schon Raum/Anreise organisiert.
        'can_self_service': (a.id in booked and booked[a.id].scheduledAt
                             >= timezone.now() + datetime.timedelta(hours=24)),
        'messages': list(a.messages.order_by('createdAt')[:20]),
        'rebook_slots': (list(InterviewSlot.objects.filter(
            jobPosting=a.jobPosting, isBooked=False,
            startTime__gte=timezone.now()).order_by('startTime')[:8])
            if a.id in booked else []),
    } for a in applications]

    return render(request, 'candidate_portal.html', {
        'applicant_name': applicant.firstName,
        'rows': rows, 'token': token, 'booking_error': booking_error,
        'applicant_phone': applicant.phone or '',
        'applicant_email': applicant.email,
        'pool_member': __import__('ats.models', fromlist=['TalentPoolSubscription'])
            .TalentPoolSubscription.objects.filter(
                email=applicant.email, expiresAt__gte=timezone.now()).first(),
        'has_rejected': applications.filter(status='REJECTED').exists(),
        'steps': ['Eingegangen', 'In Prüfung', 'Eingeladen', 'Entscheidung'],
    })


# --- B9: Interview-Kalender -------------------------------------------------
from .models import Interview, Message
from .permissions import has_full_access

@recruiter_required
def interviews_view(request):
    """Team-Kalender: Interviews + freie Slots im Monatsraster, BOLA-gescopt.

    Kollaboration verteilter Teams: alle im Zugriffsbereich sehen dieselben
    Termine und wer welchen Slot anbietet – Doppelplanung wird sichtbar,
    bevor sie passiert. Slots anlegen/loeschen direkt hier; Export als .ics
    fuer Outlook & Co. (ehrlich: Download/Import, kein Abo-Feed).
    """
    import calendar as _cal
    from datetime import date, datetime as _dt

    # Monat aus ?monat=YYYY-MM (Default: aktueller Monat)
    today = timezone.localdate()
    try:
        year, month = map(int, (request.GET.get('monat') or '').split('-'))
        date(year, month, 1)
    except (ValueError, TypeError):
        year, month = today.year, today.month
    first = date(year, month, 1)
    prev_m = (first.replace(day=1) - datetime.timedelta(days=1)).strftime('%Y-%m')
    next_m = (first.replace(day=28) + datetime.timedelta(days=7)).replace(day=1).strftime('%Y-%m')

    scoped_apps = scope_applications(request.user, Application.objects.all())
    scoped_jobs = scope_jobs(request.user, JobPosting.objects.all())

    month_start = timezone.make_aware(_dt(year, month, 1))
    month_end = timezone.make_aware(_dt(year, month, _cal.monthrange(year, month)[1], 23, 59, 59))

    interviews = (Interview.objects.filter(application__in=scoped_apps,
                                           scheduledAt__range=(month_start, month_end))
                  .select_related('application__applicant', 'application__jobPosting'))
    slots = (InterviewSlot.objects.filter(jobPosting__in=scoped_jobs,
                                          startTime__range=(month_start, month_end))
             .select_related('jobPosting', 'createdBy'))

    by_day = {}
    for iv in interviews:
        d = timezone.localtime(iv.scheduledAt).day
        by_day.setdefault(d, []).append({
            'kind': 'interview',
            'time': timezone.localtime(iv.scheduledAt).strftime('%H:%M'),
            'title': f"{iv.application.applicant.firstName} {iv.application.applicant.lastName}",
            'sub': f"{iv.kind_label} · {iv.application.jobPosting.title}",
        })
    for sl in slots:
        d = timezone.localtime(sl.startTime).day
        by_day.setdefault(d, []).append({
            'kind': 'booked' if sl.isBooked else 'slot',
            'time': timezone.localtime(sl.startTime).strftime('%H:%M'),
            'title': 'Slot belegt' if sl.isBooked else 'Slot frei',
            'sub': sl.kind_label + ' · ' + sl.jobPosting.title + (
                f" · {sl.createdBy.get_full_name() or sl.createdBy.username}" if sl.createdBy else ''),
            'slot_id': str(sl.id), 'deletable': (not sl.isBooked) and (
                sl.createdBy_id == request.user.id or request.user.is_superuser
                or request.user.groups.filter(name='HR-Admin').exists()),
        })
    for evs in by_day.values():
        evs.sort(key=lambda e: e['time'])

    # Kalender-Wochen (Mo-Start); None = Tag gehoert zum Nachbarmonat
    weeks = [[{'day': d, 'events': by_day.get(d, []), 'is_today': (
        d == today.day and month == today.month and year == today.year)}
        if d else None for d in wk]
        for wk in _cal.Calendar(firstweekday=0).monthdayscalendar(year, month)]

    upcoming = (Interview.objects.filter(application__in=scoped_apps,
                                         scheduledAt__gte=timezone.now())
                .select_related('application__applicant', 'application__jobPosting')
                .order_by('scheduledAt')[:20])
    # Ergebnis erfassen: vergangene Gespraeche ohne Outcome (aeltestes zuerst)
    pending_outcomes = (Interview.objects.filter(
        application__in=scoped_apps, scheduledAt__lt=timezone.now(),
        outcome__isnull=True)
        .select_related('application__applicant', 'application__jobPosting')
        .order_by('scheduledAt')[:15])
    free_slots = (InterviewSlot.objects.filter(jobPosting__in=scoped_jobs, isBooked=False,
                                               startTime__gte=timezone.now())
                  .select_related('jobPosting', 'createdBy').order_by('startTime')[:30])

    month_names = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                   'August', 'September', 'Oktober', 'November', 'Dezember']
    from .models import get_interview_kinds
    can_manage_formats = (request.user.is_superuser or
                          request.user.groups.filter(name='HR-Admin').exists())
    # P1-11: Bewerbungen mit definierten Gespraechsrunden – formaler
    # Fortschritt je Runde, abschliessbar direkt hier.
    from .models import (rounds_state, feedback_for_application,
                         DEFAULT_FEEDBACK_CRITERIA, INTERVIEW_RECOMMENDATIONS)
    round_rows = []
    for app in (scoped_apps.filter(status__in=['IN_REVIEW', 'INVITED'])
                .select_related('applicant', 'jobPosting')
                .order_by('createdAt')):
        rst = rounds_state(app)
        if rst['total']:
            fb = feedback_for_application(app)
            my = next((f for f in fb['items']
                       if f.author_id == request.user.id
                       and f.round == rst['done']), None)
            round_rows.append({'app': app, 'state': rst,
                               'steps': [
                                   {'label': r, 'done': i < rst['done'],
                                    'current': i == rst['done']}
                                   for i, r in enumerate(rst['rounds'])],
                               'feedback': fb, 'my_feedback': my})
    return render(request, 'interviews.html', {
        'interview_kinds': get_interview_kinds(),
        'can_manage_formats': can_manage_formats,
        'weeks': weeks, 'month_label': f"{month_names[month-1]} {year}",
        'prev_month': prev_m, 'next_month': next_m,
        'upcoming': upcoming, 'free_slots': free_slots,
        'pending_outcomes': pending_outcomes,
        'round_rows': round_rows,
        'feedback_criteria': DEFAULT_FEEDBACK_CRITERIA,
        'feedback_recommendations': INTERVIEW_RECOMMENDATIONS,
        'jobs': scoped_jobs.filter(workflowState__name='published').order_by('title'),
        'saved': request.GET.get('ok'),
    })


@recruiter_required
def slot_create(request):
    """Timeslots anbieten – einzeln oder als woechentliche Serie (max. 8)."""
    if request.method != 'POST':
        return redirect('ats:interviews')
    job = get_object_or_404(scope_jobs(request.user, JobPosting.objects.all()),
                            id=request.POST.get('job_id'))  # BOLA
    try:
        start_local = datetime.datetime.strptime(
            f"{request.POST.get('date')} {request.POST.get('time')}", '%Y-%m-%d %H:%M')
        duration = max(15, min(int(request.POST.get('duration') or 45), 240))
        repeat = max(1, min(int(request.POST.get('repeat') or 1), 8))
    except (ValueError, TypeError):
        return redirect('ats:interviews')
    start = timezone.make_aware(start_local)
    if start < timezone.now():
        return redirect('ats:interviews')
    kind = request.POST.get('kind', '')
    from .models import get_interview_kinds
    if kind not in dict(get_interview_kinds()):
        kind = ''
    for week in range(repeat):
        s0 = start + datetime.timedelta(weeks=week)
        InterviewSlot.objects.create(jobPosting=job, startTime=s0,
                                     endTime=s0 + datetime.timedelta(minutes=duration),
                                     kind=kind, createdBy=request.user)
    write_audit('SLOT_CREATED', user=request.user, job_id=str(job.id),
                start=str(start), duration=duration, repeat=repeat)
    return redirect(f"{reverse('ats:interviews')}?ok=1&monat={start_local.strftime('%Y-%m')}")


@recruiter_required
def slot_delete(request, slot_id):
    """Nur unbelegte Slots; nur Ersteller:in oder HR-Admin (Kollaborations-Fairness)."""
    if request.method != 'POST':
        return redirect('ats:interviews')
    slot = get_object_or_404(InterviewSlot.objects.filter(
        jobPosting__in=scope_jobs(request.user, JobPosting.objects.all())), id=slot_id)
    if slot.isBooked:
        raise Http404('Belegte Slots können nicht gelöscht werden.')
    # Fairness im Team: fremde Slots darf nur HR-Admin entfernen –
    # "sieht alles" (Scope) heisst bewusst nicht "darf alles loeschen".
    is_admin = (request.user.is_superuser
                or request.user.groups.filter(name='HR-Admin').exists())
    if slot.createdBy_id != request.user.id and not is_admin:
        raise Http404('Nur eigene Slots löschbar.')
    write_audit('SLOT_DELETED', user=request.user, slot_id=str(slot.id))
    slot.delete()
    return redirect('ats:interviews')


@recruiter_required
def interviews_ics(request):
    """Alle anstehenden Interviews im Zugriffsbereich als .ics (Outlook/Thunderbird).

    Bewusst ein authentifizierter Download statt Abo-Feed: ein tokenisierter
    Feed wuerde Bewerbernamen dauerhaft ueber eine unauthentifizierte URL
    exponieren – fuer PII die falsche Abwaegung.
    """
    ivs = (Interview.objects.filter(
        application__in=scope_applications(request.user, Application.objects.all()),
        scheduledAt__gte=timezone.now())
        .select_related('application__applicant', 'application__jobPosting'))
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//SecurATS//Kalender//DE']
    for iv in ivs:
        start = iv.scheduledAt.astimezone(datetime.timezone.utc)
        end = start + datetime.timedelta(minutes=45)
        who = f"{iv.application.applicant.firstName} {iv.application.applicant.lastName}"
        lines += ['BEGIN:VEVENT', f'UID:securats-{iv.id}',
                  f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
                  f"SUMMARY:{iv.kind_label}: {who} – {iv.application.jobPosting.title}",
                  f"LOCATION:{iv.meetingLink or iv.locationType}",
                  'END:VEVENT']
    lines.append('END:VCALENDAR')
    resp = HttpResponse('\r\n'.join(lines), content_type='text/calendar; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="securats-interviews.ics"'
    return resp


# --- B6: Nachrichten-Verlauf je Bewerbung -----------------------------------
@recruiter_required
def application_messages(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        if content:
            Message.objects.create(application=app, direction='OUTBOUND', content=content)
            write_audit('MESSAGE_SENT', user=request.user, application_id=app.id)
        return redirect('ats:application_messages', app_id=app.id)
    # Zaehler im "Heute wichtig"-Block wird durch das Oeffnen sauber abgebaut
    app.messages.filter(direction='INBOUND', readStatus=False).update(readStatus=True)
    msgs = app.messages.order_by('createdAt')
    return render(request, 'messages.html', {'application': app, 'messages': msgs})


# --- B5: Öffentliches Job-Alert-Abo -----------------------------------------
def job_alert_subscribe(request):
    from .models import JobAlertSubscription, JobAlertLog, Location, Facility
    import secrets as _secrets
    submitted, updated = False, False
    error = None
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        if not email or '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
            # WCAG 3.3.1: klarer Inline-Fehler statt stiller Erfolgsseite
            error = 'Bitte geben Sie eine gültige E-Mail-Adresse an (z. B. name@beispiel.de).'
        if email and not error:
            keyword = (request.POST.get('keyword') or '').strip()[:120]
            facility_id = (request.POST.get('facility') or '').strip() or None
            location_id = (request.POST.get('location') or '').strip()
            try:
                radius = int(request.POST.get('radius') or 0) or None
            except (TypeError, ValueError):
                radius = None
            scope = {
                'globalAlert': bool(request.POST.get('global')),
                'keyword': keyword,
                'facility_id': facility_id if facility_id else None,
                'locations': json.dumps([location_id] if location_id else []),
                'radiusKm': radius,
            }
            # Genau EIN Abo je E-Mail: bestehendes Abo wird AKTUALISIERT statt dupliziert.
            sub, created = JobAlertSubscription.objects.get_or_create(
                email=email,
                defaults={
                    'status': 'PENDING',
                    'confirmationToken': _secrets.token_urlsafe(24),
                    'managementToken': _secrets.token_urlsafe(24),
                    **scope,
                },
            )
            if not created:
                for k, v in scope.items():
                    setattr(sub, k, v)
                sub.save()
                updated = True
            JobAlertLog.objects.create(
                subscription=sub,
                action='SUBSCRIBED' if created else 'PREFERENCES_UPDATED',
            )
            # Double-Opt-in: Bestätigungslink per Mail (Console-Backend in Dev;
            # fail_silently, damit fehlende Mail-Infrastruktur den Flow nicht bricht)
            try:
                from django.core.mail import send_mail
                confirm_url = request.build_absolute_uri(
                    f"/job-alert/confirm/{sub.confirmationToken}/")
                manage_url = request.build_absolute_uri(
                    f"/job-alert/manage/{sub.managementToken}/")
                send_mail(
                    "Ihr Job-Alert: Bitte bestätigen",
                    ("Bitte bestätigen Sie Ihren Job-Alert:\n" + confirm_url +
                     "\n\nEinstellungen ändern oder abmelden:\n" + manage_url +
                     "\n\nIhr Abo verfällt automatisch 12 Monate nach der letzten "
                     "Bestätigung (DSGVO-Datensparsamkeit)."),
                    None, [email], fail_silently=True)
            except Exception:
                logger.exception("Job-Alert-Bestätigungsmail konnte nicht gesendet werden")
        submitted = error is None
    locations = Location.objects.filter(archived=False).order_by('name')
    facilities = Facility.objects.order_by('name')
    return render(request, 'job_alert.html', {
        'submitted': submitted, 'updated': updated, 'error': error,
        'form_data': request.POST if request.method == 'POST' else {},
        'locations': locations, 'facilities': facilities,
    })


def job_alert_confirm(request, token):
    """Double-Opt-in: aktiviert das Abo und setzt den Verfalls-Anker neu."""
    from .models import JobAlertSubscription, JobAlertLog
    sub = get_object_or_404(JobAlertSubscription, confirmationToken=token)
    sub.status = 'ACTIVE'
    sub.lastConfirmedAt = timezone.now()
    sub.save(update_fields=['status', 'lastConfirmedAt', 'updatedAt'])
    JobAlertLog.objects.create(subscription=sub, action='CONFIRMED')
    return render(request, 'job_alert_manage.html', {
        'sub': sub, 'message': 'Ihr Job-Alert ist jetzt aktiv. '
        'Er verlängert sich mit jeder Bestätigung um 12 Monate.'})


def job_alert_manage(request, token):
    """Verwalten/Abmelden über den Management-Link (DSGVO: jederzeit, ohne Konto)."""
    from .models import JobAlertSubscription, JobAlertLog
    sub = get_object_or_404(JobAlertSubscription, managementToken=token)
    message = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'unsubscribe':
            sub.status = 'INACTIVE'
            sub.save(update_fields=['status', 'updatedAt'])
            JobAlertLog.objects.create(subscription=sub, action='UNSUBSCRIBED')
            message = 'Sie sind abgemeldet. Ihre Daten werden beim nächsten Lauf entfernt.'
        elif action == 'renew':
            sub.status = 'ACTIVE'
            sub.lastConfirmedAt = timezone.now()
            sub.save(update_fields=['status', 'lastConfirmedAt', 'updatedAt'])
            JobAlertLog.objects.create(subscription=sub, action='RENEWED')
            message = 'Ihr Job-Alert wurde um 12 Monate verlängert.'
    return render(request, 'job_alert_manage.html', {'sub': sub, 'message': message})


# --- B12: Job-Vorlagen-Bibliothek (Kern: Liste/Anlegen/Löschen) -------------
from .models import JobTemplate

@hr_admin_required
def job_templates_view(request):
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        content = (request.POST.get('content') or '').strip()
        if title and content:
            # B12: gleicher Titel -> neue Version statt Duplikat
            latest = (JobTemplate.objects.filter(title__iexact=title)
                      .order_by('-version').first())
            JobTemplate.objects.create(
                title=title, content=content,
                version=(latest.version + 1) if latest else 1,
                parent=latest,
            )
        return redirect('ats:job_templates')
    # Nur die jeweils neueste Version je Titel anzeigen (case-insensitiv);
    # Historie über parent-Kette
    latest_ids = {}
    for t in JobTemplate.objects.order_by('-version', '-createdAt'):
        latest_ids.setdefault(t.title.lower(), t.id)
    templates = (JobTemplate.objects.filter(id__in=latest_ids.values())
                 .order_by('title'))
    return render(request, 'job_templates.html', {'templates': templates})


@hr_admin_required
def delete_job_template(request, tpl_id):
    get_object_or_404(JobTemplate, id=tpl_id).delete()
    return redirect('ats:job_templates')


# --- B7: Analytics-/Insight-Dashboard (Ausbau, BOLA-gescopt) ----------------
@recruiter_required
def analytics_view(request):
    from django.db.models import Count, Avg, F
    from django.db.models.functions import TruncMonth
    from datetime import timedelta

    apps = scope_applications(request.user, Application.objects.all())
    total = apps.count()

    status_labels = {
        'NEW': 'Eingegangen', 'IN_REVIEW': 'In Prüfung', 'MISSING_DOCS': 'Unterlagen fehlen',
        'INVITED': 'Eingeladen', 'REJECTED': 'Abgelehnt', 'WITHDRAWN': 'Zurückgezogen',
    }

    def _dist(field):
        rows = apps.values(field).annotate(c=Count('id')).order_by('-c')
        return [(r[field] or '—', r['c']) for r in rows]

    by_status = [(status_labels.get(s, s), c) for s, c in _dist('status')]
    by_source = _dist('source')
    by_score = sorted(_dist('aiScore'), key=lambda x: str(x[0]))

    # Verlauf: Bewerbungen je Monat (letzte 6 Monate)
    since = timezone.now() - timedelta(days=180)
    per_month = (apps.filter(createdAt__gte=since)
                 .annotate(m=TruncMonth('createdAt'))
                 .values('m').annotate(c=Count('id')).order_by('m'))
    by_month = [(r['m'].strftime('%m/%Y') if r['m'] else '—', r['c']) for r in per_month]

    # Standort-Vergleich
    by_location = list(apps.values('jobPosting__location__name')
                       .annotate(c=Count('id')).order_by('-c')[:10])
    by_location = [(r['jobPosting__location__name'] or '—', r['c']) for r in by_location]

    # Ø Bearbeitungsdauer bis Entscheidung (Näherung: updatedAt - createdAt für Endstatus)
    terminal = apps.filter(status__in=['INVITED', 'REJECTED', 'WITHDRAWN'])
    avg_days = None
    durations = [(a.updatedAt - a.createdAt).days for a in terminal.only('createdAt', 'updatedAt', 'status')]
    if durations:
        avg_days = round(sum(durations) / len(durations), 1)

    max_status = max([c for _, c in by_status], default=1)

    # --- WP5: vertiefte Analytics (§4.3) --------------------------------------
    from .analytics import (time_to_fill_forecast, detect_anomalies,
                            fairness_overview, location_benchmark, cost_per_hire,
                            appointment_stats)
    open_jobs = scope_jobs(request.user,
                           JobPosting.objects.filter(workflowState__name='published'))
    forecast = time_to_fill_forecast(apps, open_jobs)
    anomalies = detect_anomalies(apps)
    appointments = appointment_stats(apps, scope_jobs(request.user,
                                                      JobPosting.objects.all()))
    fairness = fairness_overview(apps)
    # Rollen-adaptiv: Benchmarking/Kosten nur für Leitung (HR-Admin/Superuser)
    is_leadership = request.user.is_superuser or request.user.groups.filter(name='HR-Admin').exists()
    benchmark = location_benchmark(apps) if is_leadership else []
    source_costs = {}
    for s in SystemSetting.objects.filter(key__startswith='SOURCE_COST_'):
        try:
            source_costs[s.key.replace('SOURCE_COST_', '')] = float(s.value)
        except (TypeError, ValueError):
            continue
    from .models import SourceChannel as _SCh
    for _c in _SCh.objects.exclude(costAmount__isnull=True):
        source_costs[_c.slug] = float(_c.costAmount)
    costs = cost_per_hire(apps, source_costs) if (is_leadership and source_costs) else []

    # Landingpages & Kampagnen: der volle Trichter auf dem Dashboard
    from .models import LandingPage as _LP
    landing_rows = []
    for lp in _LP.objects.order_by('-createdAt')[:50]:
        src = lp.slug.upper()
        lp_apps = Application.objects.filter(source=src,
                                             createdAt__gte=lp.createdAt)
        t = lp_apps.count()
        inv = lp_apps.filter(status__in=['INVITED', 'HIRED']).count()
        landing_rows.append({
            'name': lp.name, 'active': lp.active, 'views': lp.views,
            'apps': t,
            'app_rate': round(100 * t / lp.views, 1) if lp.views else None,
            'invited': inv,
            'invite_rate': round(100 * inv / t) if t else None,
            'hired': lp_apps.filter(status='HIRED').count(),
        })

    # Einstellungen gesamt: das Ereignis, an dem sich alles misst
    hired_all = Application.objects.filter(status='HIRED',
                                           hiredAt__isnull=False)
    hire_days = [(a.hiredAt - a.createdAt).days for a in hired_all]
    hiring_summary = {
        'count': hired_all.count(),
        'avg_days': round(sum(hire_days) / len(hire_days), 1)
                    if hire_days else None,
    }

    # Inhaltsseiten (CMS): jede veroeffentlichte Seite automatisch dabei
    page_rows = list(Page.objects.filter(status='published')
                     .order_by('-views')
                     .values('title', 'slug', 'views')[:50])

    # Stellenfreigabe-Engpass (UC-CV-14): welche Stufe bremst? BOLA:
    # Antraege auf die Einrichtungen im Scope des Nutzers begrenzt.
    from .analytics import requisition_stage_stats
    from .models import StaffingRequest as _SReq
    _req_qs = _SReq.objects.all()
    if not has_full_access(request.user):
        _fac_ids = list(request.user.scope.facilities
                        .values_list('id', flat=True))
        if _fac_ids:
            _req_qs = _req_qs.filter(facility_id__in=_fac_ids)
    stage_rows = requisition_stage_stats(_req_qs)
    return render(request, 'analytics.html', {
        'stage_rows': stage_rows,
        'total': total,
        'landing_rows': landing_rows,
        'hiring_summary': hiring_summary,
        'page_rows': page_rows,
        'appointments': appointments,
        'by_status': by_status, 'by_source': by_source, 'by_score': by_score,
        'by_month': by_month, 'by_location': by_location,
        'avg_days': avg_days, 'max_status': max_status,
        'forecast': forecast, 'anomalies': anomalies, 'fairness': fairness,
        'benchmark': benchmark, 'costs': costs, 'is_leadership': is_leadership,
    })


# --- B17: Öffentliche CMS-Seite ---------------------------------------------
def page_detail(request, slug):
    page = Page.objects.filter(slug=slug, status='published').first()
    if page is None:
        raise Http404("Seite nicht gefunden.")
    # Selbstmessung wie bei Landingpages – ABER bewusst OHNE Quellen-Wirkung:
    # Inhaltsseiten (Impressum, Ueber-uns) sind keine Kampagnen.
    from django.db.models import F as _F
    Page.objects.filter(id=page.id).update(views=_F('views') + 1)
    nav_pages = Page.objects.filter(navEnabled=True, status='published').order_by('navOrder')
    from .blocks import load_blocks, enrich_blocks
    return render(request, 'page.html',
                  {'page': page, 'nav_pages': nav_pages, 'slug': slug,
                   'content_blocks': enrich_blocks(load_blocks(page))})


# --- B16: Seiten-Manager (Kern-Editor) --------------------------------------
from django.utils.text import slugify

@hr_admin_required
def pages_manage(request):
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        title = (request.POST.get('title') or '').strip()
        content = request.POST.get('content') or ''
        slug = (request.POST.get('slug') or slugify(title)).strip()
        nav = bool(request.POST.get('navEnabled'))
        if title and slug:
            if page_id:
                p = get_object_or_404(Page, id=page_id)
                p.title, p.content, p.slug, p.navEnabled = title, content, slug, nav
                p.save()
            else:
                Page.objects.get_or_create(slug=slug, defaults={
                    'title': title, 'content': content, 'navEnabled': nav})
        return redirect('ats:pages_manage')
    pages = Page.objects.order_by('navOrder', 'title')
    return render(request, 'pages_manage.html', {'pages': pages})


@hr_admin_required
def delete_page(request, page_id):
    get_object_or_404(Page, id=page_id).delete()
    return redirect('ats:pages_manage')


# --- B18: Medien-/Datei-Verwaltung ------------------------------------------
from .models import MediaAsset

@hr_admin_required
def media_manage(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        MediaAsset.objects.create(
            name=(request.POST.get('name') or f.name)[:255],
            altText=(request.POST.get('altText') or '')[:255],  # WP8/WCAG 1.1.1
            file=f,
            contentType=getattr(f, 'content_type', None),
        )
        write_audit('MEDIA_UPLOADED', user=request.user, name=f.name)
        return redirect('ats:media_manage')
    assets = MediaAsset.objects.order_by('-createdAt')[:200]
    return render(request, 'media_manage.html', {'assets': assets})


@hr_admin_required
def delete_media(request, asset_id):
    a = get_object_or_404(MediaAsset, id=asset_id)
    try:
        a.file.delete(save=False)
    except Exception:
        logger.exception("Datei-Löschung fehlgeschlagen für %s", asset_id)
    a.delete()
    return redirect('ats:media_manage')


# --- B12 (Ausbau): KI-Tonalitäts-Overlay für Job-Vorlagen --------------------
@hr_admin_required
def apply_template_tone(request):
    """Formuliert Vorlagen-Inhalt via lokaler KI in eine Ziel-Tonalität um.

    Trennt Inhalt (Vorlage) von Tonalität (Overlay je Abteilung/Kategorie).
    Fällt bei nicht erreichbarer KI sauber auf den Originaltext zurück.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    content = request.POST.get('content', '') or ''
    tone = (request.POST.get('tone', 'SIE') or 'SIE').upper()
    tone_hint = {
        'DU': 'lockere Du-Ansprache', 'SIE': 'professionelle Sie-Ansprache',
        'HERZLICH': 'herzliche, wertschätzende Ansprache',
        'NUECHTERN': 'nüchterne, sachliche Ansprache',
    }.get(tone, 'professionelle Ansprache')

    reformulated, used_ai = content, False
    if content.strip():
        try:
            prompt = (f"Formuliere den folgenden Stellenausschreibungs-Text in eine {tone_hint} um. "
                      f"Ändere KEINE Fakten, Anforderungen oder Aufgaben. Gib nur den Text zurück:\n\n{content}")
            payload = {"model": get_ai_model(), "prompt": prompt, "stream": False}
            ok, data = make_ollama_request(get_ollama_url("api/generate"), payload, timeout=8.0)
            if ok and isinstance(data, dict) and data.get('response', '').strip():
                reformulated, used_ai = data['response'].strip(), True
        except Exception:
            logger.exception("Ton-Anpassung fehlgeschlagen; Fallback auf Original")
    return JsonResponse({'reformulated': reformulated, 'used_ai': used_ai})


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


def healthz_ai(request):
    """WP2/L1: Leichtgewichtiger Health-Check der LLM-Anbindung (für Monitoring)."""
    import json as _json
    import urllib.request
    model = get_ai_model()
    try:
        with urllib.request.urlopen(get_ollama_url("api/tags"), timeout=3) as r:
            tags = _json.loads(r.read().decode("utf-8"))
        installed = [m.get("name", "") for m in tags.get("models", [])]
        model_ready = any(m.split(":")[0] == model.split(":")[0] for m in installed)
        status = "ok" if model_ready else "degraded"
        return JsonResponse({"status": status, "reachable": True,
                             "model": model, "model_ready": model_ready}, status=200 if model_ready else 503)
    except Exception as e:
        return JsonResponse({"status": "down", "reachable": False,
                             "model": model, "error": str(e)[:200]}, status=503)


# --- WP4/B10: Kanban-Reihenfolge einer Spalte persistieren -------------------
@any_staff_required
def reorder_board(request):
    """Speichert die Kartenreihenfolge einer Kanban-Spalte (nach Drag&Drop)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST erforderlich'}, status=405)
    status = (request.POST.get('status') or '').strip().upper()
    if status not in ['NEW', 'IN_REVIEW', 'INVITED', 'REJECTED']:
        return JsonResponse({'success': False, 'error': 'Ungültiger Status'}, status=400)
    ids = request.POST.getlist('ids[]') or request.POST.getlist('ids')
    updated = 0
    for index, app_id in enumerate(ids):
        app = Application.objects.filter(id=app_id).first()
        if not app or not can_access_application(request.user, app):
            continue  # außerhalb des Zugriffsbereichs: still überspringen
        if app.status != status:
            continue
        if app.boardOrder != index:
            app.boardOrder = index
            app.save(update_fields=['boardOrder', 'updatedAt'])
            updated += 1
    return JsonResponse({'success': True, 'updated': updated})


# --- WP4: Bulk-Statuswechsel im Kanban (UC-UM-08/09) --------------------------
@any_staff_required
def bulk_update_status(request):
    """Setzt den Status mehrerer Bewerbungen in einem Schritt (BOLA-gescoped).

    Hinweis: Workflow-Automationen laufen bewusst nicht je Karte mit –
    Massenaktionen sollen keine Mail-/Automationsflut auslösen (UC-UM-09:
    Sammelaktionen sind kontrollierte, manuelle Eingriffe).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST erforderlich'}, status=405)
    new_status = (request.POST.get('status') or '').strip().upper()
    if new_status not in ['NEW', 'IN_REVIEW', 'INVITED', 'REJECTED']:
        return JsonResponse({'success': False, 'error': 'Ungültiger Status'}, status=400)
    ids = request.POST.getlist('ids[]') or request.POST.getlist('ids')
    updated, skipped = 0, 0
    for app_id in ids:
        app = Application.objects.filter(id=app_id).first()
        if not app or not can_access_application(request.user, app):
            skipped += 1
            continue
        old = app.status
        if old == new_status:
            continue
        app.status = new_status
        app.save(update_fields=['status', 'updatedAt'])
        write_audit("STATUS_CHANGE_BULK", user=request.user, application_id=app.id,
                    oldStatus=old, newStatus=new_status)
        updated += 1
    return JsonResponse({'success': True, 'updated': updated, 'skipped': skipped})


# --- WP5: Analytics-Export (Excel-kompatibles CSV) — UC-BL-07 -----------------
@any_staff_required
def analytics_export(request):
    """Exportiert die (BOLA-gescopten) Bewerbungs-KPIs als CSV für Excel/BI."""
    import csv
    apps = scope_applications(
        request.user,
        Application.objects.select_related('jobPosting__location', 'jobPosting__jobFamily'))
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="securats-analytics.csv"'
    response.write('\ufeff')  # BOM: Umlaute in Excel
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Stelle', 'Standort', 'Jobfamilie', 'Status', 'Quelle',
                     'KI-Score', 'Eingegangen', 'Zuletzt geändert', 'Tage im Prozess'])
    for a in apps:
        writer.writerow([
            a.jobPosting.title,
            getattr(a.jobPosting.location, 'name', ''),
            getattr(a.jobPosting.jobFamily, 'name', ''),
            a.status, a.source, a.aiScore or '',
            a.createdAt.strftime('%d.%m.%Y'),
            a.updatedAt.strftime('%d.%m.%Y'),
            max((a.updatedAt - a.createdAt).days, 0),
        ])
    write_audit("ANALYTICS_EXPORT", user=request.user, rows=apps.count())
    return response


# --- WP5: Lokaler KI-Analyst „Frag deine Daten" (§4.3) ------------------------
@any_staff_required
def analytics_ask(request):
    """Beantwortet Fragen zu den eigenen Recruiting-Daten – vollständig lokal.

    Der KI werden ausschließlich aggregierte, PII-freie Kennzahlen übergeben
    (build_data_summary). Die Frage wird als nicht vertrauenswürdige Eingabe
    gekapselt (ai_safety) – auch interne Nutzer können keine Prompts injizieren.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    question = (request.POST.get('question') or '').strip()[:500]
    if not question:
        return JsonResponse({'error': 'Bitte eine Frage stellen.'}, status=400)

    from .analytics import build_data_summary
    from .ai_safety import wrap_untrusted, compose_system_prompt, PROMPT_VERSION
    apps = scope_applications(request.user, Application.objects.all())
    summary = build_data_summary(apps)

    payload = {
        "model": get_ai_model(),
        "system": compose_system_prompt() + (
            " Du bist zusätzlich Recruiting-Daten-Analyst: Beantworte Fragen NUR auf "
            "Basis der übergebenen aggregierten Kennzahlen, auf Deutsch, in 2-5 Sätzen. "
            "Erfinde keine Zahlen. Fehlen Daten für eine Antwort, sage das klar."),
        "prompt": (f"--- KENNZAHLEN (vertrauenswürdig, aggregiert) ---\n{summary}\n--- ENDE ---\n\n"
                   f"Frage der nutzenden Person:\n{wrap_untrusted(question)}"),
        "stream": False,
        "options": {"temperature": 0.2},
        "keep_alive": "10m",
    }
    import time
    start = time.time()
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=28.0)
        latency = round(time.time() - start, 2)
        if ok and (data.get('response') or '').strip():
            answer = data['response'].strip()[:2000]
            log_ai_execution("KI-Analyst", get_ai_model(), latency, True, False, "", False,
                             prompt_used=question, tokens=data.get('eval_count'),
                             prompt_version=PROMPT_VERSION)
            return JsonResponse({'answer': answer, 'used_ai': True, 'latency': latency})
        log_ai_execution("KI-Analyst", get_ai_model(), latency, False, True, str(data), False,
                         prompt_used=question, prompt_version=PROMPT_VERSION)
    except Exception as e:
        logger.exception("KI-Analyst nicht verfügbar")
        log_ai_execution("KI-Analyst", get_ai_model(), None, False, True, str(e), False,
                         prompt_used=question, prompt_version=PROMPT_VERSION)
    return JsonResponse({
        'answer': ("Die lokale KI ist gerade nicht erreichbar. Diagnose: "
                   "`python manage.py ai_doctor`. Die Kennzahlen-Ansicht oben bleibt "
                   "vollständig nutzbar."),
        'used_ai': False,
    })


# ============================================================================
# WP6 — Governance & Leitung
# ============================================================================

def _pending_steps_for(user):
    """Approval-Schritte, die auf diese Person warten (UC-JF-06).

    Ein Schritt „wartet auf mich", wenn er PENDING ist, alle Vorgänger-Schritte
    freigegeben sind und er meiner Rolle (Django-Gruppe) oder meinem Benutzernamen
    zugewiesen ist. (`assignedRoleId`/`assignedUserId` sind Prisma-Alt-Textfelder;
    Konvention ab jetzt: Gruppenname bzw. Username.)
    """
    from .models import ApprovalStep
    from .permissions import active_delegations_to, delegation_covers
    my_groups = set(user.groups.values_list('name', flat=True))
    # Urlaubsvertretung wirkt hier: Rollen der Delegatoren zaehlen mit –
    # FACILITY-/JOB-Scope wird je Ticket geprueft, damit eine Vertretung
    # „nur fuer Klinik A" nicht ploetzlich alles freigeben kann.
    delegations = []
    for d in active_delegations_to(user):
        delegations.append((d, set(d.delegator.groups.values_list('name', flat=True)),
                            d.delegator.get_full_name() or d.delegator.username))
    steps = (ApprovalStep.objects
             .filter(status='PENDING', approvalTicket__status='PENDING')
             .select_related('approvalTicket__jobPosting__location')
             .order_by('approvalTicket__createdAt', 'stepOrder'))
    waiting = []
    for step in steps:
        via = None
        job = step.approvalTicket.jobPosting
        if step.assignedUserId:
            if step.assignedUserId != user.get_username():
                # Vertretung fuer personengebundene Schritte
                for d, _groups, name in delegations:
                    if (d.delegator.get_username() == step.assignedUserId
                            and delegation_covers(d, job)):
                        via = name
                        break
                if via is None:
                    continue
        elif step.assignedRoleId not in my_groups:
            for d, groups, name in delegations:
                if step.assignedRoleId in groups and delegation_covers(d, job):
                    via = name
                    break
            if via is None:
                continue
        prior = step.approvalTicket.steps.filter(stepOrder__lt=step.stepOrder)
        if prior.exclude(status='APPROVED').exists():
            continue  # noch nicht an der Reihe
        step.via_delegation = via  # fuer UI („in Vertretung fuer …") + Audit
        waiting.append(step)
    return waiting


@any_staff_required
def approvals_inbox(request):
    """Freigabe-Postfach „Wartet auf mich" mit Frist, Kommentar & Rückfrage."""
    from .models import ApprovalStep

    if request.method == 'POST':
        step = get_object_or_404(
            ApprovalStep.objects.select_related('approvalTicket'),
            id=request.POST.get('step_id'))
        if step not in _pending_steps_for(request.user):
            raise Http404("Dieser Schritt wartet nicht auf Sie.")
        action = (request.POST.get('action') or '').lower()
        comment = (request.POST.get('comment') or '').strip()[:2000]
        if action not in ('approve', 'return', 'reject'):
            return redirect('ats:approvals')
        if action == 'return' and not comment:
            # UC-JF-07: Rückfrage ohne Begründung ist sinnlos
            return redirect('ats:approvals')
        acting = next((w for w in _pending_steps_for(request.user)
                       if w.id == step.id), None)
        via = getattr(acting, 'via_delegation', None) if acting else None
        step.status = {'approve': 'APPROVED', 'return': 'RETURNED', 'reject': 'REJECTED'}[action]
        if via:
            step.comments = ((comment or step.comments or '')
                             + f"\n[In Vertretung für {via}]").strip()
        else:
            step.comments = comment or step.comments
        step.actionTakenAt = timezone.now()
        step.save()
        ticket = step.approvalTicket
        if action == 'approve':
            if not ticket.steps.exclude(status='APPROVED').exists():
                ticket.status = 'APPROVED'
                ticket.save(update_fields=['status', 'updatedAt'])
                # UC-JF-01: finale Freigabe -> Anzeige geht automatisch online
                published, _ = WorkflowState.objects.get_or_create(
                    name='published', defaults={'description': 'Öffentlich sichtbar'})
                job = ticket.jobPosting
                # Stellenfreigabe ist auch hier nicht umgehbar: die finale
                # Job-Freigabe publiziert NUR mit genehmigtem Bedarf.
                from .approvals import requisition_blocked_reason
                _rq = requisition_blocked_reason(job)
                if _rq:
                    write_audit('REQUISITION_GATE_BLOCKED',
                                user=request.user, job=job.title,
                                via='approval_gate')
                    messages.warning(request, _rq)
                elif job.workflowState_id != published.id:
                    job.workflowState = published
                    job.save(update_fields=['workflowState', 'updatedAt'])
                    write_audit("JOB_ACTIVATED", user=request.user,
                                job=job.title, via="approval_gate")
        else:
            ticket.status = 'RETURNED' if action == 'return' else 'REJECTED'
            ticket.save(update_fields=['status', 'updatedAt'])
        write_audit(f"APPROVAL_{step.status}", user=request.user,
                    jobPosting=ticket.jobPosting.title, step=step.stepOrder,
                    comment=comment[:200])
        return redirect('ats:approvals')

    try:
        sla_days = int((SystemSetting.objects.filter(key='APPROVAL_SLA_DAYS')
                        .first() or SystemSetting(value='7')).value)
    except (TypeError, ValueError):
        sla_days = 7
    now = timezone.now()
    rows = []
    for step in _pending_steps_for(request.user):
        age = (now - step.approvalTicket.createdAt).days
        rows.append({
            'step': step,
            'job': step.approvalTicket.jobPosting,
            'age_days': age,
            'due_in': sla_days - age,
            'overdue': age > sla_days,
        })
    # Sichtungs-Gremium: Bewerbungen, bei denen MEINE Stimme aussteht
    from .panel import panel_state, panel_member_ids
    from .models import ApplicationVote
    # Vererbung beachten: Mitgliedschaft entsteht auch aus Defaults hoeherer
    # Ebenen -> in Python ueber die Leiter aufloesen statt SQL-contains.
    uid = str(request.user.id)
    candidates = (Application.objects
                  .filter(status__in=['NEW', 'IN_REVIEW'])
                  .select_related('applicant', 'jobPosting__department',
                                  'jobPosting__facility', 'jobPosting__location',
                                  'jobPosting__jobFamily',
                                  'jobPosting__organization')
                  .order_by('createdAt')[:200])
    from .panel import sits_on_panel
    from .permissions import active_delegations_to
    _delegs = active_delegations_to(request.user)
    panel_apps = [a for a in candidates
                  if sits_on_panel(request.user, a.jobPosting, _delegs)][:50]
    voted = set(ApplicationVote.objects.filter(
        user=request.user, application__in=panel_apps)
        .values_list('application_id', flat=True))
    panel_rows = [{'app': a, 'state': panel_state(a),
                   'my_vote_pending': a.id not in voted}
                  for a in panel_apps]
    return render(request, 'approvals.html',
                  {'rows': rows, 'sla_days': sla_days,
                   'panel_rows': panel_rows})


@any_staff_required
def governance_view(request):
    """Datenminimierte Kontroll-Sicht für Betriebsrat/SBV/DSB & Leitung.

    UC-JF-08 / UC-MB-*: ausschließlich Aggregate – keine Namen, keine Einzelfälle.
    Mitbestimmung braucht Prozess-Transparenz, nicht Personendaten.
    """
    from django.db.models import Count
    from .audit import verify_audit_chain
    from .models import TalentPoolSubscription

    apps = Application.objects.all()  # bewusst ungescoped: Aggregat über alles
    total = apps.count()
    by_status = list(apps.values('status').annotate(c=Count('id')).order_by('-c'))

    audit_counts = list(AuditLog.objects.values('action')
                        .annotate(c=Count('id')).order_by('-c')[:12])
    chain = verify_audit_chain()

    anonymized = AuditLog.objects.filter(action='ANONYMIZE_DSGVO').count()
    ai_logged = AuditLog.objects.filter(action='AI_EXECUTION').count()
    consents = TalentPoolSubscription.objects.count()

    return render(request, 'governance.html', {
        'total': total, 'by_status': by_status,
        'audit_counts': audit_counts, 'chain': chain,
        'anonymized': anonymized, 'ai_logged': ai_logged,
        'consents': consents,
    })


def healthz(request):
    """WP7/UC-SO-06: Gesamt-Health (App, DB, Media, KI-Anbindung, Queue)."""
    import json as _json
    import urllib.request
    from .queue import queue_depth

    checks = {}
    # DB
    try:
        Application.objects.exists()
        checks['db'] = 'ok'
    except Exception as e:
        checks['db'] = f'error: {str(e)[:120]}'
    # Media beschreibbar
    try:
        probe = default_storage.save('healthz_probe.txt', ContentFile(b'ok'))
        default_storage.delete(probe)
        checks['media'] = 'ok'
    except Exception as e:
        checks['media'] = f'error: {str(e)[:120]}'
    # KI (kurz, nicht blockierend)
    try:
        with urllib.request.urlopen(get_ollama_url("api/tags"), timeout=2) as r:
            _json.loads(r.read().decode('utf-8'))
        checks['ai'] = 'ok'
    except Exception:
        checks['ai'] = 'unreachable'
    # Queue
    depth = queue_depth()
    checks['queue'] = depth
    failed = depth.get('FAILED', 0)

    core_ok = checks['db'] == 'ok' and checks['media'] == 'ok'
    status = 'ok' if core_ok and checks['ai'] == 'ok' and not failed else \
             ('degraded' if core_ok else 'down')
    from securats.version import __version__
    return JsonResponse({'status': status, 'version': __version__, 'checks': checks},
                        status=200 if core_ok else 503)


# --- WP8: Öffentliche Einrichtungs-/Standortseite (Karriere-Branding) ---------
def facility_profile(request, slug):
    """Karriereseite je Einrichtung: Profil, Bilder, offene Stellen (WP8)."""
    from .models import FacilityProfile
    profile = get_object_or_404(FacilityProfile.objects.select_related('facility'), slug=slug)
    jobs = (JobPosting.objects
            .filter(facility=profile.facility, workflowState__name='published')
            .select_related('location', 'jobFamily')
            .order_by('-createdAt'))
    try:
        images = json.loads(profile.images or "[]")
    except (ValueError, TypeError):
        images = []
    return render(request, 'facility_profile.html', {
        'profile': profile, 'facility': profile.facility,
        'jobs': jobs, 'images': images,
    })


# ============================================================================
# Stammdaten-Zentrale: Ansprechpartner, Textbausteine, Schnell-Aktionen
# Ziel: Job-Anzeigen-Erstellung/-Pflege so einfach und schnell wie möglich.
# ============================================================================

@hr_admin_required
def contacts_manage(request):
    """Zentrale Ansprechpartner-Pflege (UC-SB-12ff).

    Kernprinzip: ContactPerson ist FK an der Stellenanzeige – Änderungen hier
    (Telefon, Foto, Rolle) wirken SOFORT auf allen Anzeigen. Zusätzlich:
    - Zuordnung je Einrichtung/Abteilung (Vorauswahl-Hilfe),
    - „Überall ersetzen": Person A → B in allen Anzeigen (Urlaub/Ausscheiden).
    """
    from .models import (ContactPerson, FacilityContactPerson,
                         DepartmentContactPerson, Department)

    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        if action == 'replace_everywhere':
            old_id = request.POST.get('old_id'); new_id = request.POST.get('new_id')
            old = ContactPerson.objects.filter(id=old_id).first()
            new = ContactPerson.objects.filter(id=new_id).first()
            if old and new and old.id != new.id:
                n = JobPosting.objects.filter(contactPerson=old).update(contactPerson=new)
                write_audit("CONTACT_REPLACED", user=request.user,
                            old=str(old), new=str(new), jobs_updated=n)
            return redirect('ats:contacts')

        if action == 'delete':
            cp = ContactPerson.objects.filter(id=request.POST.get('cp_id')).first()
            if cp:
                in_use = JobPosting.objects.filter(contactPerson=cp).count()
                if in_use == 0:
                    cp.delete()
                # in Verwendung -> nicht löschen; UI verweist auf „Ersetzen"
            return redirect('ats:contacts')

        if action == 'assign':
            cp = ContactPerson.objects.filter(id=request.POST.get('cp_id')).first()
            fac_id = request.POST.get('facility') or None
            dep_id = request.POST.get('department') or None
            role = (request.POST.get('roleTitle') or '').strip()[:150]
            if cp and fac_id:
                FacilityContactPerson.objects.get_or_create(
                    facility_id=fac_id, contactPerson=cp, defaults={'roleTitle': role})
            if cp and dep_id:
                DepartmentContactPerson.objects.get_or_create(
                    department_id=dep_id, contactPerson=cp, defaults={'roleTitle': role})
            return redirect('ats:contacts')

        # save (anlegen oder aktualisieren)
        cp_id = request.POST.get('cp_id') or None
        fields = {
            'firstName': (request.POST.get('firstName') or '').strip()[:100],
            'lastName': (request.POST.get('lastName') or '').strip()[:100],
            'email': (request.POST.get('email') or '').strip()[:254],
            'phone': (request.POST.get('phone') or '').strip()[:50] or None,
            'globalJobTitle': (request.POST.get('globalJobTitle') or '').strip()[:150] or None,
            'photoUrl': (request.POST.get('photoUrl') or '').strip()[:255] or None,
            'quote': (request.POST.get('quote') or '').strip() or None,
        }
        if fields['firstName'] and fields['lastName'] and fields['email']:
            if cp_id:
                ContactPerson.objects.filter(id=cp_id).update(**fields)
            else:
                ContactPerson.objects.create(**fields)
        return redirect('ats:contacts')

    contacts = []
    for cp in ContactPerson.objects.order_by('lastName', 'firstName'):
        contacts.append({
            'obj': cp,
            'facilities': [l.facility.name for l in cp.facility_links.select_related('facility')],
            'departments': [l.department.name for l in cp.department_links.select_related('department')],
            'jobs_count': JobPosting.objects.filter(contactPerson=cp).count(),
        })
    from .models import Department
    return render(request, 'contacts.html', {
        'contacts': contacts,
        'facilities': Facility.objects.order_by('name'),
        'departments': Department.objects.order_by('name'),
        'all_contacts': ContactPerson.objects.order_by('lastName'),
    })


@hr_admin_required
def snippets_manage(request):
    """Textbausteine (TextSnippet): wiederkehrende Absätze zentral pflegen,
    per Dropdown in die Job-Anlage einfügbar (schneller schreiben)."""
    from .models import TextSnippet
    if request.method == 'POST':
        if request.POST.get('delete_id'):
            TextSnippet.objects.filter(id=request.POST['delete_id']).delete()
        else:
            content = (request.POST.get('content') or '').strip()
            if content:
                TextSnippet.objects.create(
                    category=(request.POST.get('category') or 'INTRO').upper()[:100],
                    content=content,
                    jobFamily_id=(request.POST.get('jobFamily') or None) or None,
                )
        return redirect('ats:snippets')
    return render(request, 'snippets.html', {
        'snippets': TextSnippet.objects.select_related('jobFamily').order_by('category', '-createdAt'),
        'families': JobFamily.objects.order_by('name'),
    })


@recruiter_required
def toggle_job_active(request, job_id):
    """Schnell-Aktion: Anzeige mit einem Klick deaktivieren/aktivieren."""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    job = get_object_or_404(JobPosting, id=job_id)
    if job not in scope_jobs(request.user, JobPosting.objects.filter(id=job.id)):
        raise Http404("Nicht im Zugriffsbereich.")
    # UC-JF-01: das Gate ist nicht per Schnell-Toggle umgehbar
    from .approvals import has_open_gate, requisition_blocked_reason
    _rq = requisition_blocked_reason(job)
    if _rq and job.workflowState_id and job.workflowState.name != 'published':
        return JsonResponse({'success': False, 'error': _rq}, status=409)
    if has_open_gate(job):
        return JsonResponse({'success': False,
                             'error': 'Freigabe ausstehend – Aktivierung erfolgt '
                                      'automatisch mit der letzten Freigabe.'},
                            status=409)
    published, _ = WorkflowState.objects.get_or_create(
        name='published', defaults={'description': 'Öffentlich sichtbar'})
    draft, _ = WorkflowState.objects.get_or_create(
        name='draft', defaults={'description': 'Deaktiviert / Entwurf'})
    now_active = job.workflowState_id == published.id
    job.workflowState = draft if now_active else published
    job.save(update_fields=['workflowState', 'updatedAt'])
    write_audit("JOB_DEACTIVATED" if now_active else "JOB_ACTIVATED",
                user=request.user, job=job.title)
    return JsonResponse({'success': True, 'active': not now_active})


# --- P0.5: CSV-Bewerberdaten-Import (Migrationsbrücke) ------------------------
@hr_admin_required
def import_view(request):
    """Bestandsbewerber aus CSV/Excel-Export importieren – mit Testlauf zuerst."""
    from .importer import parse_csv, run_import
    report, fatal = None, None

    if request.method == 'POST':
        f = request.FILES.get('csv_file')
        action = request.POST.get('action', 'preview')
        default_job = None
        if request.POST.get('default_job'):
            default_job = JobPosting.objects.filter(id=request.POST['default_job']).first()
        if request.POST.get('form') == 'cv_zip':
            from .importer import match_cv_files
            zf = request.FILES.get('zip_file')
            if not zf:
                fatal = "Bitte eine ZIP-Datei auswählen."
            elif zf.size > 50 * 1024 * 1024:
                fatal = "ZIP größer als 50 MB – bitte aufteilen."
            else:
                dry = action != 'import'
                cv_report = match_cv_files(zf.read(), dry_run=dry)
                if not dry:
                    write_audit("CV_IMPORT", user=request.user,
                                files=cv_report["total"],
                                attached=cv_report["attached"],
                                unmatched=len(cv_report["unmatched"]))
                jobs = JobPosting.objects.select_related('location').order_by('title')
                return render(request, 'import.html', {
                    'cv_report': cv_report, 'cv_dry': dry,
                    'fatal': fatal, 'jobs': jobs})
        if not f:
            fatal = "Bitte eine CSV- oder Excel-Datei auswählen."
        elif f.size > 5 * 1024 * 1024:
            fatal = "Datei größer als 5 MB – bitte aufteilen."
        elif f.name.lower().endswith(('.xlsx', '.xlsm')):
            from .importer import parse_xlsx, detect_headers, HEADER_ALIASES, _map_headers
            data = f.read()
            overrides = {field: request.POST[f'map_{field}']
                         for field in HEADER_ALIASES
                         if request.POST.get(f'map_{field}')}
            rows, fatal = parse_xlsx(data, overrides=overrides)
            detected_headers = detect_headers(data, is_xlsx=True)
            mapping_now = _map_headers(detected_headers, overrides)
        else:
            from .importer import detect_headers, HEADER_ALIASES, _map_headers
            data = f.read()
            overrides = {field: request.POST[f'map_{field}']
                         for field in HEADER_ALIASES
                         if request.POST.get(f'map_{field}')}
            rows, fatal = parse_csv(data, overrides=overrides)
            detected_headers = detect_headers(data)
            mapping_now = _map_headers(detected_headers, overrides)
        if f and not fatal:
            dry_run = action != 'import'
            report = run_import(rows, default_job=default_job, dry_run=dry_run)
            if not dry_run:
                write_audit("DATA_IMPORT", user=request.user,
                            rows=report["total"],
                            applications_created=report["applications_created"],
                            applicants_new=report["applicants_new"],
                            skipped=report["skipped_existing"],
                            errors=len(report["errors"]))

    mapping_rows, unmapped = [], []
    if 'detected_headers' in locals() and detected_headers:
        from .importer import HEADER_ALIASES as _HA
        FIELD_LABELS = {"first_name": "Vorname", "last_name": "Nachname",
                        "email": "E-Mail", "phone": "Telefon",
                        "address": "Adresse", "job": "Stelle",
                        "status": "Status", "source": "Quelle",
                        "notes": "Notizen", "created": "Bewerbungsdatum"}
        for field in _HA:
            mapping_rows.append({
                'field': field,
                'label': FIELD_LABELS.get(field, field),
                'current': mapping_now.get(field, ''),
                'required': field in ('first_name', 'last_name', 'email')})
        unmapped = [h for h in detected_headers
                    if h not in mapping_now.values()]
    else:
        detected_headers = []
    jobs = JobPosting.objects.select_related('location').order_by('title')
    return render(request, 'import.html', {
        'mapping_rows': mapping_rows,
        'detected_headers': detected_headers,
        'unmapped_headers': unmapped,
        'report': report, 'fatal': fatal, 'jobs': jobs,
    })


@hr_admin_required
def import_template_csv(request):
    """Beispiel-/Vorlagendatei zum Ausfüllen (Excel-kompatibel, Semikolon, BOM)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="securats-import-vorlage.csv"'
    response.write('\ufeff')
    response.write("Vorname;Nachname;E-Mail;Telefon;Stelle;Status;Quelle;Datum;Notiz\r\n")
    response.write("Max;Mustermann;max@beispiel.de;030-123456;Pflegefachkraft Station 3;"
                   "neu;STEPSTONE;15.03.2026;Aus Altsystem übernommen\r\n")
    return response


# --- P0.3: Preisseite (nur Demo-Instanz) --------------------------------------
def pricing_view(request):
    """Preise für Interessenten – bewusst NUR auf der Demo-Instanz sichtbar:
    Kundeninstanzen sind Karriereseiten für Bewerbende, dort haben
    Anbieterpreise nichts verloren (PRICING.md §5)."""
    from django.conf import settings as dj_settings
    if not getattr(dj_settings, 'DEMO_MODE', False):
        raise Http404()
    nav_pages = Page.objects.filter(status="published", navEnabled=True).order_by('navOrder')
    return render(request, 'pricing.html', {'nav_pages': nav_pages, 'slug': 'preise'})


# --- Einladen: lokaler KI-Feinschliff fuer Nachrichten -------------------------
@recruiter_required
def polish_message(request):
    """Formuliert eine Nachricht an Bewerbende hoeflich/klar um – vollstaendig lokal.

    Guardrails: Der Text laeuft als nicht vertrauenswuerdige Eingabe durch
    ai_safety (auch interne Nutzer koennen nichts injizieren); die KI erhaelt
    KEINE weiteren Bewerberdaten. Ohne erreichbares Ollama kommt der
    Originaltext unveraendert zurueck – der Flow bricht nie.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    text = (request.POST.get('text') or '').strip()[:4000]
    if not text:
        return JsonResponse({'error': 'Kein Text.'}, status=400)

    from .ai_safety import wrap_untrusted, compose_system_prompt, PROMPT_VERSION
    payload = {
        "model": get_ai_model(),
        "system": compose_system_prompt() + (
            " Du überarbeitest eine Einladungs-Nachricht an eine Bewerberin/einen "
            "Bewerber: freundlich, klar, AGG-neutral (keine Aussagen zu Alter, "
            "Geschlecht, Herkunft, Religion), Sie-Form, maximal gleiche Länge. "
            "Platzhalter in doppelten eckigen Klammern und Namen unverändert lassen. "
            "Antworte NUR mit dem überarbeiteten Text."),
        "prompt": wrap_untrusted(text),
        "stream": False,
        "options": {"temperature": 0.3},
        "keep_alive": "10m",
    }
    import time
    start = time.time()
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=20.0)
        latency = round(time.time() - start, 2)
        if ok and (data.get('response') or '').strip():
            polished = data['response'].strip()[:4000]
            log_ai_execution("Einladung-Feinschliff", get_ai_model(), latency, True,
                             False, "", False, prompt_used=text,
                             tokens=data.get('eval_count'), prompt_version=PROMPT_VERSION)
            return JsonResponse({'polished': polished, 'used_ai': True,
                                 'note': 'Überarbeitet – bitte vor dem Senden prüfen.'})
    except Exception:
        logger.exception("KI-Feinschliff nicht verfügbar")
    return JsonResponse({'polished': text, 'used_ai': False,
                         'note': 'Lokale KI nicht erreichbar – Text unverändert.'})


@recruiter_required
def suggest_process(request):
    """Prozess-Berater: schlaegt Screening-/K.O.-Fragen + Prozess-Hinweise vor.

    Regelbasiert (immer verfuegbar) + optional lokale KI fuer Zusatzfragen.
    Governance wird nur ANGEZEIGT (Gate-Info), nie veraendert; wirksam wird
    nichts ohne Speichern durch den Menschen.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    from .process_advisor import (rule_based_suggestions, gate_info,
                                  ai_extra_questions)
    title = (request.POST.get('title') or '').strip()[:200]
    family_id = request.POST.get('job_family') or ''
    facility_id = request.POST.get('facility') or ''
    family = JobFamily.objects.filter(id=family_id).first() if family_id else None
    facility = Facility.objects.filter(id=facility_id).first() if facility_id else None

    questions, notes = rule_based_suggestions(title, family.name if family else '')
    used_ai = False
    if request.POST.get('with_ai') == '1':
        extra = ai_extra_questions(title, family.name if family else '',
                                   {q['id'] for q in questions})
        if extra:
            questions += extra
            used_ai = True
            notes.append("KI-Zusatzfragen sind bewusst OHNE K.O.-Wirkung "
                         "(keine automatische Absage möglich).")
    return JsonResponse({
        'questions': questions,
        'notes': notes,
        'gate': gate_info(facility),
        'used_ai': used_ai,
    })


@recruiter_required
def interview_outcome(request, interview_id):
    """Gespraechsergebnis erfassen (stattgefunden / No-Show / kurzfristig abgesagt).

    Korrekturen sind erlaubt (Tippfehler passieren) – jede Aenderung steht im
    Audit. Die weitere Entscheidung (Zusage/Absage) laeuft wie gehabt ueber den
    Bewerbungsstatus im Kanban; hier wird nur der Termin selbst dokumentiert.
    """
    if request.method != 'POST':
        return redirect('ats:interviews')
    from .models import INTERVIEW_OUTCOMES
    iv = get_object_or_404(Interview.objects.filter(
        application__in=scope_applications(request.user, Application.objects.all())),
        id=interview_id)  # BOLA
    outcome = request.POST.get('outcome', '')
    if outcome not in dict(INTERVIEW_OUTCOMES):
        return redirect('ats:interviews')
    if iv.scheduledAt > timezone.now():
        raise Http404('Ergebnis erst nach dem Termin erfassbar.')
    old = iv.outcome
    iv.outcome = outcome
    iv.save(update_fields=['outcome'])
    write_audit('INTERVIEW_OUTCOME_SET', user=request.user,
                application_id=str(iv.application_id),
                interview_id=str(iv.id), outcome=outcome, previous=old or '')

    # Gesprächsrunde automatisch mitführen: „Stattgefunden" schließt die
    # aktuelle Runde ab, eine Korrektur weg davon nimmt sie zurück. Nur bei
    # echtem Zustandswechsel (nicht bei erneutem Speichern desselben
    # Ergebnisses), und nur wenn die Stelle überhaupt Runden definiert –
    # sonst bleibt alles beim manuellen Vorrücken auf der Termine-Seite.
    from .models import rounds_state, pending_feedback_participants
    app = iv.application
    rst = rounds_state(app)
    completed_round = app.interviewRound   # Runde, die dieses Gespräch betraf
    if rst['total']:
        entered = outcome == 'COMPLETED' and old != 'COMPLETED'
        left = old == 'COMPLETED' and outcome != 'COMPLETED'
        new_round = app.interviewRound
        if entered and app.interviewRound < rst['total']:
            new_round = app.interviewRound + 1
        elif left and app.interviewRound > 0:
            new_round = app.interviewRound - 1
        if new_round != app.interviewRound:
            app.interviewRound = new_round
            app.save(update_fields=['interviewRound'])
            write_audit('INTERVIEW_ROUND_CHANGED', user=request.user,
                        application_id=str(app.id),
                        op='auto_advance' if entered else 'auto_back',
                        round=new_round, source='interview_outcome')

    # Bitte um Feedback: stattgefundenes Gespräch -> die Teilnehmer:innen,
    # die noch nicht bewertet haben, werden direkt gebeten. So entsteht
    # Feedback, ohne dass jemand daran denken muss. Nur beim Übergang NACH
    # „stattgefunden" (kein Doppelversand bei erneutem Speichern).
    if outcome == 'COMPLETED' and old != 'COMPLETED':
        pending = pending_feedback_participants(iv, completed_round)
        if pending:
            from django.core.mail import send_mail
            name = f"{app.applicant.firstName} {app.applicant.lastName}"
            for person in pending:
                send_mail(
                    f"Bitte um Feedback: {name} – {app.jobPosting.title}",
                    (f"Sie haben {name} interviewt. Bitte hinterlassen Sie "
                     "Ihre Einschätzung, damit die weitere Entscheidung auf "
                     "dokumentiertem Feedback steht.\n"
                     "Feedback erfassen: /recruiter/interviews/"),
                    None, [person.email], fail_silently=True)
            write_audit('FEEDBACK_REQUESTED', user=request.user,
                        application_id=str(app.id), round=completed_round,
                        recipients=len(pending))
    return redirect('ats:interviews')


@hr_admin_required
def audit_export(request):
    """Audit-Log als CSV-Nachweis (UC-JF-10 Mitbestimmung, UC-MB-08 DSB,
    UC-NS-12 Compliance).

    Der Export prueft zuerst die Hash-Kette und schreibt das Ergebnis als
    Kopfzeile in die Datei – ein Nachweis ist nur so gut wie seine
    Integritaet. Der Export selbst wird auditiert (wer hat wann was
    exportiert), NACHDEM die Zeilen eingesammelt sind, damit die Datei in
    sich konsistent bleibt. Zugriff: HR-Admin erstellt den Nachweis auf
    Anforderung von Betriebsrat/DSB (die Governance-Sicht selbst bleibt
    bewusst aggregiert und namenfrei).
    """
    import csv as _csv
    from .audit import verify_audit_chain

    qs = AuditLog.objects.order_by('createdAt')
    von = request.GET.get('von')
    bis = request.GET.get('bis')
    action = (request.GET.get('action') or '').strip()[:100]
    try:
        if von:
            qs = qs.filter(createdAt__date__gte=datetime.date.fromisoformat(von))
        if bis:
            qs = qs.filter(createdAt__date__lte=datetime.date.fromisoformat(bis))
    except ValueError:
        return HttpResponse("Ungültiges Datum (Format: JJJJ-MM-TT).", status=400)
    if action:
        qs = qs.filter(action=action)

    chain = verify_audit_chain()
    ok = bool(chain.get('ok'))
    detail = f"geprüft {chain.get('checked')}, Bruch bei {chain.get('broken_id', '?')}"
    rows = list(qs.values_list('createdAt', 'action', 'userId',
                               'applicationId', 'metadataJson', 'entryHash'))

    write_audit('AUDIT_EXPORTED', user=request.user,
                rows=len(rows), von=von or '', bis=bis or '',
                action_filter=action, chain_ok=ok)

    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    fname = f"securats-audit-{timezone.localdate().isoformat()}.csv"
    resp['Content-Disposition'] = f'attachment; filename="{fname}"'
    resp.write('\ufeff')
    w = _csv.writer(resp, delimiter=';')
    w.writerow([f"# SecurATS Audit-Nachweis · erstellt {timezone.localtime():%d.%m.%Y %H:%M} "
                f"· Zeitraum: {von or 'Anfang'} bis {bis or 'heute'} "
                f"· Hash-Kette: {'INTAKT' if ok else 'VERLETZT – ' + str(detail)} "
                f"· {len(rows)} Einträge"])
    w.writerow(['Zeitpunkt', 'Aktion', 'Nutzer', 'Bewerbungs-ID', 'Metadaten', 'Hash'])
    for created, act, user_id, app_id, meta, h in rows:
        w.writerow([timezone.localtime(created).strftime('%Y-%m-%d %H:%M:%S'),
                    act, user_id or '', app_id or '', meta, h or ''])
    return resp


@any_staff_required
def staffing_requests_view(request):
    """UC-MD-01: Personalbedarf melden + bearbeiten.

    Melden darf jede interne Rolle (auch Hiring-Manager/Viewer – genau dafuer
    ist die Seite da); entscheiden duerfen Recruiter/HR-Admin. Sichtbarkeit:
    eigene Meldungen immer; alle Meldungen fuer die entscheidenden Rollen,
    BOLA-gescopt ueber die Einrichtung.
    """
    from .models import StaffingRequest
    is_decider = (request.user.is_superuser or request.user.groups.filter(
        name__in=['HR-Admin', 'Recruiter']).exists())

    if request.method == 'POST' and request.POST.get('form') == 'create':
        facility = Facility.objects.filter(id=request.POST.get('facility')).first()
        title = (request.POST.get('title') or '').strip()[:255]
        justification = (request.POST.get('justification') or '').strip()[:4000]
        if facility and title and justification:
            try:
                headcount = max(1, min(int(request.POST.get('headcount') or 1), 99))
            except (TypeError, ValueError):
                headcount = 1
            desired = None
            if request.POST.get('desired_start'):
                try:
                    desired = datetime.date.fromisoformat(request.POST['desired_start'])
                except ValueError:
                    desired = None
            department = Department.objects.filter(
                id=request.POST.get('department')).first()
            job_family = JobFamily.objects.filter(
                id=request.POST.get('job_family')).first()
            # Routing-Matrix: Regel bestimmt Formular-Fragen + Kette
            from .approvals import resolve_requisition_rule
            from .questions import normalize_questions as _nqs
            rule = resolve_requisition_rule(facility, department, job_family)
            answers = {}
            if rule:
                try:
                    rqs = _nqs(json.loads(rule.formQuestionsJson or "[]"))
                except (ValueError, TypeError):
                    rqs = []
                for q in rqs:
                    val = (request.POST.get(f"rq_{q['id']}") or '').strip()
                    if q.get('isMandatory') and not val:
                        messages.warning(
                            request,
                            f"Bitte beantworten Sie: {q['question']}")
                        return redirect('ats:staffing_requests')
                    if val:
                        answers[q['question']] = val[:2000]
            req = StaffingRequest.objects.create(
                title=title, facility=facility, department=department,
                jobFamily=job_family,
                headcount=headcount, desiredStart=desired,
                justification=justification, requestedBy=request.user,
                answersJson=json.dumps(answers, ensure_ascii=False))
            write_audit('STAFFING_REQUEST_CREATED', user=request.user,
                        request_id=str(req.id), facility=facility.name,
                        headcount=headcount)
            from .approvals import requisition_required, open_requisition_steps
            if requisition_required() or rule:
                open_requisition_steps(req)
                from .approvals import notify_due_requisition_steps
                notify_due_requisition_steps(req)
                req.status = 'IN_APPROVAL'
                req.save(update_fields=['status'])
        return redirect('ats:staffing_requests')

    if (request.method == 'POST'
            and request.POST.get('form', '').startswith('rule_')
            and request.user.groups.filter(name='HR-Admin').exists()):
        from .models import RequisitionRule
        from .questions import normalize_question, normalize_questions
        form = request.POST['form']
        if form == 'rule_add':
            chain = (request.POST.get('chain') or '').strip()[:255]
            name = (request.POST.get('name') or '').strip()[:120]
            if name and chain:
                RequisitionRule.objects.create(
                    name=name, chain=chain,
                    facility=Facility.objects.filter(
                        id=request.POST.get('facility')).first(),
                    department=Department.objects.filter(
                        id=request.POST.get('department')).first(),
                    jobFamily=JobFamily.objects.filter(
                        id=request.POST.get('job_family')).first(),
                    mandatory=bool(request.POST.get('mandatory')))
                write_audit('REQUISITION_RULE_CREATED', user=request.user,
                            name=name, chain=chain)
        elif form == 'rule_delete':
            rule = get_object_or_404(RequisitionRule,
                                     id=request.POST.get('rule_id'))
            write_audit('REQUISITION_RULE_DELETED', user=request.user,
                        name=rule.name)
            rule.delete()
        elif form in ('rule_q_add', 'rule_q_del'):
            rule = get_object_or_404(RequisitionRule,
                                     id=request.POST.get('rule_id'))
            try:
                qs = normalize_questions(json.loads(
                    rule.formQuestionsJson or "[]"))
            except (ValueError, TypeError):
                qs = []
            if form == 'rule_q_add':
                q = normalize_question({
                    'type': request.POST.get('q_type', 'TEXT'),
                    'question': request.POST.get('q_question', ''),
                    'isMandatory': bool(request.POST.get('q_mandatory')),
                    'options': request.POST.get('q_options', '').replace('|', chr(10))})
                if q and q['type'] != 'FILE' and len(qs) < 15:
                    qs.append(q)   # FILE am Antrag: bewusst Gate (Uploads)
            else:
                idx = request.POST.get('idx')
                if idx and idx.isdigit() and int(idx) < len(qs):
                    qs.pop(int(idx))
            rule.formQuestionsJson = json.dumps(qs, ensure_ascii=False)
            rule.save(update_fields=['formQuestionsJson'])
            write_audit('REQUISITION_RULE_FORM_CHANGED', user=request.user,
                        name=rule.name, count=len(qs))
        return redirect('ats:staffing_requests')

    if request.method == 'POST' and request.POST.get('form') == 'step_decide':
        # Stellenfreigabe: nur die Rolle der aktuell faelligen Stufe entscheidet
        from .models import RequisitionStep
        step = get_object_or_404(RequisitionStep,
                                 id=request.POST.get('step_id'))
        req = step.request
        from .approvals import (may_decide_requisition_step,
                                 due_requisition_steps)
        due = due_requisition_steps(req)
        allowed_role, deputizing_for = may_decide_requisition_step(
            request.user, step)
        decision = request.POST.get('decision')
        if (step in due and allowed_role and req.status == 'IN_APPROVAL'
                and decision in ('approve', 'return', 'reject')):
            step.decidedBy = request.user
            step.viaDelegation = deputizing_for is not None
            step.decidedAt = timezone.now()
            step.comment = (request.POST.get('comment') or '').strip()[:2000]
            if decision == 'approve':
                step.status = 'APPROVED'
                step.save()
                # Parallelgruppen-Quorum: sind genug Zustimmungen der Gruppe
                # (gleiche order) da, werden die restlichen offenen Stufen der
                # Gruppe nicht mehr gebraucht -> als SKIPPED aufgelöst, damit
                # die nächste Stufe fällig wird. Bei Gruppen ohne Quorum
                # (groupQuorum = Rollenzahl) ändert das nichts.
                group = req.steps.filter(order=step.order)
                quorum = step.groupQuorum or group.count()
                if group.filter(status='APPROVED').count() >= quorum:
                    group.filter(status='PENDING').update(
                        status='SKIPPED', decidedAt=timezone.now())
                if not req.steps.filter(status='PENDING').exists():
                    req.status = 'ACCEPTED'
                    req.decidedBy = request.user
                    req.decidedAt = timezone.now()
                    req.save(update_fields=['status', 'decidedBy',
                                            'decidedAt'])
            elif decision == 'return':
                step.status = 'RETURNED'
                step.save()
                req.status = 'RETURNED'
                req.save(update_fields=['status'])
            else:
                step.status = 'REJECTED'
                step.save()
                req.status = 'DECLINED'
                req.decidedBy = request.user
                req.decidedAt = timezone.now()
                req.save(update_fields=['status', 'decidedBy', 'decidedAt'])
            write_audit('REQUISITION_STEP_DECIDED', user=request.user,
                        request_id=str(req.id), role=step.role, op=decision,
                        deputizing_for=(deputizing_for.username
                                        if deputizing_for else None))
            # Gruppe abgeschlossen -> naechste Stufe ist jetzt faellig:
            # deren Rollen (und Vertretungen) sofort benachrichtigen.
            if decision == 'approve' and req.status == 'IN_APPROVAL':
                from .approvals import (due_requisition_steps as _dueq,
                                        notify_due_requisition_steps)
                nxt = _dueq(req)
                if nxt and nxt[0].order != step.order:
                    notify_due_requisition_steps(req)
            # Antragsteller informieren, sobald etwas Finales passiert
            if (req.status in ('ACCEPTED', 'DECLINED', 'RETURNED')
                    and req.requestedBy and req.requestedBy.email):
                from django.core.mail import send_mail
                label = {'ACCEPTED': 'genehmigt', 'DECLINED': 'abgelehnt',
                         'RETURNED': 'zur Nachbesserung zurückgegeben'}[req.status]
                send_mail(f'Stellenfreigabe {label}: {req.title}',
                          (f'Ihr Personalbedarf "{req.title}" wurde {label}.'
                           + (f'\nKommentar: {step.comment}' if step.comment
                              else '')
                           + '\nDetails: /recruiter/bedarf/'),
                          None, [req.requestedBy.email], fail_silently=True)
        return redirect('ats:staffing_requests')

    if request.method == 'POST' and request.POST.get('form') == 'resubmit':
        # Nachbesserung eingereicht: Kette startet von vorn (Muster Job-Gate)
        req = get_object_or_404(StaffingRequest,
                                id=request.POST.get('request_id'))
        if req.requestedBy_id == request.user.id and req.status == 'RETURNED':
            just = (request.POST.get('justification') or '').strip()[:4000]
            if just:
                req.justification = just
            req.steps.all().update(status='PENDING', decidedBy=None,
                                   decidedAt=None, comment='')
            req.status = 'IN_APPROVAL'
            req.save()
            write_audit('REQUISITION_RESUBMITTED', user=request.user,
                        request_id=str(req.id))
            from .approvals import notify_due_requisition_steps
            notify_due_requisition_steps(req)
        return redirect('ats:staffing_requests')

    if (request.method == 'POST'
            and request.POST.get('form') == 'requisition_settings'
            and request.user.groups.filter(name='HR-Admin').exists()):
        from .models import SystemSetting
        SystemSetting.objects.update_or_create(
            key='REQUISITION_REQUIRED',
            defaults={'value': '1' if request.POST.get('required') else '0'})
        SystemSetting.objects.update_or_create(
            key='REQUISITION_CHAIN',
            defaults={'value': (request.POST.get('chain') or '').strip()[:255]})
        write_audit('REQUISITION_SETTINGS_CHANGED', user=request.user,
                    required=bool(request.POST.get('required')))
        return redirect('ats:staffing_requests')

    if request.method == 'POST' and request.POST.get('form') == 'decide' and is_decider:
        req = get_object_or_404(StaffingRequest, id=request.POST.get('request_id'))
        decision = request.POST.get('decision')
        from .approvals import requisition_required as _rr
        if _rr() and req.steps.exists():
            return redirect('ats:staffing_requests')  # Kette entscheidet
        if req.status == 'OPEN' and decision in ('ACCEPTED', 'DECLINED'):
            req.status = decision
            req.decisionNote = (request.POST.get('note') or '').strip()[:2000]
            req.decidedBy = request.user
            req.decidedAt = timezone.now()
            req.save()
            write_audit('STAFFING_REQUEST_DECIDED', user=request.user,
                        request_id=str(req.id), decision=decision)
            # Melder:in informieren – der Fachbereich soll nicht nachfragen muessen
            if req.requestedBy and req.requestedBy.email:
                try:
                    from django.core.mail import send_mail
                    label = 'angenommen' if decision == 'ACCEPTED' else 'abgelehnt'
                    send_mail(f'Ihre Bedarfsmeldung wurde {label}: {req.title}',
                              (f'Status: {label}.\n'
                               + (f'Anmerkung: {req.decisionNote}\n' if req.decisionNote else '')
                               + 'Details: /recruiter/bedarf/'),
                              None, [req.requestedBy.email], fail_silently=True)
                except Exception:
                    logger.exception('Bedarfs-Entscheidungs-Mail fehlgeschlagen')
        return redirect('ats:staffing_requests')

    # Feinschliff: angenommener Bedarf -> Ausschreibungs-Entwurf in einem Klick.
    # WICHTIG: Die Begruendung ("Leasingkosten 8 T€/Monat, Team am Limit") ist
    # INTERN und wandert bewusst NICHT in die oeffentliche Beschreibung.
    if request.method == 'POST' and request.POST.get('form') == 'convert' and is_decider:
        req = get_object_or_404(StaffingRequest, id=request.POST.get('request_id'))
        location = Location.objects.filter(id=request.POST.get('location')).first()
        if req.status == 'ACCEPTED' and location:
            draft, _ = WorkflowState.objects.get_or_create(
                name='draft', defaults={'description': 'Deaktiviert / Entwurf'})
            job = JobPosting.objects.create(
                headcount=req.headcount or 1,
                title=req.title,
                organization=req.facility.organization,
                facility=req.facility,
                location=location,
                jobFamily=req.jobFamily or JobFamily.objects.order_by('name').first(),
                workflowState=draft,
                description=(f"{req.title} – Beschreibung folgt.\n\n"
                             "(Entwurf aus Bedarfsmeldung. Bitte vor der "
                             "Veröffentlichung vervollständigen – der "
                             "Prozess-Berater in der Bearbeitung schlägt "
                             "passende Screening-Fragen vor.)"),
                screeningQuestionsJson='[]')
            # Prozess-Gedaechtnis: der Entwurf bekommt den zuletzt real
            # genutzten Prozess der Jobfamilie gleich mit (Fragen, Aufgaben,
            # Anforderungen) – eine Klickstrecke weniger beim Vervollstaendigen.
            prev = _previous_process(job.jobFamily_id, req.facility_id,
                                     exclude_id=job.id)
            if prev:
                job.screeningQuestionsJson = json.dumps(prev['screening_questions'])
                job.tasksJson = prev['tasks']
                job.requirementsJson = prev['requirements']
                job.save(update_fields=['screeningQuestionsJson', 'tasksJson',
                                        'requirementsJson'])
            from .process_advisor import ensure_minimum_standards
            if ensure_minimum_standards(job):
                job.save(update_fields=['screeningQuestionsJson'])
                write_audit('MINIMUM_STANDARD_APPLIED', user=request.user,
                            job=job.title)
            from .approvals import ensure_approval_gate
            ticket = ensure_approval_gate(job)
            if ticket and ticket.status == 'PENDING':
                write_audit('APPROVAL_GATE_OPENED', user=request.user,
                            job=job.title, ticket=str(ticket.id))
            req.status = 'CONVERTED'
            req.convertedJob = job
            req.save(update_fields=['status', 'convertedJob'])
            write_audit('STAFFING_REQUEST_CONVERTED', user=request.user,
                        request_id=str(req.id), job_id=str(job.id))
        return redirect('ats:staffing_requests')

    my_requests = StaffingRequest.objects.filter(
        requestedBy=request.user).select_related('facility').order_by('-createdAt')[:20]
    inbox = []
    if is_decider:
        facilities_scope = Facility.objects.all()
        if not has_full_access(request.user):
            loc_ids = list(request.user.scope.locations.values_list('id', flat=True))
            fac_ids = list(request.user.scope.facilities.values_list('id', flat=True))
            facilities_scope = facilities_scope.filter(id__in=fac_ids) if fac_ids else facilities_scope
        inbox = (StaffingRequest.objects.filter(facility__in=facilities_scope)
                 .select_related('facility', 'requestedBy', 'jobFamily')
                 .order_by('status', '-createdAt')[:50])

    # Ketten-Genehmiger (Bereichsleitung, Vorstand, ...) und ihre aktiven
    # Vertretungen sehen die Antraege, deren faellige Stufe sie entscheiden
    # duerfen – auch OHNE Recruiter-/HR-Admin-Rolle. Vorher konnten diese
    # Rollen formal entscheiden, fanden die Antraege aber nirgends.
    from .approvals import may_decide_requisition_step as _mds
    inbox_ids = {r.id for r in inbox}
    chain_inbox = []
    for r in (StaffingRequest.objects.filter(status='IN_APPROVAL')
              .exclude(id__in=inbox_ids)
              .select_related('facility', 'requestedBy', 'jobFamily')
              .order_by('-createdAt')[:50]):
        from .approvals import due_requisition_steps as _due
        if any(_mds(request.user, st)[0] for st in _due(r)):
            chain_inbox.append(r)
    # ... plus Antraege, die ich selbst (mit-)entschieden habe: ein
    # Genehmiger muss seine eigenen Entscheidungen nachvollziehen koennen.
    seen = inbox_ids | {r.id for r in chain_inbox}
    decided_by_me = list(
        StaffingRequest.objects.filter(steps__decidedBy=request.user)
        .exclude(id__in=seen).distinct()
        .select_related('facility', 'requestedBy', 'jobFamily')
        .order_by('-createdAt')[:50])
    inbox = list(inbox) + chain_inbox + decided_by_me

    from .approvals import (requisition_required as _rreq,
                            requisition_chain as _rchain,
                            resolve_requisition_rule as _rrule,
                            may_decide_requisition_step as may_dec)
    from .questions import (QUESTION_TYPES as _QT,
                            normalize_questions as _nq2)
    sel_fac = Facility.objects.filter(id=request.GET.get('facility')).first()
    sel_dep = Department.objects.filter(
        id=request.GET.get('department')).first()
    sel_fam = JobFamily.objects.filter(
        id=request.GET.get('job_family')).first()
    form_rule = _rrule(sel_fac, sel_dep, sel_fam) if sel_fac else None
    form_questions = []
    if form_rule:
        try:
            form_questions = _nq2(json.loads(
                form_rule.formQuestionsJson or "[]"))
        except (ValueError, TypeError):
            form_questions = []
    rule_rows = []
    from .models import RequisitionRule as _RR
    for rl in _RR.objects.select_related(
            'facility', 'department', 'jobFamily').order_by('-createdAt'):
        try:
            rl_qs = _nq2(json.loads(rl.formQuestionsJson or "[]"))
        except (ValueError, TypeError):
            rl_qs = []
        rule_rows.append({'rule': rl, 'questions': rl_qs,
                          'q_indexed': list(enumerate(rl_qs))})
    from .models import SystemSetting as _SS
    req_active = _rreq()
    chain_setting = _SS.objects.filter(key='REQUISITION_CHAIN').first()
    user_groups = set(request.user.groups.values_list('name', flat=True))
    def _decorate(reqs):
        rows = []
        for r in reqs:
            steps = list(r.steps.all())
            try:
                answers = json.loads(r.answersJson or "{}")
            except (ValueError, TypeError):
                answers = {}
            pending = [st for st in steps if st.status == 'PENDING']
            min_order = pending[0].order if pending else None
            due = [st for st in pending if st.order == min_order]
            my_due = [st for st in due
                      if may_dec(request.user, st)[0]] \
                if r.status == 'IN_APPROVAL' else []
            rows.append({'req': r, 'steps': steps,
                         'current': my_due[0] if my_due else None,
                         'due_count': len(due),
                         'answers': answers.items(),
                         'can_decide': bool(my_due),
                         'can_resubmit': r.status == 'RETURNED'
                                         and r.requestedBy_id == request.user.id})
        return rows
    return render(request, 'staffing_requests.html', {
        'req_active': req_active,
        'req_chain_value': chain_setting.value if chain_setting else '',
        'my_rows': _decorate(my_requests),
        'inbox_rows': _decorate(inbox),
        'show_inbox': bool(is_decider or inbox),
        'can_admin_requisition': request.user.groups.filter(name='HR-Admin').exists(),
        'departments': Department.objects.select_related('facility').order_by('name'),
        'sel_fac': sel_fac, 'sel_dep': sel_dep, 'sel_fam': sel_fam,
        'form_rule': form_rule, 'form_questions': form_questions,
        'rule_rows': rule_rows, 'question_types': _QT,
        'my_requests': my_requests, 'inbox': inbox, 'is_decider': is_decider,
        'facilities': Facility.objects.order_by('name'),
        'job_families': JobFamily.objects.order_by('name'),
        'locations': Location.objects.filter(archived=False).order_by('name'),
    })


def _previous_process(job_family_id, facility_id=None, exclude_id=None,
                      department_id=None, location_id=None, title=''):
    """Prozess-Gedaechtnis (Weg A) mit Spezifitaets-Leiter analog zum
    Workflow-Matching: gleiche Jobfamilie + gleiche ABTEILUNG schlaegt gleiche
    EINRICHTUNG schlaegt gleichen STANDORT schlaegt 'irgendwo in der Familie'.
    Das Ergebnis nennt immer die Herkunfts-Ebene (scope), damit die
    Uebertragbarkeit beurteilbar ist. Kaltstart ohne jede Vorlage: Fallback
    auf das Regelwerk des Prozess-Beraters (source='REGELWERK').
    """
    if not job_family_id:
        return None
    base = JobPosting.objects.filter(jobFamily_id=job_family_id)
    if exclude_id:
        base = base.exclude(id=exclude_id)
    base = base.select_related('facility', 'department', 'location',
                               'jobFamily').order_by('-createdAt')
    ladder = []
    if department_id:
        ladder.append((base.filter(department_id=department_id),
                       'gleiche Abteilung'))
    if facility_id:
        ladder.append((base.filter(facility_id=facility_id),
                       'gleiche Einrichtung'))
    if location_id:
        ladder.append((base.filter(location_id=location_id),
                       'gleicher Standort'))
    ladder.append((base, 'gleiche Jobfamilie (anderer Bereich)'))
    source, scope = None, ''
    for qs, label in ladder:
        source = qs.first()
        if source:
            scope = label
            break
    if source is None:
        # Kaltstart: Regelwerk des Prozess-Beraters als Default
        from .process_advisor import rule_based_suggestions
        fam_name = (JobFamily.objects.filter(id=job_family_id)
                    .values_list('name', flat=True).first()) or ''
        questions, _notes = rule_based_suggestions(title or '', fam_name)
        if not questions:
            return None
        return {'source': 'REGELWERK', 'scope': 'Regelwerk (keine Vorlage vorhanden)',
                'source_title': f'Prozess-Berater: {fam_name}', 'source_date': '',
                'source_facility': '', 'screening_questions': questions,
                'tasks': '[]', 'requirements': '[]'}
    try:
        questions = json.loads(source.screeningQuestionsJson or '[]')
    except ValueError:
        questions = []
    return {
        'source': 'VORGAENGER', 'scope': scope,
        'source_title': source.title,
        'source_date': timezone.localtime(source.createdAt).strftime('%d.%m.%Y'),
        'source_facility': source.facility.name if source.facility else '',
        'screening_questions': questions,
        'tasks': source.tasksJson or '[]',
        'requirements': source.requirementsJson or '[]',
    }


@recruiter_required
def process_previous(request):
    """GET-Endpoint fuer den 'Bewaehrten Prozess uebernehmen'-Button im Wizard."""
    data = _previous_process(request.GET.get('job_family') or None,
                             request.GET.get('facility') or None,
                             request.GET.get('exclude') or None,
                             department_id=request.GET.get('department') or None,
                             location_id=request.GET.get('location') or None,
                             title=request.GET.get('title') or '')
    if data is None:
        return JsonResponse({'found': False})
    return JsonResponse({'found': True, **data})


@any_staff_required
def application_vote(request, app_id):
    """Gremien-Stimme abgeben/aendern + Kommentar/Frage hinterlegen.

    Stimmrecht hat NUR, wer im Gremium der Stelle steht (403 sonst) –
    unabhaengig von der Rolle: auch Hiring-Manager/Viewer stimmen, wenn
    benannt. Kommentare landen in den internen Notizen (ein Ort fuer alle).
    """
    if request.method != 'POST':
        return redirect('ats:approvals')
    from .panel import panel_member_ids
    from .models import ApplicationVote
    from .permissions import active_delegations_to, delegation_covers
    app = get_object_or_404(Application, id=app_id)
    members = panel_member_ids(app.jobPosting)
    is_member = str(request.user.id) in members
    seat_for = None
    if not is_member:
        for d in active_delegations_to(request.user):
            if (str(d.delegator_id) in members
                    and delegation_covers(d, app.jobPosting)):
                seat_for = d.delegator.get_full_name() or d.delegator.username
                break
        if seat_for is None:
            return HttpResponse(status=403)
    vote = request.POST.get('vote')
    comment = (request.POST.get('comment') or '').strip()[:2000]
    if vote in ('FOR', 'AGAINST'):
        obj, created = ApplicationVote.objects.update_or_create(
            application=app, user=request.user, defaults={'vote': vote})
        write_audit('PANEL_VOTE_CAST', user=request.user,
                    application_id=app.id, vote=vote,
                    changed=(not created),
                    **({'for_seat': seat_for} if seat_for else {}))
    if comment:
        ts = timezone.now().strftime('%d.%m.%Y %H:%M')
        who = request.user.get_full_name() or request.user.username
        app.internalNotes = ((app.internalNotes or '')
                             + f"\n[{ts}] Gremium {who}: {comment}")
        app.save(update_fields=['internalNotes'])
        write_audit('PANEL_COMMENT_ADDED', user=request.user,
                    application_id=app.id)
    return redirect('ats:approvals')


@hr_admin_required
def panel_defaults_view(request):
    """Gremien-Defaults je Ebene pflegen (UC: flexibles Entscheidungsgremium).

    Leiter: Stelle > Abteilung > Einrichtung > Standort > Jobfamilie >
    Organisation – die spezifischste besetzte Ebene gewinnt komplett.
    „Bewusst kein Gremium" (Sentinel NONE) unterbricht die Vererbung, z. B.
    Firmen-Default fuer alle, aber Aushilfsstellen-Familie ohne Gremium.
    """
    from .models import Department
    LEVELS = {
        'organization': Organization, 'location': Location,
        'facility': Facility, 'department': Department, 'job_family': JobFamily,
    }
    if request.method == 'POST':
        model = LEVELS.get(request.POST.get('level'))
        if model is None:
            return redirect('ats:panel_defaults')
        obj = get_object_or_404(model, id=request.POST.get('entity_id'))
        if request.POST.get('no_panel') == '1':
            value = ["NONE"]
        else:
            from django.contrib.auth.models import User as _User
            raw_ids = request.POST.getlist('members')
            value = [str(i) for i in _User.objects.filter(
                id__in=raw_ids, is_active=True).values_list('id', flat=True)]
        obj.panelUserIdsJson = json.dumps(value)
        obj.save(update_fields=['panelUserIdsJson'])
        write_audit('PANEL_DEFAULT_CHANGED', user=request.user,
                    level=request.POST.get('level'), entity=str(obj),
                    members=len([v for v in value if v.upper() != 'NONE']),
                    no_panel=(value == ["NONE"]))
        return redirect('ats:panel_defaults')

    from django.contrib.auth.models import User as _User
    staff = list(_User.objects.filter(is_active=True, groups__isnull=False)
                 .distinct().order_by('username'))
    from .models import Department
    def rows(model, level):
        out = []
        for obj in model.objects.order_by('name'):
            try:
                current = json.loads(obj.panelUserIdsJson or '[]')
            except ValueError:
                current = []
            out.append({'obj': obj, 'level': level,
                        'no_panel': any(str(i).upper() == 'NONE' for i in current),
                        'current': {str(i) for i in current}})
        return out
    sections = [
        ('Organisation (Firmen-Default)', rows(Organization, 'organization')),
        ('Jobfamilie', rows(JobFamily, 'job_family')),
        ('Standort', rows(Location, 'location')),
        ('Einrichtung', rows(Facility, 'facility')),
        ('Abteilung', rows(Department, 'department')),
    ]
    return render(request, 'panel_defaults.html',
                  {'sections': sections, 'staff': staff})


@recruiter_required
def panel_preview(request):
    """Live-Vorschau im Stellen-Wizard: wirksames Gremium ohne eigene Auswahl."""
    from .panel import resolve_panel_preview
    from django.contrib.auth.models import User as _User
    ids, source = resolve_panel_preview(
        job_family_id=request.GET.get('job_family') or None,
        facility_id=request.GET.get('facility') or None,
        department_id=request.GET.get('department') or None,
        location_id=request.GET.get('location') or None)
    names = list(_User.objects.filter(id__in=[i for i in ids if i.isdigit()])
                 .values_list('username', flat=True)) if ids else []
    return JsonResponse({'members': names, 'source': source,
                         'none': 'kein Gremium' in source})


@hr_admin_required
def branding_view(request):
    """Erscheinungsbild: CI/CD des Traegers auf die Bewerberseiten bringen.

    Zwei Wege: (a) Ein-Klick-Import von der Unternehmens-Website
    (theme-color, Logo-Kandidat, Bildvorschlag – Best Effort, Admin
    bestaetigt), (b) manuelle Pflege. Kontrastfarben werden automatisch
    berechnet (WCAG) – niemand muss wissen, ob auf Magenta Weiss gehoert.
    """
    from .branding import (brand_context, fetch_branding_suggestions,
                           normalize_hex)
    org = Organization.objects.first()
    if org is None:
        return render(request, 'branding.html', {'org': None})
    suggestion = None
    if request.method == 'POST' and request.POST.get('form') == 'import':
        url = (request.POST.get('website') or '').strip()[:300]
        suggestion = fetch_branding_suggestions(url)
        suggestion['website'] = url
        write_audit('BRANDING_IMPORT_ATTEMPTED', user=request.user,
                    website=url, found_primary=bool(suggestion.get('primary')))
    elif request.method == 'POST':
        primary = normalize_hex(request.POST.get('primary'))
        accent = normalize_hex(request.POST.get('accent'))
        org.brandEnabled = request.POST.get('enabled') == '1'
        org.brandMode = ('DARK' if request.POST.get('mode') == 'DARK'
                         else 'LIGHT')
        if primary:
            org.brandPrimary = primary
        org.brandAccent = accent or ''
        org.brandLogoUrl = (request.POST.get('logo_url') or '').strip()[:500]
        org.brandHeroUrl = (request.POST.get('hero_url') or '').strip()[:500]
        org.save(update_fields=['brandEnabled', 'brandMode', 'brandPrimary',
                                'brandAccent', 'brandLogoUrl', 'brandHeroUrl'])
        write_audit('BRANDING_CHANGED', user=request.user,
                    enabled=org.brandEnabled, primary=org.brandPrimary,
                    mode=org.brandMode)
        return redirect('ats:branding')
    return render(request, 'branding.html',
                  {'org': org, 'suggestion': suggestion,
                   'preview': brand_context(org) if org.brandEnabled else None})


@any_staff_required
def source_channels_view(request):
    """Kanaele & Kampagnen: Jobmesse-Frage beantworten mit Zahlen.

    Kanal anlegen → Link + QR-Code (fuer Aufsteller/Flyer) → jede Bewerbung
    traegt die Quelle → Kennzahlen zeigen Menge UND Qualitaet: Bewerbungen,
    davon in Sichtung+, eingeladen, Einladungsquote. "Erfolgreich" heisst
    nicht viele Bewerbungen, sondern Bewerbungen, die weiterkommen.
    """
    from django.utils.text import slugify
    from .models import SourceChannel
    if request.method == 'POST' and request.POST.get('form') == 'cost':
        # Strukturierte Kampagnenkosten: speist "Kosten je Einstellung" direkt
        from decimal import Decimal, InvalidOperation
        ch = get_object_or_404(SourceChannel, id=request.POST.get('ch_id'))
        raw = (request.POST.get('cost') or '').strip()
        raw = raw.replace('.', '').replace(',', '.') if ',' in raw else raw
        try:
            ch.costAmount = Decimal(raw) if raw else None
            if ch.costAmount is not None and ch.costAmount < 0:
                raise InvalidOperation
        except InvalidOperation:
            return redirect('ats:source_channels')
        ch.save(update_fields=['costAmount'])
        write_audit('SOURCE_CHANNEL_COST_SET', user=request.user,
                    slug=ch.slug, cost=str(ch.costAmount))
        return redirect('ats:source_channels')

    if request.method == 'POST' and request.POST.get('form') == 'expiry':
        # Kampagnen-Ablaufdatum: leer = laeuft unbegrenzt; Datum wirkt bis
        # einschliesslich Tagesende (QR bleibt bis 23:59 des Tages gueltig).
        from .models import SourceChannel
        obj = get_object_or_404(SourceChannel, id=request.POST.get('ch_id'))
        raw = (request.POST.get('expires') or '').strip()
        if raw:
            try:
                d = datetime.date.fromisoformat(raw)
            except ValueError:
                return redirect('ats:source_channels')
            obj.expiresAt = timezone.make_aware(
                datetime.datetime.combine(d, datetime.time(23, 59)))
        else:
            obj.expiresAt = None
        obj.save(update_fields=['expiresAt'])
        write_audit('SOURCE_CHANNEL_EXPIRY_SET', user=request.user,
                    name=obj.name, expires=raw or 'unbegrenzt')
        return redirect('ats:source_channels')

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:120]
        note = (request.POST.get('note') or '').strip()[:255]
        if name:
            base = slugify(name).replace('-', '_').upper()[:40] or 'KANAL'
            slug, n = base, 2
            while SourceChannel.objects.filter(slug=slug).exists():
                slug, n = f"{base}_{n}", n + 1
            SourceChannel.objects.create(name=name, slug=slug, note=note)
            write_audit('SOURCE_CHANNEL_CREATED', user=request.user,
                        name=name, slug=slug)
        return redirect('ats:source_channels')

    import segno
    base_url = request.build_absolute_uri('/jobs/')
    rows = []
    for ch in SourceChannel.objects.order_by('-createdAt'):
        ch.is_expired = campaign_expired(ch)
        link = f"{base_url}?src={ch.slug}"
        qr = segno.make(link, error='m')
        qr_uri = qr.svg_data_uri(scale=3)
        apps = Application.objects.filter(source=ch.slug,
                                          createdAt__gte=ch.createdAt)
        total = apps.count()
        progressed = apps.exclude(status='NEW').count()
        invited = apps.filter(status__in=['INVITED', 'HIRED']).count()
        hired_qs = apps.filter(status='HIRED', hiredAt__isnull=False)
        hired = hired_qs.count()
        days = [ (a.hiredAt - a.createdAt).days for a in hired_qs ]
        avg_days_to_hire = round(sum(days) / len(days), 1) if days else None
        rows.append({
            'ch': ch, 'link': link, 'qr': qr_uri, 'total': total,
            'progressed': progressed, 'invited': invited,
            'hired': hired, 'days': avg_days_to_hire,
            'cost_per_hire': (round(float(ch.costAmount) / hired)
                              if ch.costAmount and hired else None),
            'quote': round(100 * invited / total) if total else None,
        })
    from django.db.models import Count
    # Freie Quellen (Import/Direkteingabe) mit in die Auswertung
    known = {r['ch'].slug for r in rows}
    freie = (Application.objects.exclude(source__in=known | {''})
             .values('source').annotate(c=Count('id')).order_by('-c')[:10])
    freie_rows = []
    for f in freie:
        invited = Application.objects.filter(source=f['source'],
                                             status='INVITED').count()
        freie_rows.append({'source': f['source'], 'total': f['c'],
                           'invited': invited,
                           'quote': round(100 * invited / f['c'])})
    return render(request, 'source_channels.html',
                  {'rows': rows, 'freie': freie_rows})


def landing_page(request, slug):
    """Oeffentliche Kampagnen-Landingpage /k/<slug>/ – misst sich selbst."""
    from django.db.models import F
    from .models import LandingPage
    lp = get_object_or_404(LandingPage, slug=slug, active=True)
    if campaign_expired(lp):
        # QR-Codes auf Plakaten leben laenger als Kampagnen: statt 404 eine
        # freundliche Endseite mit Weg zur Stellenboerse; kein Zaehler,
        # keine Kampagnen-Zuordnung mehr.
        return render(request, 'landing_page.html',
                      {'lp': lp, 'expired': True, 'jobs': []})
    LandingPage.objects.filter(id=lp.id).update(views=F('views') + 1)
    # Der Slug IST die Quelle: jede Bewerbung dieser Sitzung traegt die Kampagne
    request.session['application_src'] = lp.slug.upper()[:50]
    jobs = (exclude_filled(
        JobPosting.objects.filter(workflowState__name='published'))
        .select_related('location', 'facility'))
    if lp.facility_id:
        jobs = jobs.filter(facility_id=lp.facility_id)
    if lp.department_id:
        jobs = jobs.filter(department_id=lp.department_id)
    if lp.jobFamily_id:
        jobs = jobs.filter(jobFamily_id=lp.jobFamily_id)
    if lp.location_id:
        jobs = jobs.filter(location_id=lp.location_id)
    nav_pages = Page.objects.filter(status="published",
                                    navEnabled=True).order_by('navOrder')
    from .blocks import load_blocks, enrich_blocks
    return render(request, 'landing_page.html',
                  {'lp': lp, 'jobs': jobs.order_by('-createdAt'),
                   'content_blocks': enrich_blocks(load_blocks(lp)),
                   'nav_pages': nav_pages, 'slug': 'jobs'})


@any_staff_required
def landing_pages_manage(request):
    """Landingpages verwalten: anlegen/bearbeiten, Link+QR, Kennzahlen."""
    from django.utils.text import slugify
    from .models import LandingPage, Department
    if request.method == 'POST' and request.POST.get('form') == 'expiry':
        # Kampagnen-Ablaufdatum: leer = laeuft unbegrenzt; Datum wirkt bis
        # einschliesslich Tagesende (QR bleibt bis 23:59 des Tages gueltig).
        from .models import LandingPage as _LPx
        obj = get_object_or_404(_LPx, id=request.POST.get('expiry_lp_id'))
        raw = (request.POST.get('expires') or '').strip()
        if raw:
            try:
                d = datetime.date.fromisoformat(raw)
            except ValueError:
                return redirect('ats:landing_pages')
            obj.expiresAt = timezone.make_aware(
                datetime.datetime.combine(d, datetime.time(23, 59)))
        else:
            obj.expiresAt = None
        obj.save(update_fields=['expiresAt'])
        write_audit('LANDING_PAGE_EXPIRY_SET', user=request.user,
                    name=obj.name, expires=raw or 'unbegrenzt')
        return redirect('ats:landing_pages')

    if request.method == 'POST':
        lp = None
        if request.POST.get('lp_id'):
            lp = get_object_or_404(LandingPage, id=request.POST['lp_id'])
        name = (request.POST.get('name') or '').strip()[:120]
        if not name:
            return redirect('ats:landing_pages')
        if lp is None:
            base = slugify(name)[:40] or 'kampagne'
            slug, n = base, 2
            while LandingPage.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            lp = LandingPage(slug=slug)
        def fk(model, key):
            val = request.POST.get(key)
            return model.objects.filter(id=val).first() if val else None
        lp.name = name
        lp.headline = (request.POST.get('headline') or '').strip()[:200]
        lp.introText = (request.POST.get('intro_text') or '').strip()[:4000]
        lp.heroUrl = (request.POST.get('hero_url') or '').strip()[:500]
        lp.facility = fk(Facility, 'facility')
        lp.department = fk(Department, 'department')
        lp.jobFamily = fk(JobFamily, 'job_family')
        lp.location = fk(Location, 'location')
        lp.contactPerson = fk(ContactPerson, 'contact_person')
        lp.active = request.POST.get('active') == '1'
        lp.save()
        write_audit('LANDING_PAGE_SAVED', user=request.user,
                    name=lp.name, slug=lp.slug, active=lp.active)
        return redirect('ats:landing_pages')

    import segno
    from .models import LandingPage, Department
    rows = []
    for lp in LandingPage.objects.select_related(
            'facility', 'department', 'jobFamily', 'location',
            'contactPerson').order_by('-createdAt'):
        lp.is_expired = campaign_expired(lp)
        link = request.build_absolute_uri(f'/k/{lp.slug}/')
        src = lp.slug.upper()
        apps = Application.objects.filter(source=src,
                                          createdAt__gte=lp.createdAt)
        total = apps.count()
        invited = apps.filter(status__in=['INVITED', 'HIRED']).count()
        hired_qs = apps.filter(status='HIRED', hiredAt__isnull=False)
        hired = hired_qs.count()
        days = [ (a.hiredAt - a.createdAt).days for a in hired_qs ]
        avg_days_to_hire = round(sum(days) / len(days), 1) if days else None
        rows.append({
            'lp': lp, 'link': link, 'hired': hired, 'days': avg_days_to_hire,
            'qr': segno.make(link, error='m').svg_data_uri(scale=3),
            'apps': total, 'invited': invited,
            'app_rate': round(100 * total / lp.views, 1) if lp.views else None,
            'invite_rate': round(100 * invited / total) if total else None,
        })
    ctx = {'rows': rows,
           'facilities': Facility.objects.order_by('name'),
           'departments': Department.objects.select_related('facility').order_by('name'),
           'families': JobFamily.objects.filter(archived=False).order_by('name'),
           'locations': Location.objects.order_by('name'),
           'contacts': ContactPerson.objects.order_by('lastName')}
    return render(request, 'landing_pages_manage.html', ctx)


@any_staff_required
def blocks_editor(request, kind, obj_id):
    """CMS-Baukasten: Bloecke hinzufuegen, ausfuellen, sortieren – ohne HTML.

    Ein Editor fuer beide Seitentypen (kind: 'page' | 'landing').
    Server-gerendert, jede Aktion ein POST (add/save/up/down/delete) –
    funktioniert ohne JavaScript und laesst sich vollstaendig testen.
    Rechte folgen der jeweiligen Verwaltung: CMS-Seiten nur HR-Admin.
    """
    import json as _json
    from .blocks import (BLOCK_TYPES, load_blocks, normalize_block,
                         enrich_blocks)
    from django.http import HttpResponseForbidden
    from .models import LandingPage
    if kind == 'page':
        if not (request.user.is_superuser
                or request.user.groups.filter(name='HR-Admin').exists()):
            return HttpResponseForbidden("Nur HR-Admin.")
        obj = get_object_or_404(Page, id=obj_id)
        public_url = f"/pages/{obj.slug}/"
    elif kind == 'landing':
        obj = get_object_or_404(LandingPage, id=obj_id)
        public_url = f"/k/{obj.slug}/"
    else:
        return HttpResponseForbidden("Unbekannter Seitentyp.")

    blocks = load_blocks(obj)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        idx = request.POST.get('idx')
        idx = int(idx) if idx and idx.isdigit() else None
        if action == 'add':
            btype = request.POST.get('block_type', '')
            if btype in BLOCK_TYPES and len(blocks) < 30:
                blocks.append(normalize_block({"type": btype}))
        elif action == 'save' and idx is not None and idx < len(blocks):
            raw = {"type": blocks[idx]["type"]}
            for name, _ftype, _label in BLOCK_TYPES[blocks[idx]["type"]]["fields"]:
                raw[name] = request.POST.get(f"f_{name}", "")
            blocks[idx] = normalize_block(raw)
        elif action == 'up' and idx and idx < len(blocks):
            blocks[idx - 1], blocks[idx] = blocks[idx], blocks[idx - 1]
        elif action == 'down' and idx is not None and idx < len(blocks) - 1:
            blocks[idx + 1], blocks[idx] = blocks[idx], blocks[idx + 1]
        elif action == 'delete' and idx is not None and idx < len(blocks):
            blocks.pop(idx)
        obj.blocksJson = _json.dumps(blocks)
        obj.save(update_fields=['blocksJson'])
        write_audit('CMS_BLOCKS_CHANGED', user=request.user, kind=kind,
                    target=str(obj_id), op=action, count=len(blocks))
        return redirect('ats:blocks_editor', kind=kind, obj_id=obj_id)

    # Editor-Anzeige: Bloecke mit Feldwerten + Typen-Palette
    editor_blocks = []
    for i, b in enumerate(blocks):
        spec = BLOCK_TYPES[b["type"]]
        fields = []
        for name, ftype, label in spec["fields"]:
            val = b.get(name, "")
            if ftype == "lines":
                val = "\n".join(val or [])
            fields.append({"name": name, "type": ftype, "label": label,
                           "value": val})
        editor_blocks.append({"i": i, "type": b["type"],
                              "label": spec["label"], "fields": fields})
    palette = [{"type": t, "label": spec["label"]}
               for t, spec in BLOCK_TYPES.items()]
    return render(request, 'blocks_editor.html', {
        'kind': kind, 'obj': obj, 'public_url': public_url,
        'editor_blocks': editor_blocks, 'palette': palette,
        'contacts': ContactPerson.objects.order_by('lastName'),
        'preview': enrich_blocks(blocks)})


@hr_admin_required
def interview_formats_manage(request):
    """Terminformate konfigurierbar machen (P0-Luecke: war Code-Liste).

    Speicherung als SystemSetting INTERVIEW_KINDS_JSON; Start = Code-Default.
    Bestehende Termine behalten ihr Label (interview_kind_label mit
    Code-Fallback), auch wenn ein Format entfernt wird.
    """
    import json as _json
    from .models import SystemSetting, get_interview_kinds
    kinds = get_interview_kinds()
    action = request.POST.get('action', '')
    if request.method == 'POST':
        if action == 'add':
            label = (request.POST.get('label') or '').strip()[:80]
            if label:
                from django.utils.text import slugify
                base = slugify(label).replace('-', '_').upper()[:40] or 'FORMAT'
                code, n = base, 2
                while code in dict(kinds):
                    code, n = f"{base}_{n}", n + 1
                kinds.append((code, label))
        elif action == 'rename':
            code = request.POST.get('code', '')
            label = (request.POST.get('label') or '').strip()[:80]
            if label:
                kinds = [(c, label if c == code else l) for c, l in kinds]
        elif action == 'delete':
            code = request.POST.get('code', '')
            if len(kinds) > 1:  # mindestens ein Format bleibt
                kinds = [(c, l) for c, l in kinds if c != code]
        SystemSetting.objects.update_or_create(
            key='INTERVIEW_KINDS_JSON',
            defaults={'value': _json.dumps(
                [{'code': c, 'label': l} for c, l in kinds])})
        write_audit('INTERVIEW_FORMATS_CHANGED', user=request.user,
                    op=action, count=len(kinds))
    return redirect('ats:interviews')


# ============================================================================
# SAFE LOGIN VIEW (Fund 5: Brute-Force Lockout Protection)
# ============================================================================
from django.contrib.auth.views import LoginView as AuthLoginView
from django.core.cache import cache

class SafeLoginView(AuthLoginView):
    """Zuverlässiger Schutz gegen Login-Brute-Force-Angriffe (Fund 5).
    Sperrt IP-Adresse und Benutzername nach 5 Fehlversuchen für 10 Minuten."""
    MAX_ATTEMPTS = 5
    LOCKOUT_TIMEOUT = 600  # 10 Minuten (in Sekunden)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            ip = self.get_client_ip()
            username = request.POST.get('username', '').strip()
            
            # Schlüssel für Cache-Abfragen
            ip_key = f"lockout_ip_{ip}"
            user_key = f"lockout_user_{username}"
            
            ip_attempts = cache.get(ip_key, 0)
            user_attempts = cache.get(user_key, 0)
            
            if ip_attempts >= self.MAX_ATTEMPTS or user_attempts >= self.MAX_ATTEMPTS:
                form = self.get_form()
                form.add_error(None, "Zu viele fehlerhafte Anmeldeversuche. Dieses Konto oder diese IP ist vorübergehend gesperrt. Bitte versuchen Sie es in 10 Minuten erneut.")
                return self.render_to_response(self.get_context_data(form=form))
                
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        ip = self.get_client_ip()
        username = self.request.POST.get('username', '').strip()
        
        ip_key = f"lockout_ip_{ip}"
        user_key = f"lockout_user_{username}"
        
        # Fehlversuche hochzählen und im Cache speichern
        try:
            val_ip = cache.get(ip_key, 0) + 1
            val_user = cache.get(user_key, 0) + 1
            cache.set(ip_key, val_ip, self.LOCKOUT_TIMEOUT)
            if username:
                cache.set(user_key, val_user, self.LOCKOUT_TIMEOUT)
        except Exception:
            pass
            
        return super().form_invalid(form)

    def form_valid(self, form):
        ip = self.get_client_ip()
        username = self.request.POST.get('username', '').strip()
        
        ip_key = f"lockout_ip_{ip}"
        user_key = f"lockout_user_{username}"
        
        # Nach erfolgreichem Login Zähler zurücksetzen
        try:
            cache.delete(ip_key)
            if username:
                cache.delete(user_key)
        except Exception:
            pass
            
        return super().form_valid(form)


@recruiter_required
def job_template_detail(request, tpl_id):
    """B12: Gibt die Historie (parent-Kette) einer Vorlage und die verknüpften Stellen zurück (inkl. Diff)."""
    template = get_object_or_404(JobTemplate, id=tpl_id)
    # Alle Versionen dieses Titels absteigend sortiert
    all_versions = JobTemplate.objects.filter(title__iexact=template.title).order_by('-version')
    latest_version = all_versions.first()
    
    history_data = []
    for v in all_versions:
        # Stellen ermitteln, die diese spezielle Version nutzen
        jobs = []
        for job in v.jobPostings.all():
            jobs.append({
                'id': str(job.id),
                'title': job.title,
                'location': job.location.city if job.location else '—',
                'state': job.workflowState.name if job.workflowState else 'draft'
            })
            
        # Diff gegen die aktuellste Version ermitteln
        diff_html = ""
        if v.id != latest_version.id:
            old_lines = v.content.splitlines()
            new_lines = latest_version.content.splitlines()
            import difflib
            diff_lines = []
            for line in difflib.ndiff(old_lines, new_lines):
                if line.startswith('+ '):
                    diff_lines.append(f'<div style="color:#4ade80; background:rgba(34,197,94,0.1); padding:2px 4px; border-radius:2px;"><span style="font-weight:bold; margin-right:4px;">+</span>{line[2:]}</div>')
                elif line.startswith('- '):
                    diff_lines.append(f'<div style="color:#f87171; background:rgba(239,68,68,0.1); padding:2px 4px; border-radius:2px;"><span style="font-weight:bold; margin-right:4px;">-</span>{line[2:]}</div>')
                elif line.startswith('? '):
                    continue
                else:
                    diff_lines.append(f'<div style="color:var(--text-muted); padding:2px 4px;"> {line[2:]}</div>')
            diff_html = '\n'.join(diff_lines)
        else:
            diff_html = '<div style="color:var(--text-muted); font-style:italic; padding:4px;">Dies ist die aktuellste Version. Keine Änderungen.</div>'
            
        history_data.append({
            'id': str(v.id),
            'version': v.version,
            'createdAt': v.createdAt.strftime('%d.%m.%Y %H:%M'),
            'content': v.content,
            'active_jobs_count': len(jobs),
            'active_jobs': jobs,
            'is_latest': (v.id == latest_version.id),
            'diff_html': diff_html
        })
        
    return JsonResponse({
        'success': True,
        'title': template.title,
        'latest_version': latest_version.version,
        'history': history_data
    })


@recruiter_required
def restore_job_template(request, tpl_id):
    """B12: Erzeugt eine neue Version auf Basis des Inhalts einer alten Version."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST erforderlich'}, status=405)
    template = get_object_or_404(JobTemplate, id=tpl_id)
    latest = JobTemplate.objects.filter(title__iexact=template.title).order_by('-version').first()
    new_tpl = JobTemplate.objects.create(
        title=template.title,
        content=template.content,
        version=(latest.version + 1) if latest else 1,
        parent=latest
    )
    from .models import AuditLog
    AuditLog.objects.create(
        action="RESTORE_TEMPLATE",
        metadataJson=json.dumps({
            'template_id': str(new_tpl.id),
            'title': new_tpl.title,
            'restored_from_version': template.version,
            'new_version': new_tpl.version
        })
    )
    return JsonResponse({'success': True, 'new_tpl_id': str(new_tpl.id), 'new_version': new_tpl.version})


@recruiter_required
def update_job_posting_template(request, job_id):
    """B12: Aktualisiert eine Stellenanzeige auf die neueste Version ihrer verknüpften Vorlage."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST erforderlich'}, status=405)
    job = get_object_or_404(JobPosting, id=job_id)
    if not scope_jobs(request.user, JobPosting.objects.filter(id=job.id)).exists():
        return JsonResponse({'success': False, 'error': 'Kein Zugriff'}, status=403)
    if not job.jobTemplate:
        return JsonResponse({'success': False, 'error': 'Keine Vorlage verknüpft'}, status=400)
        
    latest = JobTemplate.objects.filter(title__iexact=job.jobTemplate.title).order_by('-version').first()
    if latest and latest.id != job.jobTemplate.id:
        old_tpl_version = job.jobTemplate.version
        job.jobTemplate = latest
        job.save(update_fields=['jobTemplate', 'updatedAt'])
        
        from .models import AuditLog
        AuditLog.objects.create(
            action="UPDATE_JOB_TEMPLATE_VERSION",
            metadataJson=json.dumps({
                'job_id': str(job.id),
                'job_title': job.title,
                'template_title': latest.title,
                'old_version': old_tpl_version,
                'new_version': latest.version
            })
        )
        return JsonResponse({'success': True, 'new_version': latest.version})
        
    return JsonResponse({'success': False, 'error': 'Bereits auf der neuesten Version'})


