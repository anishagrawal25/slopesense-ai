"""
Community Validation Engine.
Evaluates incoming citizen reports, calculates spatial/temporal proximity clustering,
and promotes reports:
1 Report -> PENDING
3 Similar Reports in proximity -> COMMUNITY_CONFIRMED
Volunteer Verification -> VOLUNTEER_VERIFIED
"""
import math
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.report import Report
from backend.models.system import AuditLog

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great circle distance in kilometers between two coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class ValidationService:
    def process_new_report(self, report: Report, db: Session) -> str:
        """
        Evaluates a newly submitted report against existing recent reports in the area.
        If >= 3 reports of similar observation type occur within 2km and 6 hours,
        auto-promotes all matching reports to COMMUNITY_CONFIRMED.
        """
        six_hours_ago = datetime.utcnow() - timedelta(hours=6)
        recent_reports = (
            db.query(Report)
            .filter(
                Report.observation_type == report.observation_type,
                Report.created_at >= six_hours_ago,
                Report.status.in_(["PENDING", "COMMUNITY_CONFIRMED"])
            )
            .all()
        )

        nearby_matching_reports = []
        for r in recent_reports:
            dist = haversine_distance_km(report.latitude, report.longitude, r.latitude, r.longitude)
            if dist <= 2.0:  # within 2 km radius
                nearby_matching_reports.append(r)

        # Check if cluster threshold is met (including current report)
        if len(nearby_matching_reports) >= 3:
            for r in nearby_matching_reports:
                if r.status == "PENDING":
                    r.status = "COMMUNITY_CONFIRMED"
            
            report.status = "COMMUNITY_CONFIRMED"
            
            audit = AuditLog(
                action="COMMUNITY_CONFIRMED_CLUSTER",
                entity_type="REPORT",
                entity_id=report.id,
                details=f"Auto-confirmed cluster of {len(nearby_matching_reports)} reports of type {report.observation_type}"
            )
            db.add(audit)
            db.commit()
            return "COMMUNITY_CONFIRMED"
        
        return report.status

validation_service = ValidationService()
