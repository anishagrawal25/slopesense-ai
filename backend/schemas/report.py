"""
Community Report Pydantic Schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class ReportCreateRequest(BaseModel):
    alertId: Optional[str] = Field(None, example="123")
    observationType: str = Field(..., example="ROAD_CRACK")  # ROAD_CRACK, FALLING_ROCKS, SOIL_MOVEMENT, ROAD_BLOCKAGE, WATER_FLOW_CHANGE
    description: str = Field(..., example="Large 2-meter crack observed across NH-54")
    imageUrl: Optional[str] = Field(None, example="https://storage.slopesense.ai/reports/crack1.jpg")
    latitude: float = Field(..., example=25.1718)
    longitude: float = Field(..., example=93.1230)

class ReportResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    alert_id: Optional[str] = None
    observation_type: str
    description: str
    image_url: Optional[str] = None
    latitude: float
    longitude: float
    status: str  # PENDING, COMMUNITY_CONFIRMED, VOLUNTEER_VERIFIED, REJECTED
    created_at: datetime

    class Config:
        from_attributes = True

class EvidenceUploadResponse(BaseModel):
    image_url: str
    filename: str
    message: str = "File uploaded successfully"
