"""WP5: Vertiefte Analytics (North Star §4.3) – reine, testbare Funktionen.

Alle Funktionen erhalten bereits BOLA-gescopte Querysets (scope_applications)
und rechnen ausschließlich aggregiert – keine personenbezogenen Auswertungen.
"""
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

# --- Predictive: Time-to-Fill-Prognose ---------------------------------------

def time_to_fill_forecast(apps_qs, open_jobs_qs):
    """Prognostiziert die erwartete Besetzungsdauer offener Stellen.

    Ansatz (bewusst transparent statt Blackbox): historischer Durchschnitt
    NEW→INVITED je Jobfamilie; fehlt Historie, greift der Gesamtdurchschnitt.
    """
    hist = apps_qs.filter(status='INVITED').select_related('jobPosting__jobFamily')
    per_family, all_days = {}, []
    for a in hist:
        days = max((a.updatedAt - a.createdAt).days, 0)
        all_days.append(days)
        fam = getattr(getattr(a.jobPosting, 'jobFamily', None), 'name', None)
        if fam:
            per_family.setdefault(fam, []).append(days)

    global_avg = round(sum(all_days) / len(all_days), 1) if all_days else None
    fam_avg = {f: round(sum(v) / len(v), 1) for f, v in per_family.items()}

    rows = []
    for job in open_jobs_qs.select_related('jobFamily', 'location'):
        fam = getattr(job.jobFamily, 'name', None)
        forecast = fam_avg.get(fam, global_avg)
        age = (timezone.now() - job.createdAt).days
        rows.append({
            'job': job.title,
            'location': getattr(job.location, 'name', '—'),
            'family': fam or '—',
            'forecast_days': forecast,          # None = keine Historie
            'age_days': age,
            'overdue': bool(forecast is not None and age > forecast),
            'basis': 'Jobfamilie' if fam in fam_avg else ('Gesamt' if forecast else '—'),
        })
    return {'rows': rows, 'global_avg': global_avg}


# --- Engpass- & Anomalie-Erkennung mit Handlungsvorschlag ---------------------

def detect_anomalies(apps_qs, stale_days=14):
    """Regelbasierte Hinweise: sagt nicht nur *was*, sondern *was tun*."""
    findings = []
    now = timezone.now()

    stale = apps_qs.filter(status='NEW', createdAt__lt=now - timedelta(days=stale_days)).count()
    if stale:
        findings.append({
            'severity': 'warn',
            'title': f'{stale} Bewerbung(en) warten seit über {stale_days} Tagen auf Erstsichtung',
            'action': 'Erstsichtung priorisieren oder per Mehrfachauswahl in "In Prüfung" ziehen; '
                      'ggf. Vertretung (Delegation) einrichten.',
        })

    # Einladungsquote: letzte 30 Tage vs. 30 Tage davor
    recent = apps_qs.filter(createdAt__gte=now - timedelta(days=30))
    prev = apps_qs.filter(createdAt__gte=now - timedelta(days=60),
                          createdAt__lt=now - timedelta(days=30))

    def _rate(qs):
        t = qs.count()
        return (qs.filter(status='INVITED').count() / t) if t else None

    r_new, r_old = _rate(recent), _rate(prev)
    if r_new is not None and r_old and r_new < r_old * 0.7:
        findings.append({
            'severity': 'warn',
            'title': f'Einladungsquote fällt: {round(r_new*100)}% (Vormonat {round(r_old*100)}%)',
            'action': 'Anforderungsprofile und Absagegründe prüfen; Quellen-Mix und '
                      'Stellenbeschreibung (Leichte Sprache/Benefits) gegensteuern.',
        })

    # Quelle liefert Menge ohne Qualität
    per_source = (apps_qs.values('source').annotate(c=Count('id')).order_by('-c'))
    for row in per_source:
        if row['c'] >= 5:
            invited = apps_qs.filter(source=row['source'], status='INVITED').count()
            if invited == 0:
                findings.append({
                    'severity': 'info',
                    'title': f'Quelle "{row["source"]}" liefert {row["c"]} Bewerbungen, aber keine Einladungen',
                    'action': 'Kanal-Budget prüfen (Kosten pro Einstellung) oder Anzeigentext '
                              'für diesen Kanal schärfen.',
                })

    if not findings:
        findings.append({'severity': 'ok', 'title': 'Keine Auffälligkeiten erkannt',
                         'action': 'Weiter beobachten – Prüfregeln laufen bei jedem Aufruf.'})
    return findings


# --- Fairness-/AGG-Cockpit (datensparsam) -------------------------------------

def fairness_overview(apps_qs):
    """Überwacht die *eigenen* Systementscheidungen – ohne geschützte Merkmale.

    Bewusst datensparsam (Privacy by Design): SecurATS speichert keine
    AGG-geschützten Attribute, daher wird adverse impact je Personengruppe
    NICHT berechnet. Stattdessen: Verteilung der KI-Scores, Override-Verhalten
    (Mensch entscheidet gegen KI) und Auto-Absage-Anteil als Frühwarnsignale.
    """
    total = apps_qs.count()
    scored = apps_qs.exclude(aiScore__isnull=True).exclude(aiScore='')
    dist = {s: scored.filter(aiScore=s).count() for s in ('A', 'B', 'C', 'D')}

    # Overrides: Mensch lädt trotz D ein / lehnt trotz A ab -> KI-Mensch-Divergenz
    invited_low = apps_qs.filter(status='INVITED', aiScore='D').count()
    rejected_high = apps_qs.filter(status='REJECTED', aiScore='A').count()
    decided = apps_qs.filter(status__in=['INVITED', 'REJECTED']).count()
    override_rate = round(((invited_low + rejected_high) / decided) * 100, 1) if decided else None

    return {
        'total': total,
        'scored': scored.count(),
        'score_dist': dist,
        'invited_low': invited_low,
        'rejected_high': rejected_high,
        'override_rate_pct': override_rate,
        'note': ('Adverse-Impact-Messung je Personengruppe erfolgt bewusst nicht: '
                 'geschützte Merkmale werden nicht gespeichert (Datensparsamkeit). '
                 'Beobachtet werden die Entscheidungen des Systems selbst.'),
    }


# --- Standort-Benchmarking & Kosten pro Einstellung ---------------------------

def location_benchmark(apps_qs):
    """Standorte fair nebeneinander: Volumen, Einladungsquote, Ø Dauer."""
    rows = []
    per_loc = (apps_qs.values('jobPosting__location__name')
               .annotate(c=Count('id')).order_by('-c'))
    for r in per_loc:
        name = r['jobPosting__location__name'] or '—'
        loc_qs = apps_qs.filter(jobPosting__location__name=r['jobPosting__location__name'])
        invited = loc_qs.filter(status='INVITED').count()
        durations = [(a.updatedAt - a.createdAt).days
                     for a in loc_qs.filter(status__in=['INVITED', 'REJECTED', 'WITHDRAWN'])
                     .only('createdAt', 'updatedAt')]
        rows.append({
            'location': name,
            'total': r['c'],
            'invited': invited,
            'conversion_pct': round(invited / r['c'] * 100, 1) if r['c'] else 0.0,
            'avg_days': round(sum(durations) / len(durations), 1) if durations else None,
        })
    return rows


def cost_per_hire(apps_qs, source_costs: dict):
    """Kosten pro Einstellung je Quelle.

    source_costs: {'STEPSTONE': 1200.0, ...} – gepflegt auf der Seite
    „Kanäle & Kosten" (SourceChannel.costAmount), Monats-/Periodenkosten
    des Kanals.

    Früher stand hier zusätzlich ein SystemSetting `SOURCE_COST_<QUELLE>`.
    Es wurde ausgewertet, hatte aber kein Bedienelement – zwei Pflegeorte,
    von denen einer unsichtbar war und den anderen still überschrieb.
    """
    rows = []
    for source, cost in sorted(source_costs.items()):
        hires = apps_qs.filter(source=source, status='HIRED').count()
        rows.append({
            'source': source,
            'cost': cost,
            'hires': hires,
            'cost_per_hire': round(cost / hires, 2) if hires else None,
        })
    return rows


def build_data_summary(apps_qs):
    """Aggregierte, PII-freie Datenzusammenfassung für den lokalen KI-Analysten."""
    lines = [f"Bewerbungen gesamt: {apps_qs.count()}"]
    for label, field in [("Status", "status"), ("Quelle", "source"),
                         ("KI-Score", "aiScore"),
                         ("Standort", "jobPosting__location__name"),
                         ("Jobfamilie", "jobPosting__jobFamily__name")]:
        parts = [f"{r[field] or '—'}={r['c']}" for r in
                 apps_qs.values(field).annotate(c=Count('id')).order_by('-c')[:8]]
        lines.append(f"{label}: " + ", ".join(parts) if parts else f"{label}: –")
    bench = location_benchmark(apps_qs)[:6]
    for b in bench:
        lines.append(f"Standort {b['location']}: {b['total']} Bewerbungen, "
                     f"{b['conversion_pct']}% Einladungsquote, Ø {b['avg_days']} Tage")
    # Termin-Kennzahlen (aggregiert) – der Analyst soll auch Buchungsverhalten kennen
    try:
        from .models import JobPosting
        ap = appointment_stats(apps_qs, JobPosting.objects.filter(
            id__in=apps_qs.values_list('jobPosting_id', flat=True)))
        lines.append(
            f"Termine (90 Tage): geplant={ap['planned_total']}, "
            f"selbst gebucht={ap['self_booked']}, umgebucht={ap['rebooked']}, "
            f"abgesagt={ap['cancelled']}, Änderungswünsche={ap['change_requests']}, "
            f"Slot-Auslastung={ap['utilization'] if ap['utilization'] is not None else '–'}%, "
            f"Buchungen abends/Wochenende={ap['after_hours_share'] if ap['after_hours_share'] is not None else '–'}%")
    except Exception:
        pass
    try:
        import datetime as _dt

        from django.utils import timezone as _tz

        from .models import TalentPoolContact, TalentPoolSubscription
        _now = _tz.now()
        active = TalentPoolSubscription.objects.filter(expiresAt__gte=_now).count()
        hints_90 = TalentPoolContact.objects.filter(
            sentAt__gte=_now - _dt.timedelta(days=90)).count()
        lines.append(f"Talent-Pool: aktive Einwilligungen={active}, "
                     f"Stellen-Hinweise (90 Tage)={hints_90}")
    except Exception:
        pass
    return "\n".join(lines)


def appointment_stats(apps_qs, jobs_qs, days=90):
    """Termin-Analytik: Selbstbuchung, Umbuchungen, Absagen, Slot-Auslastung.

    Datensparsam: ausschliesslich Aggregate ueber den BOLA-Scope der
    aufrufenden Person – keine Namen, keine Einzelfaelle. Quelle sind die
    ohnehin geschriebenen Audit-Ereignisse (CANDIDATE_SLOT_BOOKED, _REBOOKED,
    _CANCELLED, CHANGE_REQUEST, INVITE_SENT, SCHEDULE_INTERVIEW) plus
    Interview/InterviewSlot – die Interaktionen werten sich selbst aus.
    """
    import datetime as _dt
    import statistics

    from django.utils import timezone

    from .models import AuditLog, Interview, InterviewSlot, interview_kind_label

    now = timezone.now()
    since = now - _dt.timedelta(days=days)
    app_ids = {str(i) for i in apps_qs.values_list('id', flat=True)}

    audits = list(AuditLog.objects.filter(createdAt__gte=since,
                                          action__in=[
                                              'CANDIDATE_SLOT_BOOKED',
                                              'CANDIDATE_APPOINTMENT_REBOOKED',
                                              'CANDIDATE_APPOINTMENT_CANCELLED',
                                              'CANDIDATE_CHANGE_REQUEST',
                                              'INVITE_SENT', 'SCHEDULE_INTERVIEW'])
                  .order_by('createdAt'))
    audits = [a for a in audits if (a.applicationId or '') in app_ids]

    def _count(action):
        return sum(1 for a in audits if a.action == action)

    self_booked = _count('CANDIDATE_SLOT_BOOKED')
    direct = _count('SCHEDULE_INTERVIEW')
    rebooked = _count('CANDIDATE_APPOINTMENT_REBOOKED')
    cancelled = _count('CANDIDATE_APPOINTMENT_CANCELLED')
    change_requests = _count('CANDIDATE_CHANGE_REQUEST')
    planned_total = self_booked + direct

    # Median-Stunden von "Bewerber:in waehlt"-Einladung bis zur Terminwahl
    invite_at = {}
    for a in audits:
        if a.action == 'INVITE_SENT' and 'CANDIDATE_CHOICE' in (a.metadataJson or ''):
            invite_at.setdefault(a.applicationId, a.createdAt)
    waits = []
    for a in audits:
        if a.action == 'CANDIDATE_SLOT_BOOKED' and a.applicationId in invite_at:
            delta = (a.createdAt - invite_at.pop(a.applicationId)).total_seconds() / 3600
            if delta >= 0:
                waits.append(delta)
    median_hours_to_choice = round(statistics.median(waits), 1) if waits else None

    # Wann buchen Bewerbende? (These: abends/Wochenende, wenn Zeit ist)
    booking_times = [timezone.localtime(a.createdAt) for a in audits
                     if a.action in ('CANDIDATE_SLOT_BOOKED',
                                     'CANDIDATE_APPOINTMENT_REBOOKED')]
    after_hours = sum(1 for t in booking_times
                      if t.hour < 8 or t.hour >= 18 or t.weekday() >= 5)
    after_hours_share = (round(100 * after_hours / len(booking_times))
                         if booking_times else None)

    # Slot-Auslastung: verfallene (vergangen + ungebucht) vs. genutzte Slots
    past_slots = InterviewSlot.objects.filter(jobPosting__in=jobs_qs,
                                              startTime__lt=now, startTime__gte=since)
    expired = past_slots.filter(isBooked=False).count()
    used = past_slots.filter(isBooked=True).count()
    open_future = InterviewSlot.objects.filter(jobPosting__in=jobs_qs,
                                               isBooked=False,
                                               startTime__gte=now).count()
    utilization = round(100 * used / (used + expired)) if (used + expired) else None

    # Formate-Verteilung der Gespraeche im Zeitraum
    kinds = {}
    for iv in Interview.objects.filter(application__in=apps_qs,
                                       scheduledAt__gte=since):
        label = interview_kind_label(iv.locationType)
        kinds[label] = kinds.get(label, 0) + 1
    kinds = sorted(kinds.items(), key=lambda kv: -kv[1])

    # Gespraechsergebnisse: No-Show-Quote wird erst durch die Outcome-Erfassung
    # im Team-Kalender moeglich – ohne gepflegte Ergebnisse bleibt sie ehrlich '–'.
    past_ivs = Interview.objects.filter(application__in=apps_qs,
                                        scheduledAt__lt=now, scheduledAt__gte=since)
    completed = past_ivs.filter(outcome='COMPLETED').count()
    no_shows = past_ivs.filter(outcome='NO_SHOW').count()
    short_cancelled = past_ivs.filter(outcome='CANCELLED').count()
    outcome_pending = past_ivs.filter(outcome__isnull=True).count()
    with_outcome = completed + no_shows + short_cancelled
    no_show_rate = (round(100 * no_shows / with_outcome)
                    if with_outcome else None)

    # Handlungsvorschlaege (im Stil der Anomalie-Hinweise: Befund -> Vorschlag)
    hints = []
    if no_show_rate is not None and no_show_rate > 15 and with_outcome >= 5:
        hints.append(f"No-Show-Quote {no_show_rate} % ({no_shows} von {with_outcome} "
                     "erfassten Gesprächen). Vorschlag: Telefonat als erste Runde "
                     "anbieten (niedrigere Hürde) und prüfen, ob die "
                     "Termin-Erinnerung ankommt.")
    if outcome_pending >= 5:
        hints.append(f"{outcome_pending} vergangene Gespräche ohne erfasstes Ergebnis "
                     "– im Team-Kalender unter 'Ergebnis erfassen' nachtragen, sonst "
                     "sind No-Show-Quote und Format-Vergleich nicht belastbar.")
    if utilization is not None and utilization < 50 and (used + expired) >= 5:
        hints.append(f"{expired} von {used + expired} angebotenen Slots sind ungenutzt "
                     "verfallen. Vorschlag: weniger, dafür passendere Zeiten anbieten "
                     "(die Buchungs-Uhrzeiten unten zeigen, wann Bewerbende aktiv sind).")
    if planned_total >= 5 and cancelled / max(planned_total, 1) > 0.2:
        hints.append(f"{cancelled} Absagen bei {planned_total} geplanten Terminen "
                     "(> 20 %). Vorschlag: Formate prüfen (Telefonat statt vor Ort "
                     "für Runde 1?) und mehr Slots am frühen Abend anbieten.")
    if after_hours_share is not None and after_hours_share >= 30:
        hints.append(f"{after_hours_share} % der Terminbuchungen passieren abends oder "
                     "am Wochenende – die Selbstbuchung erreicht Bewerbende genau dann, "
                     "wenn kein Büro besetzt ist. Beibehalten und Slots breit streuen.")
    if change_requests and not (self_booked or rebooked):
        hints.append(f"{change_requests} Änderungswünsche, aber keine Selbst-Umbuchungen: "
                     "Prüfen, ob genug freie Slots zum Ausweichen angeboten sind.")

    return {
        'planned_total': planned_total, 'self_booked': self_booked, 'direct': direct,
        'self_booking_share': (round(100 * self_booked / planned_total)
                               if planned_total else None),
        'rebooked': rebooked, 'cancelled': cancelled,
        'change_requests': change_requests,
        'median_hours_to_choice': median_hours_to_choice,
        'after_hours_share': after_hours_share,
        'slots_expired': expired, 'slots_used': used, 'slots_open': open_future,
        'utilization': utilization,
        'completed': completed, 'no_shows': no_shows,
        'short_cancelled': short_cancelled, 'outcome_pending': outcome_pending,
        'no_show_rate': no_show_rate,
        'kinds': kinds, 'hints': hints, 'days': days,
    }

def requisition_stage_stats(requests_qs):
    """Engpass-Analyse der Stellenfreigabe: Wartezeit je Rolle/Stufe.

    Faellig-Zeitpunkt einer Stufe = Antrags-Eingang (Stufe 1) bzw. der
    Abschluss der VORHERIGEN Stufe (bei parallelen Gruppen: die letzte
    Entscheidung der Vorgruppe). Wartezeit = Entscheidung minus faellig.
    Ehrliche Naeherung: Wiedervorlagen setzen Stufen zurueck, die
    Wartezeit misst dann den letzten Durchlauf ab Antrags-Eingang.

    Liefert je Rolle: entschiedene Stufen, Durchschnitts-Wartetage,
    aktuell faellige offene Stufen und das Alter der aeltesten davon.
    Die Rolle mit dem hoechsten Durchschnitt ist der Engpass.
    """
    from django.utils import timezone as _tz
    stats = {}

    def bucket(role):
        return stats.setdefault(role, {
            'role': role, 'decided': 0, 'total_days': 0.0,
            'open_now': 0, 'oldest_open_days': None})

    now = _tz.now()
    for req in requests_qs.prefetch_related('steps'):
        steps = sorted(req.steps.all(), key=lambda st: st.order)
        if not steps:
            continue
        # faellig-ab je order-Gruppe bestimmen
        due_from = {}
        prev_end = req.createdAt
        for order in sorted({st.order for st in steps}):
            due_from[order] = prev_end
            group = [st for st in steps if st.order == order]
            ends = [st.decidedAt for st in group if st.decidedAt]
            if len(ends) == len(group) and prev_end is not None:
                prev_end = max(ends)
            else:
                prev_end = None  # Gruppe (noch) nicht komplett
        first_open_order = next(
            (st.order for st in steps if st.status == 'PENDING'), None)
        for st in steps:
            base = due_from.get(st.order)
            b = bucket(st.role)
            if st.decidedAt and base:
                b['decided'] += 1
                b['total_days'] += max(
                    (st.decidedAt - base).total_seconds() / 86400.0, 0.0)
            elif (st.status == 'PENDING' and base
                  and st.order == first_open_order):
                b['open_now'] += 1
                age = (now - base).total_seconds() / 86400.0
                if (b['oldest_open_days'] is None
                        or age > b['oldest_open_days']):
                    b['oldest_open_days'] = age
    rows = []
    for b in stats.values():
        avg = (round(b['total_days'] / b['decided'], 1)
               if b['decided'] else None)
        oldest = (round(b['oldest_open_days'], 1)
                  if b['oldest_open_days'] is not None else None)
        # Ampel: bewertet die schlechtere der beiden Wartezeiten (bereits
        # verstrichene Ø-Wartezeit ODER das Alter des aeltesten offenen
        # Antrags). Schwellen bewusst konservativ; spaeter je Kunde
        # konfigurierbar (Gate).
        worst = max([v for v in (avg, oldest) if v is not None], default=None)
        if worst is None:
            level = 'none'
        elif worst <= 3:
            level = 'green'
        elif worst <= 7:
            level = 'amber'
        else:
            level = 'red'
        rows.append({
            'role': b['role'], 'decided': b['decided'], 'avg_days': avg,
            'open_now': b['open_now'], 'oldest_open_days': oldest,
            'level': level})
    rows.sort(key=lambda r: (r['avg_days'] is None, -(r['avg_days'] or 0)))
    return rows

