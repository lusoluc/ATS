from django.contrib import admin
from .models import (
    Organization, Facility, FacilityProfile, Department, Location,
    JobFamily, CareerPath, ContactPerson, FacilityContactPerson, DepartmentContactPerson,
    WorkflowState, PrivacyNoticeVersion, Role, User, UserFacility,
    JobTemplate, Benefit, TextSnippet, JobPosting, WorkflowDefinition,
    ApprovalTicket, ApprovalStep, Applicant, ApplicantToken, Application,
    AppWorkflowDef, AppTicket, AppStep, Interview, InterviewSlot,
    Message, TalentPoolSubscription, Page, JobAlertSubscription, JobAlertLog,
    SystemSetting, EmailTemplate, ScreeningQuestion, RoleDelegation,
    AuditLog, AILearningSample
)

# 1. Organization & Facilities
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'createdAt', 'updatedAt')
    search_fields = ('name',)

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_editable = ('requiresApproval', 'approvalChain')
    list_display = ('name', 'organization', 'createdAt', 'requiresApproval', 'approvalChain')
    search_fields = ('name', 'organization__name')

@admin.register(FacilityProfile)
class FacilityProfileAdmin(admin.ModelAdmin):
    list_display = ('facility', 'slug', 'createdAt')
    search_fields = ('facility__name', 'slug')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'facility', 'createdAt')
    search_fields = ('name', 'facility__name')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'postalCode', 'archived')
    list_filter = ('archived', 'city')
    search_fields = ('name', 'city', 'postalCode')

# 2. Jobs
@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'facility', 'location', 'workflowState', 'createdAt')
    list_filter = ('workflowState', 'location', 'facility')
    search_fields = ('title', 'description')

@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)

# 3. Applicants & Applications
@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('firstName', 'lastName', 'email', 'createdAt')
    search_fields = ('email',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'jobPosting', 'status', 'aiScore', 'createdAt')
    list_filter = ('status', 'aiScore')
    # applicant__email ist verschlüsselt (kein Substring-Match möglich) -> nur Titel-Suche
    search_fields = ('jobPosting__title',)

# 4. Slots & CMS
@admin.register(InterviewSlot)
class InterviewSlotAdmin(admin.ModelAdmin):
    list_display = ('jobPosting', 'startTime', 'endTime', 'isBooked')
    list_filter = ('isBooked',)

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'navEnabled', 'navOrder')
    list_filter = ('status', 'navEnabled')
    search_fields = ('title', 'slug')

# Register remaining models in standard way
admin.site.register(JobFamily)
admin.site.register(CareerPath)
admin.site.register(ContactPerson)
admin.site.register(FacilityContactPerson)
admin.site.register(DepartmentContactPerson)
admin.site.register(WorkflowState)
admin.site.register(PrivacyNoticeVersion)
admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserFacility)
admin.site.register(JobTemplate)
admin.site.register(TextSnippet)
admin.site.register(WorkflowDefinition)
admin.site.register(ApprovalTicket)
admin.site.register(ApprovalStep)
admin.site.register(ApplicantToken)
admin.site.register(AppWorkflowDef)
admin.site.register(AppTicket)
admin.site.register(AppStep)
admin.site.register(Interview)
admin.site.register(Message)
admin.site.register(TalentPoolSubscription)
admin.site.register(JobAlertSubscription)
admin.site.register(JobAlertLog)
admin.site.register(SystemSetting)
admin.site.register(EmailTemplate)
admin.site.register(ScreeningQuestion)
admin.site.register(RoleDelegation)
admin.site.register(AuditLog)
admin.site.register(AILearningSample)


# BOLA UserScope – Zuweisung erlaubter Standorte/Einrichtungen je Auth-User
from .models import UserScope

@admin.register(UserScope)
class UserScopeAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_access', 'createdAt')
    list_filter = ('full_access',)
    search_fields = ('user__username',)
    filter_horizontal = ('locations', 'facilities')


from .models import ApplicationDocument

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'application', 'docType', 'createdAt')
    search_fields = ('name',)
    list_filter = ('docType',)
