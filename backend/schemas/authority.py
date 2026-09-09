"""
Authority Command Center and Monitoring Pydantic Schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class SendAlertRequest(BaseModel):
    district: str = Field(..., example="Dima Hasao")
    riskLevel: str = Field("HIGH", example="HIGH")
    title: str = Field(..., example="URGENT: Landslide Evacuation Advisory")
    message: str = Field(..., example="Immediate evacuation ordered for vulnerable slopes along NH-54.")
    sendSms: bool = Field(True, example=True)
    sendIvr: bool = Field(True, example=True)
    predictionId: Optional[str] = None

class AuthorityDashboardSummary(BaseModel):
    activeAlerts: int = Field(..., example=12)
    safeCitizens: int = Field(..., example=250)
    needHelp: int = Field(..., example=15)
    noResponse: int = Field(..., example=7)
    activeVolunteers: int = Field(..., example=18)
    pendingReports: int = Field(..., example=4)
    verifiedReports: int = Field(..., example=9)
    highRiskLocations: int = Field(..., example=3)

class CommunityStatusSummary(BaseModel):
    totalCitizensContacted: int
    safeCitizens: int
    needHelpCitizens: int
    noResponseCitizens: int
    responseRatePercent: float
    districtBreakdown: List[Dict[str, Any]] = []

class VolunteerActivitySummary(BaseModel):
    totalVolunteers: int
    activeVolunteers: int
    assignedCases: int
    inProgressCases: int
    resolvedCases: int
    completionRatePercent: float
    recentActivities: List[Dict[str, Any]] = []

class DistrictRiskAnalytics(BaseModel):
    district: str
    riskScore: float
    riskLevel: str
    predictedRainfallMm: float
    vulnerablePopulation: int
    evacuationStatus: str
