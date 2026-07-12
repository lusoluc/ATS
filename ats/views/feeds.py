"""SecurATS Views — Externe Feeds und Schnittstellen (Stepstone, BA-XML, SAP SF).

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import os
import json
import uuid
import logging
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from ..permissions import any_staff_required, recruiter_required, hr_admin_required
from ..permissions import scope_applications, scope_jobs, can_access_application
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from ..models import (
    Organization, Facility, FacilityProfile, Department, Location,
    JobFamily, ContactPerson, WorkflowState, JobTemplate, Benefit,
    JobPosting, Applicant, Application, Interview, InterviewSlot,
    Message, Page, AuditLog, AILearningSample, SystemSetting, AppWorkflowDef
, get_interview_kinds)
import os as _os
from django.http import FileResponse, Http404
from django.urls import reverse
from ..audit import write_audit
from ..models import (
    AuditLog, TalentPoolSubscription, ScreeningQuestion, RoleDelegation,
    ApplicantToken, ApplicationDocument,
)
from ..models import JobFamily, Location
from ..models import Interview, Message
from ..permissions import has_full_access
from ..models import JobTemplate
from django.utils.text import slugify
from ..models import MediaAsset
from django.contrib.auth.views import LoginView as AuthLoginView
from django.core.cache import cache

logger = logging.getLogger(__name__)

__all__ = ["feed_token_required", "stepstone_feed", "hr_ba_xml_feed", "sap_sf_mapper"]


def feed_token_required(view):
    """WP2/UC-NS-06: Erzwingt ein Feed-Token, sobald FEED_ACCESS_TOKEN gesetzt ist."""
    import hmac
    from functools import wraps
    from django.conf import settings

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
        xml_content += f"    <arbeitsort>\n"
        xml_content += f"      <ort><![CDATA[{job.location.city}]]></ort>\n"
        xml_content += f"      <plz>{job.location.postalCode or ''}</plz>\n"
        xml_content += f"      <strasse><![CDATA[{job.location.address or ''}]]></strasse>\n"
        xml_content += f"    </arbeitsort>\n"
        xml_content += f"    <veroeffentlichungsdatum>{job.createdAt.strftime('%Y-%m-%d')}</veroeffentlichungsdatum>\n"
        xml_content += "  </stellenangebot>\n"
    xml_content += "</ba_stellenangebote>"
    
    return HttpResponse(xml_content, content_type="application/xml")


@hr_admin_required
def sap_sf_mapper(request):
    """Renders the SAP SuccessFactors Field Mapper UI and serves as the sync broker."""
    if request.method == 'POST':
        # Handles a mock field synchronization
        mapping_data = request.POST.get('mapping_data', '{}')
        sync_target = request.POST.get('sync_target', 'MOCK_SAP_SANDBOX')
        
        # Simulate connecting to SAP SuccessFactors APIs, field transformation and sending data
        AuditLog.objects.create(
            action="SAP_SF_SYNC",
            metadataJson=json.dumps({"target": sync_target, "mapping": mapping_data})
        )
        return JsonResponse({
            'success': True,
            'message': 'Datenübertragung an SAP SuccessFactors erfolgreich simuliert.',
            'timestamp': timezone.now().isoformat(),
            'records_exported': Application.objects.filter(status='INVITED').count()
        })
        
    # GET: render mapping management page
    applications_to_sync = Application.objects.filter(status='INVITED').select_related('applicant', 'jobPosting')
    
    # Predefined target schema mapping
    sap_schema_fields = [
        {'id': 'sf_candidate_id', 'label': 'Candidate ID (UUID)', 'type': 'String'},
        {'id': 'sf_first_name', 'label': 'First Name', 'type': 'String'},
        {'id': 'sf_last_name', 'label': 'Last Name', 'type': 'String'},
        {'id': 'sf_email', 'label': 'E-Mail Address', 'type': 'String'},
        {'id': 'sf_job_req_id', 'label': 'Job Requisition ID', 'type': 'String'},
        {'id': 'sf_score_rating', 'label': 'AI Screening Rating', 'type': 'String'},
    ]
    
    context = {
        'applications': applications_to_sync,
        'sap_schema_fields': sap_schema_fields,
        'slug': 'sap-sf'
    }
    return render(request, 'sap_sf_mapper.html', context)
