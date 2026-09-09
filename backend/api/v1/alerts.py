"""
Alert Management and Citizen Response Endpoints.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.security import get_current_user, require_roles
from backend.models.alert import Alert, AlertRecipient, AlertResponse
from backend.models.user import User
from backend.models.system import AuditLog
from backend.services.notification_service import notification_service
from backend.services.escalation_service import escalation_service
from backend.schemas.alert import (
    AlertCreateRequest, AlertResponse as AlertSchemaResponse,
    AlertDetailResponse, CitizenAlertResponseCreate, CitizenAlertResponseItem
)

router = APIRouter()

@router.post("", response_model=AlertSchemaResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["authority"]))
):
    """Authority creates and broadcasts an emergency alert."""
    title = payload.title or f"Landslide Warning: {payload.riskLevel} Risk in {payload.district}"
    description = payload.description or (
        f"SlopeSense AI has detected critical environmental threshold breach in {payload.district}. "
        "Residents are advised to avoid unstable slopes and monitor safety bulletins."
    )

    alert = Alert(
        prediction_id=payload.predictionId,
        title=title,
        description=description,
        risk_level=payload.riskLevel,
        status="ACTIVE",
        sent_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Find recipient citizens in district (or all citizens if none specific)
    recipients = (
        db.query(User)
        .filter(User.role == "citizen")
        .filter(User.district == payload.district)
        .all()
    )
    if not recipients:
        recipients = db.query(User).filter(User.role == "citizen").all()

    # Broadcast via multi-channel notification service
    if recipients:
        notification_service.broadcast_alert(
            alert=alert,
            users=recipients,
            db=db,
            send_sms=payload.sendSms,
            send_ivr=payload.sendIvr
        )

    return AlertSchemaResponse(
        id=alert.id,
        prediction_id=alert.prediction_id,
        title=alert.title,
        description=alert.description,
        risk_level=alert.risk_level,
        status=alert.status,
        sent_at=alert.sent_at,
        expires_at=alert.expires_at,
        total_recipients=len(recipients),
        total_responses=0,
        safe_count=0,
        need_help_count=0,
        no_response_count=0
    )

@router.get("", response_model=List[AlertSchemaResponse])
def list_alerts(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all alerts with live aggregate response counts."""
    query = db.query(Alert).order_by(desc(Alert.sent_at))
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    alerts = query.all()

    results = []
    for a in alerts:
        total_recipients = db.query(AlertRecipient).filter(AlertRecipient.alert_id == a.id).count()
        responses = db.query(AlertResponse).filter(AlertResponse.alert_id == a.id).all()
        safe_count = sum(1 for r in responses if r.response_type == "SAFE")
        need_help_count = sum(1 for r in responses if r.response_type == "NEED_HELP")
        no_resp_count = max(0, total_recipients - len(responses))

        results.append(AlertSchemaResponse(
            id=a.id,
            prediction_id=a.prediction_id,
            title=a.title,
            description=a.description,
            risk_level=a.risk_level,
            status=a.status,
            sent_at=a.sent_at,
            expires_at=a.expires_at,
            total_recipients=total_recipients,
            total_responses=len(responses),
            safe_count=safe_count,
            need_help_count=need_help_count,
            no_response_count=no_resp_count
        ))
    return results

@router.get("/{id}", response_model=AlertDetailResponse)
def get_alert_detail(id: str, db: Session = Depends(get_db)):
    """Get detailed information for a single alert including recipients and responses."""
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    recipients = db.query(AlertRecipient).filter(AlertRecipient.alert_id == alert.id).all()
    responses = db.query(AlertResponse).filter(AlertResponse.alert_id == alert.id).all()

    safe_c = sum(1 for r in responses if r.response_type == "SAFE")
    help_c = sum(1 for r in responses if r.response_type == "NEED_HELP")
    no_resp_c = max(0, len(recipients) - len(responses))

    return AlertDetailResponse(
        id=alert.id,
        prediction_id=alert.prediction_id,
        title=alert.title,
        description=alert.description,
        risk_level=alert.risk_level,
        status=alert.status,
        sent_at=alert.sent_at,
        expires_at=alert.expires_at,
        total_recipients=len(recipients),
        total_responses=len(responses),
        safe_count=safe_c,
        need_help_count=help_c,
        no_response_count=no_resp_c,
        recipients=[
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_name": r.user.full_name if r.user else "Citizen",
                "delivery_method": r.delivery_method,
                "delivery_status": r.delivery_status,
                "delivered_at": r.delivered_at
            }
            for r in recipients
        ],
        responses=[
            {
                "id": resp.id,
                "alert_id": resp.alert_id,
                "user_id": resp.user_id,
                "user_name": resp.user.full_name if resp.user else "Citizen",
                "user_phone": resp.user.phone_number if resp.user else None,
                "response_type": resp.response_type,
                "responded_at": resp.responded_at
            }
            for resp in responses
        ]
    )

@router.post("/respond", response_model=dict)
def respond_to_alert(
    payload: CitizenAlertResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Citizen responds to an active alert with SAFE, NEED_HELP, or NO_RESPONSE.
    Automatically triggers escalation workflow if NEED_HELP or NO_RESPONSE.
    """
    alert = db.query(Alert).filter(Alert.id == payload.alertId).first()
    if not alert:
        # If alert ID is generic or latest, attach to latest active alert
        alert = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(desc(Alert.sent_at)).first()
        if not alert:
            raise HTTPException(status_code=404, detail="No active alert found to respond to.")

    # Check for existing response
    existing_resp = (
        db.query(AlertResponse)
        .filter(AlertResponse.alert_id == alert.id, AlertResponse.user_id == current_user.id)
        .first()
    )

    response_type = payload.response.upper()
    if response_type not in ("SAFE", "NEED_HELP", "NO_RESPONSE"):
        response_type = "SAFE"

    if existing_resp:
        existing_resp.response_type = response_type
        existing_resp.responded_at = datetime.utcnow()
        db_response = existing_resp
    else:
        db_response = AlertResponse(
            alert_id=alert.id,
            user_id=current_user.id,
            response_type=response_type,
            responded_at=datetime.utcnow()
        )
        db.add(db_response)

    db.commit()
    db.refresh(db_response)

    # Trigger Critical Escalation Workflow
    emergency_case = escalation_service.handle_citizen_response(db_response, db)

    return {
        "message": "Response recorded successfully",
        "response_type": response_type,
        "escalated": emergency_case is not None,
        "emergency_case_id": emergency_case.id if emergency_case else None
    }

@router.get("/responses/me", response_model=List[CitizenAlertResponseItem])
def get_my_responses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve check-in history of current authenticated citizen."""
    responses = (
        db.query(AlertResponse)
        .filter(AlertResponse.user_id == current_user.id)
        .order_by(desc(AlertResponse.responded_at))
        .all()
    )
    return [
        CitizenAlertResponseItem(
            id=r.id,
            alert_id=r.alert_id,
            user_id=r.user_id,
            user_name=current_user.full_name,
            user_phone=current_user.phone_number,
            response_type=r.response_type,
            responded_at=r.responded_at
        )
        for r in responses
    ]

# ---------- TWILIO WEBHOOKS ----------
@router.post("/webhook/twilio-sms")
async def twilio_sms_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook for incoming SMS replies from citizens."""
    form_data = await request.form()
    from_number = form_data.get("From")
    body = form_data.get("Body", "")

    response_type = notification_service.parse_response_text(body)

    # Find user by phone number
    user = db.query(User).filter(User.phone_number == from_number).first()
    if not user:
        user = db.query(User).filter(User.role == "citizen").first()

    latest_alert = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(desc(Alert.sent_at)).first()
    if user and latest_alert:
        resp = AlertResponse(
            alert_id=latest_alert.id,
            user_id=user.id,
            response_type=response_type,
            responded_at=datetime.utcnow()
        )
        db.add(resp)
        db.commit()
        db.refresh(resp)
        escalation_service.handle_citizen_response(resp, db)

    reply_msg = (
        "SlopeSense AI: Thank you. Your safety status 'SAFE' has been registered."
        if response_type == "SAFE"
        else "SlopeSense AI: HELP REQUEST RECEIVED! Rescue teams and volunteers have been notified."
    )
    twiml_resp = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>{reply_msg}</Message></Response>"
    return Response(content=twiml_resp, media_type="application/xml")

@router.post("/webhook/twilio-voice")
async def twilio_voice_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook for interactive DTMF digit responses on IVR voice calls."""
    form_data = await request.form()
    from_number = form_data.get("From")
    digits = form_data.get("Digits", "1")

    response_type = "SAFE" if str(digits) == "1" else "NEED_HELP"

    user = db.query(User).filter(User.phone_number == from_number).first()
    if not user:
        user = db.query(User).filter(User.role == "citizen").first()

    latest_alert = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(desc(Alert.sent_at)).first()
    if user and latest_alert:
        resp = AlertResponse(
            alert_id=latest_alert.id,
            user_id=user.id,
            response_type=response_type,
            responded_at=datetime.utcnow()
        )
        db.add(resp)
        db.commit()
        db.refresh(resp)
        escalation_service.handle_citizen_response(resp, db)

    ack_text = "Thank you. Your safe status is logged." if response_type == "SAFE" else "Emergency assistance request registered. Stand by for emergency responders."
    twiml = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Say voice='alice' language='en-IN'>{ack_text}</Say></Response>"
    return Response(content=twiml, media_type="application/xml")
