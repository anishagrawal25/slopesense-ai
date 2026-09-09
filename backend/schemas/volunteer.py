"""
Volunteer Operations and Field Verification Pydantic Schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class VolunteerVerifyRequest(BaseModel):
    caseId: str = Field(..., example="123")
    status: str = Field(..., example="CONFIRMED")  # CONFIRMED, PARTIALLY_CONFIRMED, FALSE_ALARM
    findings: str = Field(..., example="Active soil displacement observed near bridge support.")
    evidenceUrl: Optional[str] = Field(None, example="https://storage.slopesense.ai/evidence/evidence1.jpg")

class CaseStatusUpdateRequest(BaseModel):
    status: str = Field(..., example="IN_PROGRESS")  # ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
    notes: Optional[str] = None

class VerificationReportResponse(BaseModel):
    id: str
    assignment_id: str
    volunteer_id: str
    volunteer_name: Optional[str] = None
    findings: str
    evidence_url: Optional[str] = None
    verification_status: str
    verified_at: datetime

    class Config:
        from_attributes = True

class VolunteerCaseItem(BaseModel):
    id: str
    case_type: str  # NEED_HELP, NO_RESPONSE, REPORT_VERIFICATION, ALERT_FOLLOWUP
    priority: str   # LOW, MEDIUM, HIGH, CRITICAL
    status: str     # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
    citizen_name: Optional[str] = None
    citizen_phone: Optional[str] = None
    citizen_id: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    alert_title: Optional[str] = None
    description: Optional[str] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime
    verifications: List[VerificationReportResponse] = []

    class Config:
        from_attributes = True
