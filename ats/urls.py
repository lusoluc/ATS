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
    path('integrations/sap-sf/', views.sap_sf_mapper, name='sap_sf_mapper'),
]
