"""SecurATS Views — Administration: Stammdaten, Workflows, Vorlagen, Import, Kanaele.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from ..audit import write_audit
from ..models import (
    Application,
    AppWorkflowDef,
    AuditLog,
    ContactPerson,
    Department,
    Facility,
    JobFamily,
    JobPosting,
    Location,
    ScreeningQuestion,
    SystemSetting,
    WorkflowState,
)
from ..permissions import any_staff_required, hr_admin_required
from .common import campaign_expired

logger = logging.getLogger(__name__)

__all__ = ["save_app_workflow", "save_workflow_state", "save_email_template", "save_system_setting", "screening_questions_view", "archive_screening_question", "categories_view", "archive_category", "locations_view", "archive_location", "contacts_manage", "import_view", "import_template_csv", "source_channels_view", "pay_bands_view", "archive_pay_band"]


@hr_admin_required
def save_app_workflow(request):
    """Creates or updates an AppWorkflowDef (specialized recruiting pipeline)."""
    if request.method == 'POST':
        workflow_id = request.POST.get('workflow_id')
        name = request.POST.get('name', '').strip()
        facility_id = request.POST.get('facility')

        location_ids = request.POST.getlist('locations')
        category_ids = request.POST.getlist('categories')
        job_ids = request.POST.getlist('jobs')
        steps = request.POST.getlist('steps')
        custom_actions_raw = request.POST.get('custom_actions_json', '').strip()

        custom_actions = []
        if custom_actions_raw:
            try:
                custom_actions = json.loads(custom_actions_raw)
            except Exception:
                custom_actions = []

        # Construct structured step objects containing automation actions
        structured_steps = []
        for step in steps:
            step_actions = []
            # Check if there is an explicit override in custom_actions
            for item in custom_actions:
                if isinstance(item, dict) and item.get('step', '').upper() == step.upper():
                    step_actions = item.get('actions', [])
                    break

            # Ohne ausdrueckliche Aktion: sinnvolle, WIRKSAME Vorbelegung.
            # (Frueher standen hier Phantasie-Aktionen wie AUTO_INVITE_INTERVIEW,
            # TRIGGER_PROCESS oder SEND_CONTRACT – die gab es nie, sie wurden
            # stillschweigend uebersprungen. Ein Admin sah "Vertrag senden" in
            # der Pipeline, und es passierte nichts. Jetzt werden nur Aktionen
            # vorbelegt, die tatsaechlich ausgefuehrt werden.)
            if not step_actions:
                if step.upper() == 'IN_REVIEW':
                    step_actions = [
                        {"type": "ADD_NOTE",
                         "text": "In Prüfung genommen."},
                    ]
                elif step.upper() == 'INVITED':
                    step_actions = [
                        {"type": "CREATE_TASK",
                         "title": "Gespräch terminieren und Unterlagen prüfen",
                         "role": "Recruiter", "due_days": 3},
                    ]
                elif step.upper() == 'REJECTED':
                    step_actions = [
                        {"type": "EMAIL_NOTIFICATION",
                         "recipient": "applicant", "template": "Absage"}
                    ]
                # NEW/andere: bewusst KEINE Vorbelegung – lieber nichts als
                # etwas, das nur so aussieht, als täte es etwas.

            structured_steps.append({
                "name": step,
                "state": step.upper(),
                "actions": step_actions
            })

        with transaction.atomic():
            facility = Facility.objects.filter(id=facility_id).first() if facility_id else None

            if workflow_id:
                wf = get_object_or_404(AppWorkflowDef, id=workflow_id)
                wf.name = name
                wf.facility = facility
                wf.locationIdsJson = json.dumps(location_ids)
                wf.categoryIdsJson = json.dumps(category_ids)
                wf.jobIdsJson = json.dumps(job_ids)
                wf.stepsJson = json.dumps(structured_steps)
                wf.save()
                action = "UPDATE_APP_WORKFLOW"
            else:
                wf = AppWorkflowDef.objects.create(
                    name=name,
                    facility=facility,
                    locationIdsJson=json.dumps(location_ids),
                    categoryIdsJson=json.dumps(category_ids),
                    jobIdsJson=json.dumps(job_ids),
                    stepsJson=json.dumps(structured_steps)
                )
                action = "CREATE_APP_WORKFLOW"

            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"workflowId": str(wf.id), "name": wf.name})
            )

        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_workflow_state(request):
    """Creates or updates a recruiting process WorkflowState."""
    if request.method == 'POST':
        state_id = request.POST.get('state_id')
        name = request.POST.get('name', '').strip().lower()
        description = request.POST.get('description', '').strip()

        with transaction.atomic():
            if state_id:
                state = get_object_or_404(WorkflowState, id=state_id)
                old_name = state.name
                state.name = name
                state.description = description
                state.save()
                action = "UPDATE_WORKFLOW_STATE"
                metadata = {"oldName": old_name, "newName": name}
            else:
                state = WorkflowState.objects.create(name=name, description=description)
                action = "CREATE_WORKFLOW_STATE"
                metadata = {"name": name}

            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps(metadata)
            )

        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_email_template(request):
    """Creates or updates an EmailTemplate."""
    from ..models import EmailTemplate
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        name = request.POST.get('name', '').strip()
        subject = request.POST.get('subject', '').strip()
        html_content = request.POST.get('html_content', '').strip()
        text_content = request.POST.get('text_content', '').strip()

        with transaction.atomic():
            if template_id:
                template = get_object_or_404(EmailTemplate, id=template_id)
                template.name = name
                template.subject = subject
                template.htmlContent = html_content
                template.textContent = text_content
                template.save()
                action = "UPDATE_EMAIL_TEMPLATE"
            else:
                template = EmailTemplate.objects.create(
                    name=name,
                    subject=subject,
                    htmlContent=html_content,
                    textContent=text_content
                )
                action = "CREATE_EMAIL_TEMPLATE"

            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"templateId": str(template.id), "name": template.name})
            )

        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


@hr_admin_required
def save_system_setting(request):
    """Creates or updates a SystemSetting (template variable)."""
    if request.method == 'POST':
        setting_id = request.POST.get('setting_id')
        key = request.POST.get('key', '').strip().upper()
        value = request.POST.get('value', '').strip()

        with transaction.atomic():
            if setting_id:
                setting = get_object_or_404(SystemSetting, id=setting_id)
                old_key = setting.key
                setting.key = key
                setting.value = value
                setting.save()
                action = "UPDATE_SYSTEM_SETTING"
                metadata = {"oldKey": old_key, "newKey": key}
            else:
                setting = SystemSetting.objects.create(key=key, value=value)
                action = "CREATE_SYSTEM_SETTING"
                metadata = {"key": key}

            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps(metadata)
            )

        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


# --- B15: Screening-Fragen-Bank --------------------------------------------
@hr_admin_required
def screening_questions_view(request):
    if request.method == "POST" and request.POST.get("form") == "minimum_builder":
        # Formular-Builder: HR pflegt Mindeststandards OHNE Technik-Vorwissen.
        # Aktionen add/save/delete/up/down je Frage; Speicherformat bleibt
        # dieselbe JSON-Liste (ensure_minimum_standards unveraendert).
        from ..questions import normalize_question, normalize_questions
        fam = get_object_or_404(JobFamily, id=request.POST.get("family_id"))
        try:
            qs = normalize_questions(json.loads(fam.minimumQuestionsJson or "[]"))
        except (ValueError, TypeError):
            qs = []
        action = request.POST.get("action", "")
        idx = request.POST.get("idx")
        idx = int(idx) if idx and idx.isdigit() else None
        if action == "add":
            q = normalize_question({
                "type": request.POST.get("q_type", "YES_NO"),
                "question": request.POST.get("q_question", ""),
                "isMandatory": True,  # Mindeststandard ist per Definition Pflicht
                "options": request.POST.get("q_options", ""),
                "expectedAnswer": request.POST.get("q_expected", ""),
            })
            if q:
                qs.append(q)
        elif action == "save" and idx is not None and idx < len(qs):
            q = normalize_question({
                "id": qs[idx]["id"],
                "type": request.POST.get("q_type", qs[idx]["type"]),
                "question": request.POST.get("q_question", ""),
                "isMandatory": True,
                "options": request.POST.get("q_options", ""),
                "expectedAnswer": request.POST.get("q_expected", ""),
            })
            if q:
                qs[idx] = q
        elif action == "up" and idx and idx < len(qs):
            qs[idx - 1], qs[idx] = qs[idx], qs[idx - 1]
        elif action == "down" and idx is not None and idx < len(qs) - 1:
            qs[idx + 1], qs[idx] = qs[idx], qs[idx + 1]
        elif action == "delete" and idx is not None and idx < len(qs):
            qs.pop(idx)
        # Entgelttransparenz (Art. 5 Abs. 2): Gehaltshistorie-Fragen fliegen
        # raus, bevor sie als Mindeststandard in jede Stelle wandern.
        from ..pay_transparency import PAY_HISTORY_MESSAGE, salary_history_violation
        blocked = [q for q in qs if salary_history_violation(str(q.get("question", "")))]
        if blocked:
            qs = [q for q in qs if q not in blocked]
            write_audit("PAY_HISTORY_QUESTION_BLOCKED", user=request.user,
                        family=fam.name,
                        removed=[q.get("question") for q in blocked])
            messages.warning(request, PAY_HISTORY_MESSAGE)
        fam.minimumQuestionsJson = json.dumps(qs, ensure_ascii=False)
        fam.save(update_fields=["minimumQuestionsJson"])
        write_audit("MINIMUM_STANDARD_CHANGED", user=request.user,
                    family=fam.name, count=len(qs), op=action)
        return redirect("ats:screening_questions")

    if request.method == "POST" and request.POST.get("form") == "minimum":
        # Vorstands-Mindeststandards je Jobfamilie (nur HR-Admin erreicht diese View)
        fam = get_object_or_404(JobFamily, id=request.POST.get("family_id"))
        raw = (request.POST.get("minimum_json") or "[]").strip() or "[]"
        try:
            parsed = json.loads(raw)
            assert isinstance(parsed, list)
        except (ValueError, AssertionError):
            questions = ScreeningQuestion.objects.filter(archived=False).order_by("-createdAt")
            return render(request, "screening_questions.html",
                          {"questions": questions,
                           "families": JobFamily.objects.filter(archived=False).order_by("name"),
                           "minimum_error": f"Ungültiges JSON für {fam.name} – nichts gespeichert."})
        from ..pay_transparency import PAY_HISTORY_MESSAGE, salary_history_violation
        blocked = [q for q in parsed if isinstance(q, dict)
                   and salary_history_violation(str(q.get("question", "")))]
        if blocked:
            parsed = [q for q in parsed if q not in blocked]
            write_audit("PAY_HISTORY_QUESTION_BLOCKED", user=request.user,
                        family=fam.name,
                        removed=[q.get("question") for q in blocked])
            messages.warning(request, PAY_HISTORY_MESSAGE)
        fam.minimumQuestionsJson = json.dumps(parsed, ensure_ascii=False)
        fam.save(update_fields=["minimumQuestionsJson"])
        write_audit("MINIMUM_STANDARD_CHANGED", user=request.user,
                    family=fam.name, count=len(parsed))
        return redirect("ats:screening_questions")
    if request.method == "POST":
        text = (request.POST.get("question") or "").strip()
        from ..pay_transparency import PAY_HISTORY_MESSAGE, salary_history_violation
        if text and salary_history_violation(text):
            write_audit("PAY_HISTORY_QUESTION_BLOCKED", user=request.user,
                        removed=[text])
            messages.error(request, PAY_HISTORY_MESSAGE)
        elif text:
            ScreeningQuestion.objects.create(question=text)
            write_audit("SCREENING_Q_ADDED", user=request.user)
        return redirect("ats:screening_questions")
    questions = ScreeningQuestion.objects.filter(archived=False).order_by("-createdAt")
    from ..questions import QUESTION_TYPES
    from ..questions import normalize_questions as _nq
    family_rows = []
    for f in JobFamily.objects.filter(archived=False).order_by("name"):
        try:
            fqs = _nq(json.loads(f.minimumQuestionsJson or "[]"))
        except (ValueError, TypeError):
            fqs = []
        rows = [{"i": i, "q": q,
                 "options_text": "\n".join(q.get("options", []))}
                for i, q in enumerate(fqs)]
        family_rows.append({"family": f, "questions": rows})
    return render(request, "screening_questions.html",
                  {"questions": questions,
                   "families": JobFamily.objects.filter(archived=False).order_by("name"),
                   "family_rows": family_rows,
                   "question_types": QUESTION_TYPES})


@hr_admin_required
def archive_screening_question(request, q_id):
    q = get_object_or_404(ScreeningQuestion, id=q_id)
    q.archived = True
    q.save()
    return redirect("ats:screening_questions")


@hr_admin_required
def categories_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            JobFamily.objects.create(name=name, description=(request.POST.get("description") or "").strip() or None)
        return redirect("ats:categories")
    families = JobFamily.objects.filter(archived=False).order_by("name")
    return render(request, "categories.html", {"families": families})


@hr_admin_required
def archive_category(request, cat_id):
    c = get_object_or_404(JobFamily, id=cat_id)
    c.archived = True
    c.save()
    return redirect("ats:categories")


# --- E1: Entgeltbänder (Entgelttransparenz, EU-RL 2023/970) -----------------
@hr_admin_required
def pay_bands_view(request):
    from decimal import Decimal, InvalidOperation

    from ..models import PayBand
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:120]
        try:
            min_amount = Decimal(request.POST.get("minAmount") or "")
            max_amount = Decimal(request.POST.get("maxAmount") or "")
        except InvalidOperation:
            min_amount = max_amount = None
        if name and min_amount is not None and max_amount is not None \
                and Decimal(0) <= min_amount <= max_amount:
            PayBand.objects.create(
                name=name,
                tariffSystem=(request.POST.get("tariffSystem") or "HAUSTARIF")[:30],
                minAmount=min_amount,
                maxAmount=max_amount,
                period=(request.POST.get("period") or "MONTH")[:10],
                collectiveAgreement=(request.POST.get("collectiveAgreement") or "").strip()[:255],
                note=(request.POST.get("note") or "").strip()[:255],
            )
            write_audit("PAY_BAND_CREATED", user=request.user, name=name)
        return redirect("ats:pay_bands")
    bands = PayBand.objects.filter(archived=False).order_by("tariffSystem", "name")
    return render(request, "pay_bands.html",
                  {"bands": bands,
                   "tariff_systems": PayBand.TARIFF_SYSTEMS,
                   "periods": PayBand.PERIODS})


@hr_admin_required
def archive_pay_band(request, band_id):
    from ..models import PayBand
    band = get_object_or_404(PayBand, id=band_id)
    band.archived = True
    band.save(update_fields=["archived"])
    write_audit("PAY_BAND_ARCHIVED", user=request.user, name=band.name)
    return redirect("ats:pay_bands")


# --- B14: Standorte ---------------------------------------------------------
@hr_admin_required
def locations_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            Location.objects.create(
                name=name,
                address=(request.POST.get("address") or "").strip() or None,
                city=(request.POST.get("city") or "").strip() or None,
                postalCode=(request.POST.get("postalCode") or "").strip() or None,
            )
        return redirect("ats:locations")
    locations = Location.objects.filter(archived=False).order_by("name")
    return render(request, "locations.html", {"locations": locations})


@hr_admin_required
def archive_location(request, loc_id):
    loc = get_object_or_404(Location, id=loc_id)
    loc.archived = True
    loc.save()
    return redirect("ats:locations")


@hr_admin_required
def contacts_manage(request):
    """Zentrale Ansprechpartner-Pflege (UC-SB-12ff).

    Kernprinzip: ContactPerson ist FK an der Stellenanzeige – Änderungen hier
    (Telefon, Foto, Rolle) wirken SOFORT auf allen Anzeigen. Zusätzlich:
    - Zuordnung je Einrichtung/Abteilung (Vorauswahl-Hilfe),
    - „Überall ersetzen": Person A → B in allen Anzeigen (Urlaub/Ausscheiden).
    """
    from ..models import DepartmentContactPerson, FacilityContactPerson

    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        if action == 'replace_everywhere':
            old_id = request.POST.get('old_id')
            new_id = request.POST.get('new_id')
            old = ContactPerson.objects.filter(id=old_id).first()
            new = ContactPerson.objects.filter(id=new_id).first()
            if old and new and old.id != new.id:
                n = JobPosting.objects.filter(contactPerson=old).update(contactPerson=new)
                write_audit("CONTACT_REPLACED", user=request.user,
                            old=str(old), new=str(new), jobs_updated=n)
            return redirect('ats:contacts')

        if action == 'delete':
            cp = ContactPerson.objects.filter(id=request.POST.get('cp_id')).first()
            if cp:
                in_use = JobPosting.objects.filter(contactPerson=cp).count()
                if in_use == 0:
                    cp.delete()
                # in Verwendung -> nicht löschen; UI verweist auf „Ersetzen"
            return redirect('ats:contacts')

        if action == 'assign':
            cp = ContactPerson.objects.filter(id=request.POST.get('cp_id')).first()
            fac_id = request.POST.get('facility') or None
            dep_id = request.POST.get('department') or None
            role = (request.POST.get('roleTitle') or '').strip()[:150]
            if cp and fac_id:
                FacilityContactPerson.objects.get_or_create(
                    facility_id=fac_id, contactPerson=cp, defaults={'roleTitle': role})
            if cp and dep_id:
                DepartmentContactPerson.objects.get_or_create(
                    department_id=dep_id, contactPerson=cp, defaults={'roleTitle': role})
            return redirect('ats:contacts')

        # save (anlegen oder aktualisieren)
        cp_id = request.POST.get('cp_id') or None
        fields = {
            'firstName': (request.POST.get('firstName') or '').strip()[:100],
            'lastName': (request.POST.get('lastName') or '').strip()[:100],
            'email': (request.POST.get('email') or '').strip()[:254],
            'phone': (request.POST.get('phone') or '').strip()[:50] or None,
            'globalJobTitle': (request.POST.get('globalJobTitle') or '').strip()[:150] or None,
            'photoUrl': (request.POST.get('photoUrl') or '').strip()[:255] or None,
            'quote': (request.POST.get('quote') or '').strip() or None,
        }
        if fields['firstName'] and fields['lastName'] and fields['email']:
            if cp_id:
                ContactPerson.objects.filter(id=cp_id).update(**fields)
            else:
                ContactPerson.objects.create(**fields)
        return redirect('ats:contacts')

    contacts = []
    for cp in ContactPerson.objects.order_by('lastName', 'firstName'):
        contacts.append({
            'obj': cp,
            'facilities': [link.facility.name for link in cp.facility_links.select_related('facility')],
            'departments': [link.department.name for link in cp.department_links.select_related('department')],
            'jobs_count': JobPosting.objects.filter(contactPerson=cp).count(),
        })
    return render(request, 'contacts.html', {
        'contacts': contacts,
        'facilities': Facility.objects.order_by('name'),
        'departments': Department.objects.order_by('name'),
        'all_contacts': ContactPerson.objects.order_by('lastName'),
    })


# --- P0.5: CSV-Bewerberdaten-Import (Migrationsbrücke) ------------------------
@hr_admin_required
def import_view(request):
    """Bestandsbewerber aus CSV/Excel-Export importieren – mit Testlauf zuerst."""
    from ..importer import parse_csv, run_import
    report, fatal = None, None

    if request.method == 'POST':
        f = request.FILES.get('csv_file')
        action = request.POST.get('action', 'preview')
        default_job = None
        if request.POST.get('default_job'):
            default_job = JobPosting.objects.filter(id=request.POST['default_job']).first()
        if request.POST.get('form') == 'cv_zip':
            from ..importer import match_cv_files
            zf = request.FILES.get('zip_file')
            if not zf:
                fatal = "Bitte eine ZIP-Datei auswählen."
            elif zf.size > 50 * 1024 * 1024:
                fatal = "ZIP größer als 50 MB – bitte aufteilen."
            else:
                dry = action != 'import'
                cv_report = match_cv_files(zf.read(), dry_run=dry)
                if not dry:
                    write_audit("CV_IMPORT", user=request.user,
                                files=cv_report["total"],
                                attached=cv_report["attached"],
                                unmatched=len(cv_report["unmatched"]))
                jobs = JobPosting.objects.select_related('location').order_by('title')
                return render(request, 'import.html', {
                    'cv_report': cv_report, 'cv_dry': dry,
                    'fatal': fatal, 'jobs': jobs})
        if not f:
            fatal = "Bitte eine CSV- oder Excel-Datei auswählen."
        elif f.size > 5 * 1024 * 1024:
            fatal = "Datei größer als 5 MB – bitte aufteilen."
        elif f.name.lower().endswith(('.xlsx', '.xlsm')):
            from ..importer import HEADER_ALIASES, _map_headers, detect_headers, parse_xlsx
            data = f.read()
            overrides = {field: request.POST[f'map_{field}']
                         for field in HEADER_ALIASES
                         if request.POST.get(f'map_{field}')}
            rows, fatal = parse_xlsx(data, overrides=overrides)
            detected_headers = detect_headers(data, is_xlsx=True)
            mapping_now = _map_headers(detected_headers, overrides)
        else:
            from ..importer import HEADER_ALIASES, _map_headers, detect_headers
            data = f.read()
            overrides = {field: request.POST[f'map_{field}']
                         for field in HEADER_ALIASES
                         if request.POST.get(f'map_{field}')}
            rows, fatal = parse_csv(data, overrides=overrides)
            detected_headers = detect_headers(data)
            mapping_now = _map_headers(detected_headers, overrides)
        if f and not fatal:
            dry_run = action != 'import'
            report = run_import(rows, default_job=default_job, dry_run=dry_run)
            if not dry_run:
                write_audit("DATA_IMPORT", user=request.user,
                            rows=report["total"],
                            applications_created=report["applications_created"],
                            applicants_new=report["applicants_new"],
                            skipped=report["skipped_existing"],
                            errors=len(report["errors"]))

    mapping_rows, unmapped = [], []
    if 'detected_headers' in locals() and detected_headers:
        from ..importer import HEADER_ALIASES as _HA
        FIELD_LABELS = {"first_name": "Vorname", "last_name": "Nachname",
                        "email": "E-Mail", "phone": "Telefon",
                        "address": "Adresse", "job": "Stelle",
                        "status": "Status", "source": "Quelle",
                        "notes": "Notizen", "created": "Bewerbungsdatum"}
        for field in _HA:
            mapping_rows.append({
                'field': field,
                'label': FIELD_LABELS.get(field, field),
                'current': mapping_now.get(field, ''),
                'required': field in ('first_name', 'last_name', 'email')})
        unmapped = [h for h in detected_headers
                    if h not in mapping_now.values()]
    else:
        detected_headers = []
    jobs = JobPosting.objects.select_related('location').order_by('title')
    return render(request, 'import.html', {
        'mapping_rows': mapping_rows,
        'detected_headers': detected_headers,
        'unmapped_headers': unmapped,
        'report': report, 'fatal': fatal, 'jobs': jobs,
    })


@hr_admin_required
def import_template_csv(request):
    """Beispiel-/Vorlagendatei zum Ausfüllen (Excel-kompatibel, Semikolon, BOM)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="securats-import-vorlage.csv"'
    response.write('\ufeff')
    response.write("Vorname;Nachname;E-Mail;Telefon;Stelle;Status;Quelle;Datum;Notiz\r\n")
    response.write("Max;Mustermann;max@beispiel.de;030-123456;Pflegefachkraft Station 3;"
                   "neu;STEPSTONE;15.03.2026;Aus Altsystem übernommen\r\n")
    return response


@any_staff_required
def source_channels_view(request):
    """Kanaele & Kampagnen: Jobmesse-Frage beantworten mit Zahlen.

    Kanal anlegen → Link + QR-Code (fuer Aufsteller/Flyer) → jede Bewerbung
    traegt die Quelle → Kennzahlen zeigen Menge UND Qualitaet: Bewerbungen,
    davon in Sichtung+, eingeladen, Einladungsquote. "Erfolgreich" heisst
    nicht viele Bewerbungen, sondern Bewerbungen, die weiterkommen.
    """
    from ..models import SourceChannel
    if request.method == 'POST' and request.POST.get('form') == 'cost':
        # Strukturierte Kampagnenkosten: speist "Kosten je Einstellung" direkt
        from decimal import Decimal, InvalidOperation
        ch = get_object_or_404(SourceChannel, id=request.POST.get('ch_id'))
        raw = (request.POST.get('cost') or '').strip()
        raw = raw.replace('.', '').replace(',', '.') if ',' in raw else raw
        try:
            ch.costAmount = Decimal(raw) if raw else None
            if ch.costAmount is not None and ch.costAmount < 0:
                raise InvalidOperation
        except InvalidOperation:
            return redirect('ats:source_channels')
        ch.save(update_fields=['costAmount'])
        write_audit('SOURCE_CHANNEL_COST_SET', user=request.user,
                    slug=ch.slug, cost=str(ch.costAmount))
        return redirect('ats:source_channels')

    if request.method == 'POST' and request.POST.get('form') == 'expiry':
        # Kampagnen-Ablaufdatum: leer = laeuft unbegrenzt; Datum wirkt bis
        # einschliesslich Tagesende (QR bleibt bis 23:59 des Tages gueltig).
        from ..models import SourceChannel
        obj = get_object_or_404(SourceChannel, id=request.POST.get('ch_id'))
        raw = (request.POST.get('expires') or '').strip()
        if raw:
            try:
                d = datetime.date.fromisoformat(raw)
            except ValueError:
                return redirect('ats:source_channels')
            obj.expiresAt = timezone.make_aware(
                datetime.datetime.combine(d, datetime.time(23, 59)))
        else:
            obj.expiresAt = None
        obj.save(update_fields=['expiresAt'])
        write_audit('SOURCE_CHANNEL_EXPIRY_SET', user=request.user,
                    name=obj.name, expires=raw or 'unbegrenzt')
        return redirect('ats:source_channels')

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:120]
        note = (request.POST.get('note') or '').strip()[:255]
        if name:
            base = slugify(name).replace('-', '_').upper()[:40] or 'KANAL'
            slug, n = base, 2
            while SourceChannel.objects.filter(slug=slug).exists():
                slug, n = f"{base}_{n}", n + 1
            SourceChannel.objects.create(name=name, slug=slug, note=note)
            write_audit('SOURCE_CHANNEL_CREATED', user=request.user,
                        name=name, slug=slug)
        return redirect('ats:source_channels')

    import segno
    base_url = request.build_absolute_uri('/jobs/')
    rows = []
    for ch in SourceChannel.objects.order_by('-createdAt'):
        ch.is_expired = campaign_expired(ch)
        link = f"{base_url}?src={ch.slug}"
        qr = segno.make(link, error='m')
        qr_uri = qr.svg_data_uri(scale=3)
        apps = Application.objects.filter(source=ch.slug,
                                          createdAt__gte=ch.createdAt)
        total = apps.count()
        progressed = apps.exclude(status='NEW').count()
        invited = apps.filter(status__in=['INVITED', 'HIRED']).count()
        hired_qs = apps.filter(status='HIRED', hiredAt__isnull=False)
        hired = hired_qs.count()
        days = [ (a.hiredAt - a.createdAt).days for a in hired_qs ]
        avg_days_to_hire = round(sum(days) / len(days), 1) if days else None
        rows.append({
            'ch': ch, 'link': link, 'qr': qr_uri, 'total': total,
            'progressed': progressed, 'invited': invited,
            'hired': hired, 'days': avg_days_to_hire,
            'cost_per_hire': (round(float(ch.costAmount) / hired)
                              if ch.costAmount and hired else None),
            'quote': round(100 * invited / total) if total else None,
        })
    from django.db.models import Count
    # Freie Quellen (Import/Direkteingabe) mit in die Auswertung
    known = {r['ch'].slug for r in rows}
    freie = (Application.objects.exclude(source__in=known | {''})
             .values('source').annotate(c=Count('id')).order_by('-c')[:10])
    freie_rows = []
    for f in freie:
        invited = Application.objects.filter(source=f['source'],
                                             status='INVITED').count()
        freie_rows.append({'source': f['source'], 'total': f['c'],
                           'invited': invited,
                           'quote': round(100 * invited / f['c'])})
    return render(request, 'source_channels.html',
                  {'rows': rows, 'freie': freie_rows})
