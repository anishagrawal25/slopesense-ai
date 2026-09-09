"""
Community Reports, Volunteer Assignments, Verification Reports, and Emergency Cases ORM Models.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=True)
    observation_type = Column(String(50), nullable=False)  # ROAD_CRACK, FALLING_ROCKS, SOIL_MOVEMENT, ROAD_BLOCKAGE, WATER_FLOW_CHANGE
    description = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(30), default="PENDING")  # PENDING, COMMUNITY_CONFIRMED, VOLUNTEER_VERIFIED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="reports")
    alert = relationship("Alert", back_populates="reports")
    assignments = relationship("VolunteerAssignment", back_populates="report")

class VolunteerAssignment(Base):
    __tablename__ = "volunteer_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volunteer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=True)
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=True)
    emergency_case_id = Column(String(36), ForeignKey("emergency_cases.id"), nullable=True)
    assigned_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    priority = Column(String(20), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="ASSIGNED")  # ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    volunteer = relationship("User", foreign_keys=[volunteer_id], back_populates="assignments")
    alert = relationship("Alert", back_populates="assignments")
    report = relationship("Report", back_populates="assignments")
    emergency_case = relationship("EmergencyCase", back_populates="assignments")
    verification_reports = relationship("VerificationReport", back_populates="assignment", cascade="all, delete-orphan")

class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(String(36), ForeignKey("volunteer_assignments.id"), nullable=False)
    volunteer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    findings = Column(Text, nullable=False)
    evidence_url = Column(Text, nullable=True)
    verification_status = Column(String(30), nullable=False)  # CONFIRMED, PARTIALLY_CONFIRMED, FALSE_ALARM
    verified_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assignment = relationship("VolunteerAssignment", back_populates="verification_reports")
    volunteer = relationship("User")

class EmergencyCase(Base):
    __tablename__ = "emergency_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_response_id = Column(String(36), ForeignKey("alert_responses.id"), nullable=True)
    citizen_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    case_type = Column(String(20), nullable=False)  # NEED_HELP, NO_RESPONSE
    priority = Column(String(20), default="CRITICAL")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="OPEN")  # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    alert_response = relationship("AlertResponse", back_populates="emergency_case")
    citizen = relationship("User", back_populates="emergency_cases")
    assignments = relationship("VolunteerAssignment", back_populates="emergency_case")
