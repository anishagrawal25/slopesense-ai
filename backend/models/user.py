"""
User ORM Model with Role-Based Access Control and Registration Approval Status.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="citizen")  # citizen, volunteer, authority, admin
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True, default="Assam")
    village_area = Column(String(150), nullable=True)
    status = Column(String(20), nullable=False, default="approved")  # approved, pending, rejected
    is_active = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    alert_responses = relationship("AlertResponse", back_populates="user")
    alert_recipients = relationship("AlertRecipient", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    assignments = relationship("VolunteerAssignment", foreign_keys="VolunteerAssignment.volunteer_id", back_populates="volunteer")
    emergency_cases = relationship("EmergencyCase", back_populates="citizen")
