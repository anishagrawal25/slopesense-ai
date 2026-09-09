"""
Alert and Citizen Response Pydantic Schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class AlertCreateRequest(BaseModel):
    predictionId: Optional[str] = Field(None, example="123")
    title: Optional[str] = Field(None, example="Landslide Warning: High Risk in Haflong")
    description: Optional[str] = Field(None, example="Heavy monsoon rainfall has triggered slope instability.")
    riskLevel: str = Field("HIGH", example="HIGH")
    district: Optional[str] = Field("Dima Hasao", example="Dima Hasao")
    sendSms: bool = Field(True, example=True)
    sendIvr: bool = Field(True, example=True)

class CitizenAlertResponseCreate(BaseModel):
    alertId: str = Field(..., example="123")
    response: str = Field(..., example="SAFE")  # SAFE, NEED_HELP, NO_RESPONSE

class CitizenAlertResponseItem(BaseModel):
    id: str
    alert_id: str
    user_id: str
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    response_type: str
    responded_at: datetime

    class Config:
        from_attributes = True

class AlertRecipientItem(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    delivery_method: str
    delivery_status: str
    delivered_at: datetime

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: str
    prediction_id: Optional[str] = None
    title: str
    description: str
    risk_level: str
    status: str
    sent_at: datetime
    expires_at: Optional[datetime] = None
    total_recipients: Optional[int] = 0
    total_responses: Optional[int] = 0
    safe_count: Optional[int] = 0
    need_help_count: Optional[int] = 0
    no_response_count: Optional[int] = 0

    class Config:
        from_attributes = True

class AlertDetailResponse(AlertResponse):
    recipients: List[AlertRecipientItem] = []
    responses: List[CitizenAlertResponseItem] = []
