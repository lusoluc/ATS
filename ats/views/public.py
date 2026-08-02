"""SecurATS Views — Oeffentliche Seiten: Stellenboerse, Bewerbung, Kandidatenportal, CMS-Seiten.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ..audit import write_audit
from ..models import (
    Applicant,
    ApplicantToken,
    Application,
    ApplicationDocument,
    AuditLog,
    Department,
    Facility,
    FacilityProfile,
    Interview,
    InterviewSlot,
    JobFamily,
    JobPosting,
    Location,
    Message,
    Page,
    SystemSetting,
)
from .ai import evaluate_with_local_gemma, get_ollama_url
from .common import _remember_campaign_src, campaign_expired, exclude_filled, seed_data_if_empty

logger = logging.getLogger(__name__)

__all__ = ["home", "job_list", "job_detail", "bewerben", "candidate_portal", "page_detail", "facility_profile", "landing_page", "job_alert_subscribe", "job_alert_confirm", "job_alert_manage", "pricing_view", "healthz"]


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

    # Modulare Bestandteile (JSONField liefert direkt Listen)
    tasks = job.tasksJson or []
    requirements = job.requirementsJson or []

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

    # Screening-Fragen (JSONField liefert direkt eine Liste)
    screening_questions = job.screeningQuestionsJson or []

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
            # § 164 SGB IX: freiwillige Angabe (Art. 9 -> verschluesselt,
            # nur bei ausdruecklichem Ankreuzen, nie Scoring-Eingabe).
            disability_disclosed = request.POST.get('disability_disclosure') == 'on'
            application = Application.objects.create(
                applicant=applicant,
                jobPosting=job,
                cvStorageId=cv_storage_path,
                coverLetterTxt=cover_letter,
                screeningAnswersJson=answers_dict,
                aiScore=ai_score,
                aiRationale=ai_rationale,
                status=initial_status,
                withdrawReason=withdraw_reason,
                severeDisability='JA' if disability_disclosed else '',
                consentTalentPool=consent_pool,
                source=(request.POST.get('source') or request.GET.get('src')
                        or request.session.get('application_src')
                        or 'DIRECT').upper()[:50],
            )

            # L6: Async-Scoring nachreichen (Worker füllt aiScore/aiRationale)
            if ai_scoring_on and ai_async and not ko_failed:
                from ..queue import enqueue
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

            # § 164 SGB IX: Bei freiwilliger Angabe wird die Schwerbehinderten-
            # vertretung unmittelbar unterrichtet (Gruppe "SBV"). Fail-safe:
            # ein Mail-Fehler darf die Bewerbung nie blockieren. Das Audit
            # traegt bewusst KEINE Gesundheitsdaten, nur das Ereignis.
            if disability_disclosed:
                try:
                    from django.contrib.auth.models import Group as _Group
                    _sbv, _ = _Group.objects.get_or_create(name='SBV')
                    _mails = [u.email for u in _sbv.user_set.all() if u.email]
                    if _mails:
                        from django.core.mail import send_mail as _send
                        _send(
                            f"SBV-Beteiligung: neue Bewerbung – {job.title}",
                            ("Zu der Stelle ist eine Bewerbung mit freiwilliger "
                             "Angabe einer Schwerbehinderung/Gleichstellung "
                             "eingegangen. Bitte beziehen Sie sich nach "
                             "§ 164/§ 178 Abs. 2 SGB IX ein: "
                             f"/recruiter/dashboard/#card-{application.id}"),
                            None, _mails, fail_silently=True)
                    write_audit('SBV_NOTIFIED', application_id=application.id,
                                recipients=len(_mails))
                except Exception:
                    logger.exception('SBV-Unterrichtung fehlgeschlagen')

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

            # Eingangsbestaetigung an die Bewerber:in.
            # WARUM das wichtig ist: Die Erfolgsseite verspricht eine
            # Bestaetigung per Mail – bisher wurde KEINE verschickt. Schlimmer:
            # der Magic-Link zum Status-Portal stand nur auf dieser einen Seite.
            # Wer den Tab schloss, kam nie wieder ins Portal (Status, Termine,
            # Rueckfragen) – das Feature war praktisch unbenutzbar.
            # Eine Vorlage "Eingangsbestaetigung" wird genutzt, wenn vorhanden
            # (Platzhalter {name}, {stelle}, {firma}, {portal}); sonst
            # freundlicher Standardtext.
            # Ein Mailfehler darf die Bewerbung NIE scheitern lassen.
            try:
                from django.core.mail import send_mail

                from ..models import EmailTemplate
                _fs = SystemSetting.objects.filter(key='FIRMA').first()
                company = (_fs.value if _fs else '') or 'SecurATS'
                tpl = (EmailTemplate.objects
                       .filter(name__icontains='eingangsbest').first())
                if tpl:
                    body = (tpl.textContent or tpl.htmlContent or '')
                    subject = (tpl.subject or 'Ihre Bewerbung ist eingegangen')
                    for k, v in (('{name}', applicant.firstName or ''),
                                 ('{stelle}', job.title),
                                 ('{firma}', company),
                                 ('{portal}', portal_url)):
                        body = body.replace(k, v)
                        subject = subject.replace(k, v)
                else:
                    subject = f'Ihre Bewerbung ist eingegangen – {job.title}'
                    body = (
                        f'Guten Tag {applicant.firstName},\n\n'
                        f'vielen Dank für Ihre Bewerbung auf die Stelle '
                        f'"{job.title}". Wir haben Ihre Unterlagen erhalten '
                        f'und melden uns, sobald wir sie gesichtet haben.\n\n'
                        f'Ihren Bewerbungsstatus können Sie jederzeit hier '
                        f'einsehen – ohne Passwort, der Link ist persönlich '
                        f'und 90 Tage gültig:\n{portal_url}\n\n'
                        f'Dort sehen Sie den aktuellen Stand, können Termine '
                        f'wahrnehmen und uns Rückfragen stellen.\n\n'
                        f'Freundliche Grüße\n{company}')
                if applicant.email:
                    send_mail(subject, body, None, [applicant.email],
                              fail_silently=True)
                    write_audit('APPLICATION_CONFIRMATION_SENT',
                                application_id=application.id)
            except Exception:
                # Bewerbung ist bereits gespeichert – sie darf an einer
                # fehlgeschlagenen Mail nicht scheitern.
                logger.exception(
                    'Eingangsbestaetigung fuer Bewerbung %s fehlgeschlagen',
                    application.id)

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
        from ..models import TalentPoolSubscription
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
            # Stufe 4: Auto-Antwort NUR fuer sichere, eindeutige Anliegen
            # (Stand/Ablauf), wenn freigeschaltet. Fail-safe: ein Fehler darf
            # die Bewerber-Nachricht nie blockieren.
            auto_replied = False
            try:
                from ..auto_reply import maybe_auto_reply
                auto_replied = maybe_auto_reply(app, content)
            except Exception:
                logger.exception('Auto-Antwort fehlgeschlagen')
            cp = app.jobPosting.contactPerson
            if cp and cp.email:
                try:
                    from django.core.mail import send_mail
                    auto_note = ('\n\n(Eine automatische Status-Antwort wurde '
                                 'bereits gesendet – bitte bei Bedarf ergänzen.)'
                                 if auto_replied else '')
                    send_mail(
                        f'Rückfrage zur Bewerbung – {app.jobPosting.title}',
                        (f'{app.applicant.firstName} {app.applicant.lastName} fragt:\n\n'
                         f'{content}\n\nAntworten: /recruiter/applications/{app.id}/messages/'
                         f'{auto_note}'),
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
    from ..blocks import enrich_blocks, load_blocks
    return render(request, 'page.html',
                  {'page': page, 'nav_pages': nav_pages, 'slug': slug,
                   'content_blocks': enrich_blocks(load_blocks(page))})


# --- WP8: Öffentliche Einrichtungs-/Standortseite (Karriere-Branding) ---------
def facility_profile(request, slug):
    """Karriereseite je Einrichtung: Profil, Bilder, offene Stellen (WP8)."""
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


def landing_page(request, slug):
    """Oeffentliche Kampagnen-Landingpage /k/<slug>/ – misst sich selbst."""
    from django.db.models import F

    from ..models import LandingPage
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
    from ..blocks import enrich_blocks, load_blocks
    return render(request, 'landing_page.html',
                  {'lp': lp, 'jobs': jobs.order_by('-createdAt'),
                   'content_blocks': enrich_blocks(load_blocks(lp)),
                   'nav_pages': nav_pages, 'slug': 'jobs'})


# --- B5: Öffentliches Job-Alert-Abo -----------------------------------------
def job_alert_subscribe(request):
    import secrets as _secrets

    from ..models import JobAlertLog, JobAlertSubscription, Location
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
    from ..models import JobAlertLog, JobAlertSubscription
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
    from ..models import JobAlertLog, JobAlertSubscription
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


def healthz(request):
    """WP7/UC-SO-06: Gesamt-Health (App, DB, Media, KI-Anbindung, Queue)."""
    import json as _json
    import urllib.request

    from ..queue import queue_depth

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
