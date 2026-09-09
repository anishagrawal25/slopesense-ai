"""
Community Hazard Reports and Image Upload Endpoints.
"""
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.core.config import settings
from backend.models.report import Report
from backend.models.user import User
from backend.models.system import AuditLog
from backend.services.validation_service import validation_service
from backend.schemas.report import (
    ReportCreateRequest, ReportResponse, EvidenceUploadResponse
)

router = APIRouter()

@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a community hazard report (road crack, falling rocks, soil movement, road blockage, water flow change).
    Passes through the Community Validation Engine for spatial-temporal clustering.
    """
    valid_obs = [
        "ROAD_CRACK", "FALLING_ROCKS", "SOIL_MOVEMENT", "ROAD_BLOCKAGE", "WATER_FLOW_CHANGE"
    ]
    obs_type = payload.observationType.upper()
    if obs_type not in valid_obs:
        obs_type = "SOIL_MOVEMENT"

    report = Report(
        user_id=current_user.id,
        alert_id=payload.alertId,
        observation_type=obs_type,
        description=payload.description,
        image_url=payload.imageUrl,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status="PENDING"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Pass through Community Validation Engine
    new_status = validation_service.process_new_report(report, db)

    audit = AuditLog(
        user_id=current_user.id,
        action="REPORT_SUBMITTED",
        entity_type="REPORT",
        entity_id=report.id,
        details=f"Observation: {obs_type}, Status: {new_status}"
    )
    db.add(audit)
    db.commit()
    db.refresh(report)

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        user_name=current_user.full_name,
        alert_id=report.alert_id,
        observation_type=report.observation_type,
        description=report.description,
        image_url=report.image_url,
        latitude=report.latitude,
        longitude=report.longitude,
        status=report.status,
        created_at=report.created_at
    )

@router.post("/upload", response_model=EvidenceUploadResponse)
async def upload_report_image(file: UploadFile = File(...)):
    """Upload photos / evidence for hazard reports."""
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return EvidenceUploadResponse(
        image_url=f"/uploads/{unique_filename}",
        filename=unique_filename,
        message="Hazard photo uploaded successfully"
    )

@router.get("", response_model=List[ReportResponse])
def get_reports(
    status_filter: Optional[str] = None,
    observation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all community hazard reports."""
    query = db.query(Report).order_by(desc(Report.created_at))
    if status_filter:
        query = query.filter(Report.status == status_filter)
    if observation_type:
        query = query.filter(Report.observation_type == observation_type.upper())

    reports = query.all()
    return [
        ReportResponse(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user.full_name if r.user else "Citizen",
            alert_id=r.alert_id,
            observation_type=r.observation_type,
            description=r.description,
            image_url=r.image_url,
            latitude=r.latitude,
            longitude=r.longitude,
            status=r.status,
            created_at=r.created_at
        )
        for r in reports
    ]

@router.get("/{id}", response_model=ReportResponse)
def get_report_by_id(id: str, db: Session = Depends(get_db)):
    """Retrieve a single report by ID."""
    report = db.query(Report).filter(Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        user_name=report.user.full_name if report.user else "Citizen",
        alert_id=report.alert_id,
        observation_type=report.observation_type,
        description=report.description,
        image_url=report.image_url,
        latitude=report.latitude,
        longitude=report.longitude,
        status=report.status,
        created_at=report.created_at
    )
