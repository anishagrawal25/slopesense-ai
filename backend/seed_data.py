"""
Database Seeding Script for SlopeSense AI.
Populates default approved users for all roles (Citizen, Volunteer, Authority, Admin)
and a sample pending volunteer registration for testing the approval workflow.
"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from datetime import datetime, timedelta
from backend.core.database import SessionLocal, Base, engine
from backend.core.security import get_password_hash
from backend.models.user import User
from backend.models.risk import RiskPrediction, RiskZone
from backend.models.alert import Alert, AlertRecipient, AlertResponse
from backend.models.report import Report, EmergencyCase, VolunteerAssignment, VerificationReport
from backend.models.system import Notification, AuditLog
from backend.services.ml_service import ml_service
from backend.services.gee_service import NORTHEAST_MONITORING_POINTS

def seed_initial_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if authority user exists
        auth_user = db.query(User).filter(User.email == "authority@slopesense.ai").first()
        if auth_user:
            return  # Already seeded

        print("[Seed] Seeding initial SlopeSense AI data...")

        # 1. Create Core Role Users
        citizen1 = User(
            full_name="Anisha Agrawal",
            email="citizen@slopesense.ai",
            phone_number="+919876543210",
            password_hash=get_password_hash("password123"),
            role="citizen",
            state="Assam",
            district="Dima Hasao",
            village_area="Haflong Hill Sector 4",
            status="approved",
            is_active=True,
            latitude=25.1718,
            longitude=93.1230
        )
        citizen2 = User(
            full_name="Rahul Bora",
            email="rahul@slopesense.ai",
            phone_number="+919876543213",
            password_hash=get_password_hash("password123"),
            role="citizen",
            state="Meghalaya",
            district="East Khasi Hills",
            village_area="Shillong Peak Corridor",
            status="approved",
            is_active=True,
            latitude=25.5788,
            longitude=91.8933
        )
        citizen3 = User(
            full_name="Keviselie Angami",
            email="kevi@slopesense.ai",
            phone_number="+919876543215",
            password_hash=get_password_hash("password123"),
            role="citizen",
            state="Nagaland",
            district="Kohima",
            village_area="Bypass Sector",
            status="approved",
            is_active=True,
            latitude=25.6747,
            longitude=94.1105
        )
        volunteer1 = User(
            full_name="Tenzing Norgay",
            email="volunteer@slopesense.ai",
            phone_number="+919876543211",
            password_hash=get_password_hash("password123"),
            role="volunteer",
            state="Assam",
            district="Dima Hasao",
            village_area="Haflong Town",
            status="approved",
            is_active=True,
            latitude=25.1600,
            longitude=93.1100
        )
        volunteer_pending = User(
            full_name="Rohit Das (Applicant)",
            email="pending_vol@slopesense.ai",
            phone_number="+919876543299",
            password_hash=get_password_hash("password123"),
            role="volunteer",
            state="Assam",
            district="Dima Hasao",
            village_area="Jatinga Sector",
            status="pending",
            is_active=True,
            latitude=25.1550,
            longitude=93.0280
        )
        authority1 = User(
            full_name="SDMA Disaster Control Commissioner",
            email="authority@slopesense.ai",
            phone_number="+919876543212",
            password_hash=get_password_hash("password123"),
            role="authority",
            state="Assam",
            district="State Disaster Management Authority",
            village_area="Disaster Command HQ",
            status="approved",
            is_active=True,
            latitude=26.1445,
            longitude=91.7362
        )
        admin1 = User(
            full_name="System Super Administrator",
            email="admin@slopesense.ai",
            phone_number="+919876543200",
            password_hash=get_password_hash("password123"),
            role="admin",
            state="Assam",
            district="State Capital Secretariat",
            village_area="HQ Admin",
            status="approved",
            is_active=True,
            latitude=26.1445,
            longitude=91.7362
        )

        db.add_all([citizen1, citizen2, citizen3, volunteer1, volunteer_pending, authority1, admin1])
        db.commit()
        db.refresh(citizen1)
        db.refresh(citizen2)
        db.refresh(volunteer1)
        db.refresh(authority1)

        # 2. Seed Baseline Predictions & Risk Zones from Monitoring Points
        saved_predictions = []
        for point in NORTHEAST_MONITORING_POINTS:
            pred = ml_service.predict_risk(point, db=db, save_to_db=True)
            db_pred = db.query(RiskPrediction).filter(RiskPrediction.id == pred.get("id")).first()
            if db_pred:
                saved_predictions.append(db_pred)
                zone = RiskZone(
                    prediction_id=db_pred.id,
                    zone_name=f"{point['location_name']} Sector",
                    district=point["district"],
                    state=point["state"],
                    risk_level=db_pred.risk_level,
                    created_at=datetime.utcnow()
                )
                db.add(zone)

        db.commit()

        # 3. Create Sample Active Alert in Dima Hasao
        high_pred = next((p for p in saved_predictions if p.risk_level in ("HIGH", "CRITICAL")), saved_predictions[0])
        alert1 = Alert(
            prediction_id=high_pred.id,
            title="CRITICAL RED ALERT: Imminent Slope Failure in Haflong Hill",
            description=(
                "Continuous torrential rainfall (125mm in 24h) has triggered severe soil saturation "
                "along NH-54 and Haflong bypass. Immediate evacuation to Haflong Relief Camp ordered."
            ),
            risk_level="CRITICAL",
            status="ACTIVE",
            sent_at=datetime.utcnow() - timedelta(minutes=45),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(alert1)
        db.commit()
        db.refresh(alert1)

        # 4. Alert Recipients
        rc1 = AlertRecipient(
            alert_id=alert1.id,
            user_id=citizen1.id,
            delivery_method="SMS",
            delivered_at=datetime.utcnow() - timedelta(minutes=44),
            delivery_status="DELIVERED"
        )
        rc2 = AlertRecipient(
            alert_id=alert1.id,
            user_id=citizen2.id,
            delivery_method="IVR",
            delivered_at=datetime.utcnow() - timedelta(minutes=43),
            delivery_status="DELIVERED"
        )
        db.add_all([rc1, rc2])

        # 5. Alert Responses & Escalations
        resp1 = AlertResponse(
            alert_id=alert1.id,
            user_id=citizen1.id,
            response_type="NEED_HELP",
            responded_at=datetime.utcnow() - timedelta(minutes=30)
        )
        resp2 = AlertResponse(
            alert_id=alert1.id,
            user_id=citizen2.id,
            response_type="SAFE",
            responded_at=datetime.utcnow() - timedelta(minutes=25)
        )
        db.add_all([resp1, resp2])
        db.commit()
        db.refresh(resp1)

        # 6. Emergency Case & Volunteer Assignment for NEED_HELP
        case1 = EmergencyCase(
            alert_response_id=resp1.id,
            citizen_id=citizen1.id,
            case_type="NEED_HELP",
            priority="CRITICAL",
            status="IN_PROGRESS",
            notes="Elderly family trapped on steep lower slope near Haflong Lake road.",
            created_at=datetime.utcnow() - timedelta(minutes=28)
        )
        db.add(case1)
        db.commit()
        db.refresh(case1)

        assign1 = VolunteerAssignment(
            volunteer_id=volunteer1.id,
            alert_id=alert1.id,
            emergency_case_id=case1.id,
            priority="CRITICAL",
            status="IN_PROGRESS",
            assigned_at=datetime.utcnow() - timedelta(minutes=26)
        )
        db.add(assign1)
        db.commit()
        db.refresh(assign1)

        # Volunteer Verification Report
        v_report1 = VerificationReport(
            assignment_id=assign1.id,
            volunteer_id=volunteer1.id,
            findings="Inspected site: 3-meter road crack with ongoing mud sliding. Family safely escorted to high ground.",
            evidence_url=None,
            verification_status="CONFIRMED",
            verified_at=datetime.utcnow() - timedelta(minutes=15)
        )
        db.add(v_report1)

        # 7. Non-responsive case (NO_RESPONSE)
        case2 = EmergencyCase(
            alert_response_id=None,
            citizen_id=citizen3.id,
            case_type="NO_RESPONSE",
            priority="HIGH",
            status="OPEN",
            notes="No SMS/IVR response received from Kohima resident after alert broadcast.",
            created_at=datetime.utcnow() - timedelta(minutes=35)
        )
        db.add(case2)

        # 8. Community Reports
        rep1 = Report(
            user_id=citizen1.id,
            alert_id=alert1.id,
            observation_type="ROAD_CRACK",
            description="Massive longitudinal cracks appearing across NH-54 curve near Haflong.",
            image_url=None,
            latitude=25.1725,
            longitude=93.1245,
            status="VOLUNTEER_VERIFIED",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        rep2 = Report(
            user_id=citizen2.id,
            alert_id=alert1.id,
            observation_type="SOIL_MOVEMENT",
            description="Mud and gravel washing down slopes onto village path.",
            image_url=None,
            latitude=25.1680,
            longitude=93.1190,
            status="COMMUNITY_CONFIRMED",
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        rep3 = Report(
            user_id=citizen1.id,
            alert_id=alert1.id,
            observation_type="FALLING_ROCKS",
            description="Boulders falling near railway tunnel section.",
            image_url=None,
            latitude=25.1750,
            longitude=93.1290,
            status="PENDING",
            created_at=datetime.utcnow() - timedelta(minutes=20)
        )
        db.add_all([rep1, rep2, rep3])

        # 9. In-App Notifications
        notif1 = Notification(
            user_id=citizen1.id,
            title="Red Alert Dispatched",
            message=alert1.description,
            type="ALERT",
            is_read=False
        )
        notif2 = Notification(
            user_id=volunteer1.id,
            title="High-Priority Rescue Dispatch",
            message="Citizen Anisha Agrawal needs urgent rescue support near Haflong.",
            type="ASSIGNMENT",
            is_read=False
        )
        notif3 = Notification(
            user_id=authority1.id,
            title="Live Disaster Overview",
            message="1 Critical alert active in Dima Hasao. 1 Emergency rescue in progress.",
            type="SYSTEM",
            is_read=False
        )
        db.add_all([notif1, notif2, notif3])

        db.commit()
        print("[Seed] Successfully seeded SlopeSense AI database with demo data!")
    except Exception as e:
        db.rollback()
        print(f"[Seed] Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_data()
