"""
Risk Prediction and Geospatial Mapping Endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.models.risk import RiskPrediction, RiskZone
from backend.models.alert import Alert
from backend.services.ml_service import ml_service
from backend.services.gee_service import gee_service
from backend.schemas.risk import (
    MLPredictRequest, RiskPredictionRequest, RiskPredictionResponse,
    RiskLatestResponse, RiskMapItem
)

router = APIRouter()

@router.get("/latest", response_model=RiskLatestResponse)
def get_latest_risk(
    location: str = Query("Shillong", description="Location name or district"),
    db: Session = Depends(get_db)
):
    """
    Get latest calculated risk prediction for a location.
    Falls back to real-time calculation if not yet stored.
    """
    prediction = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.location_name.ilike(f"%{location}%"))
        .order_by(desc(RiskPrediction.predicted_at))
        .first()
    )

    if prediction:
        return RiskLatestResponse(
            location=prediction.location_name,
            riskLevel=prediction.risk_level,
            riskScore=prediction.risk_score,
            confidence=prediction.confidence_score,
            factors=prediction.factors or ["Environmental Monitoring Active"],
            lastUpdated=prediction.predicted_at
        )

    # Compute on the fly using GEE service & ML model
    features = gee_service.get_features_for_location(25.5788, 91.8933, location_name=location)
    result = ml_service.predict_risk(features, db=db, save_to_db=True)
    return RiskLatestResponse(
        location=result["location_name"],
        riskLevel=result["riskLevel"],
        riskScore=result["riskScore"],
        confidence=result["confidence"],
        factors=result["factors"],
        safetyRecommendation=result["safetyRecommendation"],
        lastUpdated=result["predicted_at"]
    )

@router.get("/map", response_model=List[RiskMapItem])
def get_risk_map(db: Session = Depends(get_db)):
    """
    Get geospatial risk map points across Northeast India monitoring sectors.
    """
    monitoring_points = gee_service.get_all_monitoring_points()
    results = []

    for point in monitoring_points:
        # Score point using ML model
        pred = ml_service.predict_risk(point, db=db, save_to_db=False)
        
        # Check active alerts count for district
        active_alerts = (
            db.query(Alert)
            .filter(Alert.status == "ACTIVE")
            .count()
        )

        results.append(RiskMapItem(
            district=point.get("district", "Dima Hasao"),
            location_name=point.get("location_name"),
            latitude=point["latitude"],
            longitude=point["longitude"],
            riskLevel=pred["riskLevel"],
            riskScore=pred["riskScore"],
            confidence=pred["confidence"],
            rainfall_mm=point.get("rainfall_mm"),
            activeAlerts=active_alerts
        ))

    return results

@router.post("/predict", response_model=RiskPredictionResponse)
def predict_custom_risk(payload: RiskPredictionRequest, db: Session = Depends(get_db)):
    """
    POST /risk/predict - Execute ML risk prediction on custom parameters.
    """
    features = payload.dict()
    result = ml_service.predict_risk(features, db=db, save_to_db=True)
    return RiskPredictionResponse(**result)

@router.post("/ml/predict", response_model=RiskPredictionResponse)
def predict_ml_alias(payload: MLPredictRequest, db: Session = Depends(get_db)):
    """
    POST /ml/predict - Alias endpoint specified in API_SPEC.md.
    """
    features = payload.dict()
    result = ml_service.predict_risk(features, db=db, save_to_db=True)
    return RiskPredictionResponse(**result)
