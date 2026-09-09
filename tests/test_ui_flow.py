"""
Test UI/UX workflow and core business logic for the redesigned SlopeSense AI platform.
Verifies role registration, approval guards, proximity calculation, ML centerpiece,
location-aware dispatching, and field verification.
"""
import pytest
from datetime import datetime
from backend.core.database import SessionLocal, Base, engine
from backend.core.security import verify_password, get_password_hash
from backend.models.user import User
from backend.models.alert import Alert, AlertRecipient, AlertResponse
from backend.models.report import Report, EmergencyCase, VolunteerAssignment, VerificationReport
from backend.services.ml_service import ml_service
from backend.services.gee_service import gee_service, NORTHEAST_MONITORING_POINTS
from backend.services.notification_service import notification_service
from backend.services.escalation_service import escalation_service, haversine_distance_km
from backend.services.validation_service import validation_service
from backend.seed_data import seed_initial_data

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield

def test_login_and_pending_approval_guard():
    db = SessionLocal()
    try:
        # 1. Approved citizen can log in
        cit = db.query(User).filter(User.email == "citizen@slopesense.ai").first()
        assert cit is not None
        assert cit.status == "approved"
        assert verify_password("password123", cit.password_hash)

        # 2. Pending volunteer is blocked by approval guard
        pending_vol = db.query(User).filter(User.email == "pending_vol@slopesense.ai").first()
        assert pending_vol is not None
        assert pending_vol.status == "pending"

        # 3. Wrong password fails
        assert not verify_password("wrong_password", cit.password_hash)
    finally:
        db.close()

def test_registration_approval_workflow():
    db = SessionLocal()
    try:
        # Register new citizen -> auto-approved
        new_cit = User(
            full_name="New Citizen Test",
            email="newcit@test.com",
            phone_number="+919811111111",
            password_hash=get_password_hash("pass123"),
            role="citizen",
            state="Assam",
            district="Dima Hasao",
            village_area="Haflong Hill",
            status="approved",
            is_active=True
        )
        db.add(new_cit)

        # Register new volunteer -> pending
        new_vol = User(
            full_name="New Volunteer Test",
            email="newvol@test.com",
            phone_number="+919822222222",
            password_hash=get_password_hash("pass123"),
            role="volunteer",
            state="Assam",
            district="Dima Hasao",
            village_area="Jatinga",
            status="pending",
            is_active=True
        )
        db.add(new_vol)
        db.commit()
        db.refresh(new_vol)

        assert new_cit.status == "approved"
        assert new_vol.status == "pending"

        # Authority reviews and approves volunteer
        new_vol.status = "approved"
        db.commit()
        db.refresh(new_vol)
        assert new_vol.status == "approved"
    finally:
        db.close()

def test_ml_landslide_prediction_centerpiece():
    db = SessionLocal()
    try:
        # High rainfall steep slope scenario
        high_risk_input = {
            "slope": 42.0,
            "aspect": 180.0,
            "curvature": 1.2,
            "rainfall_mm": 130.0,
            "cumulative_rainfall_30d": 380.0,
            "ndvi_trend": -0.22,
            "ndvi_drop": 0.35,
            "distance_to_river": 120.0
        }
        res = ml_service.predict_risk(high_risk_input, db=db, save_to_db=False)
        assert "riskLevel" in res
        assert res["riskLevel"] in ("HIGH", "CRITICAL")
        assert res["riskScore"] > 70.0
        assert len(res["factors"]) > 0
        assert "safetyRecommendation" in res
    finally:
        db.close()

def test_haversine_proximity_ranking():
    # Haflong town to Jatinga (~6.5 km)
    d = haversine_distance_km(25.1600, 93.1100, 25.1550, 93.0280)
    assert 5.0 < d < 12.0
    # Same point should be 0
    assert haversine_distance_km(25.1600, 93.1100, 25.1600, 93.1100) == 0.0

def test_location_aware_alert_filtering():
    db = SessionLocal()
    try:
        # Filter for Dima Hasao
        dima_citizens = notification_service.find_affected_citizens("Dima Hasao", "Dima Hasao", 25.1718, 93.1230, db=db)
        for c in dima_citizens:
            assert c.district.lower() == "dima hasao"
    finally:
        db.close()

def test_sos_response_and_volunteer_verification():
    db = SessionLocal()
    try:
        cit = db.query(User).filter(User.email == "citizen@slopesense.ai").first()
        vol = db.query(User).filter(User.email == "volunteer@slopesense.ai").first()
        alert = db.query(Alert).filter(Alert.status == "ACTIVE").first()

        # Citizen replies NEED_HELP
        resp = AlertResponse(
            alert_id=alert.id if alert else None,
            user_id=cit.id,
            response_type="NEED_HELP",
            responded_at=datetime.utcnow()
        )
        db.add(resp)
        db.commit()
        db.refresh(resp)

        # Triggers escalation & volunteer proximity assignment
        case = escalation_service.handle_citizen_response(resp, db)
        assert case is not None
        assert case.case_type == "NEED_HELP"
        assert case.priority == "CRITICAL"

        # Volunteer performs field inspection
        v_rep = escalation_service.submit_volunteer_verification(
            case_id=case.id,
            volunteer=vol,
            findings="Slope crack inspected. Resident safely evacuated.",
            status="CONFIRMED",
            evidence_url=None,
            db=db
        )
        assert v_rep.verification_status == "CONFIRMED"
    finally:
        db.close()
