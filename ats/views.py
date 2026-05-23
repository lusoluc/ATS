import os
import json
import uuid
import datetime
from django.shortcuts import render, get_object_or_404, redirect
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
    Message, Page, AuditLog, AILearningSample, SystemSetting
)

# ============================================================================
# AUTO-SEEDING UTILITY
# ============================================================================

def seed_data_if_empty():
    """Seeds the SQLite database with fully functional mock data if it is empty."""
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


def job_list(request):
    """Renders the career board with search & filtering capabilities."""
    nav_pages = Page.objects.filter(status="published", navEnabled=True).order_by('navOrder')
    
    # Filter only published jobs
    jobs = JobPosting.objects.filter(workflowState__name="published").select_related('location', 'facility', 'department')
    
    # Search and filter inputs
    search_query = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    
    if search_query:
        jobs = jobs.filter(title__icontains=search_query)
    if location_filter:
        jobs = jobs.filter(location__id=location_filter)
    if dept_filter:
        jobs = jobs.filter(department__id=dept_filter)
        
    locations = Location.objects.filter(archived=False)
    departments = Department.objects.all()
    
    context = {
        'nav_pages': nav_pages,
        'jobs': jobs,
        'locations': locations,
        'departments': departments,
        'search_query': search_query,
        'location_filter': location_filter,
        'dept_filter': dept_filter,
        'slug': 'jobs'
    }
    return render(request, 'job_list.html', context)


def job_detail(request, job_id):
    """Renders a single job's detail page with modular descriptions."""
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
        
        # 3. Evaluate screening questions
        ko_failed = False
        answers_dict = {}
        
        for q in screening_questions:
            q_id = q['id']
            ans = request.POST.get(f'question_{q_id}', '').strip()
            answers_dict[q['question']] = ans
            
            # If mandatory and answer differs from expected
            if q.get('isMandatory') and ans != q.get('expectedAnswer'):
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
            applicant, created = Applicant.objects.get_or_create(
                email=email,
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
                
            # 7. Mock AI Screening Score calculation
            ai_score = 'C'
            ai_rationale = 'Automatische Analyse ausstehend.'
            if not ko_failed:
                # Give a beautiful, realistic reasoning
                content_to_scan = (cover_letter + " " + (cv_file.name if cv_file else "")).lower()
                if 'django' in content_to_scan or 'python' in content_to_scan:
                    ai_score = 'A'
                    ai_rationale = 'Sehr hohe Übereinstimmung mit dem Anforderungsprofil (Django/Python Fokus erkannt).'
                elif 'javascript' in content_to_scan or 'react' in content_to_scan:
                    ai_score = 'B'
                    ai_rationale = 'Gute Frontend-Kenntnisse, Django/Python-Kenntnisse müssen im Gespräch verifiziert werden.'
                else:
                    ai_score = 'C'
                    ai_rationale = 'Durchschnittliche Passgenauigkeit. Motivierte Bewerbung, Qualifikation im Detail prüfen.'

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
                consentTalentPool=consent_pool
            )
            
            # Log audit trail
            AuditLog.objects.create(
                action="SUBMIT_APPLICATION",
                applicationId=str(application.id),
                metadataJson=json.dumps({"jobTitle": job.title, "koFailed": ko_failed})
            )
            
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

def dashboard(request):
    """Renders the recruiter Kanban ATS dashboard with stage columns and interactive modals."""
    applications = Application.objects.select_related('applicant', 'jobPosting', 'jobPosting__location').order_by('-createdAt')
    
    # Categorize applications into Kanban columns
    columns = {
        'NEW': [],
        'IN_REVIEW': [],
        'INVITED': [],
        'REJECTED': [],
    }
    
    for app in applications:
        status = app.status
        # Handle unmapped fallback
        if status not in columns:
            status = 'NEW'
        columns[status].append(app)
        
    # Extra data for interactive modals
    active_jobs = JobPosting.objects.filter(workflowState__name="published")
    interview_slots = InterviewSlot.objects.filter(isBooked=False)
    
    # Calculate some fast stats
    stats = {
        'total': applications.count(),
        'new': len(columns['NEW']),
        'in_review': len(columns['IN_REVIEW']),
        'invited': len(columns['INVITED']),
        'rejected': len(columns['REJECTED']),
    }
    
    context = {
        'columns': columns,
        'active_jobs': active_jobs,
        'interview_slots': interview_slots,
        'stats': stats,
        'slug': 'dashboard'
    }
    return render(request, 'dashboard.html', context)


@csrf_exempt
def update_status(request, app_id):
    """API view to update an application's status (for drag-and-drop or status changes)."""
    if request.method == 'POST':
        app = get_object_or_404(Application, id=app_id)
        new_status = request.POST.get('status', '').strip().upper()
        
        valid_statuses = ['NEW', 'IN_REVIEW', 'INVITED', 'REJECTED']
        if new_status in valid_statuses:
            old_status = app.status
            app.status = new_status
            app.save()
            
            # Log action
            AuditLog.objects.create(
                action="STATUS_CHANGE",
                applicationId=str(app.id),
                metadataJson=json.dumps({"oldStatus": old_status, "newStatus": new_status})
            )
            
            # Handle automatic responses/rejection reasons if needed
            if new_status == 'REJECTED':
                app.withdrawReason = request.POST.get('reason', 'Durch Recruiter abgelehnt.')
                app.save()
                
            return JsonResponse({'success': True, 'old_status': old_status, 'new_status': new_status})
            
    return JsonResponse({'success': False, 'error': 'Invalid status or request method.'})


@csrf_exempt
def add_note(request, app_id):
    """POST view to add recruiter notes to an application."""
    if request.method == 'POST':
        app = get_object_or_404(Application, id=app_id)
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


@csrf_exempt
def schedule_interview(request):
    """POST view to schedule an interview with an applicant."""
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        slot_id = request.POST.get('slot_id')
        location_type = request.POST.get('location_type', 'REMOTE')
        meeting_link = request.POST.get('meeting_link', '')
        
        app = get_object_or_404(Application, id=app_id)
        
        with transaction.atomic():
            if slot_id:
                slot = get_object_or_404(InterviewSlot, id=slot_id)
                slot.isBooked = True
                slot.application = app
                slot.save()
                scheduled_time = slot.startTime
            else:
                # Custom quick schedule (default to 2 days from now)
                scheduled_time = timezone.now() + datetime.timedelta(days=2)
                
            # Create Interview record
            Interview.objects.create(
                application=app,
                scheduledAt=scheduled_time,
                locationType=location_type,
                meetingLink=meeting_link or "https://meet.google.com/securats-mock-call"
            )
            
            # Advance application status to INVITED
            old_status = app.status
            app.status = 'INVITED'
            app.save()
            
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
