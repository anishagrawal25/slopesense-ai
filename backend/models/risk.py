"""
Risk Predictions and Risk Zones ORM Models.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.core.database import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_name = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    risk_score = Column(Float, nullable=False)  # 0 to 100
    confidence_score = Column(Float, nullable=False)  # percentage, e.g. 92
    rainfall = Column(Float, nullable=True)
    slope = Column(Float, nullable=True)
    ndvi = Column(Float, nullable=True)
    factors = Column(JSON, nullable=True)  # List of contributing factors
    predicted_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    alerts = relationship("Alert", back_populates="prediction", cascade="all, delete-orphan")
    risk_zones = relationship("RiskZone", back_populates="prediction", cascade="all, delete-orphan")

class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id = Column(String(36), ForeignKey("risk_predictions.id"), nullable=True)
    zone_name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, default="Assam")
    geometry_data = Column(JSON, nullable=True)  # GeoJSON polygon or bounds
    risk_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prediction = relationship("RiskPrediction", back_populates="risk_zones")
