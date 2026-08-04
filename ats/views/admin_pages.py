"""SecurATS Views — eigenstaendige Verwaltungs-Seiten (B2).

Bis hierher steckten KPIs, Prozess-Flow, E-Mail-Vorlagen, CMS, KI-Zentrale
und die HRIS-Anbindung als versteckte Tabs im Recruiter-Dashboard. Zwei
Probleme folgten daraus:

1. Das Dashboard berechnete und lieferte bei JEDEM Aufruf Daten und Markup
   aus, die im Alltag niemand braucht — nur damit sechs unsichtbare
   `div.tab-content` gefuellt sind.
2. Die Seitenleiste mischte In-Page-Tabs (`switchTab`) mit echten Links.
   Zwei Bedienmuster nebeneinander, ohne erkennbare Regel.

Jede dieser Sichten ist jetzt eine eigene Seite: eigene URL, eigener
Kontext, eigener serverseitiger Rollenschutz. Das Ausblenden in der
Seitenleiste bleibt reine Benutzerfuehrung — der Schutz sitzt hier im
Decorator (@hr_admin_required), nicht im Template.

Teil des View-Pakets; oeffentliche Namen werden in ats/views/__init__.py
re-exportiert.
"""

from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Count
from django.shortcuts import redirect, render

from ..models import (
    Application,
    AppWorkflowDef,
    EmailTemplate,
    Facility,
    JobFamily,
    JobPosting,
    Location,
    Page,
    SystemSetting,
    WorkflowState,
)
from ..permissions import hr_admin_required, scope_applications, scope_jobs

__all__ = ["stats_page", "process_page", "templates_page", "cms_page", "ki_page", "hris_page", "save_auto_reply_settings", "retention_page", "privacy_notice_page", "learned_scoring_view", "save_learned_scoring_settings"]


def gemma_status() -> str:
    """Erreichbarkeit der lokalen KI als ONLINE/OFFLINE.

    Wird sowohl von der KI-Zentrale als auch vom Dashboard-Abzeichen genutzt.

    Frueher stand hier eine eigene Verbindungspruefung mit fest verdrahtetem
    Port 11434. Zwei Folgen:

    * Wer OLLAMA_PORT setzte, sah ein OFFLINE-Abzeichen ueber einer laufenden
      KI - die Anzeige widersprach der Funktion.
    * Ohne KI kostete jeder Dashboard-Aufruf bis zu vier Sekunden, weil zwei
      Verbindungsversuche mit je zwei Sekunden ins Leere liefen. Beim Kunden
      ohne KI-Profil ist genau das der Normalfall.

    Beides erledigt `ollama_reachable()`: dieselbe Adresse wie die echten
    KI-Aufrufe, und die Antwort gilt kurz nach.
    """
    from .ai import ollama_reachable
    return 'ONLINE' if ollama_reachable() else 'OFFLINE'


@hr_admin_required
def stats_page(request):
    """KPIs & Inklusions-ROI: Funnel-Zahlen + SGB-IX-Rechner.

    Der Rechner selbst laeuft im Browser (reine Modellrechnung); vom Server
    kommen nur die Funnel-Zahlen. Gezaehlt wird im Zugriffsbereich des
    Nutzers (BOLA) und mit derselben Spalten-Logik wie auf dem Board:
    ein unbekannter Status faellt auf „Neu" zurueck.
    """
    counts = {'NEW': 0, 'IN_REVIEW': 0, 'INVITED': 0, 'HIRED': 0, 'REJECTED': 0}
    total = 0
    scoped = scope_applications(request.user, Application.objects.all())
    for status in scoped.values_list('status', flat=True):
        total += 1
        counts[status if status in counts else 'NEW'] += 1

    return render(request, 'admin_pages/stats.html', {
        'stats': {
            'total': total,
            'new': counts['NEW'],
            'in_review': counts['IN_REVIEW'],
            'invited': counts['INVITED'],
            'rejected': counts['REJECTED'],
        },
    })


@hr_admin_required
def process_page(request):
    """Prozess Flow Manager: Status-Phasen und spezialisierte Pipelines.

    Die Auswahlfelder (Einrichtung, Standort, Kategorie, Stelle) speisen den
    Geltungsbereich einer Pipeline; die Rollenliste fuellt den
    Automatik-Baukasten (Aufgaben- und Benachrichtigungs-Empfaenger).
    """
    return render(request, 'admin_pages/process.html', {
        'all_workflows': WorkflowState.objects.all().order_by('name'),
        'app_workflows': AppWorkflowDef.objects.all().select_related('facility').order_by('name'),
        'all_roles': list(Group.objects.order_by('name').values_list('name', flat=True)),
        'facilities': Facility.objects.all(),
        'locations': Location.objects.filter(archived=False),
        'job_families': JobFamily.objects.filter(archived=False),
        'active_jobs': scope_jobs(request.user, JobPosting.objects.all().order_by('-createdAt')),
    })


@hr_admin_required
def templates_page(request):
    """E-Mail-Vorlagen und globale Variablen (SystemSettings)."""
    return render(request, 'admin_pages/templates.html', {
        'all_system_settings': SystemSetting.objects.all().order_by('key'),
        'all_email_templates': EmailTemplate.objects.all().order_by('name'),
    })


@hr_admin_required
def cms_page(request):
    """CMS Seiten-Editor: Karriere-Landingpages und Hauptseiten."""
    return render(request, 'admin_pages/cms.html', {
        'all_pages': Page.objects.all().order_by('navOrder'),
    })


@hr_admin_required
def ki_page(request):
    """KI-Zentrale: Verbindungstest, AGG-Checker, Leichte Sprache, Regelwerk.

    `ai_settings` ist die flache Schluessel/Wert-Sicht auf die
    SystemSettings — das Formular liest daraus seine Vorbelegung.
    """
    from ..auto_reply import enabled_intents, is_master_enabled
    from ..inbox_intents import AUTO_SAFE_INTENTS, INTENT_LABELS
    active = enabled_intents()
    auto_reply_choices = [
        {'code': i, 'label': INTENT_LABELS[i], 'on': i in active}
        for i in sorted(AUTO_SAFE_INTENTS)]
    return render(request, 'admin_pages/ki.html', {
        'ai_settings': {s.key: s.value for s in SystemSetting.objects.all()},
        'gemma_status': gemma_status(),
        'auto_reply_master': is_master_enabled(),
        'auto_reply_choices': auto_reply_choices,
    })


@hr_admin_required
def save_auto_reply_settings(request):
    """Governance der Auto-Antwort (Stufe 4): Hauptschalter + welche sicheren
    Anliegen automatisch beantwortet werden. Auswahl wird hart auf die
    sicheren Anliegen gefiltert - ein Entscheidungs-Anliegen laesst sich hier
    nicht freischalten."""
    import json

    from ..audit import write_audit
    from ..auto_reply import AUTO_REPLY_ENABLED_KEY, AUTO_REPLY_INTENTS_KEY
    from ..inbox_intents import AUTO_SAFE_INTENTS
    if request.method != 'POST':
        return redirect('ats:ki_page')
    master = '1' if request.POST.get('auto_reply_enabled') else '0'
    chosen = [i for i in request.POST.getlist('auto_reply_intents')
              if i in AUTO_SAFE_INTENTS]
    SystemSetting.objects.update_or_create(
        key=AUTO_REPLY_ENABLED_KEY, defaults={'value': master})
    SystemSetting.objects.update_or_create(
        key=AUTO_REPLY_INTENTS_KEY, defaults={'value': json.dumps(chosen)})
    write_audit('AUTO_REPLY_SETTINGS_CHANGED', user=request.user,
                enabled=(master == '1'), intents=chosen)
    messages.success(request, "Einstellungen der Auto-Antwort gespeichert.")
    return redirect('ats:ki_page')


@hr_admin_required
def learned_scoring_view(request):
    """L3-Governance + Messstrecke: je Kontext den Backtest (gelernt vs.
    regelbasierte Grundlinie), die Kalibrierung und das Vertrauens-Verdikt -
    damit die Entscheidung zum Freischalten INFORMIERT faellt. Standardmaessig
    aus (EU AI Act, Hochrisiko)."""
    from ..insights import resolve_learning_scope
    from ..models import JobFamily, JobPosting
    from ..scoring_eval import backtest, drift_report, is_scoring_enabled
    families = list(JobFamily.objects.all()[:40])
    rows = []
    for fam in families:
        job = JobPosting.objects.filter(jobFamily=fam).first()
        if not job:
            continue
        scope = resolve_learning_scope(job)
        # L5: neben der Momentaufnahme (Backtest) auch die Fruehwarnung -
        # wird das Modell schlechter, und entscheidet das Team dagegen?
        rows.append({'family': fam.name, 'bt': backtest(scope),
                     'drift': drift_report(scope)})
    rows.sort(key=lambda r: (not r['bt'].beats_baseline, -r['bt'].total))
    # Handlungsbedarf nach oben: fallender Trend oder hohe Gegen-Quote.
    alerts = [r for r in rows
              if r['drift'].trend == 'fallend'
              or (r['drift'].override_rate or 0) >= 0.30]
    return render(request, 'admin_pages/learned_scoring.html', {
        'enabled': is_scoring_enabled(), 'rows': rows, 'alerts': alerts})


@hr_admin_required
def save_learned_scoring_settings(request):
    """Hauptschalter fuers gelernte Scoring. Aktivieren ist eine bewusste,
    auditierte Entscheidung mit ZWEI Voraussetzungen: Rechtsgutachten UND
    Zustimmung des Betriebsrats - eine leistungs-/verhaltensbewertende
    Automatik ist nach § 87 Abs. 1 Nr. 6 BetrVG mitbestimmungspflichtig."""
    from ..audit import write_audit
    from ..scoring_eval import LEARNED_SCORING_ENABLED_KEY
    if request.method != 'POST':
        return redirect('ats:learned_scoring')
    enable = bool(request.POST.get('enable'))
    legal = bool(request.POST.get('legal_confirmed'))
    br = bool(request.POST.get('br_confirmed'))
    if enable and not (legal and br):
        missing = []
        if not legal:
            missing.append("Rechtsgutachten")
        if not br:
            missing.append("Betriebsrats-Zustimmung (§ 87 Abs. 1 Nr. 6 BetrVG)")
        messages.warning(request, "Aktivierung nur mit bestätigter "
                         + " und ".join(missing) + " – Kästchen ankreuzen.")
        return redirect('ats:learned_scoring')
    SystemSetting.objects.update_or_create(
        key=LEARNED_SCORING_ENABLED_KEY,
        defaults={'value': '1' if enable else '0'})
    write_audit('LEARNED_SCORING_TOGGLED', user=request.user, enabled=enable,
                legal_confirmed=legal, br_confirmed=br)
    messages.success(request, "Gelerntes Scoring "
                     + ("aktiviert." if enable else "deaktiviert."))
    return redirect('ats:learned_scoring')


@hr_admin_required
def retention_page(request):
    """P4 (UC-AR-13/UC-MB-06): Loeschfrist als Verwaltungsseite statt
    verstecktem SystemSetting - mit Trockenlauf-Vorschau (nur Zahlen, keine
    Namen: die Seite dient DSB/HR-Admin, nicht der Einzelfall-Recherche)."""
    from ..audit import write_audit
    from ..retention import (
        MAX_DAYS,
        MIN_DAYS,
        RETENTION_DAYS_KEY,
        configured_retention_days,
        dry_run_preview,
    )
    if request.method == 'POST':
        try:
            days = int(request.POST.get('days', ''))
        except (TypeError, ValueError):
            days = None
        if days is None or not (MIN_DAYS <= days <= MAX_DAYS):
            messages.warning(request, f"Frist muss zwischen {MIN_DAYS} und "
                                      f"{MAX_DAYS} Tagen liegen.")
            return redirect('ats:retention')
        old = configured_retention_days()
        SystemSetting.objects.update_or_create(
            key=RETENTION_DAYS_KEY, defaults={'value': str(days)})
        write_audit('RETENTION_POLICY_CHANGED', user=request.user,
                    old_days=old, new_days=days)
        messages.success(request, f"Löschfrist auf {days} Tage gesetzt.")
        return redirect('ats:retention')
    return render(request, 'admin_pages/retention.html', {
        'days': configured_retention_days(),
        'min_days': MIN_DAYS, 'max_days': MAX_DAYS,
        'preview': dry_run_preview(),
    })


@hr_admin_required
def privacy_notice_page(request):
    """Fassungen des Datenschutzhinweises pflegen (Art. 7 Abs. 1 DSGVO).

    Die Nachweispflicht verlangt, belegen zu koennen, WORIN eingewilligt
    wurde. Bisher ging das nur ueber die Django-Administration - eine
    technische Oberflaeche, die niemand aus der Personalabteilung oeffnet.
    Die Governance-Sicht benannte die Luecke, aber der Weg zur Behebung
    fuehrte aus dem Produkt heraus.

    ANFUEGEN STATT AENDERN: Eine bestehende Fassung laesst sich hier nicht
    umschreiben. Wer den Text aendert, legt eine neue Fassung an. Ein
    nachtraeglich geaenderter Text wuerde den Nachweis zerstoeren, den er
    sein soll - die Bewerbungen zeigen dann auf eine Fassung, die es so nie
    gab.
    """
    from ..audit import write_audit
    from ..dsgvo import privacy_notice_status
    from ..models import PrivacyNoticeVersion

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        if action == 'activate':
            target = PrivacyNoticeVersion.objects.filter(
                id=request.POST.get('version_id')).first()
            if target is not None:
                # Genau EINE Fassung ist gueltig - sonst waere unklar, welche
                # eine neue Bewerbung gesehen hat.
                PrivacyNoticeVersion.objects.exclude(id=target.id).update(active=False)
                PrivacyNoticeVersion.objects.filter(id=target.id).update(active=True)
                write_audit('PRIVACY_NOTICE_ACTIVATED', user=request.user,
                            version=target.version)
                messages.success(
                    request, f"Fassung {target.version} ist ab jetzt gültig. "
                             "Bereits eingegangene Bewerbungen behalten die "
                             "Fassung, die sie gesehen haben.")
            return redirect('ats:privacy_notice')

        version = (request.POST.get('version') or '').strip()[:50]
        content = (request.POST.get('content') or '').strip()
        if not version or not content:
            messages.warning(request, "Fassungsnummer und Text sind beide nötig.")
            return redirect('ats:privacy_notice')
        if PrivacyNoticeVersion.objects.filter(version=version).exists():
            messages.warning(
                request, f"Fassung {version} gibt es schon. Eine bestehende "
                         "Fassung wird nicht überschrieben – vergeben Sie eine "
                         "neue Nummer.")
            return redirect('ats:privacy_notice')
        PrivacyNoticeVersion.objects.update(active=False)
        notice = PrivacyNoticeVersion.objects.create(
            version=version, content=content, active=True)
        write_audit('PRIVACY_NOTICE_CREATED', user=request.user,
                    version=notice.version, length=len(content))
        messages.success(request, f"Fassung {version} angelegt und gültig gesetzt.")
        return redirect('ats:privacy_notice')

    versions = list(PrivacyNoticeVersion.objects.order_by('-createdAt'))
    used = {
        row['privacyNoticeVersion']: row['n']
        for row in Application.objects
        .filter(privacyNoticeVersion__isnull=False)
        .values('privacyNoticeVersion')
        .annotate(n=Count('id'))
    }
    rows = [{'notice': v, 'used': used.get(v.id, 0)} for v in versions]
    return render(request, 'admin_pages/privacy_notice.html', {
        'rows': rows,
        'status': privacy_notice_status(),
    })


@hr_admin_required
def hris_page(request):
    """HRIS-/SAP-Anbindung: Feldzuordnung als Uebersicht.

    Diese Seite uebertraegt nichts. Sie zeigt, welches SecurATS-Feld auf
    welches HRIS-Feld abgebildet wird; die Uebertragung macht der Befehl
    `hris_export` und nur bei gesetztem HRIS_ENDPOINT.
    """
    return render(request, 'admin_pages/hris.html', {
        'sap_schema_fields': [
            {'id': 'sf_candidate_id', 'label': 'Candidate ID (UUID)', 'type': 'String'},
            {'id': 'sf_first_name', 'label': 'First Name', 'type': 'String'},
            {'id': 'sf_last_name', 'label': 'Last Name', 'type': 'String'},
            {'id': 'sf_email', 'label': 'E-Mail Address', 'type': 'String'},
            {'id': 'sf_job_req_id', 'label': 'Job Requisition ID', 'type': 'String'},
            {'id': 'sf_score_rating', 'label': 'AI Screening Rating', 'type': 'String'},
        ],
    })
