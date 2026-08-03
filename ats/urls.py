from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'ats'

urlpatterns = [
    # Authentifizierung (Recruiter/Admin)
    path('recruiter/login/', views.SafeLoginView.as_view(), name='login'),
    path('recruiter/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Public Career Portal URLs
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('k/<slug:slug>/', views.landing_page, name='landing_page'),
    path('jobs/<uuid:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<uuid:job_id>/bewerben/', views.bewerben, name='bewerben'),
    path('bewerber/<str:token>/', views.candidate_portal, name='candidate_portal'),  # B4 Magic-Link
    path('ki-transparenz/', views.ai_transparency, name='ai_transparency'),  # N3 Art. 86 EU AI Act

    # Recruiter ATS Dashboard URLs
    path('recruiter/dashboard/', views.dashboard, name='dashboard'),
    path('recruiter/suche/', views.global_search, name='global_search'),  # B1
    path('recruiter/applications/<uuid:app_id>/update-status/', views.update_status, name='update_status'),
    path('recruiter/applications/<uuid:app_id>/add-note/', views.add_note, name='add_note'),
    path('recruiter/interviews/schedule/', views.schedule_interview, name='schedule_interview'),
    path('recruiter/interviews/round/<uuid:app_id>/', views.advance_interview_round, name='advance_interview_round'),
    path('recruiter/interviews/feedback/<uuid:app_id>/', views.save_interview_feedback, name='save_interview_feedback'),
    path('recruiter/applications/<uuid:app_id>/feedback.json', views.application_feedback_json, name='application_feedback_json'),
    path('recruiter/messages/polish/', views.polish_message, name='polish_message'),
    path('recruiter/process/suggest/', views.suggest_process, name='suggest_process'),
    path('recruiter/process/previous/', views.process_previous, name='process_previous'),
    path('recruiter/applications/<uuid:app_id>/vote/', views.application_vote, name='application_vote'),
    path('recruiter/gremien/', views.panel_defaults_view, name='panel_defaults'),
    path('recruiter/panel/preview/', views.panel_preview, name='panel_preview'),
    path('recruiter/branding/', views.branding_view, name='branding'),
    path('recruiter/kanaele/', views.source_channels_view, name='source_channels'),
    path('recruiter/landingpages/', views.landing_pages_manage, name='landing_pages'),
    path('recruiter/baukasten/<str:kind>/<uuid:obj_id>/', views.blocks_editor, name='blocks_editor'),
    path('recruiter/interview-formate/', views.interview_formats_manage, name='interview_formats'),

    # B2: Verwaltungs-Bereiche als eigene Seiten (frueher Tabs im Dashboard).
    # Alle sechs sind serverseitig auf HR-Admin beschraenkt.
    path('recruiter/kpis/', views.stats_page, name='stats_page'),
    path('recruiter/prozess-flow/', views.process_page, name='process_page'),
    path('recruiter/email-vorlagen/', views.templates_page, name='templates_page'),
    path('recruiter/cms/', views.cms_page, name='cms_page'),
    path('recruiter/ki-zentrale/', views.ki_page, name='ki_page'),
    path('recruiter/ki-zentrale/auto-antwort/', views.save_auto_reply_settings, name='save_auto_reply_settings'),
    path('recruiter/lernendes-scoring/', views.learned_scoring_view, name='learned_scoring'),  # L3
    path('recruiter/lernendes-scoring/speichern/', views.save_learned_scoring_settings, name='save_learned_scoring'),
    path('recruiter/hris/', views.hris_page, name='hris_page'),
    path('recruiter/datenaufbewahrung/', views.retention_page, name='retention'),  # P4

    # API Feeds & Integrations
    path('healthz/', views.healthz, name='healthz'),  # WP7
    path('healthz/ai/', views.healthz_ai, name='healthz_ai'),
    path('api/v1/integrations/stepstone/', views.stepstone_feed, name='stepstone_feed'),
    path('api/v1/integrations/hr-ba-xml/', views.hr_ba_xml_feed, name='hr_ba_xml_feed'),
    # Recruiter Dashboard & Gemma AI CRUD Operations
    path('recruiter/jobs/create/', views.create_job, name='create_job'),
    path('recruiter/pages/save/', views.save_page, name='save_page'),
    path('recruiter/workflows/save/', views.save_workflow_state, name='save_workflow_state'),
    path('recruiter/workflows/definition/save/', views.save_app_workflow, name='save_app_workflow'),
    path('recruiter/templates/email/save/', views.save_email_template, name='save_email_template'),
    path('recruiter/settings/save/', views.save_system_setting, name='save_system_setting'),
    path('recruiter/ki/test/', views.test_gemma, name='test_gemma'),
    path('recruiter/ki/agg-check/', views.gemma_agg_check, name='gemma_agg_check'),
    path('recruiter/ki/agg-check/status/<uuid:task_id>/', views.gemma_agg_check_status, name='gemma_agg_check_status'),
    path('recruiter/ki/simple-german/', views.gemma_translate_simple_german, name='gemma_translate_simple_german'),
    path('recruiter/ki/settings/save/', views.save_ai_settings, name='save_ai_settings'),
    path('recruiter/ki/logs/', views.get_ai_execution_logs, name='get_ai_execution_logs'),
    path('recruiter/ki/validate-prompt/', views.validate_ai_prompt, name='validate_ai_prompt'),
    path('recruiter/ki/validate-prompt/status/<uuid:task_id>/', views.validate_ai_prompt_status, name='validate_ai_prompt_status'),
    path('recruiter/sap-sf/', views.sap_sf_mapper, name='sap_sf_mapper'),

    # Backlog-Features (siehe FEATURE_BACKLOG.md)
    path('recruiter/board/reorder/', views.reorder_board, name='reorder_board'),  # B10
    path('recruiter/board/bulk-status/', views.bulk_update_status, name='bulk_update_status'),  # WP4
    path('recruiter/applications/<uuid:app_id>/cv/', views.download_cv, name='download_cv'),      # B1
    path('recruiter/documents/<uuid:doc_id>/', views.download_document, name='download_document'),  # WP1
    path('recruiter/audit/', views.audit_log_view, name='audit_log'),
    path('recruiter/approvals/', views.approvals_inbox, name='approvals'),  # WP6
    path('recruiter/governance/', views.governance_view, name='governance'),  # WP6                              # B2
    path('recruiter/governance/roi-export.csv', views.roi_export, name='roi_export'),  # P5
    path('recruiter/talent-pool/', views.talent_pool_view, name='talent_pool'),
    path('recruiter/jobs/<uuid:job_id>/talent-pool/', views.job_pool_matches, name='job_pool_matches'),  # C3
    path('recruiter/applications/<uuid:app_id>/verlauf/', views.application_timeline, name='application_timeline'),  # Aktionsverlauf
    path('recruiter/jobs/<uuid:job_id>/verlauf/', views.job_timeline, name='job_timeline'),  # Aktionsverlauf
    path('recruiter/jobs/<uuid:job_id>/serien-nachricht/', views.job_series_message, name='job_series_message'),  # P3
    path('recruiter/aufgaben/', views.tasks_view, name='tasks'),   # Automatik-Aufgaben                    # B11
    path('recruiter/screening-questions/', views.screening_questions_view, name='screening_questions'),  # B15
    path('recruiter/screening-questions/<uuid:q_id>/archive/', views.archive_screening_question, name='archive_screening_question'),
    path('recruiter/delegations/', views.delegations_view, name='delegations'),                    # B8
    path('recruiter/categories/', views.categories_view, name='categories'),                        # B13
    path('recruiter/categories/<uuid:cat_id>/archive/', views.archive_category, name='archive_category'),
    path('recruiter/pay-bands/', views.pay_bands_view, name='pay_bands'),                            # E1 Entgelttransparenz
    path('recruiter/pay-bands/<uuid:band_id>/archive/', views.archive_pay_band, name='archive_pay_band'),
    path('recruiter/locations/', views.locations_view, name='locations'),
    path('recruiter/contacts/', views.contacts_manage, name='contacts'),
    path('recruiter/import/', views.import_view, name='data_import'),  # P0.5
    path('recruiter/import/vorlage.csv', views.import_template_csv, name='import_template'),
    path('recruiter/snippets/', views.snippets_manage, name='snippets'),
    path('recruiter/best-performers/ingest/', views.ingest_best_performers, name='ingest_best_performers'),
    path('recruiter/best-performers/', views.best_performer_profiles, name='best_performer_profiles'),
    path('recruiter/jobs/<uuid:job_id>/toggle/', views.toggle_job_active, name='toggle_job_active'),                           # B14
    path('recruiter/jobs/<uuid:job_id>/frage-hinweise/', views.job_question_hints, name='job_question_hints'),  # L1-4
    path('recruiter/locations/<uuid:loc_id>/archive/', views.archive_location, name='archive_location'),
    path('recruiter/interviews/', views.interviews_view, name='interviews'),                        # B9
    path('recruiter/interviews/slots/', views.slot_create, name='slot_create'),
    path('recruiter/interviews/slots/<uuid:slot_id>/delete/', views.slot_delete, name='slot_delete'),
    path('recruiter/interviews/export.ics', views.interviews_ics, name='interviews_ics'),
    path('recruiter/interviews/<uuid:interview_id>/outcome/', views.interview_outcome, name='interview_outcome'),
    path('recruiter/audit/export.csv', views.audit_export, name='audit_export'),
    path('recruiter/bedarf/', views.staffing_requests_view, name='staffing_requests'),
    path('recruiter/applications/<uuid:app_id>/messages/', views.application_messages, name='application_messages'),  # B6
    path('recruiter/applications/<uuid:app_id>/draft-reply/', views.draft_reply, name='draft_reply'),  # C4
    path('recruiter/applications/<uuid:app_id>/steckbrief.json', views.application_summary, name='application_summary'),  # L2
    path('recruiter/postfach/', views.inbox_view, name='inbox'),  # Sammel-Postfach
    path('recruiter/postfach/sammel-antwort/', views.batch_reply, name='batch_reply'),
    path('recruiter/postfach/baustein-speichern/', views.save_reply_snippet, name='save_reply_snippet'),
    path('recruiter/postfach/anliegen-aendern/', views.reclassify_message, name='reclassify_message'),
    path('job-alert/', views.job_alert_subscribe, name='job_alert'),
    path('preise/', views.pricing_view, name='pricing'),  # P0.3 (nur DEMO_MODE)
    path('job-alert/confirm/<str:token>/', views.job_alert_confirm, name='job_alert_confirm'),
    path('job-alert/manage/<str:token>/', views.job_alert_manage, name='job_alert_manage'),
    path('einrichtung/<slug:slug>/', views.facility_profile, name='facility_profile'),  # WP8                                # B5 (public)
    path('recruiter/job-templates/', views.job_templates_view, name='job_templates'),               # B12
    path('recruiter/job-templates/<uuid:tpl_id>/delete/', views.delete_job_template, name='delete_job_template'),
    path('recruiter/job-templates/<uuid:tpl_id>/', views.job_template_detail, name='job_template_detail'),
    path('recruiter/job-templates/<uuid:tpl_id>/restore/', views.restore_job_template, name='restore_job_template'),
    path('recruiter/jobs/<uuid:job_id>/update-template/', views.update_job_posting_template, name='update_job_posting_template'),
    path('recruiter/analytics/', views.analytics_view, name='analytics'),
    path('recruiter/analytics/export.csv', views.analytics_export, name='analytics_export'),  # WP5
    path('recruiter/analytics/ask/', views.analytics_ask, name='analytics_ask'),  # WP5                            # B7
    path('pages/<slug:slug>/', views.page_detail, name='page_detail'),                                # B17 (public)
    path('recruiter/pages/', views.pages_manage, name='pages_manage'),                               # B16
    path('recruiter/pages/<uuid:page_id>/delete/', views.delete_page, name='delete_page'),
    path('recruiter/media/', views.media_manage, name='media_manage'),                                # B18
    path('recruiter/media/<uuid:asset_id>/delete/', views.delete_media, name='delete_media'),
    path('recruiter/job-templates/tone/', views.apply_template_tone, name='apply_template_tone'),     # B12
]

