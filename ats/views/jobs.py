"""SecurATS Views — Stellenanzeigen und Job-Vorlagen (inkl. Versionierung).

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import json
import logging

from django.contrib import messages
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..audit import write_audit
from ..models import (
    AuditLog,
    Benefit,
    Facility,
    JobFamily,
    JobPosting,
    JobTemplate,
    Location,
    Organization,
    WorkflowState,
)
from ..permissions import hr_admin_required, recruiter_required, scope_jobs

logger = logging.getLogger(__name__)

__all__ = ["create_job", "toggle_job_active", "job_templates_view", "delete_job_template", "job_template_detail", "restore_job_template", "update_job_posting_template"]


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
            from ..process_advisor import ensure_minimum_standards
            enforced = ensure_minimum_standards(job)
            if enforced:
                job.save(update_fields=['screeningQuestionsJson'])
                write_audit('MINIMUM_STANDARD_APPLIED', user=request.user,
                            job=job.title, corrections=enforced)
            from ..approvals import ensure_approval_gate
            ticket = ensure_approval_gate(job)
            if ticket and ticket.status == "PENDING":
                write_audit("APPROVAL_GATE_OPENED", user=request.user,
                            job=job.title, ticket=str(ticket.id))
            # Stellenfreigabe (optional, dann Pflicht): ohne genehmigten
            # Bedarf bleibt die Stelle Entwurf statt online zu gehen.
            from ..approvals import draft_state, requisition_blocked_reason
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


@recruiter_required
def toggle_job_active(request, job_id):
    """Schnell-Aktion: Anzeige mit einem Klick deaktivieren/aktivieren."""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    job = get_object_or_404(JobPosting, id=job_id)
    if job not in scope_jobs(request.user, JobPosting.objects.filter(id=job.id)):
        raise Http404("Nicht im Zugriffsbereich.")
    # UC-JF-01: das Gate ist nicht per Schnell-Toggle umgehbar
    from ..approvals import has_open_gate, requisition_blocked_reason
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
    from ..models import AuditLog
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

        from ..models import AuditLog
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
