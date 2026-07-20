"""SecurATS Views — Externe Feeds und Schnittstellen (Stepstone, BA-XML, SAP SF).

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import json
import logging
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from ..audit import write_audit
from ..models import (
    Application,
    JobPosting,
    SystemSetting,
)
from ..permissions import (
    hr_admin_required,
)

logger = logging.getLogger(__name__)

__all__ = ["feed_token_required", "stepstone_feed", "hr_ba_xml_feed", "sap_sf_mapper"]


def feed_token_required(view):
    """WP2/UC-NS-06: Erzwingt ein Feed-Token, sobald FEED_ACCESS_TOKEN gesetzt ist."""
    import hmac
    from functools import wraps

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        token = getattr(settings, 'FEED_ACCESS_TOKEN', '') or ''
        if token:
            provided = request.GET.get('token') or request.headers.get('X-Feed-Token', '') or ''
            if not hmac.compare_digest(str(provided), str(token)):
                logger.warning("Feed-Zugriff ohne gültiges Token von %s",
                               request.META.get('REMOTE_ADDR', '?'))
                return HttpResponse("Forbidden", status=403)
        return view(request, *args, **kwargs)
    return _wrapped


@feed_token_required
def stepstone_feed(request):
    """Generates the multiposter StepStone XML feed of active job postings."""
    jobs = JobPosting.objects.filter(workflowState__name="published").select_related('location', 'facility', 'organization')

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<stepstone_jobs>\n'
    for job in jobs:
        xml_content += f"  <job id=\"{job.id}\">\n"
        xml_content += f"    <title><![CDATA[{job.title}]]></title>\n"
        xml_content += f"    <company><![CDATA[{job.organization.name}]]></company>\n"
        xml_content += f"    <location><![CDATA[{job.location.name}, {job.location.city}]]></location>\n"
        xml_content += f"    <description><![CDATA[{job.description or ''}]]></description>\n"
        xml_content += f"    <created_at>{job.createdAt.isoformat()}</created_at>\n"
        xml_content += "  </job>\n"
    xml_content += "</stepstone_jobs>"

    return HttpResponse(xml_content, content_type="application/xml")


@feed_token_required
def hr_ba_xml_feed(request):
    """Generates the official HR-BA-XML feed (Bundesagentur für Arbeit) for automatic syndication."""
    jobs = JobPosting.objects.filter(workflowState__name="published").select_related('location', 'facility', 'organization')

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<ba_stellenangebote>\n'
    for job in jobs:
        xml_content += f"  <stellenangebot id=\"{job.id}\">\n"
        xml_content += f"    <arbeitgeber><![CDATA[{job.organization.name}]]></arbeitgeber>\n"
        xml_content += f"    <beruf><![CDATA[{job.title}]]></beruf>\n"
        xml_content += "    <arbeitsort>\n"
        xml_content += f"      <ort><![CDATA[{job.location.city}]]></ort>\n"
        xml_content += f"      <plz>{job.location.postalCode or ''}</plz>\n"
        xml_content += f"      <strasse><![CDATA[{job.location.address or ''}]]></strasse>\n"
        xml_content += "    </arbeitsort>\n"
        xml_content += f"    <veroeffentlichungsdatum>{job.createdAt.strftime('%Y-%m-%d')}</veroeffentlichungsdatum>\n"
        xml_content += "  </stellenangebot>\n"
    xml_content += "</ba_stellenangebote>"

    return HttpResponse(xml_content, content_type="application/xml")


@hr_admin_required
def sap_sf_mapper(request):
    """Feldzuordnung für den HRIS-/SAP-Export.

    EHRLICHKEIT: Diese Seite überträgt KEINE Daten. Sie war früher ein
    Blender – der POST tat nichts, meldete aber "Synchronisation
    erfolgreich", zählte "exportierte Bewerbersätze" und die Oberfläche gab
    einen frei erfundenen "SAP Response-Code: 201 Created" aus. Ein
    Interessent hätte in der Demo geglaubt, die SAP-Anbindung funktioniere.

    Jetzt: Hier wird die Feldzuordnung GESPEICHERT (SystemSetting
    HRIS_FIELD_MAPPING). Die tatsächliche Übertragung übernimmt der Befehl
    `hris_export` – und nur, wenn ein echter Endpunkt (HRIS_ENDPOINT)
    konfiguriert ist.
    """

    if request.method == 'POST':
        mapping_raw = request.POST.get('mapping_data', '{}')
        try:
            mapping = json.loads(mapping_raw)
            if not isinstance(mapping, dict):
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({'success': False,
                                 'error': 'Ungültige Zuordnung.'}, status=400)

        SystemSetting.objects.update_or_create(
            key='HRIS_FIELD_MAPPING',
            defaults={'value': json.dumps(mapping)})
        write_audit('HRIS_MAPPING_SAVED', user=request.user,
                    fields=len(mapping))

        endpoint_set = bool(os.environ.get('HRIS_ENDPOINT', '').strip())
        return JsonResponse({
            'success': True,
            'saved_fields': len(mapping),
            'endpoint_configured': endpoint_set,
            # Klartext statt Schein-Erfolg:
            'message': (
                'Feldzuordnung gespeichert. Es wurden KEINE Daten übertragen. '
                + ('Die Übertragung erfolgt über den Befehl "hris_export".'
                   if endpoint_set else
                   'Für eine echte Übertragung muss HRIS_ENDPOINT gesetzt sein '
                   '(derzeit nicht konfiguriert).')),
        })

    # GET: Zuordnungs-Oberfläche
    applications_to_sync = (Application.objects.filter(status='INVITED')
                            .select_related('applicant', 'jobPosting'))
    sap_schema_fields = [
        {'id': 'sf_candidate_id', 'label': 'Candidate ID (UUID)', 'type': 'String'},
        {'id': 'sf_first_name', 'label': 'First Name', 'type': 'String'},
        {'id': 'sf_last_name', 'label': 'Last Name', 'type': 'String'},
        {'id': 'sf_email', 'label': 'E-Mail Address', 'type': 'String'},
        {'id': 'sf_job_req_id', 'label': 'Job Requisition ID', 'type': 'String'},
        {'id': 'sf_score_rating', 'label': 'AI Screening Rating', 'type': 'String'},
    ]
    saved = SystemSetting.objects.filter(key='HRIS_FIELD_MAPPING').first()
    context = {
        'applications': applications_to_sync,
        'sap_schema_fields': sap_schema_fields,
        'saved_mapping_json': saved.value if saved else '{}',
        'endpoint_configured': bool(os.environ.get('HRIS_ENDPOINT', '').strip()),
        'slug': 'sap-sf'
    }
    return render(request, 'sap_sf_mapper.html', context)
