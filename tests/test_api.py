"""
Unit and Integration Test Suite for SlopeSense AI.
Tests Authentication, ML Prediction, Risk APIs, Alerts, Citizen Responses,
Location-Aware Alert Filtering, Proximity-Based Volunteer Dispatch,
Community Reports, Volunteer Field Verification, Authority Monitoring, and Webhooks.
"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal, Base, engine
from backend.models.user import User
from backend.models.alert import Alert, AlertRecipient, AlertResponse
from backend.models.report import EmergencyCase, VolunteerAssignment
from backend.services.notification_service import notification_service
from backend.services.escalation_service import escalation_service
from backend.seed_data import seed_initial_data

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure clean database schema is created and seeded before tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield

def test_health_check():
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SlopeSense AI"

def test_user_registration_and_login():
    """Test user registration and JWT login."""
    reg_payload = {
        "full_name": "Test Citizen User",
        "email": "test_citizen_unique_01@slopesense.ai",
        "phone_number": "+919999900099",
        "password": "testpassword123",
        "role": "citizen",
        "district": "Dima Hasao",
        "state": "Assam",
        "latitude": 25.1718,
        "longitude": 93.1230
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code in (201, 400)

    login_payload = {
        "email": "test_citizen_unique_01@slopesense.ai",
        "password": "testpassword123"
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_citizen_unique_01@slopesense.ai"

    # Test /auth/me
    token = data["access_token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Test Citizen User"

def test_ml_risk_prediction():
    """Test ML risk prediction with existing Random Forest model."""
    predict_payload = {
        "rainfall": 120.0,
        "slope": 45.0,
        "ndvi": 0.65,
        "aspect": 180.0,
        "curvature": 0.02,
        "cumulative_rainfall_30d": 310.0,
        "distance_to_river": 950.0,
        "location_name": "Haflong Test Sector",
        "latitude": 25.1718,
        "longitude": 93.1230
    }
    
    # Test /api/v1/risk/predict
    response = client.post("/api/v1/risk/predict", json=predict_payload)
    assert response.status_code == 200
    data = response.json()
    assert "riskLevel" in data
    assert "riskScore" in data
    assert "confidence" in data
    assert isinstance(data["factors"], list)
    assert len(data["factors"]) > 0

    # Test API_SPEC alias /api/v1/risk/ml/predict
    alias_resp = client.post("/api/v1/risk/ml/predict", json=predict_payload)
    assert alias_resp.status_code == 200

    # Test root compatibility endpoint /api/predict
    compat_resp = client.post("/api/predict", json=predict_payload)
    assert compat_resp.status_code == 200

def test_risk_latest_and_map():
    """Test /risk/latest and /risk/map endpoints."""
    latest_resp = client.get("/api/v1/risk/latest?location=Shillong")
    assert latest_resp.status_code == 200
    assert "riskLevel" in latest_resp.json()
    assert "riskScore" in latest_resp.json()

    map_resp = client.get("/api/v1/risk/map")
    assert map_resp.status_code == 200
    items = map_resp.json()
    assert isinstance(items, list)
    assert len(items) > 0
    assert "riskLevel" in items[0]

def test_location_aware_alert_filtering():
    """
    Test Location-Based Alerting:
    When alert is sent for East Khasi Hills (Shillong),
    only Rahul Bora (East Khasi Hills) receives it.
    Anisha Agrawal (Dima Hasao) and Keviselie (Kohima) do NOT receive it.
    """
    db = SessionLocal()
    try:
        shillong_citizens = notification_service.find_affected_citizens(
            target_location_name="Shillong, Meghalaya",
            target_district="East Khasi Hills",
            center_lat=25.5788,
            center_lon=91.8933,
            db=db
        )
        emails = [c.email for c in shillong_citizens]
        assert "rahul@slopesense.ai" in emails
        assert "citizen@slopesense.ai" not in emails  # In Dima Hasao
        assert "kevi@slopesense.ai" not in emails     # In Kohima
    finally:
        db.close()

def test_proximity_volunteer_dispatch():
    """
    Test Proximity-Based Volunteer Dispatch:
    When citizen in Dima Hasao requests NEED_HELP,
    the nearest volunteer (Tenzing Norgay in Dima Hasao) is prioritized and assigned.
    """
    db = SessionLocal()
    try:
        citizen_dima = db.query(User).filter(User.email == "citizen@slopesense.ai").first()
        nearest_vol, dist_km = escalation_service.find_nearest_volunteer(citizen_dima, db)
        assert nearest_vol is not None
        assert "Tenzing" in nearest_vol.full_name
        assert dist_km < 20.0  # Close proximity in same district
    finally:
        db.close()

def test_sms_and_ivr_response_parsing():
    """Test SMS text and IVR DTMF parsing into standard SAFE / NEED_HELP."""
    assert notification_service.parse_response_text("1") == "SAFE"
    assert notification_service.parse_response_text("SAFE") == "SAFE"
    assert notification_service.parse_response_text("I am safe") == "SAFE"
    assert notification_service.parse_response_text("2") == "NEED_HELP"
    assert notification_service.parse_response_text("HELP") == "NEED_HELP"
    assert notification_service.parse_response_text("Need rescue assistance") == "NEED_HELP"
    assert notification_service.parse_response_text("Unknown message") == "NO_RESPONSE"

def test_alert_lifecycle_and_citizen_response():
    """Test alert creation, listing, and citizen check-in."""
    # Login as authority
    auth_login = client.post("/api/v1/auth/login", json={
        "email": "authority@slopesense.ai",
        "password": "password123"
    })
    assert auth_login.status_code == 200, f"Authority login failed: {auth_login.text}"
    auth_token = auth_login.json()["access_token"]

    # Authority creates alert
    alert_payload = {
        "title": "URGENT TEST: High Landslide Warning",
        "description": "Heavy rainfall detected in Dima Hasao test sector.",
        "riskLevel": "HIGH",
        "district": "Dima Hasao",
        "sendSms": False,
        "sendIvr": False
    }
    create_resp = client.post(
        "/api/v1/alerts",
        json=alert_payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert create_resp.status_code == 201
    alert_id = create_resp.json()["id"]

    # Login as citizen
    cit_login = client.post("/api/v1/auth/login", json={
        "email": "citizen@slopesense.ai",
        "password": "password123"
    })
    assert cit_login.status_code == 200, f"Citizen login failed: {cit_login.text}"
    cit_token = cit_login.json()["access_token"]

    # Citizen responds NEED_HELP (SOS)
    resp_payload = {
        "alertId": alert_id,
        "response": "NEED_HELP"
    }
    respond_resp = client.post(
        "/api/v1/alerts/respond",
        json=resp_payload,
        headers={"Authorization": f"Bearer {cit_token}"}
    )
    assert respond_resp.status_code == 200
    assert respond_resp.json()["response_type"] == "NEED_HELP"
    assert respond_resp.json()["escalated"] is True

    # Check alert details
    detail_resp = client.get(f"/api/v1/alerts/{alert_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["need_help_count"] >= 1

def test_community_hazard_report():
    """Test community ground hazard report submission."""
    cit_login = client.post("/api/v1/auth/login", json={
        "email": "citizen@slopesense.ai",
        "password": "password123"
    })
    assert cit_login.status_code == 200
    cit_token = cit_login.json()["access_token"]

    rep_payload = {
        "observationType": "ROAD_CRACK",
        "description": "5-meter wide ground fissure observed across hill road",
        "latitude": 25.1720,
        "longitude": 93.1235
    }
    rep_resp = client.post(
        "/api/v1/reports",
        json=rep_payload,
        headers={"Authorization": f"Bearer {cit_token}"}
    )
    assert rep_resp.status_code == 201
    assert rep_resp.json()["observation_type"] == "ROAD_CRACK"

def test_volunteer_operations():
    """Test volunteer case queues and field verification."""
    vol_login = client.post("/api/v1/auth/login", json={
        "email": "volunteer@slopesense.ai",
        "password": "password123"
    })
    assert vol_login.status_code == 200, f"Volunteer login failed: {vol_login.text}"
    vol_token = vol_login.json()["access_token"]

    # Fetch cases
    cases_resp = client.get(
        "/api/v1/volunteer/cases",
        headers={"Authorization": f"Bearer {vol_token}"}
    )
    assert cases_resp.status_code == 200
    cases = cases_resp.json()
    assert isinstance(cases, list)

    if len(cases) > 0:
        case_id = cases[0]["id"]
        # Volunteer verifies case
        verify_payload = {
            "caseId": case_id,
            "status": "CONFIRMED",
            "findings": "Inspected ground: active soil displacement confirmed."
        }
        v_resp = client.post(
            "/api/v1/volunteer/verify",
            json=verify_payload,
            headers={"Authorization": f"Bearer {vol_token}"}
        )
        assert v_resp.status_code == 200
        assert v_resp.json()["verification_status"] == "CONFIRMED"

def test_authority_dashboard_and_analytics():
    """Test authority command center endpoints."""
    dash_resp = client.get("/api/v1/authority/dashboard")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "activeAlerts" in dash_data
    assert "safeCitizens" in dash_data

    comm_resp = client.get("/api/v1/authority/community-status")
    assert comm_resp.status_code == 200

    vol_resp = client.get("/api/v1/authority/volunteers")
    assert vol_resp.status_code == 200

    analytics_resp = client.get("/api/v1/authority/analytics")
    assert analytics_resp.status_code == 200
    assert len(analytics_resp.json()) > 0
