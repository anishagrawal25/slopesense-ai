"""
Risk Prediction and Geospatial Pydantic Schemas.
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MLPredictRequest(BaseModel):
    """
    Teammate ML Model input schema matching API_SPEC.md.
    Supports both direct parameters and full environmental inputs.
    """
    rainfall: Optional[float] = Field(None, example=120.0, description="Current rainfall in mm (maps to rainfall_mm)")
    slope: Optional[float] = Field(None, example=45.0, description="Slope gradient in degrees")
    ndvi: Optional[float] = Field(None, example=0.65, description="Vegetation index")
    aspect: Optional[float] = Field(None, example=180.0, description="Aspect angle")
    curvature: Optional[float] = Field(None, example=0.02, description="Surface curvature")
    cumulative_rainfall_30d: Optional[float] = Field(None, example=250.0, description="30-day cumulative rainfall in mm")
    ndvi_trend: Optional[float] = Field(None, example=-0.03, description="Multi-year NDVI trend")
    ndvi_drop: Optional[float] = Field(None, example=0.25, description="Seasonal NDVI drop")
    distance_to_river: Optional[float] = Field(None, example=1200.0, description="Distance to nearest river stream in meters")
    location_name: Optional[str] = Field("Custom Location", example="Haflong, Dima Hasao")
    latitude: Optional[float] = Field(25.1718, example=25.1718)
    longitude: Optional[float] = Field(93.1230, example=93.1230)

class RiskPredictionRequest(MLPredictRequest):
    pass

class RiskPredictionResponse(BaseModel):
    id: Optional[str] = None
    location_name: str
    latitude: float
    longitude: float
    riskLevel: str = Field(..., example="HIGH")  # LOW, MODERATE, HIGH, CRITICAL
    riskScore: float = Field(..., example=87.0)  # 0 to 100
    confidence: float = Field(..., example=92.0)  # percentage
    factors: List[str] = Field(default_factory=list, example=["Heavy Rainfall (120mm)", "Steep Terrain (45°)"])
    safetyRecommendation: Optional[str] = None
    predicted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RiskLatestResponse(BaseModel):
    location: str = Field(..., example="Shillong")
    riskLevel: str = Field(..., example="HIGH")
    riskScore: float = Field(..., example=87.0)
    confidence: float = Field(..., example=92.0)
    factors: List[str] = Field(default_factory=list)
    safetyRecommendation: Optional[str] = None
    lastUpdated: Optional[datetime] = None

class RiskMapItem(BaseModel):
    district: str = Field(..., example="Dima Hasao")
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    riskLevel: str = Field(..., example="HIGH")
    riskScore: float = Field(..., example=87.0)
    confidence: float = Field(..., example=92.0)
    rainfall_mm: Optional[float] = None
    activeAlerts: int = 0

class RiskZoneItem(BaseModel):
    id: str
    zone_name: str
    district: str
    state: str
    risk_level: str
    geometry_data: Optional[Any] = None
