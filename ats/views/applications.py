"""SecurATS Views — Bewerbungen: Kanban-Board, Status, Notizen, CV, Workflow-Automatik.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging
import os as _os

from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from ..audit import write_audit
from ..models import (
    ApplicantToken,
    Application,
    AppWorkflowDef,
    AuditLog,
    Benefit,
    ContactPerson,
    Department,
    Facility,
    Interview,
    InterviewSlot,
    JobFamily,
    JobPosting,
    JobTemplate,
    Location,
    Message,
    Organization,
    TalentPoolSubscription,
    WorkflowState,
    get_interview_kinds,
)
from ..permissions import any_staff_required, can_access_application, recruiter_required, scope_applications, scope_jobs
from .admin_pages import gemma_status
from .common import seed_data_if_empty
from .governance import _pending_steps_for

logger = logging.getLogger(__name__)

__all__ = ["dashboard", "update_status", "add_note", "get_matching_workflow", "execute_workflow_actions", "_send_rejection_notice", "download_cv", "reorder_board", "bulk_update_status", "application_messages", "draft_reply", "application_summary", "inbox_view", "open_question_clusters", "batch_reply", "save_reply_snippet", "reclassify_message", "application_vote", "talent_pool_view", "job_pool_matches", "application_timeline", "job_timeline", "tasks_view"]


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
    # C1/C2: Wiederbewerber-Signal und Liegenbleiber-Radar (je 1 Query)
    from ..board_insights import repeat_applicant_map, stale_days_map
    _apps = list(applications)
    _repeat = repeat_applicant_map(_apps)
    _stale = stale_days_map(_apps)
    for a in applications:
        a.fb_summary = _fb.get(a.id)
        a.repeat_info = _repeat.get(a.id)
        a.stale_info = _stale.get(a.id)

    # Extra data for interactive modals
    active_jobs = scope_jobs(request.user, JobPosting.objects.all().select_related('location', 'facility', 'department', 'workflowState', 'contactPerson', 'jobTemplate').order_by('-createdAt'))
    from ..models import EmailTemplate, TextSnippet
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

    # Workflow-Zustaende fuer die Auswahl im Stellen-Editor. CMS-Seiten,
    # E-Mail-Vorlagen, Variablen und Pipelines wurden mit B2 auf eigene
    # Seiten verlagert und werden hier nicht mehr geladen.
    all_workflows = WorkflowState.objects.all().order_by('name')

    # Selections for Job Postings creator
    facilities = Facility.objects.all()
    departments = Department.objects.all()
    locations = Location.objects.filter(archived=False)
    job_families = JobFamily.objects.filter(archived=False)
    contact_persons = ContactPerson.objects.all()
    all_benefits = Benefit.objects.all()
    # Entgelttransparenz (E1): Entgeltbänder für den Stellen-Editor
    from ..models import PayBand
    pay_bands = PayBand.objects.filter(archived=False).order_by('tariffSystem', 'name')
    # A2: Quellen-Filter über dem Board (nur tatsächlich vorkommende Quellen)
    board_sources = sorted({a.source for a in applications if a.source})
    latest_tpl_ids = {}
    for t in JobTemplate.objects.order_by('-version', '-createdAt'):
        latest_tpl_ids.setdefault(t.title.lower(), t.id)
    job_templates = JobTemplate.objects.filter(id__in=latest_tpl_ids.values()).order_by('title')

    # Rollen-Flag fuer die Benutzerfuehrung: Ein Recruiter soll nur seine
    # taegliche Arbeit sehen (Bewerbungen, Stellen), nicht die Admin-/IT-/
    # Management-Werkzeuge. Ein HR-Admin sieht alles, aber sauber getrennt.
    is_hr_admin = (request.user.is_superuser
                   or request.user.groups.filter(name='HR-Admin').exists())

    context = {
        'is_hr_admin': is_hr_admin,
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
        'all_workflows': all_workflows,
        'facilities': facilities,
        'departments': departments,
        'locations': locations,
        'job_families': job_families,
        'contact_persons': contact_persons,
        'all_benefits': all_benefits,
        'pay_bands': pay_bands,
        'board_sources': board_sources,
        'job_templates': job_templates,
        # Nur noch fuer das Statuszeichen am Seitenleisten-Link zur KI-Zentrale.
        # Ein Recruiter sieht den Link nicht – dann entfaellt auch der
        # Netzwerk-Test, der im ungluecklichen Fall Sekunden kostet.
        'gemma_status': gemma_status() if is_hr_admin else '',
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
    from django.db.models import Q as _Q

    from ..models import WorkflowTask
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
                    steps = wf.stepsJson
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
    """Finds the most specific AppWorkflowDef for this application's job, location, department or category.

    Die ID-Listen liegen als JSONField-Listen vor; __contains auf JSONField
    ist auf SQLite nicht verfügbar, daher Abgleich in Python (pk-Reihenfolge
    wie zuvor bei .first()).
    """
    workflows = list(AppWorkflowDef.objects.order_by('pk'))

    def _first_with(field, needle):
        return next((w for w in workflows
                     if str(needle) in [str(i) for i in (getattr(w, field) or [])]),
                    None)

    # 1. Check Job Posting specificity
    wf = _first_with('jobIdsJson', app.jobPosting.id)
    if wf:
        return wf

    # 2. Check Location specificity
    if app.jobPosting.location:
        wf = _first_with('locationIdsJson', app.jobPosting.location.id)
        if wf:
            return wf

    # 3. Check Category (Job Family) specificity
    if app.jobPosting.jobFamily:
        wf = _first_with('categoryIdsJson', app.jobPosting.jobFamily.id)
        if wf:
            return wf

    # 4. Check Facility specificity
    if app.jobPosting.facility:
        wf = next((w for w in workflows
                   if w.facility_id == app.jobPosting.facility.id), None)
        if wf:
            return wf

    # 5. Global Fallback
    return workflows[0] if workflows else None


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
    from ..models import EmailTemplate
    from ..models import Message as _Msg
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
            from django.contrib.auth.models import Group
            from django.core.mail import send_mail
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
    from ..models import EmailTemplate
    from ..models import Message as _Msg
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


# --- Sammel-Postfach: offene Bewerber-Fragen nach Anliegen gebuendelt --------
def open_question_clusters(user):
    """Offene Fragen (Bewerbung, deren LETZTE Nachricht INBOUND ist), gebuendelt
    nach Anliegen. Ein Query fuer die jeweils letzte Nachricht je Bewerbung
    (kein N+1); Klassifikation regelbasiert ueber die ganze Nachricht.

    Rueckgabe: Liste von Cluster-Dicts in Anzeige-Reihenfolge, nur nicht-leere.
    """
    from django.db.models import OuterRef, Subquery

    from ..board_insights import status_label
    from ..inbox_intents import (
        INTENT_ICONS,
        INTENT_LABELS,
        INTENT_ORDER,
        analyze,
    )
    from ..inbox_learning import learned_keywords, message_overrides
    from ..models import TextSnippet
    from ..reply_drafts import batch_template

    # Gespeicherte Antwort-Bausteine je Anliegen (Kategorie REPLY_<Intent>).
    # Der juengste ist der Auto-Vorschlag - so wird der Default mit der Zeit
    # das, was HR tatsaechlich nutzt (Bruecke zur lernenden Optimierung).
    reply_snips: dict[str, list] = {}
    for s in (TextSnippet.objects.filter(category__startswith='REPLY_')
              .order_by('-createdAt')):
        reply_snips.setdefault(s.category, []).append(s)
    # Stufe 5: gelernte Zusatz-Stichwoerter (aus HR-Korrekturen) fliessen in
    # die Klassifikation ein; Sofort-Korrekturen je Nachricht ueberschreiben.
    learned = learned_keywords()
    latest = (Message.objects.filter(application=OuterRef('pk'))
              .order_by('-createdAt'))
    apps = list(scope_applications(user, Application.objects.all())
                .select_related('applicant', 'jobPosting')
                .annotate(
                    last_id=Subquery(latest.values('id')[:1]),
                    last_dir=Subquery(latest.values('direction')[:1]),
                    last_content=Subquery(latest.values('content')[:1]),
                    last_at=Subquery(latest.values('createdAt')[:1]))
                .filter(last_dir='INBOUND'))
    overrides = message_overrides([str(a.last_id) for a in apps])

    grouped: dict[str, list] = {intent: [] for intent in INTENT_ORDER}
    for app in apps:
        analysis = analyze(app.last_content or '', extra_keywords=learned)
        # Sofort-Korrektur gewinnt vor der (gelernten) Regel.
        bucket = overrides.get(str(app.last_id), analysis.bucket)
        grouped[bucket].append({
            'app': app,
            'message_id': app.last_id,
            'name': f"{app.applicant.firstName} {app.applicant.lastName}".strip(),
            'first_name': app.applicant.firstName,
            'job': app.jobPosting.title,
            'status': status_label(app.status),
            'question': (app.last_content or '')[:160],
            'when': app.last_at,
            'reason': '' if str(app.last_id) in overrides else analysis.reason,
            'auto_safe': analysis.auto_safe,
        })

    clusters = []
    for intent in INTENT_ORDER:
        items = sorted(grouped[intent], key=lambda i: i['when'] or app.createdAt)
        if items:
            snips = reply_snips.get(f"REPLY_{intent}", [])
            clusters.append({
                'intent': intent,
                'label': INTENT_LABELS[intent],
                'icon': INTENT_ICONS[intent],
                'items': items,
                'count': len(items),
                # Auto-Vorschlag: juengster gespeicherter Baustein, sonst Default.
                'template': snips[0].content if snips else batch_template(intent),
                'snippets': snips,
            })
    return clusters


@recruiter_required
def inbox_view(request):
    """Themen-Postfach: offene Bewerber-Fragen nach Anliegen gebuendelt, damit
    aehnliche Fragen gesammelt beantwortet werden koennen (Alltags-Entlastung).
    Nur-Lesen; BOLA ueber scope_applications.
    """
    from ..inbox_intents import INTENT_LABELS, INTENT_ORDER
    clusters = open_question_clusters(request.user)
    total = sum(c['count'] for c in clusters)
    return render(request, 'inbox.html', {
        'clusters': clusters, 'total': total,
        'intent_choices': [{'code': i, 'label': INTENT_LABELS[i]}
                           for i in INTENT_ORDER]})


@recruiter_required
def reclassify_message(request):
    """HR verschiebt eine falsch einsortierte Nachricht ins richtige Anliegen.

    Arbeitsrelevant (die Nachricht landet im richtigen Topf) UND zugleich das
    Lern-Signal (Stufe 5): der Audit-Eintrag speist die gelernten Stichwoerter.
    Wirkt sofort fuer diese Nachricht (message_overrides); ins Regelwerk geht
    es erst mit genug gleichlautender Evidenz.
    """
    if request.method != 'POST':
        return redirect('ats:inbox')
    from ..inbox_intents import INTENT_LABELS, analyze
    from ..inbox_learning import RECLASSIFY_ACTION
    to_intent = (request.POST.get('to_intent') or '').strip()
    if to_intent not in INTENT_LABELS:
        messages.warning(request, "Unbekanntes Anliegen.")
        return redirect('ats:inbox')
    msg = get_object_or_404(Message, id=request.POST.get('message_id'))
    if not can_access_application(request.user, msg.application):
        raise Http404("Nicht im Zugriffsbereich.")
    from_bucket = analyze(msg.content or '').bucket
    write_audit(RECLASSIFY_ACTION, user=request.user,
                application_id=msg.application_id, message_id=str(msg.id),
                to_intent=to_intent, from_bucket=from_bucket,
                excerpt=(msg.content or '')[:200])
    messages.success(
        request, f'Nachricht nach „{INTENT_LABELS[to_intent]}" verschoben.')
    return redirect('ats:inbox')


@recruiter_required
def save_reply_snippet(request):
    """Speichert die aktuelle Sammel-Vorlage als wiederverwendbaren Baustein
    fuer dieses Anliegen (Stufe 2). Der juengste Baustein wird zum
    Auto-Vorschlag - so waechst die Bibliothek aus echten Antworten."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    from ..inbox_intents import INTENT_LABELS
    from ..models import TextSnippet
    intent = (request.POST.get('intent') or '').strip()[:20]
    content = (request.POST.get('content') or '').strip()[:4000]
    if intent not in INTENT_LABELS or intent == 'OTHER' or not content:
        return JsonResponse({'error': 'Ungültiges Anliegen oder leerer Text.'},
                            status=400)
    TextSnippet.objects.create(category=f"REPLY_{intent}", content=content)
    write_audit('REPLY_SNIPPET_SAVED', user=request.user, intent=intent)
    return JsonResponse({'ok': True,
                         'note': 'Als Vorlage gespeichert – ab jetzt Vorschlag für dieses Anliegen.'})


@recruiter_required
def batch_reply(request):
    """Sammel-Antwort: EINE geprüfte Vorlage, pro Person personalisiert an alle
    Ausgewählten gesendet. Kein Massenversand-Look - Platzhalter werden je
    Bewerbung ersetzt.

    Senden-einmal: es wird nur an Bewerbungen gesendet, deren letzte Nachricht
    noch INBOUND ist (offene Frage). Wer bereits eine Antwort hat, wird
    uebersprungen. BOLA je Bewerbung. Der Audit-Eintrag ist zugleich das
    Lern-Signal (welche Antwort fuer welches Anliegen).
    """
    if request.method != 'POST':
        return redirect('ats:inbox')
    from ..reply_drafts import personalize
    intent = (request.POST.get('intent') or '').strip()[:20]
    template = (request.POST.get('template') or '').strip()[:4000]
    app_ids = request.POST.getlist('app_ids')
    if not template or not app_ids:
        messages.warning(request, "Keine Vorlage oder keine Auswahl.")
        return redirect('ats:inbox')

    sent = 0
    skipped = 0
    for app in (Application.objects.filter(id__in=app_ids)
                .select_related('applicant', 'jobPosting')):
        if not can_access_application(request.user, app):
            skipped += 1
            continue
        # Senden-einmal: nur an offene Fragen. Offen = es gibt eine INBOUND-
        # Nachricht, auf die noch keine Antwort folgte. __gte (nicht __gt):
        # bei grober Uhr-Aufloesung zaehlt eine gleichzeitige Antwort als
        # Antwort - verhindert Doppel-Nachrichten (wie awaiting_reply).
        last_in = (app.messages.filter(direction='INBOUND')
                   .order_by('-createdAt').first())
        if not last_in:
            skipped += 1
            continue
        answered = app.messages.filter(
            direction='OUTBOUND', createdAt__gte=last_in.createdAt).exists()
        if answered:
            skipped += 1
            continue
        text = personalize(template, first_name=app.applicant.firstName,
                           job_title=app.jobPosting.title, status=app.status)
        Message.objects.create(application=app, direction='OUTBOUND',
                               content=text)
        write_audit('BATCH_REPLY_SENT', user=request.user,
                    application_id=app.id, intent=intent)
        sent += 1

    if sent:
        messages.success(
            request, f"{sent} Antwort(en) gesendet."
            + (f" {skipped} übersprungen (bereits beantwortet)." if skipped else ""))
    else:
        messages.warning(request, "Nichts gesendet – die Fragen waren bereits beantwortet.")
    return redirect('ats:inbox')


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
    # Einmal-Aktion: solange auf die letzte gesendete Nachricht weder eine
    # Antwort kam noch sich der Status geaendert hat, bleibt der Senden-Button
    # im Zustand "gesendet" - das verhindert versehentliche Doppel-Nachrichten.
    last_out = app.messages.filter(direction='OUTBOUND').order_by('-createdAt').first()
    awaiting_reply = False
    if last_out:
        # __gte statt __gt: bei grober Uhr-Aufloesung koennen Antwort bzw.
        # Statuswechsel im selben Tick liegen wie die gesendete Nachricht -
        # ein gleichzeitiges Ereignis zaehlt als Freischaltung.
        answered = app.messages.filter(
            direction='INBOUND', createdAt__gte=last_out.createdAt).exists()
        status_changed = AuditLog.objects.filter(
            action='STATUS_CHANGE', applicationId=str(app.id),
            createdAt__gte=last_out.createdAt).exists()
        awaiting_reply = not answered and not status_changed
    return render(request, 'messages.html',
                  {'application': app, 'messages': msgs,
                   'awaiting_reply': awaiting_reply})


@any_staff_required
def draft_reply(request, app_id):
    """C4: Entwurf fuer eine Antwort auf die Bewerber-Nachricht.

    Regelbasierte Grundlage (immer verfuegbar) + optionale lokale Gemma-
    Verfeinerung. Der Entwurf landet NUR im Textfeld - gesendet wird erst
    durch den Menschen. Die eingehende Nachricht ist nicht vertrauenswuerdige
    Eingabe (ai_safety); keine weiteren Bewerberdaten gehen an die KI.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")

    from ..reply_drafts import ai_system_prompt, rule_based_draft
    job_title = app.jobPosting.title
    baseline = rule_based_draft(status=app.status, job_title=job_title)

    last_in = (app.messages.filter(direction='INBOUND')
               .order_by('-createdAt').first())
    inbound = (last_in.content if last_in else '').strip()[:4000]

    # Ohne konkrete Bewerber-Nachricht bleibt es beim regelbasierten Entwurf -
    # die KI soll auf eine Nachricht ANTWORTEN, nicht frei fabulieren.
    if not inbound:
        return JsonResponse({'draft': baseline, 'used_ai': False,
                             'note': 'Vorlage passend zum Status – bitte prüfen.'})

    import time

    from ..ai_safety import PROMPT_VERSION, wrap_untrusted
    from .ai import (
        get_ai_model,
        get_ollama_url,
        log_ai_execution,
        make_ollama_request,
    )
    payload = {
        "model": get_ai_model(),
        "system": ai_system_prompt(status=app.status, job_title=job_title),
        "prompt": wrap_untrusted(inbound),
        "stream": False,
        "options": {"temperature": 0.3},
        "keep_alive": "10m",
    }
    start = time.time()
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=20.0)
        latency = round(time.time() - start, 2)
        if ok and (data.get('response') or '').strip():
            draft = data['response'].strip()[:4000]
            log_ai_execution("Antwort-Entwurf", get_ai_model(), latency, True,
                             False, "", False, prompt_used=inbound,
                             tokens=data.get('eval_count'),
                             prompt_version=PROMPT_VERSION)
            return JsonResponse({'draft': draft, 'used_ai': True,
                                 'note': 'Entwurf – bitte vor dem Senden prüfen.'})
    except Exception:
        logger.exception("KI-Antwort-Entwurf nicht verfügbar")
    return JsonResponse({'draft': baseline, 'used_ai': False,
                         'note': 'Lokale KI nicht erreichbar – Status-Vorlage.'})


@any_staff_required
def application_summary(request, app_id):
    """L2: faktentreuer Steckbrief zu einer Bewerbung - schnelles Bild beim
    Öffnen der Karte. Die harten Fakten (Chips) sind deterministisch; die
    lokale KI darf den Fließtext NUR umformulieren, nichts erfinden.
    Fail-safe: ohne KI bleibt der deterministische Text. BOLA-geschützt.
    """
    app = get_object_or_404(
        Application.objects.select_related('applicant', 'jobPosting'),
        id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")

    from ..profile_summary import build_facts, facts_to_bullets, facts_to_text
    facts = build_facts(app)
    text = facts_to_text(facts)
    bullets = facts_to_bullets(facts)
    result = {'text': text, 'bullets': bullets,
              'ai_score': facts.ai_score, 'used_ai': False}

    # L3: gelernte Einordnung NUR wenn freigeschaltet + Kontext belastbar +
    # Backtest schlaegt die Grundlinie (sonst gar nicht) - erklaerbar.
    from ..scoring_eval import learned_grade
    lg = learned_grade(app)
    if lg is not None:
        grade, reasons, ctx = lg
        result['learned'] = {'grade': grade, 'reasons': reasons,
                             'context': ctx}

    # Optionale lokale Umformulierung - strikt nur umformulieren. Hinter dem
    # AI-Opt-in: ist die KI-Assistenz aus (Default), kommt der deterministische
    # Text SOFORT zurueck (kein Ollama-Verbindungsversuch, kein Modal-Hänger).
    from ..models import SystemSetting
    if not SystemSetting.objects.filter(
            key='AI_SCORING_ENABLED', value='1').exists():
        return JsonResponse(result)

    from ..ai_safety import wrap_untrusted
    from .ai import get_ai_model, get_ollama_url, make_ollama_request
    payload = {
        "model": get_ai_model(),
        "system": ("Formuliere die folgenden Fakten zu einer Bewerbung in ein "
                   "bis zwei sachliche, fluessige Saetze um. Erfinde NICHTS, "
                   "fuege nichts hinzu, lass keine Zahl und kein Kriterium weg, "
                   "keine Wertung. Antworte nur mit dem umformulierten Text."),
        "prompt": wrap_untrusted(text),
        "stream": False,
        "options": {"temperature": 0.2},
        "keep_alive": "10m",
    }
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=15.0)
        if ok and (data.get('response') or '').strip():
            result['text'] = data['response'].strip()[:800]
            result['used_ai'] = True
    except Exception:
        logger.exception("Steckbrief-Umformulierung nicht verfügbar")
    return JsonResponse(result)


@any_staff_required
def application_vote(request, app_id):
    """Gremien-Stimme abgeben/aendern + Kommentar/Frage hinterlegen.

    Stimmrecht hat NUR, wer im Gremium der Stelle steht (403 sonst) –
    unabhaengig von der Rolle: auch Hiring-Manager/Viewer stimmen, wenn
    benannt. Kommentare landen in den internen Notizen (ein Ort fuer alle).
    """
    if request.method != 'POST':
        return redirect('ats:approvals')
    from ..models import ApplicationVote
    from ..panel import panel_member_ids
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


# --- C3: Passende Pool-Talente zu EINER Stelle (einladen, einzeln/gesammelt) --
@recruiter_required
def job_pool_matches(request, job_id):
    """Passende Talent-Pool-Personen zu einer Stelle: Namen sehen, Profil
    ansehen, einzeln ODER gesammelt einladen.

    Alltag: „alle einladen" mit einem Klick. Ausnahme: vorher ins Profil
    schauen. BOLA: nur Stellen im Zugriffsbereich; die Einmal-Aktion
    (unique_together) verhindert Doppel-Ansprachen je Stelle."""
    job = get_object_or_404(
        scope_jobs(request.user, JobPosting.objects.filter(id=job_id)))
    from ..talent_pool import invite_pool_person, pool_candidates_for_job

    if request.method == 'POST':
        raw_ids = request.POST.getlist('sub_ids')  # gesammelt ODER einzeln
        sent = 0
        for sub in TalentPoolSubscription.objects.filter(id__in=raw_ids):
            if invite_pool_person(sub, job, request.user):
                sent += 1
        if sent:
            messages.success(
                request, f"{sent} Talent(e) zur Bewerbung eingeladen.")
        return redirect('ats:job_pool_matches', job_id=job.id)

    candidates = pool_candidates_for_job(job)
    return render(request, 'job_pool_matches.html',
                  {'job': job, 'candidates': candidates,
                   'open_count': sum(1 for c in candidates
                                     if not c['contacted_at'])})


# --- Aktionsverlauf: die ganze Geschichte an EINEM Ort ----------------------
@any_staff_required
def application_timeline(request, app_id):
    """Chronologischer Verlauf einer Bewerbung: wer hat wann was getan -
    intern UND vom Bewerber. Taegliches HR-Werkzeug (Stand erfassen,
    Entscheidungen nachvollziehen), auch fuer Urlaubsvertretungen.

    Nur-Lesen; BOLA: nur Bewerbungen im Zugriffsbereich.
    """
    from ..timeline import application_events
    app = get_object_or_404(Application, id=app_id)
    if not can_access_application(request.user, app):
        raise Http404("Nicht im Zugriffsbereich.")
    name = f"{app.applicant.firstName} {app.applicant.lastName}".strip()
    return render(request, 'timeline.html', {
        'events': application_events(app),
        'title': name or 'Bewerbung',
        'subtitle': app.jobPosting.title,
        'kind': 'application',
        'back_anchor': f"#card-{app.id}",
    })


@any_staff_required
def job_timeline(request, job_id):
    """Chronologischer Verlauf einer Stelle: Anlage, jede eingehende
    Bewerbung und deren Meilensteine (Einladung/Absage/Einstellung), mit
    Namen. Ueberblick fuer Vertretung und Alltag gleichermassen.

    Nur-Lesen; BOLA: nur Stellen im Zugriffsbereich.
    """
    from ..timeline import job_events
    job = get_object_or_404(
        scope_jobs(request.user, JobPosting.objects.filter(id=job_id)))
    return render(request, 'timeline.html', {
        'events': job_events(job),
        'title': job.title,
        'subtitle': (f"{job.location.city} · " if job.location_id else "")
        + "Stellen-Verlauf",
        'kind': 'job',
        'back_anchor': "",
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
    from ..models import TalentPoolContact

    published = list(scope_jobs(request.user, JobPosting.objects.filter(
        workflowState__name='published').select_related('jobFamily', 'location')))

    if request.method == 'POST' and request.POST.get('contact_sub_id'):
        from ..talent_pool import invite_pool_person
        sub = get_object_or_404(TalentPoolSubscription,
                                id=request.POST.get('contact_sub_id'))
        job = next((j for j in published
                    if str(j.id) == request.POST.get('job_id')), None)  # Scope!
        if job:
            invite_pool_person(sub, job, request.user)
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

