"""SecurATS-Modellpaket.

Die frueher 1.500-zeilige models.py ist in Domaenen-Module zerlegt. Dieses
Paket re-exportiert alle Modelle, Hilfsfunktionen und Konstanten, damit
`from ats.models import X` sowie `ats.models.EncryptedCharField` in den
bestehenden Migrationen unveraendert weiterlaufen.

Die Abhaengigkeitsrichtung zwischen den Submodulen ist strikt einbahnig:
base -> organization -> governance -> jobs -> system -> applications ->
{job_alerts, iam, audit, ai}. Neue Querverweise nur in diese Richtung
anlegen, sonst entstehen Zirkelimporte (die Reihenfolge der Zeilen hier
ist dagegen egal, sie folgt der Import-Sortierung).
"""

from .ai import AiTask, BestPerformerProfile
from .applications import (
    DEFAULT_FEEDBACK_CRITERIA,
    INTERVIEW_KINDS,
    INTERVIEW_OUTCOMES,
    INTERVIEW_RECOMMENDATIONS,
    WORKFLOW_TASK_STATUS,
    Applicant,
    ApplicantManager,
    ApplicantToken,
    Application,
    ApplicationDocument,
    ApplicationVote,
    AppWorkflowDef,
    Interview,
    InterviewFeedback,
    InterviewSlot,
    Message,
    SourceChannel,
    TalentPoolContact,
    TalentPoolSubscription,
    WorkflowTask,
    derive_recommendation,
    feedback_for_application,
    feedback_summaries,
    get_interview_kinds,
    interview_kind_label,
    interview_outcome_label,
    interview_rounds,
    pending_feedback_participants,
    rounds_state,
)
from .audit import AuditLog
from .base import (
    EncryptedCharField,
    EncryptedTextField,
    email_blind_index,
    get_fernet_cipher,
)
from .governance import (
    PrivacyNoticeVersion,
    WorkflowState,
)
from .iam import RoleDelegation, UserScope
from .job_alerts import JobAlertLog, JobAlertSubscription
from .jobs import (
    ApprovalStep,
    ApprovalTicket,
    Benefit,
    JobPosting,
    JobTemplate,
    PayBand,
    TextSnippet,
)
from .organization import (
    ContactPerson,
    Department,
    DepartmentContactPerson,
    Facility,
    FacilityContactPerson,
    FacilityProfile,
    JobFamily,
    Location,
    Organization,
)
from .system import (
    EmailTemplate,
    LandingPage,
    MediaAsset,
    Page,
    RequisitionRule,
    RequisitionStep,
    ScreeningQuestion,
    StaffingRequest,
    SystemSetting,
)

__all__ = [
    "AiTask",
    "Applicant",
    "ApplicantManager",
    "ApplicantToken",
    "Application",
    "ApplicationDocument",
    "ApplicationVote",
    "AppWorkflowDef",
    "ApprovalStep",
    "ApprovalTicket",
    "AuditLog",
    "Benefit",
    "BestPerformerProfile",
    "ContactPerson",
    "DEFAULT_FEEDBACK_CRITERIA",
    "Department",
    "DepartmentContactPerson",
    "derive_recommendation",
    "email_blind_index",
    "EmailTemplate",
    "EncryptedCharField",
    "EncryptedTextField",
    "Facility",
    "FacilityContactPerson",
    "FacilityProfile",
    "feedback_for_application",
    "feedback_summaries",
    "get_fernet_cipher",
    "get_interview_kinds",
    "INTERVIEW_KINDS",
    "INTERVIEW_OUTCOMES",
    "INTERVIEW_RECOMMENDATIONS",
    "Interview",
    "InterviewFeedback",
    "interview_kind_label",
    "interview_outcome_label",
    "interview_rounds",
    "InterviewSlot",
    "JobAlertLog",
    "JobAlertSubscription",
    "JobFamily",
    "JobPosting",
    "JobTemplate",
    "LandingPage",
    "Location",
    "MediaAsset",
    "Message",
    "Organization",
    "Page",
    "PayBand",
    "pending_feedback_participants",
    "PrivacyNoticeVersion",
    "RequisitionRule",
    "RequisitionStep",
    "RoleDelegation",
    "rounds_state",
    "ScreeningQuestion",
    "SourceChannel",
    "StaffingRequest",
    "SystemSetting",
    "TalentPoolContact",
    "TalentPoolSubscription",
    "TextSnippet",
    "UserScope",
    "WORKFLOW_TASK_STATUS",
    "WorkflowState",
    "WorkflowTask",
]
