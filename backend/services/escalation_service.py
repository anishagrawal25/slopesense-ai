"""
Critical Response and Volunteer Escalation Service.
Implements the mandatory disaster response workflow:
Citizen Response (NEED_HELP / NO_RESPONSE)
   ↓
Emergency Case Created
   ↓
Assign Nearby Volunteer (Proximity-based Haversine ranking)
   ↓
Field Verification
   ↓
Authority Review & Resolution
"""
import math
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.alert import AlertResponse, Alert
from backend.models.report import EmergencyCase, VolunteerAssignment, VerificationReport
from backend.models.user import User
from backend.models.system import Notification, AuditLog

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great circle distance in kilometers between two coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class EscalationService:
    def find_nearest_volunteer(
        self,
        citizen: User,
        db: Session
    ) -> Tuple[Optional[User], Optional[float]]:
        """
        LOCATION-BASED VOLUNTEER DISPATCH:
        Finds the nearest active volunteer prioritized by:
        1. Closest Haversine distance in kilometers
        2. Same district matching
        """
        volunteers = db.query(User).filter(User.role == "volunteer", User.status == "approved").all()
        if not volunteers:
            return None, None

        cit_lat = citizen.latitude or 25.1718
        cit_lon = citizen.longitude or 93.1230

        scored_volunteers = []
        for vol in volunteers:
            vol_lat = vol.latitude or 25.1718
            vol_lon = vol.longitude or 93.1230
            dist = haversine_distance_km(cit_lat, cit_lon, vol_lat, vol_lon)
            
            # If in same district, give proximity bonus (subtract virtual distance)
            same_district = (vol.district and citizen.district and vol.district.lower() == citizen.district.lower())
            score = dist - (10.0 if same_district else 0.0)
            
            scored_volunteers.append((score, dist, vol))

        scored_volunteers.sort(key=lambda x: x[0])
        best_score, actual_dist, best_vol = scored_volunteers[0]
        return best_vol, round(actual_dist, 1)

    def handle_citizen_response(
        self,
        alert_response: AlertResponse,
        db: Session
    ) -> Optional[EmergencyCase]:
        """
        Executes critical response workflow on incoming citizen check-in.
        """
        user = alert_response.user
        alert = alert_response.alert

        if alert_response.response_type == "SAFE":
            audit = AuditLog(
                user_id=user.id,
                action="CITIZEN_SAFE",
                entity_type="ALERT_RESPONSE",
                entity_id=alert_response.id,
                details=f"Citizen {user.full_name} ({user.district or 'Northeast'}) marked SAFE."
            )
            db.add(audit)
            db.commit()
            return None

        # Determine priority and case type
        if alert_response.response_type == "NEED_HELP":
            case_type = "NEED_HELP"
            priority = "CRITICAL"
            notes = f"Citizen {user.full_name} ({user.phone_number or 'No phone'}) in {user.district or 'vulnerable zone'} requested immediate rescue assistance."
        else:  # NO_RESPONSE
            case_type = "NO_RESPONSE"
            priority = "HIGH"
            notes = f"No response received from citizen {user.full_name} ({user.district or 'sector'}) after early warning delivery."

        # Create Emergency Case
        emergency_case = EmergencyCase(
            alert_response_id=alert_response.id,
            citizen_id=user.id,
            case_type=case_type,
            priority=priority,
            status="OPEN",
            notes=notes,
            created_at=datetime.utcnow()
        )
        db.add(emergency_case)
        db.flush()

        # Find nearest volunteer based on location proximity
        nearest_volunteer, distance_km = self.find_nearest_volunteer(user, db)

        if nearest_volunteer:
            assignment = VolunteerAssignment(
                volunteer_id=nearest_volunteer.id,
                alert_id=alert.id if alert else None,
                emergency_case_id=emergency_case.id,
                priority=priority,
                status="ASSIGNED",
                assigned_at=datetime.utcnow()
            )
            db.add(assignment)
            emergency_case.status = "ASSIGNED"
            dist_str = f"{distance_km} km away" if distance_km is not None else "same sector"
            emergency_case.notes = f"{emergency_case.notes} [Assigned to nearest responder {nearest_volunteer.full_name}, {dist_str}]"

            # Notify Volunteer
            notif = Notification(
                user_id=nearest_volunteer.id,
                title=f"🚨 PROXIMITY DISPATCH: {case_type} Case ({dist_str})",
                message=f"Citizen {user.full_name} at {user.district or 'vulnerable area'} needs field response: {notes}",
                type="ASSIGNMENT",
                is_read=False
            )
            db.add(notif)

        # Notify Authorities
        authorities = db.query(User).filter(User.role == "authority").all()
        for auth in authorities:
            notif = Notification(
                user_id=auth.id,
                title=f"🚨 Critical Escalation: {case_type}",
                message=f"Incident in {user.district or 'Northeast'}: {user.full_name} ({case_type}). Case ID: {emergency_case.id}",
                type="ALERT",
                is_read=False
            )
            db.add(notif)

        db.commit()
        db.refresh(emergency_case)
        return emergency_case

    def submit_volunteer_verification(
        self,
        case_id: str,
        volunteer: User,
        findings: str,
        status: str,  # CONFIRMED, PARTIALLY_CONFIRMED, FALSE_ALARM
        evidence_url: Optional[str],
        db: Session
    ) -> VerificationReport:
        """
        Records volunteer ground verification and updates emergency case status.
        """
        emergency_case = db.query(EmergencyCase).filter(EmergencyCase.id == case_id).first()
        if not emergency_case:
            raise ValueError(f"Emergency case {case_id} not found")

        assignment = (
            db.query(VolunteerAssignment)
            .filter(VolunteerAssignment.emergency_case_id == case_id)
            .first()
        )
        if not assignment:
            assignment = VolunteerAssignment(
                volunteer_id=volunteer.id,
                emergency_case_id=emergency_case.id,
                priority=emergency_case.priority,
                status="IN_PROGRESS",
                assigned_at=datetime.utcnow()
            )
            db.add(assignment)
            db.flush()

        v_report = VerificationReport(
            assignment_id=assignment.id,
            volunteer_id=volunteer.id,
            findings=findings,
            evidence_url=evidence_url,
            verification_status=status,
            verified_at=datetime.utcnow()
        )
        db.add(v_report)

        if status == "CONFIRMED":
            emergency_case.status = "IN_PROGRESS"
            assignment.status = "IN_PROGRESS"
        elif status == "FALSE_ALARM":
            emergency_case.status = "RESOLVED"
            assignment.status = "RESOLVED"
        else:
            emergency_case.status = "IN_PROGRESS"

        audit = AuditLog(
            user_id=volunteer.id,
            action="VOLUNTEER_VERIFICATION_SUBMITTED",
            entity_type="EMERGENCY_CASE",
            entity_id=emergency_case.id,
            details=f"Volunteer {volunteer.full_name} verified status '{status}': {findings}"
        )
        db.add(audit)
        db.commit()
        db.refresh(v_report)
        return v_report

escalation_service = EscalationService()
