"""SecurATS Views — Termine, Gespraechsrunden und strukturiertes Interview-Feedback.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging

from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ..audit import write_audit
from ..models import (
    Application,
    AuditLog,
    Interview,
    InterviewSlot,
    JobPosting,
    Message,
    SystemSetting,
    get_interview_kinds,
)
from ..permissions import (
    can_access_application,
    hr_admin_required,
    recruiter_required,
    scope_applications,
    scope_jobs,
)
from .common import _safe_next_url

logger = logging.getLogger(__name__)

__all__ = ["schedule_interview", "interviews_view", "slot_create", "slot_delete", "interviews_ics", "interview_outcome", "interview_formats_manage", "save_interview_feedback", "advance_interview_round", "application_feedback_json"]


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

        from ..panel import invitation_blocked_reason
        reason = invitation_blocked_reason(app)
        if reason:
            from urllib.parse import quote
            return redirect(f"{reverse('ats:dashboard')}?gremium={quote(reason)}")

        with transaction.atomic():
            # Dritter Weg: Bewerber:in waehlt den Termin SELBST im Portal.
            # Kein Interview jetzt – Status INVITED + Nachricht mit Hinweis;
            # die Buchung passiert atomar im Portal (candidate_portal).
            if slot_id == 'CANDIDATE_CHOICE':
                app.status = 'INVITED'
                app.save()
                message_text = (request.POST.get('message_text') or '').strip()[:4000]
                hint = ('\n\nBitte wählen Sie Ihren Wunschtermin direkt in Ihrem '
                        'Bewerbungsportal aus (Link aus Ihrer Eingangsbestätigung).')
                if message_text:
                    Message.objects.create(application=app, direction='OUTBOUND',
                                           content=message_text + hint)
                    try:
                        from ..mail_send import send_notice
                        send_notice(
                            f"Einladung zum Gespräch – {app.jobPosting.title}",
                            message_text + hint,
                            None,
                            [app.applicant.email],
                            request=request, context='Gespraechseinladung')
                    except Exception:
                        logger.exception('Einladungs-Mail (Terminwahl) fehlgeschlagen')
                write_audit('INVITE_SENT', user=request.user,
                            application_id=str(app.id), mode='CANDIDATE_CHOICE')
                return redirect('ats:dashboard')

            if slot_id:
                # Der Slot MUSS zur Stelle dieser Bewerbung gehoeren und darf
                # nicht schon belegt sein - der Portal-Pfad prueft das laengst
                # (views/public.py), hier fehlte es: fremde Slots waren buchbar.
                slot = get_object_or_404(InterviewSlot, id=slot_id,
                                         jobPosting=app.jobPosting,
                                         isBooked=False)
                slot.isBooked = True
                slot.application = app
                slot.save()
                scheduled_time = slot.startTime
                # Format aus dem Slot uebernehmen, wenn dort eines hinterlegt
                # ist - der Portal-Pfad macht es genauso; doppelte Eingabe
                # desselben Sachverhalts entfaellt.
                if getattr(slot, 'kind', ''):
                    location_type = slot.kind
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
                from ..models import interview_kind_label as _kl
                when_s = timezone.localtime(scheduled_time).strftime('%d.%m.%Y %H:%M')
                try:
                    from ..mail_send import send_notice
                    for member in team:
                        if member.email:
                            send_notice(
                                f"Interview-Team: {_kl(location_type)} am {when_s} Uhr",
                                f"Du bist Teil des Interview-Teams:\n"
                                 f"{app.applicant.firstName} {app.applicant.lastName} – "
                                 f"{app.jobPosting.title}\n{_kl(location_type)} am {when_s} Uhr."
                                 + (f"\nOrt/Link: {meeting_link}" if meeting_link else "")
                                 + "\n\nTeam-Kalender: /recruiter/interviews/",
                                None,
                                [member.email],
                                request=request, context='Interview-Team')
                except Exception:
                    logger.exception('Team-Benachrichtigung fehlgeschlagen')

            # Advance application status to INVITED
            app.status = 'INVITED'
            app.save()

            # Einladen = Termin + Kommunikation in EINEM Schritt:
            # Nachricht an Bewerber:in (Portal-Postfach) + E-Mail (fail_silently)
            message_text = (request.POST.get('message_text') or '').strip()[:4000]
            if message_text:
                Message.objects.create(application=app, direction='OUTBOUND',
                                       content=message_text)
                try:
                    from ..mail_send import send_notice
                    send_notice(
                        f"Einladung zum Gespräch – {app.jobPosting.title}",
                        message_text +
                        f"\n\nTermin: {timezone.localtime(scheduled_time).strftime('%d.%m.%Y %H:%M')} Uhr"
                        + (f"\nOrt/Link: {meeting_link}" if meeting_link else ""),
                        None,
                        [app.applicant.email],
                        request=request, context='Gespraechseinladung')
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


@recruiter_required
def interviews_view(request):
    """Team-Kalender: Interviews + freie Slots im Monatsraster, BOLA-gescopt.

    Kollaboration verteilter Teams: alle im Zugriffsbereich sehen dieselben
    Termine und wer welchen Slot anbietet – Doppelplanung wird sichtbar,
    bevor sie passiert. Slots anlegen/loeschen direkt hier; Export als .ics
    fuer Outlook & Co. (ehrlich: Download/Import, kein Abo-Feed).
    """
    import calendar as _cal
    from datetime import date
    from datetime import datetime as _dt

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
    can_manage_formats = (request.user.is_superuser or
                          request.user.groups.filter(name='HR-Admin').exists())
    # P1-11: Bewerbungen mit definierten Gespraechsrunden – formaler
    # Fortschritt je Runde, abschliessbar direkt hier.
    from ..models import DEFAULT_FEEDBACK_CRITERIA, INTERVIEW_RECOMMENDATIONS, feedback_for_application, rounds_state
    round_rows = []
    for app in (scoped_apps.filter(status__in=['IN_REVIEW', 'INVITED'])
                .select_related('applicant', 'jobPosting')
                .order_by('createdAt')):
        rst = rounds_state(app)
        # V3: Auch OHNE definierte Gespraechsrunden muss Feedback erfassbar
        # sein. Vorher haengte das ganze Feedback-Formular an rst['total'] -
        # liess jemand das Runden-Feld im Wizard leer, gab es in der gesamten
        # Oberflaeche keine Moeglichkeit, ein Gespraech zu bewerten. Ohne
        # definierte Runden gilt genau ein implizites "Gespraech".
        if not rst['total']:
            rst = {'rounds': ['Gespräch'], 'total': 1,
                   'done': min(app.interviewRound or 0, 1),
                   'complete': (app.interviewRound or 0) >= 1,
                   'current_label': 'Gespräch' if not (app.interviewRound or 0) else None,
                   'implicit': True}
        if rst['total']:
            fb = feedback_for_application(app)
            my = next((f for f in fb['items']
                       if f.author_id == request.user.id
                       and f.round == rst['done']), None)
            # V3: "Runde abschliessen" nur anbieten, solange die Runde NICHT
            # schon durch ein erfasstes Gespraechs-Ergebnis vorgerueckt ist.
            # Wer beides klickte, uebersprang eine Runde (interview_outcome
            # rueckt automatisch vor, advance_interview_round rechnet +1).
            auto_advanced = app.interviews.filter(
                outcome__isnull=False).exclude(outcome='').exists()
            round_rows.append({'app': app, 'state': rst,
                               'auto_advanced': auto_advanced,
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
        start = iv.scheduledAt.astimezone(datetime.UTC)
        end = start + datetime.timedelta(minutes=45)
        who = f"{iv.application.applicant.firstName} {iv.application.applicant.lastName}"
        lines += ['BEGIN:VEVENT', f'UID:securats-{iv.id}',
                  f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
                  f"SUMMARY:{iv.kind_label}: {who} – {iv.application.jobPosting.title}",
                  f"LOCATION:{iv.meetingLink or iv.locationType}",
                  'END:VEVENT']
    lines.append('END:VCALENDAR')
    # Diese Datei enthaelt Klarnamen aller anstehenden Gespraeche - derselbe
    # Nachweis wie beim CV-Download (READ_CV) gehoert also auch hierher.
    # Vorher war es der einzige Datei-Download der Anwendung ohne Spur.
    write_audit('CALENDAR_EXPORT', user=request.user, events=len(ivs))
    resp = HttpResponse('\r\n'.join(lines), content_type='text/calendar; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="securats-interviews.ics"'
    return resp


@recruiter_required
def interview_outcome(request, interview_id):
    """Gespraechsergebnis erfassen (stattgefunden / No-Show / kurzfristig abgesagt).

    Korrekturen sind erlaubt (Tippfehler passieren) – jede Aenderung steht im
    Audit. Die weitere Entscheidung (Zusage/Absage) laeuft wie gehabt ueber den
    Bewerbungsstatus im Kanban; hier wird nur der Termin selbst dokumentiert.
    """
    if request.method != 'POST':
        return redirect('ats:interviews')
    from ..models import INTERVIEW_OUTCOMES
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
    from ..models import pending_feedback_participants, rounds_state
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
            from ..mail_send import send_notice
            name = f"{app.applicant.firstName} {app.applicant.lastName}"
            for person in pending:
                send_notice(
                    f"Bitte um Feedback: {name} – {app.jobPosting.title}",
                    f"Sie haben {name} interviewt. Bitte hinterlassen Sie "
                     "Ihre Einschätzung, damit die weitere Entscheidung auf "
                     "dokumentiertem Feedback steht.\n"
                     "Feedback erfassen: /recruiter/interviews/",
                    None,
                    [person.email],
                    context='Feedback-Erinnerung')
            write_audit('FEEDBACK_REQUESTED', user=request.user,
                        application_id=str(app.id), round=completed_round,
                        recipients=len(pending))
    return redirect('ats:interviews')


@hr_admin_required
def interview_formats_manage(request):
    """Terminformate konfigurierbar machen (P0-Luecke: war Code-Liste).

    Speicherung als SystemSetting INTERVIEW_KINDS_JSON; Start = Code-Default.
    Bestehende Termine behalten ihr Label (interview_kind_label mit
    Code-Fallback), auch wenn ein Format entfernt wird.
    """
    import json as _json
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
                kinds = [(c, label if c == code else lbl) for c, lbl in kinds]
        elif action == 'delete':
            code = request.POST.get('code', '')
            if len(kinds) > 1:  # mindestens ein Format bleibt
                kinds = [(c, lbl) for c, lbl in kinds if c != code]
        SystemSetting.objects.update_or_create(
            key='INTERVIEW_KINDS_JSON',
            defaults={'value': _json.dumps(
                [{'code': c, 'label': lbl} for c, lbl in kinds])})
        write_audit('INTERVIEW_FORMATS_CHANGED', user=request.user,
                    op=action, count=len(kinds))
    return redirect('ats:interviews')


@recruiter_required
def save_interview_feedback(request, app_id):
    """Strukturiertes Interview-Feedback speichern/aktualisieren.

    Eine Rueckmeldung je Person, Bewerbung und Runde – erneutes Absenden
    aktualisiert die eigene (Korrektur erlaubt, auditiert). Runde wird aus
    dem aktuellen Stand der Bewerbung abgeleitet, kann aber mitgegeben
    werden (Feedback zu einer bereits abgeschlossenen Runde)."""
    from ..models import (
        DEFAULT_FEEDBACK_CRITERIA,
        INTERVIEW_RECOMMENDATIONS,
        InterviewFeedback,
        derive_recommendation,
        rounds_state,
    )
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
    # N1: Leitfaden-Abdeckung - nur Themen, die die Stelle wirklich definiert
    # (kein Freitext-Schmuggel ueber die Checkbox-Namen).
    guide = app.jobPosting.interview_guide
    covered = [t for t in request.POST.getlist('guide_topic') if t in guide]
    fb, created = InterviewFeedback.objects.update_or_create(
        application=app, author=request.user, round=rnd,
        defaults={
            'recommendation': recommendation,
            'ratingsJson': ratings,
            'guideCoverageJson': covered,
            'strengths': (request.POST.get('strengths') or '').strip()[:4000],
            'concerns': (request.POST.get('concerns') or '').strip()[:4000],
            'comment': (request.POST.get('comment') or '').strip()[:4000],
        })
    write_audit('INTERVIEW_FEEDBACK_SAVED', user=request.user,
                application_id=str(app.id), round=rnd,
                recommendation=recommendation,
                created=created, has_concerns=bool(fb.concerns.strip()),
                **({'guide_covered': len(covered),
                    'guide_total': len(guide)} if guide else {}))
    _nxt = _safe_next_url(request)
    return redirect(_nxt) if _nxt else redirect('ats:interviews')


@recruiter_required
def advance_interview_round(request, app_id):
    """Gespraechsrunde formal abschliessen (op=advance) oder zur Korrektur
    zuruecknehmen (op=back) – gekappt auf [0, Anzahl Runden], auditiert."""
    from ..models import rounds_state
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
def application_feedback_json(request, app_id):
    """Strukturiertes Interview-Feedback einer Bewerbung als JSON – fuer das
    Kandidaten-Modal (die zentrale Entscheidungsflaeche). Damit sieht ein
    Recruiter beim Oeffnen sofort den Team-Eindruck inkl. Bedenken."""
    from ..models import feedback_for_application
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
