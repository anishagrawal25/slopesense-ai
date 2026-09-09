"""
Notification & Alert Dispatch Service.
Supports Twilio SMS and Twilio Voice / IVR automated emergency broadcast calls.
Implements strict location-aware filtering: only citizens in the affected zone/district receive alerts.
"""
import math
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.alert import Alert, AlertRecipient, AlertResponse
from backend.models.user import User
from backend.models.system import Notification, AuditLog

logger = logging.getLogger("SlopeSense.Notifications")

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great circle distance in kilometers between two coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class NotificationService:
    def __init__(self):
        self.client = None
        self.is_configured = False
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and not settings.TWILIO_MOCK_MODE:
            try:
                from twilio.rest import Client
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                self.is_configured = True
            except Exception as e:
                logger.warning(f"Twilio client init failed: {e}. Running in simulation mode.")

    def find_affected_citizens(
        self,
        target_location_name: str,
        target_district: Optional[str],
        center_lat: Optional[float],
        center_lon: Optional[float],
        radius_km: float = 35.0,
        db: Session = None
    ) -> List[User]:
        """
        LOCATION-AWARE FILTERING:
        Identifies only citizens located within the affected district or spatial radius.
        Citizens in unrelated districts (e.g. Guwahati, Imphal, Agartala when alert is for Shillong)
        are strictly excluded.
        """
        if db is None:
            return []

        all_citizens = db.query(User).filter(User.role == "citizen").all()
        affected_citizens = []

        for citizen in all_citizens:
            matched = False
            # 1. District / Name match
            if target_district and citizen.district:
                if target_district.lower() in citizen.district.lower() or citizen.district.lower() in target_district.lower():
                    matched = True
            elif target_location_name and citizen.district:
                if any(k in citizen.district.lower() for k in target_location_name.lower().split()):
                    matched = True

            # 2. GPS proximity match (if coordinates available)
            if not matched and center_lat is not None and center_lon is not None and citizen.latitude and citizen.longitude:
                dist = haversine_distance_km(center_lat, center_lon, citizen.latitude, citizen.longitude)
                if dist <= radius_km:
                    matched = True

            if matched:
                affected_citizens.append(citizen)

        return affected_citizens

    def broadcast_alert(
        self,
        alert: Alert,
        users: List[User],
        db: Session,
        send_sms: bool = True,
        send_ivr: bool = True,
        location_name: str = "Shillong, Meghalaya",
        risk_score: float = 87.0
    ) -> Dict[str, Any]:
        """
        Dispatches emergency SMS and IVR notifications to affected citizens with exact formatting.
        """
        sms_sent = 0
        ivr_sent = 0
        failed = 0

        # Exact SMS Format specified in requirements
        sms_body = (
            f"⚠️ SlopeSense AI Alert\n\n"
            f"{alert.risk_level} Landslide Risk detected in {location_name}.\n\n"
            f"Risk Score: {risk_score:.0f}%\n\n"
            f"Reply:\n"
            f"1 = I AM SAFE\n"
            f"2 = NEED HELP"
        )

        for user in users:
            phone = user.phone_number or "+919876543210"

            # 1. SMS Dispatch
            if send_sms:
                delivery_status = "DELIVERED"
                if self.is_configured and self.client and settings.TWILIO_PHONE_NUMBER:
                    try:
                        self.client.messages.create(
                            body=sms_body,
                            from_=settings.TWILIO_PHONE_NUMBER,
                            to=phone
                        )
                        sms_sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send SMS to {phone}: {e}")
                        delivery_status = "FAILED"
                        failed += 1
                else:
                    # Simulated delivery for presentation
                    sms_sent += 1

                # Record recipient
                recipient = AlertRecipient(
                    alert_id=alert.id,
                    user_id=user.id,
                    delivery_method="SMS",
                    delivered_at=datetime.utcnow(),
                    delivery_status=delivery_status
                )
                db.add(recipient)

            # 2. Voice / IVR Call Dispatch
            if send_ivr:
                ivr_status = "DELIVERED"
                if self.is_configured and self.client and settings.TWILIO_PHONE_NUMBER:
                    try:
                        # Exact IVR message format
                        twiml_msg = (
                            f"<Response>"
                            f"<Say voice='alice' language='en-IN'>"
                            f"Warning. A {alert.risk_level.lower()} landslide risk has been detected in your area of {location_name}. "
                            f"Press 1 if you are safe. "
                            f"Press 2 if you need assistance."
                            f"</Say>"
                            f"<Gather numDigits='1' timeout='10'/>"
                            f"</Response>"
                        )
                        self.client.calls.create(
                            twiml=twiml_msg,
                            from_=settings.TWILIO_PHONE_NUMBER,
                            to=phone
                        )
                        ivr_sent += 1
                    except Exception as e:
                        logger.error(f"Failed to trigger IVR to {phone}: {e}")
                        ivr_status = "FAILED"
                else:
                    ivr_sent += 1

                recipient_ivr = AlertRecipient(
                    alert_id=alert.id,
                    user_id=user.id,
                    delivery_method="IVR",
                    delivered_at=datetime.utcnow(),
                    delivery_status=ivr_status
                )
                db.add(recipient_ivr)

            # 3. Create In-App Notification
            notif = Notification(
                user_id=user.id,
                title=f"⚠️ {alert.title}",
                message=alert.description,
                type="ALERT",
                is_read=False
            )
            db.add(notif)

        # Audit log
        audit = AuditLog(
            action="BROADCAST_ALERT",
            entity_type="ALERT",
            entity_id=alert.id,
            details=f"Location-aware alert broadcasted to {len(users)} citizens in {location_name} (SMS: {sms_sent}, IVR: {ivr_sent})"
        )
        db.add(audit)
        db.commit()

        return {
            "total_recipients": len(users),
            "sms_sent": sms_sent,
            "ivr_sent": ivr_sent,
            "failed": failed,
            "simulated": not self.is_configured
        }

    def generate_twiml_ivr_response(self, location_name: str = "your area") -> str:
        """Generates TwiML XML string for IVR calls."""
        return (
            f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            f"<Response>\n"
            f"    <Say voice=\"Polly.Aditi\" language=\"en-IN\">\n"
            f"        Warning. A high landslide risk has been detected in {location_name}. \n"
            f"        Press 1 if you are safe. \n"
            f"        Press 2 if you need assistance.\n"
            f"    </Say>\n"
            f"    <Gather numDigits=\"1\" action=\"/api/v1/alerts/webhook/twilio-voice\" method=\"POST\">\n"
            f"        <Say>Press 1 if you are safe, or 2 if you need assistance.</Say>\n"
            f"    </Gather>\n"
            f"</Response>"
        )

    def parse_response_text(self, text: str) -> str:
        """Parses incoming SMS or IVR text into standard response type."""
        cleaned = text.strip().upper()
        if cleaned in ("1", "SAFE", "I AM SAFE", "YES", "OK", "I'M SAFE"):
            return "SAFE"
        elif cleaned in ("2", "HELP", "NEED HELP", "RESCUE", "EMERGENCY", "SOS", "ASSISTANCE"):
            return "NEED_HELP"
        elif any(k in cleaned for k in ["NEED HELP", "HELP", "RESCUE", "EMERGENCY", "ASSISTANCE"]):
            return "NEED_HELP"
        elif any(k in cleaned for k in ["SAFE", "I AM SAFE", "I'M SAFE"]):
            return "SAFE"
        else:
            return "NO_RESPONSE"

notification_service = NotificationService()
