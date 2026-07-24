"""SecurATS Views — Analytics-Dashboard und Exporte.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from ..audit import write_audit
from ..models import Application, JobPosting, Page, SystemSetting
from ..permissions import any_staff_required, has_full_access, recruiter_required, scope_applications, scope_jobs

logger = logging.getLogger(__name__)

__all__ = ["analytics_view", "analytics_export"]


# --- B7: Analytics-/Insight-Dashboard (Ausbau, BOLA-gescopt) ----------------
@recruiter_required
def analytics_view(request):
    from datetime import timedelta

    from django.db.models import Count
    from django.db.models.functions import TruncMonth

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
    from ..analytics import (
        appointment_stats,
        cost_per_hire,
        detect_anomalies,
        fairness_overview,
        location_benchmark,
        time_to_fill_forecast,
    )
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
    from ..models import SourceChannel as _SCh
    for _c in _SCh.objects.exclude(costAmount__isnull=True):
        source_costs[_c.slug] = float(_c.costAmount)
    costs = cost_per_hire(apps, source_costs) if (is_leadership and source_costs) else []

    # Landingpages & Kampagnen: der volle Trichter auf dem Dashboard
    from ..models import LandingPage as _LP
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
    from ..analytics import requisition_stage_stats
    from ..models import StaffingRequest as _SReq
    _req_qs = _SReq.objects.all()
    if not has_full_access(request.user):
        _fac_ids = list(request.user.scope.facilities
                        .values_list('id', flat=True))
        if _fac_ids:
            _req_qs = _req_qs.filter(facility_id__in=_fac_ids)
    stage_rows = requisition_stage_stats(_req_qs)
    from ..pay_transparency import transparency_overview
    pay_overview = transparency_overview()

    # L1: „Erkenntnisse & Vorschläge" – Zahl plus konkreter naechster Schritt.
    # Im BOLA-Rahmen des Nutzers (apps ist bereits gescoped; Stellen ebenso).
    from ..suggestions import aggregate_suggestions
    _sugg_jobs = list(scope_jobs(request.user, JobPosting.objects.all()))
    insights, insights_truncated = aggregate_suggestions(_sugg_jobs, apps)
    return render(request, 'analytics.html', {
        'insights': insights,
        'insights_truncated': insights_truncated,
        'pay_overview': pay_overview,
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
