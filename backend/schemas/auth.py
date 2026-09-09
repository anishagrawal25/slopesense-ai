"""
Authentication and User Pydantic Schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class UserRegisterRequest(BaseModel):
    full_name: str
    phone_number: Optional[str] = None
    email: str
    password: str = Field(..., min_length=6)
    confirm_password: Optional[str] = None
    role: str = "citizen"  # citizen, volunteer, authority
    state: Optional[str] = "Assam"
    district: Optional[str] = "Dima Hasao"
    village_area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    full_name: str
    phone_number: Optional[str] = None
    email: str
    role: str
    state: Optional[str] = None
    district: Optional[str] = None
    village_area: Optional[str] = None
    status: str = "approved"  # approved, pending, rejected
    is_active: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserStatusUpdateRequest(BaseModel):
    status: str  # approved, rejected
    reason: Optional[str] = None
