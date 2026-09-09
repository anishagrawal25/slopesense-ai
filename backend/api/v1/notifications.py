"""
User Notification Endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.system import Notification
from backend.schemas.notification import NotificationResponse, NotificationUpdate

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all notifications for authenticated user."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .all()
    )
    return [NotificationResponse.from_orm(n) for n in notifications]

@router.patch("/{id}", response_model=NotificationResponse)
def mark_notification_read(
    id: str,
    payload: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = payload.is_read
    db.commit()
    db.refresh(notif)
    return NotificationResponse.from_orm(notif)
