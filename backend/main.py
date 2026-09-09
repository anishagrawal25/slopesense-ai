"""
SlopeSense AI - FastAPI Backend Application Entrypoint.
Provides RESTful APIs for Landslide Prediction, Early Warning, Community Validation,
and Multi-Agency Response Coordination.
"""
from datetime import datetime
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from backend.core.config import settings
from backend.core.database import engine, Base, SessionLocal
from backend.api.v1 import api_router
from backend.schemas.risk import RiskPredictionRequest, RiskPredictionResponse
from backend.services.ml_service import ml_service

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "SlopeSense AI: Government-grade AI-powered landslide prediction, "
        "early warning, community validation, and disaster response coordination platform."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploaded media directory
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level / API_SPEC.md Compatibility Endpoints
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint specified in API_SPEC.md."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/predict", response_model=RiskPredictionResponse, tags=["ML Prediction Compatibility"])
def api_predict_compatibility(payload: RiskPredictionRequest):
    """
    POST /api/predict - Root level prediction endpoint as specified in requirements.
    """
    db = SessionLocal()
    try:
        result = ml_service.predict_risk(payload.dict(), db=db, save_to_db=True)
        return RiskPredictionResponse(**result)
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    """Seed initial data if empty."""
    from backend.seed_data import seed_initial_data
    seed_initial_data()
