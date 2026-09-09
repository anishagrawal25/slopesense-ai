"""
Export all Pydantic schemas.
"""
from backend.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from backend.schemas.risk import (
    MLPredictRequest, RiskPredictionRequest, RiskPredictionResponse,
    RiskLatestResponse, RiskMapItem, RiskZoneItem
)
from backend.schemas.alert import (
    AlertCreateRequest, AlertResponse, AlertDetailResponse,
    CitizenAlertResponseCreate, CitizenAlertResponseItem, AlertRecipientItem
)
from backend.schemas.report import ReportCreateRequest, ReportResponse, EvidenceUploadResponse
from backend.schemas.volunteer import (
    VolunteerVerifyRequest, CaseStatusUpdateRequest,
    VerificationReportResponse, VolunteerCaseItem
)
from backend.schemas.authority import (
    SendAlertRequest, AuthorityDashboardSummary, CommunityStatusSummary,
    VolunteerActivitySummary, DistrictRiskAnalytics
)
from backend.schemas.notification import NotificationResponse, NotificationUpdate

__all__ = [
    "UserRegisterRequest", "UserLoginRequest", "TokenResponse", "UserResponse",
    "MLPredictRequest", "RiskPredictionRequest", "RiskPredictionResponse",
    "RiskLatestResponse", "RiskMapItem", "RiskZoneItem",
    "AlertCreateRequest", "AlertResponse", "AlertDetailResponse",
    "CitizenAlertResponseCreate", "CitizenAlertResponseItem", "AlertRecipientItem",
    "ReportCreateRequest", "ReportResponse", "EvidenceUploadResponse",
    "VolunteerVerifyRequest", "CaseStatusUpdateRequest",
    "VerificationReportResponse", "VolunteerCaseItem",
    "SendAlertRequest", "AuthorityDashboardSummary", "CommunityStatusSummary",
    "VolunteerActivitySummary", "DistrictRiskAnalytics",
    "NotificationResponse", "NotificationUpdate"
]
