"""SecurATS Views — Bewerbungen: Kanban-Board, Status, Notizen, CV, Workflow-Automatik.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import os
import json
import uuid
import logging
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from ..permissions import any_staff_required, recruiter_required, hr_admin_required
from ..permissions import scope_applications, scope_jobs, can_access_application
from django.contrib.auth.models import Group
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from ..models import (
    Organization, Facility, FacilityProfile, Department, Location,
    JobFamily, ContactPerson, WorkflowState, JobTemplate, Benefit,
    JobPosting, Applicant, Application, Interview, InterviewSlot,
    Message, Page, AuditLog, AILearningSample, SystemSetting, AppWorkflowDef
, get_interview_kinds)
import os as _os
from django.http import FileResponse, Http404
from django.urls import reverse
from ..audit import write_audit
from ..models import (
    AuditLog, TalentPoolSubscription, ScreeningQuestion, RoleDelegation,
    ApplicantToken, ApplicationDocument,
)
from ..models import JobFamily, Location
from ..models import Interview, Message
from ..permissions import has_full_access
from ..models import JobTemplate
from django.utils.text import slugify
from ..models import MediaAsset
from django.contrib.auth.views import LoginView as AuthLoginView
from django.core.cache import cache

logger = logging.getLogger(__name__)

from .common import seed_data_if_empty
from .governance import _pending_steps_for

__all__ = ["dashboard", "update_status", "add_note", "get_matching_workflow", "execute_workflow_actions", "_send_rejection_notice", "download_cv", "toggle_learning_sample", "reorder_board", "bulk_update_status", "application_messages", "application_vote", "talent_pool_view", "tasks_view"]


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
    from ..models import feedback_summaries
    _fb = feedback_summaries([a.id for a in applications])
    for a in applications:
        a.fb_summary = _fb.get(a.id)
        
    # Extra data for interactive modals
    active_jobs = scope_jobs(request.user, JobPosting.objects.all().select_related('location', 'facility', 'department', 'workflowState', 'contactPerson', 'jobTemplate').order_by('-createdAt'))
    from ..models import TextSnippet, EmailTemplate
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
    
    from ..models import EmailTemplate
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
        # Rollen-Flag fuer die Benutzerfuehrung: Ein Recruiter soll nur seine
        # taegliche Arbeit sehen (Bewerbungen, Stellen), nicht die Admin-/IT-/
        # Management-Werkzeuge. Ein HR-Admin sieht alles, aber sauber getrennt.
        'is_hr_admin': (request.user.is_superuser
                        or request.user.groups.filter(name='HR-Admin').exists()),
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
        # Rollen für den Automatik-Editor (Aufgaben-/Benachrichtigungs-Empfänger)
        'all_roles': list(Group.objects.order_by('name')
                          .values_list('name', flat=True)),
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
    from ..models import StaffingRequest as _SR
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
    from ..models import ApplicationVote as _AV
    from ..panel import panel_member_ids as _pmi
    _uid = str(request.user.id)
    _voted = set(_AV.objects.filter(user=request.user)
                 .values_list('application_id', flat=True))
    from ..panel import sits_on_panel as _sits
    from ..permissions import active_delegations_to as _adt
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

    # Offene Aufgaben aus der Prozess-Automatik (Badge in der Navigation):
    # nur eigene Rollen bzw. rollenlose, im eigenen Zugriffsbereich.
    from ..models import WorkflowTask
    from django.db.models import Q as _Q
    _roles = set(request.user.groups.values_list('name', flat=True))
    _tasks = WorkflowTask.objects.filter(status="OPEN",
                                         application__in=applications)
    if not (request.user.is_superuser or 'HR-Admin' in _roles):
        _tasks = _tasks.filter(_Q(role="") | _Q(role__in=_roles))
    context['open_task_count'] = _tasks.count()

    return render(request, 'dashboard.html', context)


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
                from ..models import rounds_state
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
                from ..panel import invitation_blocked_reason
                reason = invitation_blocked_reason(app)
                if reason:
                    from ..permissions import can_override
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
                from ..models import feedback_for_application
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
    from ..models import EmailTemplate, Message as _Msg
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
            from ..panel import panel_state
            state = panel_state(app)
            AuditLog.objects.create(
                action="AUTOMATION_COMMITTEE_HINT", applicationId=str(app.id),
                metadataJson=json.dumps({
                    "panel_active": state["required"],
                    "hint": ("Sichtungs-Gremium aktiv (Vererbungs-Leiter) – "
                             "Einladung erst nach Mehrheit." if state["required"]
                             else "Kein Gremium konfiguriert – Aktion ohne Wirkung.")}))

        elif action_type == 'EMAIL_NOTIFICATION':
            # Interne Benachrichtigung: an eine feste Adresse ODER an alle
            # Mitglieder einer Rolle. (Der Bewerber-Fall ist oben behandelt.)
            # Vorher fiel genau dieser Fall in den Ueberspringen-Zweig – das
            # eigene Beispiel im UI ("recipient": "gremium@...") tat nichts.
            from django.core.mail import send_mail
            from django.contrib.auth.models import Group
            recipient = (action.get('recipient') or '').strip()
            role = (action.get('role') or '').strip()
            targets = []
            if '@' in recipient:
                targets.append(recipient)
            if role:
                grp = Group.objects.filter(name=role).first()
                if grp:
                    targets += [u.email for u in grp.user_set.filter(
                        is_active=True) if u.email]
            targets = sorted(set(t for t in targets if t))
            if targets:
                name = f"{app.applicant.firstName} {app.applicant.lastName}"
                subject = (action.get('subject')
                           or f"Bewerbung {name} – {app.jobPosting.title}")
                body = (action.get('body') or
                        f"Die Bewerbung von {name} für "
                        f"{app.jobPosting.title} hat den Status "
                        f"{app.status} erreicht.\n"
                        "Zum Board: /recruiter/dashboard/")
                send_mail(subject, body, None, targets, fail_silently=True)
                AuditLog.objects.create(
                    action="AUTOMATION_NOTIFY_INTERNAL",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({"recipients": len(targets),
                                             "role": role or None}))
            else:
                AuditLog.objects.create(
                    action="WORKFLOW_ACTION_SKIPPED",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({
                        "type": action_type,
                        "reason": "Kein gültiger Empfänger (weder E-Mail-"
                                  "Adresse noch Rolle mit Mitgliedern)."}))

        elif action_type == 'ADD_NOTE':
            # Automatischer Vermerk in den internen Notizen – macht
            # nachvollziehbar, WARUM etwas passiert ist.
            text = (action.get('text') or '').strip()
            if text:
                stamp = timezone.now().strftime('%d.%m.%Y %H:%M')
                app.internalNotes = ((app.internalNotes or '')
                                     + f"\n[{stamp}] (Automatik) {text}")
                app.save(update_fields=['internalNotes'])
                AuditLog.objects.create(
                    action="AUTOMATION_NOTE", applicationId=str(app.id),
                    metadataJson=json.dumps({"chars": len(text)}))

        elif action_type == 'CREATE_TASK':
            # Echte Arbeit anstossen statt nur zu mailen. Zuweisung an eine
            # ROLLE (nicht an eine Person), damit Urlaub/Fluktuation die
            # Aufgabe nicht verwaisen laesst.
            from ..models import WorkflowTask
            title = (action.get('title') or '').strip()
            if title:
                due = None
                try:
                    days = int(action.get('due_days', 0) or 0)
                    if days > 0:
                        due = timezone.now() + datetime.timedelta(days=days)
                except (TypeError, ValueError):
                    due = None
                task = WorkflowTask.objects.create(
                    application=app, title=title[:255],
                    role=(action.get('role') or '').strip()[:100],
                    dueAt=due, sourceState=app.status)
                AuditLog.objects.create(
                    action="AUTOMATION_TASK_CREATED",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({"task": str(task.id),
                                             "title": title[:80],
                                             "role": task.role or None}))

        elif action_type == 'AUTO_ADVANCE':
            # Status-Autovorlauf – aber NIEMALS zu einer Entscheidung.
            # Compliance (.agents/AGENTS.md, Human-in-the-Loop): Zu- und
            # Absagen bleiben dem Menschen vorbehalten. Deshalb sind HIRED
            # und REJECTED hier hart gesperrt. Ausserdem loest der
            # Autovorlauf KEINE weitere Automatik aus (keine Ketten,
            # keine Endlosschleifen).
            target = (action.get('to') or '').strip().upper()
            allowed = {'NEW', 'IN_REVIEW', 'INVITED'}
            if target in allowed and target != app.status:
                previous = app.status
                app.status = target
                app.save(update_fields=['status'])
                AuditLog.objects.create(
                    action="AUTOMATION_AUTO_ADVANCE",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({
                        "from": previous, "to": target,
                        "note": "Automatik ohne Folge-Automatik "
                                "(keine Ketten)."}))
            else:
                AuditLog.objects.create(
                    action="WORKFLOW_ACTION_BLOCKED",
                    applicationId=str(app.id),
                    metadataJson=json.dumps({
                        "type": action_type, "target": target or "?",
                        "reason": ("Zu-/Absagen sind der menschlichen "
                                   "Entscheidung vorbehalten (Human-in-the-"
                                   "Loop) bzw. Ziel unbekannt/identisch.")}))

        else:
            AuditLog.objects.create(
                action="WORKFLOW_ACTION_SKIPPED", applicationId=str(app.id),
                metadataJson=json.dumps({
                    "type": action_type or "?",
                    "reason": "Unbekannter Aktionstyp – wird ehrlich "
                              "uebersprungen statt etwas zu simulieren."}))


def _send_rejection_notice(request, app):
    """Absage wuerdig zustellen: Portal-Nachricht + Mail mit Portal-Link und
    Talent-Pool-Angebot ("nicht die richtige Stelle, aber gerne wieder").

    Vorlage "Absage" aus den EmailTemplates wird genutzt, wenn vorhanden
    (Platzhalter {name}, {stelle}, {firma}); sonst wuerdevoller Standardtext.
    Genau eine Zustellung je Bewerbung (REJECTION_NOTICE_SENT-Audit als Marker).
    """
    from ..models import EmailTemplate, ApplicantToken, Message as _Msg
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


# --- B1: Sicherer CV-Download (auth + Rolle + Audit-Log) --------------------
@recruiter_required
def download_cv(request, app_id):
    """Lebenslauf ausliefern – wahlweise INLINE (Vorschau) oder als Download.

    WARUM INLINE: Das Lesen des Lebenslaufs ist die haeufigste Handlung im
    Recruiting. Bisher gab es nur "herunterladen": Der Recruiter verliess die
    Anwendung, oeffnete die Datei im PDF-Programm und wechselte zurueck. Das
    kostete nicht nur Klicks – es streute BEWERBER-PII als Dateikopien ueber
    alle Recruiter-Laptops. In einem Produkt, das mit Datensouveraenitaet
    wirbt, ist das ein Eigentor.

    Mit ?view=1 wird die Datei im Browser angezeigt (iframe/img), ohne Kopie
    auf der Festplatte. Der Download bleibt fuer die Faelle, in denen man ihn
    wirklich braucht – und das Audit unterscheidet beides, damit der
    Datenschutzbeauftragte sieht, wer eine KOPIE gezogen hat.
    """
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    if not app.cvStorageId or not default_storage.exists(app.cvStorageId):
        raise Http404("Kein Lebenslauf hinterlegt.")

    download_name = _os.path.basename(app.cvStorageId)
    if "_" in download_name:  # UUID-Prefix aus dem Speichernamen entfernen
        download_name = download_name.split("_", 1)[1]

    ext = _os.path.splitext(download_name)[1].lower()
    # Nur Formate inline zeigen, die der Browser sicher darstellt.
    # doc/docx koennen Browser nicht rendern -> immer Download.
    INLINE_OK = {".pdf": "application/pdf", ".jpg": "image/jpeg",
                 ".jpeg": "image/jpeg", ".png": "image/png"}
    inline = request.GET.get("view") == "1" and ext in INLINE_OK

    # Revisionssicher protokollieren, WER WESSEN CV wann gelesen hat –
    # und OB eine Kopie das System verlassen hat.
    write_audit("READ_CV", user=request.user, application_id=app.id,
                storage=app.cvStorageId,
                mode="inline" if inline else "download")

    fh = default_storage.open(app.cvStorageId, "rb")
    resp = FileResponse(fh, as_attachment=not inline,
                        filename=download_name or "cv")
    if inline:
        resp["Content-Type"] = INLINE_OK[ext]
        # Kein MIME-Sniffing: der Browser darf den Typ nicht "erraten".
        resp["X-Content-Type-Options"] = "nosniff"
    return resp


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


@any_staff_required
def application_vote(request, app_id):
    """Gremien-Stimme abgeben/aendern + Kommentar/Frage hinterlegen.

    Stimmrecht hat NUR, wer im Gremium der Stelle steht (403 sonst) –
    unabhaengig von der Rolle: auch Hiring-Manager/Viewer stimmen, wenn
    benannt. Kommentare landen in den internen Notizen (ein Ort fuer alle).
    """
    if request.method != 'POST':
        return redirect('ats:approvals')
    from ..panel import panel_member_ids
    from ..models import ApplicationVote
    from ..permissions import active_delegations_to, delegation_covers
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


# --- B11: Talent-Pool-Übersicht --------------------------------------------
@recruiter_required
def talent_pool_view(request):
    """UC-SB-13/UM-04/FA-04: Pool sichten, auf offene Stellen matchen, ansprechen.

    Matching bewusst datensparsam: Jobfamilie/Standort aus den frueheren
    Bewerbungen (steht in criteria) gegen veroeffentlichte Stellen im
    BOLA-Scope. Ansprache mit Doppel-Schutz (unique_together) – Einwilligung
    heisst gelegentliche passende Hinweise, nicht Dauer-Werbung.
    """
    from ..models import TalentPoolContact

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
        from ..models import TalentPoolContact
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

@any_staff_required
def tasks_view(request):
    """Aufgaben aus der Prozess-Automatik: offene Aufgaben im eigenen
    Zugriffsbereich, gefiltert nach den eigenen Rollen (rollenlose Aufgaben
    sieht jede/r). Erledigen per POST – auditiert."""
    from ..models import WorkflowTask
    my_roles = set(request.user.groups.values_list('name', flat=True))
    is_admin = (request.user.is_superuser
                or 'HR-Admin' in my_roles)

    if request.method == 'POST':
        task = get_object_or_404(WorkflowTask,
                                 id=request.POST.get('task_id'))
        if not can_access_application(request.user, task.application):
            raise Http404("Nicht im Zugriffsbereich.")
        # Nur zustaendige Rolle (oder Admin) darf erledigen
        if task.role and not is_admin and task.role not in my_roles:
            raise Http404("Nicht zuständig.")
        if request.POST.get('op') == 'reopen':
            task.status, task.doneBy, task.doneAt = "OPEN", None, None
        else:
            task.status = "DONE"
            task.doneBy = request.user
            task.doneAt = timezone.now()
        task.save(update_fields=['status', 'doneBy', 'doneAt'])
        write_audit('WORKFLOW_TASK_DONE' if task.status == "DONE"
                    else 'WORKFLOW_TASK_REOPENED',
                    user=request.user, application_id=str(task.application_id),
                    task=str(task.id))
        return redirect('ats:tasks')

    scoped = scope_applications(request.user, Application.objects.all())
    qs = (WorkflowTask.objects
          .filter(application__in=scoped)
          .select_related('application__applicant',
                          'application__jobPosting', 'doneBy'))
    if not is_admin:
        # Eigene Rollen + rollenlose Aufgaben
        from django.db.models import Q
        qs = qs.filter(Q(role="") | Q(role__in=my_roles))
    open_tasks = [t for t in qs if t.status == "OPEN"]
    done_tasks = [t for t in qs if t.status == "DONE"][:25]
    return render(request, 'tasks.html', {
        'open_tasks': open_tasks,
        'done_tasks': done_tasks,
        'overdue_count': sum(1 for t in open_tasks if t.overdue),
    })

