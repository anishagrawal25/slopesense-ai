"""
Alerts, Alert Recipients, and Alert Responses ORM Models.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id = Column(String(36), ForeignKey("risk_predictions.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    status = Column(String(20), default="ACTIVE")  # PENDING, SENT, ACTIVE, EXPIRED
    sent_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    prediction = relationship("RiskPrediction", back_populates="alerts")
    recipients = relationship("AlertRecipient", back_populates="alert", cascade="all, delete-orphan")
    responses = relationship("AlertResponse", back_populates="alert", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="alert")
    assignments = relationship("VolunteerAssignment", back_populates="alert")

class AlertRecipient(Base):
    __tablename__ = "alert_recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    delivery_method = Column(String(20), default="SMS")  # SMS, IVR, APP
    delivered_at = Column(DateTime, default=datetime.utcnow)
    delivery_status = Column(String(20), default="DELIVERED")  # SENT, FAILED, DELIVERED

    # Relationships
    alert = relationship("Alert", back_populates="recipients")
    user = relationship("User", back_populates="alert_recipients")

class AlertResponse(Base):
    __tablename__ = "alert_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    response_type = Column(String(20), nullable=False)  # SAFE, NEED_HELP, NO_RESPONSE
    responded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    alert = relationship("Alert", back_populates="responses")
    user = relationship("User", back_populates="alert_responses")
    emergency_case = relationship("EmergencyCase", back_populates="alert_response", uselist=False)
