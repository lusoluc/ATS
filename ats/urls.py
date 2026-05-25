from django.urls import path
from . import views

app_name = 'ats'

urlpatterns = [
    # Public Career Portal URLs
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<uuid:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<uuid:job_id>/bewerben/', views.bewerben, name='bewerben'),
    
    # Recruiter ATS Dashboard URLs
    path('recruiter/dashboard/', views.dashboard, name='dashboard'),
    path('recruiter/applications/<uuid:app_id>/update-status/', views.update_status, name='update_status'),
    path('recruiter/applications/<uuid:app_id>/add-note/', views.add_note, name='add_note'),
    path('recruiter/interviews/schedule/', views.schedule_interview, name='schedule_interview'),
    
    # API Feeds & Integrations
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
    path('recruiter/applications/<uuid:app_id>/toggle-learning/', views.toggle_learning_sample, name='toggle_learning_sample'),
    path('recruiter/sap-sf/', views.sap_sf_mapper, name='sap_sf_mapper'),
]

