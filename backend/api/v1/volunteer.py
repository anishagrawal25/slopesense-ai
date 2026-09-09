"""
Volunteer Operations & Field Verification Endpoints.
"""
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.security import get_current_user, require_roles
from backend.core.config import settings
from backend.models.report import EmergencyCase, VolunteerAssignment, VerificationReport, Report
from backend.models.user import User
from backend.models.alert import Alert
from backend.services.escalation_service import escalation_service
from backend.schemas.volunteer import (
    VolunteerCaseItem, VolunteerVerifyRequest, VerificationReportResponse,
    CaseStatusUpdateRequest
)
from backend.schemas.report import EvidenceUploadResponse

router = APIRouter()

def format_case_item(case: EmergencyCase, db: Session) -> VolunteerCaseItem:
    """Helper to convert EmergencyCase ORM to Pydantic VolunteerCaseItem."""
    verifications = (
        db.query(VerificationReport)
        .join(VolunteerAssignment)
        .filter(VolunteerAssignment.emergency_case_id == case.id)
        .all()
    )
    v_list = [
        VerificationReportResponse(
            id=v.id,
            assignment_id=v.assignment_id,
            volunteer_id=v.volunteer_id,
            volunteer_name=v.volunteer.full_name if v.volunteer else "Volunteer",
            findings=v.findings,
            evidence_url=v.evidence_url,
            verification_status=v.verification_status,
            verified_at=v.verified_at
        )
        for v in verifications
    ]

    alert_title = None
    if case.alert_response and case.alert_response.alert:
        alert_title = case.alert_response.alert.title

    assignment = (
        db.query(VolunteerAssignment)
        .filter(VolunteerAssignment.emergency_case_id == case.id)
        .first()
    )

    return VolunteerCaseItem(
        id=case.id,
        case_type=case.case_type,
        priority=case.priority,
        status=case.status,
        citizen_name=case.citizen.full_name if case.citizen else "Resident",
        citizen_phone=case.citizen.phone_number if case.citizen else None,
        citizen_id=case.citizen_id,
        location_name=case.citizen.district if case.citizen else "Dima Hasao",
        latitude=case.citizen.latitude if case.citizen else 25.1718,
        longitude=case.citizen.longitude if case.citizen else 93.1230,
        alert_title=alert_title,
        description=case.notes,
        assigned_at=assignment.assigned_at if assignment else None,
        created_at=case.created_at,
        verifications=v_list
    )

@router.get("/cases", response_model=List[VolunteerCaseItem])
def get_all_cases(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all emergency escalation cases."""
    query = db.query(EmergencyCase).order_by(desc(EmergencyCase.created_at))
    if status_filter:
        query = query.filter(EmergencyCase.status == status_filter)
    cases = query.all()
    return [format_case_item(c, db) for c in cases]

@router.get("/need-help", response_model=List[VolunteerCaseItem])
def get_need_help_cases(db: Session = Depends(get_db)):
    """Retrieve all high-priority NEED_HELP cases."""
    cases = (
        db.query(EmergencyCase)
        .filter(EmergencyCase.case_type == "NEED_HELP")
        .order_by(desc(EmergencyCase.created_at))
        .all()
    )
    return [format_case_item(c, db) for c in cases]

@router.get("/no-response", response_model=List[VolunteerCaseItem])
def get_no_response_cases(db: Session = Depends(get_db)):
    """Retrieve all non-responsive citizen welfare follow-up cases."""
    cases = (
        db.query(EmergencyCase)
        .filter(EmergencyCase.case_type == "NO_RESPONSE")
        .order_by(desc(EmergencyCase.created_at))
        .all()
    )
    return [format_case_item(c, db) for c in cases]

@router.post("/verify", response_model=VerificationReportResponse)
def verify_incident(
    payload: VolunteerVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Volunteer submits on-the-ground field verification for an emergency case.
    Carries higher trust and promotes community validation status.
    """
    v_report = escalation_service.submit_volunteer_verification(
        case_id=payload.caseId,
        volunteer=current_user,
        findings=payload.findings,
        status=payload.status,
        evidence_url=payload.evidenceUrl,
        db=db
    )
    return VerificationReportResponse(
        id=v_report.id,
        assignment_id=v_report.assignment_id,
        volunteer_id=v_report.volunteer_id,
        volunteer_name=current_user.full_name,
        findings=v_report.findings,
        evidence_url=v_report.evidence_url,
        verification_status=v_report.verification_status,
        verified_at=v_report.verified_at
    )

@router.post("/evidence", response_model=EvidenceUploadResponse)
async def upload_verification_evidence(file: UploadFile = File(...)):
    """Upload volunteer field inspection photos."""
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"evidence_{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return EvidenceUploadResponse(
        image_url=f"/uploads/{unique_filename}",
        filename=unique_filename,
        message="Verification evidence photo uploaded"
    )

@router.patch("/cases/{id}/status", response_model=dict)
def update_case_status(
    id: str,
    payload: CaseStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update progress status of an emergency case."""
    case = db.query(EmergencyCase).filter(EmergencyCase.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = payload.status
    if payload.notes:
        case.notes = f"{case.notes or ''} | Update: {payload.notes}"
    db.commit()

    return {"message": "Case status updated", "case_id": case.id, "status": case.status}
