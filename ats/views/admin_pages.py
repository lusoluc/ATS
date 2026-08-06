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
    SystemSetting,
    WorkflowState,
)
from ..permissions import hr_admin_required, scope_applications, scope_jobs

__all__ = ["stats_page", "process_page", "templates_page", "ki_page", "hris_page", "save_auto_reply_settings", "retention_page", "privacy_notice_page", "settings_hub", "mail_settings_page", "learned_scoring_view", "save_learned_scoring_settings"]


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
def settings_hub(request):
    """Eine Startseite für alles, was eingerichtet wird.

    Die Konfigurations-Seiten sind über die Jahre einzeln entstanden und hingen
    verstreut in der Seitenleiste - zwischen Tagesgeschäft wie Board und
    Postfach. Wer SecurATS neu aufsetzt, musste raten, was alles einzurichten
    ist, und sah nirgends, was noch fehlt.

    Diese Seite sammelt die Bereiche und zeigt je Eintrag den ZUSTAND, nicht
    nur einen Link: Was nicht eingerichtet ist, sagt das hier - statt dass es
    im Betrieb still ausfällt.
    """
    from ..dsgvo import privacy_notice_status
    from ..geo import lookup_plz
    from ..mail_config import mail_status
    from ..models import EmailTemplate, Location, PayBand, SourceChannel

    mail = mail_status()
    notice = privacy_notice_status()
    locations = list(Location.objects.filter(archived=False))
    missing_coords = sum(1 for loc in locations
                         if loc.lat is None and lookup_plz(loc.postalCode))

    def state(ok, good, bad, warn=False):
        return {'ok': bool(ok), 'label': good if ok else bad,
                'warn': bool(warn)}

    groups = [
        {
            'title': 'Zustellung & Kommunikation',
            'items': [
                {'name': 'E-Mail-Versand', 'url': 'ats:mail_settings',
                 'icon': 'fa-paper-plane',
                 'hint': 'Mailserver des Trägers, Absenderadresse, Testversand',
                 'state': state(mail['configured'], f"über {mail['host']}",
                                'nicht eingerichtet – es wird nichts zugestellt')},
                {'name': 'E-Mail-Vorlagen', 'url': 'ats:templates_page',
                 'icon': 'fa-envelope-open-text',
                 'hint': 'Texte für Eingangsbestätigung, Einladung, Absage',
                 'state': state(EmailTemplate.objects.exists(),
                                f"{EmailTemplate.objects.count()} Vorlagen",
                                'keine Vorlagen')},
                {'name': 'Textbausteine', 'url': 'ats:snippets',
                 'icon': 'fa-quote-right',
                 'hint': 'Antwort-Bausteine für das Sammel-Postfach',
                 'state': None},
            ],
        },
        {
            'title': 'Datenschutz & Aufbewahrung',
            'items': [
                {'name': 'Datenschutzhinweis', 'url': 'ats:privacy_notice',
                 'icon': 'fa-file-shield',
                 'hint': 'Fassungen pflegen (Art. 7 Abs. 1 DSGVO)',
                 'state': state(not notice['missing'],
                                f"Fassung {notice['version']}",
                                'keine Fassung gepflegt')},
                {'name': 'Datenaufbewahrung', 'url': 'ats:retention',
                 'icon': 'fa-clock-rotate-left',
                 'hint': 'Löschfrist und Trockenlauf-Vorschau',
                 'state': None},
                # Vertretungen stehen bewusst NICHT hier: Sie sind
                # Selbstbedienung fuer jede interne Rolle (ein Vorstand legt
                # seine Vertretung selbst an), keine Administration.
                {'name': 'Audit-Log', 'url': 'ats:audit_log',
                 'icon': 'fa-clipboard-list',
                 'hint': 'Revisionssichere Zugriffs-Protokolle samt CSV-Export',
                 'state': None},
            ],
        },
        {
            'title': 'Stammdaten',
            'items': [
                {'name': 'Standorte', 'url': 'ats:locations',
                 'icon': 'fa-location-dot',
                 'hint': 'Adressen und Koordinaten für die Umkreissuche',
                 'state': state(not missing_coords, f"{len(locations)} Standorte",
                                f"{missing_coords} ohne Koordinaten – "
                                "Umkreissuche wirkt dort nicht", warn=True)},
                {'name': 'Entgeltbänder', 'url': 'ats:pay_bands',
                 'icon': 'fa-euro-sign',
                 'hint': 'Pflicht vor Veröffentlichung (EU-RL 2023/970)',
                 'state': state(PayBand.objects.filter(archived=False).exists(),
                                f"{PayBand.objects.filter(archived=False).count()} Bänder",
                                'keine Bänder – Stellen lassen sich nicht veröffentlichen')},
                {'name': 'Ansprechpersonen', 'url': 'ats:contacts',
                 'icon': 'fa-address-card',
                 'hint': 'Kontakte für Stellenanzeigen', 'state': None},
                {'name': 'Kategorien', 'url': 'ats:categories',
                 'icon': 'fa-tags', 'hint': 'Berufsfelder', 'state': None},
                {'name': 'Kanäle & Kosten', 'url': 'ats:source_channels',
                 'icon': 'fa-bullhorn',
                 'hint': 'Bewerbungsquellen und ihre Kosten',
                 'state': state(SourceChannel.objects.exists(),
                                f"{SourceChannel.objects.count()} Kanäle",
                                'keine Kanäle')},
                {'name': 'Screening-Fragen', 'url': 'ats:screening_questions',
                 'icon': 'fa-clipboard-question',
                 'hint': 'Wiederverwendbare Fragen für Stellen', 'state': None},
                {'name': 'Stellen-Vorlagen', 'url': 'ats:job_templates',
                 'icon': 'fa-copy',
                 'hint': 'Versionierte Textvorlagen für Ausschreibungen',
                 'state': None},
            ],
        },
        {
            'title': 'Verfahren & Automatik',
            'items': [
                {'name': 'KI-Zentrale', 'url': 'ats:ki_page',
                 'icon': 'fa-robot',
                 'hint': 'Lokale KI, AGG-Check, Auto-Antwort',
                 'state': state(gemma_status() == 'ONLINE', 'lokale KI erreichbar',
                                'lokale KI nicht erreichbar', warn=True)},
                {'name': 'Lernendes Scoring', 'url': 'ats:learned_scoring',
                 'icon': 'fa-graduation-cap',
                 'hint': 'Messstrecke und Freischaltung (Opt-in)', 'state': None},
                {'name': 'Prozess-Phasen', 'url': 'ats:process_page',
                 'icon': 'fa-diagram-project',
                 'hint': 'Status-Phasen und Pipelines', 'state': None},
                {'name': 'Gremien-Vorgaben', 'url': 'ats:panel_defaults',
                 'icon': 'fa-users-rectangle',
                 'hint': 'Sichtungs-Gremium je Ebene', 'state': None},
                {'name': 'Gesprächsformate', 'url': 'ats:interview_formats',
                 'icon': 'fa-comments',
                 'hint': 'Von der schriftlichen Aufgabe bis zum Assessment',
                 'state': None},
            ],
        },
        {
            'title': 'Auftritt & Schnittstellen',
            'items': [
                {'name': 'Branding', 'url': 'ats:branding',
                 'icon': 'fa-palette',
                 'hint': 'Farben, Logo, Hero-Bild der Karriereseiten',
                 'state': None},
                {'name': 'Seiten & Navigation', 'url': 'ats:pages_manage',
                 'icon': 'fa-file-lines',
                 'hint': 'Anlegen, veröffentlichen, in die Navigation nehmen – '
                         'Baukasten je Seite in der Liste', 'state': None},
                {'name': 'Landingpages', 'url': 'ats:landing_pages',
                 'icon': 'fa-flag',
                 'hint': 'Kampagnen-Seiten mit QR-Code und Ablaufdatum',
                 'state': None},
                {'name': 'Mediathek', 'url': 'ats:media_manage',
                 'icon': 'fa-photo-film',
                 'hint': 'Bilder samt Alt-Texten', 'state': None},
                {'name': 'HRIS / SAP', 'url': 'ats:hris_page',
                 'icon': 'fa-cloud-arrow-up',
                 'hint': 'Feldzuordnung für die Übergabe eingestellter Personen',
                 'state': None},
                {'name': 'SAP-Feldtabelle', 'url': 'ats:sap_sf_mapper',
                 'icon': 'fa-table-columns',
                 'hint': 'Zuordnung SecurATS-Feld → SuccessFactors-Feld',
                 'state': None},
                {'name': 'Datenimport', 'url': 'ats:data_import',
                 'icon': 'fa-file-import',
                 'hint': 'Bestandsdaten aus einem Vorsystem', 'state': None},
            ],
        },
    ]
    open_points = [i for g in groups for i in g['items']
                   if i['state'] and not i['state']['ok']]
    return render(request, 'admin_pages/settings_hub.html', {
        'groups': groups, 'open_points': open_points,
    })


@hr_admin_required
def mail_settings_page(request):
    """Mailserver des Trägers einrichten - und nachweisen, dass er geht.

    Das Passwort wird verschlüsselt abgelegt (dieselbe Fernet-Schicht wie die
    Bewerber-PII) und nie zurück ins Formular geschrieben; angezeigt wird nur,
    OB eines hinterlegt ist. Werte aus Umgebungsvariablen sind gesperrt statt
    stillschweigend wirkungslos - sonst tippt jemand einen Wert ein, der nie
    greift.
    """
    from ..audit import write_audit
    from ..mail_config import (
        FROM_KEY,
        HOST_KEY,
        PORT_KEY,
        SECURITY_CHOICES,
        SECURITY_KEY,
        USER_KEY,
        mail_status,
        send_test_mail,
        store_password,
    )

    if request.method == 'POST':
        if request.POST.get('action') == 'test':
            recipient = (request.POST.get('recipient') or '').strip()
            if not recipient:
                messages.warning(request, "Bitte eine Empfängeradresse angeben.")
                return redirect('ats:mail_settings')
            ok, detail = send_test_mail(recipient)
            write_audit('MAIL_TEST_SENT', user=request.user, ok=ok,
                        detail=detail[:200])
            (messages.success if ok else messages.error)(request, detail)
            return redirect('ats:mail_settings')

        status = mail_status()
        locked = set(status['from_env'])

        def save(field, key, raw, maxlen=255):
            if field in locked:
                return
            value = (raw or '').strip()[:maxlen]
            if value:
                SystemSetting.objects.update_or_create(
                    key=key, defaults={'value': value})
            else:
                SystemSetting.objects.filter(key=key).delete()

        save('host', HOST_KEY, request.POST.get('host'))
        save('user', USER_KEY, request.POST.get('user'))
        save('from_address', FROM_KEY, request.POST.get('from_address'))
        port_raw = (request.POST.get('port') or '').strip()
        save('port', PORT_KEY, port_raw if port_raw.isdigit() else '')
        security = (request.POST.get('security') or '').strip()
        save('security', SECURITY_KEY,
             security if security in SECURITY_CHOICES else '')
        # Leeres Passwortfeld heisst „unveraendert lassen" - sonst loeschte
        # jedes Speichern das Passwort, weil es nie im Formular steht.
        if 'password' not in locked and request.POST.get('password'):
            store_password(request.POST['password'])
        if request.POST.get('clear_password') and 'password' not in locked:
            store_password('')

        write_audit('MAIL_SETTINGS_CHANGED', user=request.user,
                    host=(request.POST.get('host') or '')[:120])
        messages.success(request, "Einstellungen für den Mailversand gespeichert.")
        return redirect('ats:mail_settings')

    return render(request, 'admin_pages/mail_settings.html', {
        'status': mail_status(),
        'security_choices': SECURITY_CHOICES,
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
