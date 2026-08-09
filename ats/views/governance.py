"""SecurATS Views — Freigaben, Gremium, Stellenfreigabe-Ketten, Vertretung, Audit.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging
from typing import Any
from urllib.parse import urlencode

from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..audit import write_audit
from ..models import (
    Application,
    AuditLog,
    Department,
    Facility,
    JobFamily,
    JobPosting,
    Location,
    Organization,
    RoleDelegation,
    SystemSetting,
    TalentPoolSubscription,
    WorkflowState,
)
from ..permissions import (
    HR_ADMIN,
    any_staff_required,
    denies_viewer_writes,
    has_full_access,
    hr_admin_required,
    recruiter_required,
    scope_jobs,
)

logger = logging.getLogger(__name__)

__all__ = ["_pending_steps_for", "approvals_inbox", "governance_view", "roi_export", "panel_defaults_view", "panel_preview", "delegations_view", "audit_log_view", "audit_export", "staffing_requests_view", "_previous_process", "process_previous"]


def _pending_steps_for(user):
    """Approval-Schritte, die auf diese Person warten (UC-JF-06).

    Ein Schritt „wartet auf mich", wenn er PENDING ist, alle Vorgänger-Schritte
    freigegeben sind und er meiner Rolle (Django-Gruppe) oder meinem Benutzernamen
    zugewiesen ist. (`assignedRoleId`/`assignedUserId` sind Prisma-Alt-Textfelder;
    Konvention ab jetzt: Gruppenname bzw. Username.)
    """
    from ..models import ApprovalStep
    from ..permissions import active_delegations_to, delegation_covers
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


#: Wie viele ausstehende Gremiums-Stimmen die Freigaben-Seite zeigt.
PANEL_ROWS = 50

@any_staff_required
def approvals_inbox(request):
    """Freigabe-Postfach „Wartet auf mich" mit Frist, Kommentar & Rückfrage."""
    from ..models import ApprovalStep

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

        # § 99 Abs. 2 BetrVG: Der Betriebsrat verweigert die Zustimmung nur
        # aus den sechs gesetzlichen Gruenden - und MUSS begruenden. Ein
        # formloses "Ablehnen" ohne Grund/Begruendung ist fuer BR-Stufen
        # deshalb gesperrt; Grund + Text wandern strukturiert ins Audit.
        from ..approvals import W99_GROUNDS, is_betriebsrat_step
        w99_selected = [g for g in request.POST.getlist('w99_grounds')
                        if g in W99_GROUNDS]
        if action == 'reject' and is_betriebsrat_step(step):
            if not w99_selected or not comment:
                messages.warning(
                    request, "Zustimmungsverweigerung nach § 99 BetrVG "
                    "braucht mindestens einen Grund (Abs. 2) und eine "
                    "Begründung.")
                return redirect('ats:approvals')
            grounds_text = "; ".join(W99_GROUNDS[g] for g in w99_selected)
            comment = (f"Widerspruch § 99 Abs. 2 BetrVG – Gründe: "
                       f"{grounds_text}. {comment}")[:2000]
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
        # Wer zugestimmt hat, gehoert an die Zustimmung - bisher stand hier nur
        # ein Zeitpunkt. Bei einer Vertretung ist der Urheber die handelnde
        # Person; fuer wen sie gehandelt hat, steht im Kommentar.
        step.actionTakenBy = request.user
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
                # Die Veroeffentlichungs-Gates sind auch hier nicht umgehbar.
                # Beide muessen offen sein - vorher fehlte hier das
                # Entgelt-Gate, wodurch eine Stelle OHNE Entgeltband ueber
                # die Freigabekette online ging, obwohl create_job und der
                # Schnell-Toggle sie blockieren (EU-RL 2023/970 Art. 5).
                from ..approvals import requisition_blocked_reason
                from ..pay_transparency import pay_blocked_reason
                _rq = requisition_blocked_reason(job)
                _pay = pay_blocked_reason(job)
                if _rq or _pay:
                    write_audit(
                        'REQUISITION_GATE_BLOCKED' if _rq else 'PAY_GATE_BLOCKED',
                        user=request.user, job=job.title, via='approval_gate')
                    messages.warning(request, _rq or _pay)
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
                    comment=comment[:200],
                    **({'w99_grounds': w99_selected} if w99_selected else {}))
        return redirect('ats:approvals')

    try:
        sla_days = int((SystemSetting.objects.filter(key='APPROVAL_SLA_DAYS')
                        .first() or SystemSetting(value='7')).value)
    except (TypeError, ValueError):
        sla_days = 7
    now = timezone.now()
    rows = []
    from ..approvals import W99_DEADLINE_DAYS, W99_GROUNDS, is_betriebsrat_step
    for step in _pending_steps_for(request.user):
        age = (now - step.approvalTicket.createdAt).days
        # BR-Stufen laufen auf der GESETZLICHEN Wochenfrist (§ 99 Abs. 3),
        # nicht auf dem hausinternen SLA - die Frist ist keine Hausregel.
        is_br = is_betriebsrat_step(step)
        limit = W99_DEADLINE_DAYS if is_br else sla_days
        rows.append({
            'step': step,
            'job': step.approvalTicket.jobPosting,
            'age_days': age,
            'due_in': limit - age,
            'overdue': age > limit,
            'is_br': is_br,
        })
    # Sichtungs-Gremium: Bewerbungen, bei denen MEINE Stimme aussteht
    from ..models import ApplicationVote
    from ..panel import panel_state
    # Vererbung beachten: Mitgliedschaft entsteht auch aus Defaults hoeherer
    # Ebenen -> in Python ueber die Leiter aufloesen statt SQL-contains.
    candidates = (Application.objects
                  .filter(status__in=['NEW', 'IN_REVIEW'])
                  .select_related('applicant', 'jobPosting__department',
                                  'jobPosting__facility', 'jobPosting__location',
                                  'jobPosting__jobFamily',
                                  'jobPosting__organization')
                  .order_by('createdAt'))
    from ..panel import sits_on_panel
    from ..permissions import active_delegations_to
    _delegs = active_delegations_to(request.user)
    # Gekappt wird das ERGEBNIS, nicht die Eingabe.
    #
    # Vorher stand hier `[:200]` an der Abfrage und `[:50]` hinter dem Filter:
    # Es wurden die 200 aeltesten offenen Bewerbungen der ganzen Organisation
    # geholt und ERST DANACH geprueft, wer in welchem Gremium sitzt. In einem
    # Haus mit mehr als 200 offenen Bewerbungen konnten die 200 aeltesten
    # saemtlich aus fremden Einrichtungen stammen - dann blieb die Liste leer,
    # obwohl die eigene Stimme ausstand. Eine ausbleibende Gremiums-Stimme
    # blockiert die Einladung; niemand haette den Grund gesehen.
    #
    # Kein BOLA-Scoping davor: Die Gremiums-Mitgliedschaft entsteht auch aus
    # Vorgaben hoeherer Ebenen und folgt nicht dem Einrichtungs-Zugriffsbereich.
    # Wer hier scopte, versteckte Pflichten statt Daten. Die Mitgliedschaft
    # SELBST ist die Zugriffspruefung.
    panel_apps = []
    for a in candidates.iterator(chunk_size=200):
        if sits_on_panel(request.user, a.jobPosting, _delegs):
            panel_apps.append(a)
            if len(panel_apps) >= PANEL_ROWS:
                break
    # Einmal-Aktion: die abgegebene Stimme wird am Button sichtbar; nur das
    # AENDERN auf die Gegenstimme bleibt moeglich (dokumentiertes Feature).
    my_votes = dict(ApplicationVote.objects.filter(
        user=request.user, application__in=panel_apps)
        .values_list('application_id', 'vote'))
    panel_rows = [{'app': a, 'state': panel_state(a),
                   'my_vote': my_votes.get(a.id),
                   'my_vote_pending': a.id not in my_votes}
                  for a in panel_apps]
    return render(request, 'approvals.html',
                  {'rows': rows, 'sla_days': sla_days,
                   'panel_rows': panel_rows,
                   'my_decisions': _my_decisions(request.user),
                   'open_chains': _open_chains(request.user, sla_days),
                   'w99_grounds': W99_GROUNDS})


def _my_decisions(user, limit=15):
    """Was diese Person selbst schon entschieden hat.

    Die Freigabe-Seite zeigte ausschliesslich „wartet auf mich". Wer nach dem
    Wochenende wissen wollte, ob er eine Stelle bereits freigegeben hat, fand
    dazu nichts - der Schritt war aus der Liste verschwunden, sonst nichts.
    Die Daten lagen die ganze Zeit da; seit U6 auch mit Urheber.
    """
    from ..models import ApprovalStep
    return list(ApprovalStep.objects
                .filter(actionTakenBy=user)
                .exclude(status='PENDING')
                .select_related('approvalTicket__jobPosting__location')
                .order_by('-actionTakenAt')[:limit])


def _open_chains(user, sla_days):
    """Laufende Freigabeketten im Zugriffsbereich - wo haengt was, seit wann.

    Fuer die Leitung war bisher nicht erkennbar, ob eine Ausschreibung in der
    Kette steht oder vergessen wurde. Die Engpass-Kennzahl in der Analytik
    beantwortet „welche Stufe bremst im Schnitt", nicht „welche Stelle haengt
    gerade bei wem".

    BOLA: nur Stellen im Zugriffsbereich; die Zeile nennt Rollen, keine Namen.
    """
    from ..models import ApprovalStep, ApprovalTicket
    tickets = (ApprovalTicket.objects
               .filter(status='PENDING')
               .select_related('jobPosting__location'))
    scoped_ids = set(scope_jobs(user, JobPosting.objects.all())
                     .values_list('id', flat=True))
    now = timezone.now()
    rows = []
    for ticket in tickets:
        if ticket.jobPosting_id not in scoped_ids:
            continue
        pending = [s for s in ApprovalStep.objects
                   .filter(approvalTicket=ticket, status='PENDING')
                   .order_by('stepOrder')]
        done = ApprovalStep.objects.filter(
            approvalTicket=ticket, status='APPROVED').count()
        total = ApprovalStep.objects.filter(approvalTicket=ticket).count()
        if not pending:
            continue
        # Faellig ist die NIEDRIGSTE offene Stufe - hoehere warten noch auf sie.
        current = pending[0]
        waiting_on = [s.assignedRoleId or s.assignedUserId or '—'
                      for s in pending if s.stepOrder == current.stepOrder]
        age = (now - ticket.createdAt).days
        rows.append({
            'job': ticket.jobPosting,
            'step_no': current.stepOrder,
            'done': done,
            'total': total,
            'waiting_on': ', '.join(waiting_on),
            'age_days': age,
            'overdue': age > sla_days,
        })
    rows.sort(key=lambda r: -r['age_days'])
    return rows


@any_staff_required
def governance_view(request):
    """Datenminimierte Kontroll-Sicht für Betriebsrat/SBV/DSB & Leitung.

    UC-JF-08 / UC-MB-*: ausschließlich Aggregate – keine Namen, keine Einzelfälle.
    Mitbestimmung braucht Prozess-Transparenz, nicht Personendaten.
    """
    from django.db.models import Count

    from ..audit import verify_audit_chain

    apps = Application.objects.all()  # bewusst ungescoped: Aggregat über alles
    total = apps.count()
    by_status = list(apps.values('status').annotate(c=Count('id')).order_by('-c'))

    audit_counts = list(AuditLog.objects.values('action')
                        .annotate(c=Count('id')).order_by('-c')[:12])
    chain = verify_audit_chain()

    anonymized = AuditLog.objects.filter(action='ANONYMIZE_DSGVO').count()
    ai_logged = AuditLog.objects.filter(action='AI_EXECUTION').count()
    consents = TalentPoolSubscription.objects.count()

    inclusion = _inclusion_aggregate()
    # Art. 7 Abs. 1: Nachweis, worin eingewilligt wurde. Fehlt die versionierte
    # Fassung, sagt die Seite das - statt die Luecke unsichtbar zu lassen.
    from ..dsgvo import privacy_notice_status
    notice_status = privacy_notice_status()

    return render(request, 'governance.html', {
        'total': total, 'by_status': by_status,
        'audit_counts': audit_counts, 'chain': chain,
        'anonymized': anonymized, 'ai_logged': ai_logged,
        'consents': consents, 'inclusion': inclusion,
        'notice_status': notice_status,
        # Export nur Leitung (Rollen-Check wie hr_admin_required, NICHT
        # has_full_access: das ist BOLA-Scoping und gilt auch fuer Viewer
        # ohne Einschraenkung): BR/SBV sehen die Seite, aber keinen Knopf.
        'can_export': request.user.is_superuser
        or request.user.groups.filter(name=HR_ADMIN).exists(),
    })


def _inclusion_aggregate():
    """§ 164 SGB IX / SBV-Kennzahlen (Katrin Sommer): NUR Aggregate.

    Das Feld ist verschluesselt (Art. 9) -> Auswertung entschluesselt in
    Python, nie per SQL-Filter. Quoten erst ab 5 Faellen je Gruppe
    (Anonymitaet). Eine Wahrheit fuer Governance-Seite UND ROI-Export.
    """
    from ..models.applications import disability_value_disclosed
    _INVITED = ('INVITED', 'HIRED')
    disclosed_n = disclosed_inv = other_n = other_inv = 0
    for status, dis in Application.objects.values_list('status', 'severeDisability'):
        if disability_value_disclosed(dis):
            disclosed_n += 1
            disclosed_inv += 1 if status in _INVITED else 0
        else:
            other_n += 1
            other_inv += 1 if status in _INVITED else 0
    return {
        'disclosed': disclosed_n,
        # Nur zugestellte Unterrichtungen zaehlen. Ein Vermerk ueber eine
        # Mail, die nie ankam, ist als Nachweis nach § 164/§ 178 Abs. 2
        # SGB IX wertlos - und als Kennzahl irrefuehrend. Alteintraege ohne
        # das Feld gelten weiter als zugestellt: Damals wurde der Vermerk nur
        # im Erfolgsfall ueberhaupt erreicht, wenn auch nicht geprueft.
        'sbv_notified': (AuditLog.objects.filter(action='SBV_NOTIFIED')
                         .exclude(metadataJson__contains='"delivered": false')
                         .count()),
        'rates_visible': disclosed_n >= 5 and other_n >= 5,
        'disclosed_rate': round(100 * disclosed_inv / disclosed_n)
        if disclosed_n else None,
        'other_rate': round(100 * other_inv / other_n) if other_n else None,
    }


@hr_admin_required
def roi_export(request):
    """P5 (CFO Braun, UC-AR-13): Kennzahlen als CSV fuer Excel/Controlling.

    Ausschliesslich Aggregate - keine Namen, keine Einzelfaelle. Flussgroessen
    (Bewerbungen, Einstellungen, Automatisierung) auf die letzten 365 Tage
    bezogen, Inklusion als Bestand wie auf der Governance-Seite. Jede
    Annahme steht als eigene Zeile im Export, nicht versteckt in der Zahl.
    """
    import csv

    from django.db.models import Sum

    from ..models import SourceChannel

    year_ago = timezone.now() - datetime.timedelta(days=365)
    apps_new = Application.objects.filter(createdAt__gte=year_ago).count()
    hired_qs = Application.objects.filter(status='HIRED', updatedAt__gte=year_ago)
    hires = hired_qs.count()
    hire_days = [max((a.updatedAt - a.createdAt).days, 0) for a in hired_qs]
    avg_days = round(sum(hire_days) / len(hire_days)) if hire_days else None

    cost_total = SourceChannel.objects.aggregate(s=Sum('costAmount'))['s']
    cost_per_hire = round(float(cost_total) / hires, 2) if cost_total and hires else None

    def _acts(action: str) -> int:
        return AuditLog.objects.filter(action=action, createdAt__gte=year_ago).count()

    inclusion = _inclusion_aggregate()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="securats-roi-inklusion.csv"'
    response.write('\ufeff')  # BOM: Umlaute in Excel
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Bereich', 'Kennzahl', 'Wert', 'Erläuterung'])
    rows = [
        ('Besetzung', 'Bewerbungen eingegangen', apps_new, 'letzte 365 Tage'),
        ('Besetzung', 'Einstellungen', hires, 'letzte 365 Tage'),
        ('Besetzung', 'Ø Tage bis Einstellung', avg_days if avg_days is not None else '',
         'Eingang bis Status EINGESTELLT'),
        ('Kanalkosten', 'Kampagnenkosten gesamt', cost_total or 0,
         'Summe der an Kanälen hinterlegten Kosten'),
        ('Kanalkosten', 'Kosten je Einstellung', cost_per_hire if cost_per_hire is not None else '',
         'Kampagnenkosten / Einstellungen (Näherung)'),
        ('Entlastung', 'Automatische Antworten', _acts('AUTO_REPLY_SENT'),
         'sofort beantwortete Bewerberfragen (letzte 365 Tage)'),
        ('Entlastung', 'Sammel-Antworten (Versandvorgänge)', _acts('BATCH_REPLY_SENT'),
         'einmal geprüft, an alle Betroffenen gesendet'),
        ('Entlastung', 'Serien-Nachrichten (Empfänger)', _acts('SERIES_MESSAGE_SENT'),
         'z. B. Ausbildungs-/Event-Einladungen'),
        ('Entlastung', 'DSGVO-Anonymisierungen', _acts('ANONYMIZE_DSGVO'),
         'automatische Aufbewahrungs-Läufe'),
        ('Inklusion', 'Bewerbungen mit § 164-Angabe', inclusion['disclosed'],
         'freiwillige Angabe, Bestand gesamt'),
        ('Inklusion', 'SBV-Unterrichtungen versendet', inclusion['sbv_notified'],
         '§ 164 Abs. 1 SGB IX'),
    ]
    if inclusion['rates_visible']:
        rows.append(('Inklusion', 'Einladungsquote mit/ohne Angabe',
                     f"{inclusion['disclosed_rate']} % / {inclusion['other_rate']} %",
                     'nur Aggregat, ab 5 Fällen je Gruppe'))
    else:
        rows.append(('Inklusion', 'Einladungsquote mit/ohne Angabe', '',
                     'unter Anonymitätsschwelle (5 Fälle je Gruppe)'))
    for row in rows:
        writer.writerow(row)
    write_audit('ROI_EXPORT', user=request.user, rows=len(rows))
    return response


@hr_admin_required
def panel_defaults_view(request):
    """Gremien-Defaults je Ebene pflegen (UC: flexibles Entscheidungsgremium).

    Leiter: Stelle > Abteilung > Einrichtung > Standort > Jobfamilie >
    Organisation – die spezifischste besetzte Ebene gewinnt komplett.
    „Bewusst kein Gremium" (Sentinel NONE) unterbricht die Vererbung, z. B.
    Firmen-Default fuer alle, aber Aushilfsstellen-Familie ohne Gremium.
    """
    from ..models import Department
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
        obj.panelUserIdsJson = value
        obj.save(update_fields=['panelUserIdsJson'])
        write_audit('PANEL_DEFAULT_CHANGED', user=request.user,
                    level=request.POST.get('level'), entity=str(obj),
                    members=len([v for v in value if v.upper() != 'NONE']),
                    no_panel=(value == ["NONE"]))
        return redirect('ats:panel_defaults')

    from django.contrib.auth.models import User as _User
    staff = list(_User.objects.filter(is_active=True, groups__isnull=False)
                 .distinct().order_by('username'))
    from ..models import Department
    def rows(model, level):
        out = []
        for obj in model.objects.order_by('name'):
            current = obj.panelUserIdsJson or []
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
    from django.contrib.auth.models import User as _User

    from ..panel import resolve_panel_preview
    ids, source = resolve_panel_preview(
        job_family_id=request.GET.get('job_family') or None,
        facility_id=request.GET.get('facility') or None,
        department_id=request.GET.get('department') or None,
        location_id=request.GET.get('location') or None)
    names = list(_User.objects.filter(id__in=[i for i in ids if i.isdigit()])
                 .values_list('username', flat=True)) if ids else []
    return JsonResponse({'members': names, 'source': source,
                         'none': 'kein Gremium' in source})


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


# --- B2: Audit-Log-Viewer ---------------------------------------------------

#: Zeilen je Seite. Steht hier und nicht zweimal im Code, damit Ansicht und
#: Export nie unterschiedlich rechnen.
AUDIT_PAGE_SIZE = 100

#: Wie lange ein Personen-Filter als derselbe Vorgang gilt (Minuten).
PERSON_FILTER_DEDUP_MINUTES = 15

#: Wie viele der eigenen ENTSCHIEDENEN Personalbedarfe die Seite zeigt.
#: Offene Antraege sind durch die Arbeit begrenzt; entschiedene wachsen ueber
#: Jahre. Der Deckel bleibt, aber die Seite nennt ihn.
DECIDED_HISTORY_LIMIT = 50


class AuditSelectionError(ValueError):
    """Unbrauchbare Filterangabe – Text ist fuer die Anzeige gedacht."""


def _audit_selection(request) -> tuple[Any, dict[str, str]]:
    """Die EINE Auswahl-Logik – fuer Ansicht und Export.

    Vorher hatten beide ihre eigene: Die Seite kannte nur `action`, der Export
    zusaetzlich `von`/`bis`. Der Knopf verspricht „aktuelle Auswahl als CSV" –
    und lieferte etwas anderes als der Bildschirm zeigte. Bei einem Nachweis
    fuer Betriebsrat oder Datenschutzbeauftragte ist das keine Kleinigkeit.
    """
    qs = AuditLog.objects.all()
    active = {
        'von': (request.GET.get('von') or '').strip()[:10],
        'bis': (request.GET.get('bis') or '').strip()[:10],
        'action': (request.GET.get('action') or '').strip()[:100],
        'person': (request.GET.get('person') or '').strip()[:255],
        'bewerbung': (request.GET.get('bewerbung') or '').strip()[:255],
    }
    try:
        if active['von']:
            qs = qs.filter(createdAt__date__gte=datetime.date.fromisoformat(active['von']))
        if active['bis']:
            qs = qs.filter(createdAt__date__lte=datetime.date.fromisoformat(active['bis']))
    except ValueError:
        raise AuditSelectionError("Ungültiges Datum (Format: JJJJ-MM-TT).") from None
    if active['von'] and active['bis'] and active['von'] > active['bis']:
        raise AuditSelectionError("Das Bis-Datum liegt vor dem Von-Datum.")
    if active['action']:
        qs = qs.filter(action=active['action'])
    if active['person']:
        qs = qs.filter(userId=active['person'])
    if active['bewerbung']:
        # Die Tabelle zeigt die ID gekuerzt – wer sie abschreibt, hat einen
        # Praefix. Der Filter nimmt beides an.
        qs = qs.filter(applicationId__startswith=active['bewerbung'])
    return qs, active


def _selection_label(active: dict[str, str]) -> str:
    """Die Auswahl in Worten – fuer die Kopfzeile des Nachweises."""
    teile = [f"Zeitraum {active['von'] or 'Anfang'} bis {active['bis'] or 'heute'}"]
    if active['action']:
        teile.append(f"Aktion {active['action']}")
    if active['person']:
        teile.append(f"Person {active['person']}")
    if active['bewerbung']:
        teile.append(f"Bewerbung {active['bewerbung']}…")
    return " · ".join(teile)


def _note_person_filter(request, person: str) -> None:
    """§ 87 Abs. 1 Nr. 6 BetrVG: Wer nach einer Person sucht, wird selbst notiert.

    Ohne diesen Vermerk waere der Personen-Filter ein Werkzeug zur
    Verhaltenskontrolle ohne Gegengewicht – jemand koennte unbemerkt nachsehen,
    was eine Kollegin den ganzen Tag getan hat. Mit ihm bleibt es
    nachvollziehbar, und der Betriebsrat kann es im selben Log nachlesen.

    Entprellt: Blaettern und Nachjustieren gehoeren zu EINEM Vorgang. Zwanzig
    gleiche Eintraege waeren zwar vollstaendig, aber unlesbar – und eine Kette,
    die niemand mehr liest, schuetzt niemanden.
    """
    since = timezone.now() - datetime.timedelta(minutes=PERSON_FILTER_DEDUP_MINUTES)
    marker = json.dumps({"person": person}, default=str)
    recent = (AuditLog.objects
              .filter(action='AUDIT_PERSON_FILTER',
                      userId=request.user.get_username(), createdAt__gte=since)
              .values_list('metadataJson', flat=True)[:50])
    if marker not in list(recent):
        write_audit('AUDIT_PERSON_FILTER', user=request.user, person=person)


@hr_admin_required
def audit_log_view(request):
    """Audit-Log durchsuchen – ohne stille Kappung.

    Vorher endete die Seite bei `logs[:500]`. Fuer eine Anfrage zu einem
    Vorgang von vor drei Monaten war der Eintrag damit schlicht nicht
    auffindbar, und die Seite schrieb ihre eigene Grenze als Merkmal hin
    („max. 500 Eintraege"). Ein Nachweis, der nur die juengste Vergangenheit
    kennt, ist fuer § 99 BetrVG oder Art. 15 DSGVO wertlos.

    Die Ketten-Pruefung laeuft NUR auf Anforderung: sie liest und hasht jeden
    Eintrag. Bei jedem Seitenaufruf mitzulaufen waere derselbe Fehler wie die
    KI-Abfrage, die frueher das Dashboard blockiert hat.
    """
    from django.core.paginator import Paginator

    try:
        qs, active = _audit_selection(request)
        fehler = ""
    except AuditSelectionError as exc:
        qs, active, fehler = AuditLog.objects.none(), {
            'von': '', 'bis': '', 'action': '', 'person': '', 'bewerbung': ''}, str(exc)

    if active['person']:
        _note_person_filter(request, active['person'])

    paginator = Paginator(qs.order_by('-createdAt', '-seq'), AUDIT_PAGE_SIZE)
    page = paginator.get_page(request.GET.get('seite'))

    chain = None
    if request.GET.get('pruefen'):
        from ..audit import verify_audit_chain
        chain = verify_audit_chain()
        write_audit('AUDIT_CHAIN_VERIFIED', user=request.user,
                    ok=bool(chain.get('ok')), checked=chain.get('checked'))

    query = {k: v for k, v in active.items() if v}
    return render(request, "audit_log.html", {
        "page": page,
        "logs": page.object_list,
        "gesamt": paginator.count,
        "actions": sorted(a for a in AuditLog.objects
                          .values_list("action", flat=True).distinct() if a),
        "personen": sorted(p for p in AuditLog.objects
                           .values_list("userId", flat=True).distinct() if p),
        "active": active,
        "fehler": fehler,
        "chain": chain,
        "querystring": urlencode(query),
    })


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

    Gefiltert wird ueber `_audit_selection` – dieselbe Funktion wie die
    Ansicht, damit „aktuelle Auswahl" auch wirklich die aktuelle Auswahl ist.
    """
    import csv as _csv

    from ..audit import verify_audit_chain

    try:
        qs, active = _audit_selection(request)
    except AuditSelectionError as exc:
        return HttpResponse(str(exc), status=400)
    qs = qs.order_by('createdAt')
    if active['person']:
        _note_person_filter(request, active['person'])

    chain = verify_audit_chain()
    ok = bool(chain.get('ok'))
    detail = f"geprüft {chain.get('checked')}, Bruch bei {chain.get('broken_id', '?')}"
    rows = list(qs.values_list('createdAt', 'action', 'userId',
                               'applicationId', 'metadataJson', 'entryHash'))

    write_audit('AUDIT_EXPORTED', user=request.user,
                rows=len(rows), von=active['von'], bis=active['bis'],
                action_filter=active['action'], person_filter=active['person'],
                application_filter=active['bewerbung'], chain_ok=ok)

    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    fname = f"securats-audit-{timezone.localdate().isoformat()}.csv"
    resp['Content-Disposition'] = f'attachment; filename="{fname}"'
    resp.write('\ufeff')
    w = _csv.writer(resp, delimiter=';')
    w.writerow([f"# SecurATS Audit-Nachweis · erstellt {timezone.localtime():%d.%m.%Y %H:%M} "
                f"· Auswahl: {_selection_label(active)} "
                f"· Hash-Kette: {'INTAKT' if ok else 'VERLETZT – ' + str(detail)} "
                f"· {len(rows)} Einträge"])
    w.writerow(['Zeitpunkt', 'Aktion', 'Nutzer', 'Bewerbungs-ID', 'Metadaten', 'Hash'])
    for created, act, user_id, app_id, meta, h in rows:
        w.writerow([timezone.localtime(created).strftime('%Y-%m-%d %H:%M:%S'),
                    act, user_id or '', app_id or '', meta, h or ''])
    return resp


@any_staff_required
@denies_viewer_writes
def staffing_requests_view(request):
    """UC-MD-01: Personalbedarf melden + bearbeiten.

    Melden darf jede interne Rolle (auch Hiring-Manager/Viewer – genau dafuer
    ist die Seite da); entscheiden duerfen Recruiter/HR-Admin. Sichtbarkeit:
    eigene Meldungen immer; alle Meldungen fuer die entscheidenden Rollen,
    BOLA-gescopt ueber die Einrichtung.
    """
    from ..models import StaffingRequest
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
            from ..approvals import resolve_requisition_rule
            from ..questions import normalize_questions as _nqs
            rule = resolve_requisition_rule(facility, department, job_family)
            answers = {}
            if rule:
                try:
                    rqs = _nqs(rule.formQuestionsJson or [])
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
                answersJson=answers)
            write_audit('STAFFING_REQUEST_CREATED', user=request.user,
                        request_id=str(req.id), facility=facility.name,
                        headcount=headcount)
            from ..approvals import open_requisition_steps, requisition_required
            if requisition_required() or rule:
                open_requisition_steps(req)
                from ..approvals import notify_due_requisition_steps
                notify_due_requisition_steps(req)
                req.status = 'IN_APPROVAL'
                req.save(update_fields=['status'])
        return redirect('ats:staffing_requests')

    if (request.method == 'POST'
            and request.POST.get('form', '').startswith('rule_')
            and request.user.groups.filter(name='HR-Admin').exists()):
        from ..models import RequisitionRule
        from ..questions import normalize_question, normalize_questions
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
                qs = normalize_questions(rule.formQuestionsJson or [])
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
            rule.formQuestionsJson = qs
            rule.save(update_fields=['formQuestionsJson'])
            write_audit('REQUISITION_RULE_FORM_CHANGED', user=request.user,
                        name=rule.name, count=len(qs))
        return redirect('ats:staffing_requests')

    if request.method == 'POST' and request.POST.get('form') == 'step_decide':
        # Stellenfreigabe: nur die Rolle der aktuell faelligen Stufe entscheidet
        from ..models import RequisitionStep
        step = get_object_or_404(RequisitionStep,
                                 id=request.POST.get('step_id'))
        req = step.request
        from ..approvals import due_requisition_steps, may_decide_requisition_step
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
                from ..approvals import due_requisition_steps as _dueq
                from ..approvals import notify_due_requisition_steps
                nxt = _dueq(req)
                if nxt and nxt[0].order != step.order:
                    notify_due_requisition_steps(req)
            # Antragsteller informieren, sobald etwas Finales passiert
            if (req.status in ('ACCEPTED', 'DECLINED', 'RETURNED')
                    and req.requestedBy and req.requestedBy.email):
                from ..mail_send import send_notice
                label = {'ACCEPTED': 'genehmigt', 'DECLINED': 'abgelehnt',
                         'RETURNED': 'zur Nachbesserung zurückgegeben'}[req.status]
                send_notice(
                    f'Stellenfreigabe {label}: {req.title}',
                    f'Ihr Personalbedarf "{req.title}" wurde {label}.'
                           + (f'\nKommentar: {step.comment}' if step.comment
                              else '')
                           + '\nDetails: /recruiter/bedarf/',
                    None,
                    [req.requestedBy.email],
                    request=request, context='Freigabe-Entscheidung')
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
            from ..approvals import notify_due_requisition_steps
            notify_due_requisition_steps(req)
        return redirect('ats:staffing_requests')

    if (request.method == 'POST'
            and request.POST.get('form') == 'requisition_settings'
            and request.user.groups.filter(name='HR-Admin').exists()):
        from ..models import SystemSetting
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
        from ..approvals import requisition_required as _rr
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
                    from ..mail_send import send_notice
                    label = 'angenommen' if decision == 'ACCEPTED' else 'abgelehnt'
                    send_notice(
                        f'Ihre Bedarfsmeldung wurde {label}: {req.title}',
                        f'Status: {label}.\n'
                               + (f'Anmerkung: {req.decisionNote}\n' if req.decisionNote else '')
                               + 'Details: /recruiter/bedarf/',
                        None,
                        [req.requestedBy.email],
                        request=request, context='Bedarfs-Entscheidung')
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
                screeningQuestionsJson=[])
            # Prozess-Gedaechtnis: der Entwurf bekommt den zuletzt real
            # genutzten Prozess der Jobfamilie gleich mit (Fragen, Aufgaben,
            # Anforderungen) – eine Klickstrecke weniger beim Vervollstaendigen.
            prev = _previous_process(job.jobFamily_id, req.facility_id,
                                     exclude_id=job.id)
            if prev:
                job.screeningQuestionsJson = prev['screening_questions']
                job.tasksJson = prev['tasks']
                job.requirementsJson = prev['requirements']
                job.save(update_fields=['screeningQuestionsJson', 'tasksJson',
                                        'requirementsJson'])
            from ..process_advisor import ensure_minimum_standards
            if ensure_minimum_standards(job):
                job.save(update_fields=['screeningQuestionsJson'])
                write_audit('MINIMUM_STANDARD_APPLIED', user=request.user,
                            job=job.title)
            # Frageverbot gilt auch hier: Dieser Pfad uebernimmt die Fragen
            # einer Vorgaengerstelle wortgleich - stammt dort (aus Altbestand,
            # Import oder Django-Admin) eine Gehaltshistorie-Frage, wurde sie
            # ungefiltert in jede neue Ausschreibung vererbt, samt
            # automatischer K.O.-Absage (EU-RL 2023/970 Art. 5 Abs. 2).
            from ..pay_transparency import strip_salary_history_questions
            _removed = strip_salary_history_questions(job)
            if _removed:
                job.save(update_fields=['screeningQuestionsJson'])
                write_audit('PAY_HISTORY_QUESTION_BLOCKED', user=request.user,
                            job=job.title, removed=len(_removed),
                            via='requisition_conversion')
            from ..approvals import ensure_approval_gate
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

    # Eigene Meldungen vollstaendig: Wer seine eigene Meldung von vor einem
    # halben Jahr sucht und sie nicht findet, meldet sie ein zweites Mal.
    my_requests = StaffingRequest.objects.filter(
        requestedBy=request.user).select_related('facility').order_by('-createdAt')
    inbox = []
    if is_decider:
        facilities_scope = Facility.objects.all()
        if not has_full_access(request.user):
            fac_ids = list(request.user.scope.facilities.values_list('id', flat=True))
            facilities_scope = facilities_scope.filter(id__in=fac_ids) if fac_ids else facilities_scope
        inbox = (StaffingRequest.objects.filter(facility__in=facilities_scope)
                 .select_related('facility', 'requestedBy', 'jobFamily')
                 .order_by('status', '-createdAt'))

    # Ketten-Genehmiger (Bereichsleitung, Vorstand, ...) und ihre aktiven
    # Vertretungen sehen die Antraege, deren faellige Stufe sie entscheiden
    # duerfen – auch OHNE Recruiter-/HR-Admin-Rolle. Vorher konnten diese
    # Rollen formal entscheiden, fanden die Antraege aber nirgends.
    from ..approvals import may_decide_requisition_step as _mds
    inbox_ids = {r.id for r in inbox}
    chain_inbox = []
    for r in (StaffingRequest.objects.filter(status='IN_APPROVAL')
              .exclude(id__in=inbox_ids)
              .select_related('facility', 'requestedBy', 'jobFamily')
              .order_by('-createdAt')):
        from ..approvals import due_requisition_steps as _due
        if any(_mds(request.user, st)[0] for st in _due(r)):
            chain_inbox.append(r)
    # ... plus Antraege, die ich selbst (mit-)entschieden habe: ein
    # Genehmiger muss seine eigenen Entscheidungen nachvollziehen koennen.
    seen = inbox_ids | {r.id for r in chain_inbox}
    # Offene Antraege sind durch die Arbeit begrenzt und werden vollstaendig
    # gezeigt. Die eigenen ENTSCHIEDENEN wachsen dagegen ueber Jahre - hier
    # bleibt ein Deckel, aber er wird genannt statt verschwiegen.
    entschieden_qs = (StaffingRequest.objects.filter(steps__decidedBy=request.user)
                      .exclude(id__in=seen).distinct()
                      .select_related('facility', 'requestedBy', 'jobFamily')
                      .order_by('-createdAt'))
    entschieden_gesamt = entschieden_qs.count()
    decided_by_me = list(entschieden_qs[:DECIDED_HISTORY_LIMIT])
    inbox = list(inbox) + chain_inbox + decided_by_me

    from ..approvals import may_decide_requisition_step as may_dec
    from ..approvals import requisition_required as _rreq
    from ..approvals import resolve_requisition_rule as _rrule
    from ..questions import QUESTION_TYPES as _QT
    from ..questions import normalize_questions as _nq2
    sel_fac = Facility.objects.filter(id=request.GET.get('facility')).first()
    sel_dep = Department.objects.filter(
        id=request.GET.get('department')).first()
    sel_fam = JobFamily.objects.filter(
        id=request.GET.get('job_family')).first()
    form_rule = _rrule(sel_fac, sel_dep, sel_fam) if sel_fac else None
    form_questions = []
    if form_rule:
        try:
            form_questions = _nq2(form_rule.formQuestionsJson or [])
        except (ValueError, TypeError):
            form_questions = []
    rule_rows = []
    from ..models import RequisitionRule as _RR
    for rl in _RR.objects.select_related(
            'facility', 'department', 'jobFamily').order_by('-createdAt'):
        try:
            rl_qs = _nq2(rl.formQuestionsJson or [])
        except (ValueError, TypeError):
            rl_qs = []
        rule_rows.append({'rule': rl, 'questions': rl_qs,
                          'q_indexed': list(enumerate(rl_qs))})
    from ..models import SystemSetting as _SS
    req_active = _rreq()
    chain_setting = _SS.objects.filter(key='REQUISITION_CHAIN').first()
    def _decorate(reqs):
        rows = []
        for r in reqs:
            steps = list(r.steps.all())
            answers = r.answersJson or {}
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
        # Genannt statt verschwiegen: Wenn die eigene Entscheidungs-Historie
        # laenger ist als der Deckel, sagt die Seite das.
        'entschieden_gesamt': entschieden_gesamt,
        'entschieden_gezeigt': len(decided_by_me),
        'entschieden_gekappt': entschieden_gesamt > len(decided_by_me),
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
        from ..process_advisor import rule_based_suggestions
        fam_name = (JobFamily.objects.filter(id=job_family_id)
                    .values_list('name', flat=True).first()) or ''
        questions, _notes = rule_based_suggestions(title or '', fam_name)
        if not questions:
            return None
        return {'source': 'REGELWERK', 'scope': 'Regelwerk (keine Vorlage vorhanden)',
                'source_title': f'Prozess-Berater: {fam_name}', 'source_date': '',
                'source_facility': '', 'screening_questions': questions,
                'tasks': [], 'requirements': []}
    questions = source.screeningQuestionsJson or []
    return {
        'source': 'VORGAENGER', 'scope': scope,
        'source_title': source.title,
        'source_date': timezone.localtime(source.createdAt).strftime('%d.%m.%Y'),
        'source_facility': source.facility.name if source.facility else '',
        'screening_questions': questions,
        'tasks': source.tasksJson or [],
        'requirements': source.requirementsJson or [],
        # V2: Die Quell-Stelle ist ohnehin geladen - dann soll sie auch die
        # Einordnung und den Auswahlprozess mitgeben, statt dass beides
        # erneut zusammengeklickt wird. Alles VORSCHLAEGE: der Nutzer sieht
        # sie im Formular und kann jede aendern.
        'facility_id': str(source.facility_id) if source.facility_id else '',
        'department_id': str(source.department_id) if source.department_id else '',
        'location_id': str(source.location_id) if source.location_id else '',
        'pay_band_id': str(source.payBand_id) if source.payBand_id else '',
        'contact_person_id': (str(source.contactPerson_id)
                              if source.contactPerson_id else ''),
        'interview_rounds': list(source.interviewRoundsJson or []),
        'interview_guide': list(source.interviewGuideJson or []),
        'panel_quorum': source.panelQuorum if source.panelQuorum else '',
        'panel_deadline_days': (source.panelDeadlineDays
                                if source.panelDeadlineDays else ''),
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
