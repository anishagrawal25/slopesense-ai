"""
API v1 Router registry.
"""
from fastapi import APIRouter
from backend.api.v1.auth import router as auth_router
from backend.api.v1.risk import router as risk_router
from backend.api.v1.alerts import router as alerts_router
from backend.api.v1.reports import router as reports_router
from backend.api.v1.volunteer import router as volunteer_router
from backend.api.v1.authority import router as authority_router
from backend.api.v1.notifications import router as notifications_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(risk_router, prefix="/risk", tags=["Risk Prediction"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts & Responses"])
api_router.include_router(reports_router, prefix="/reports", tags=["Community Reports"])
api_router.include_router(volunteer_router, prefix="/volunteer", tags=["Volunteer Operations"])
api_router.include_router(authority_router, prefix="/authority", tags=["Authority Command Center"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
