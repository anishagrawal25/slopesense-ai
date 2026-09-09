"""
SLOPESENSE AI — Disaster Intelligence & Emergency Response Platform.
A clean, intuitive, and modern web application for Citizens, Volunteers, and Disaster Authorities.
Designed for Northeast India (Assam, Meghalaya, Nagaland, Mizoram, Arunachal Pradesh, Manipur, Tripura, Sikkim).
"""
import os
import sys
import math
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal, engine, Base
from backend.core.security import verify_password, get_password_hash
from backend.models.user import User
from backend.models.risk import RiskPrediction, RiskZone
from backend.models.alert import Alert, AlertRecipient, AlertResponse
from backend.models.report import Report, EmergencyCase, VolunteerAssignment, VerificationReport
from backend.models.system import Notification, AuditLog
from backend.services.ml_service import ml_service
from backend.services.gee_service import gee_service, NORTHEAST_MONITORING_POINTS
from backend.services.notification_service import notification_service
from backend.services.escalation_service import escalation_service, haversine_distance_km
from backend.services.validation_service import validation_service
from backend.seed_data import seed_initial_data

# Ensure tables and seed data exist safely
try:
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
except Exception:
    pass

# ----------------- STREAMLIT PAGE CONFIG -----------------
st.set_page_config(
    page_title="SlopeSense AI | Citizen Safety & Disaster Alert Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- MODERN LIGHT THEME CSS & INPUT FIXES -----------------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a;
}

.stApp {
    background-color: #f8fafc;
}

.block-container {
    padding-top: 20px;
    padding-bottom: 48px;
    max-width: 1200px;
}

/* Fix Streamlit form inputs for clean light theme */
div[data-baseweb="input"], div[data-baseweb="base-input"] {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}
input, textarea {
    color: #0f172a !important;
    background-color: #ffffff !important;
}

/* Primary Button Styling */
button[kind="primary"] {
    background-color: #1e3a8a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
button[kind="primary"]:hover {
    background-color: #1e40af !important;
}

button[kind="secondary"] {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Modern Top Navigation Bar */
.site-navbar {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}
.brand-logo-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}
.brand-icon {
    width: 38px;
    height: 38px;
    background: #1e3a8a;
    color: #ffffff;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 18px;
}
.brand-name {
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.1;
}
.brand-tagline {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

/* Threat Status Banners */
.threat-banner-red {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 6px solid #dc2626;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 20px;
}
.threat-banner-yellow {
    background: #fefce8;
    border: 1px solid #fef08a;
    border-left: 6px solid #ca8a04;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 20px;
}
.threat-banner-green {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 6px solid #16a34a;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 20px;
}

.threat-title-red {
    color: #991b1b;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 4px;
}
.threat-title-yellow {
    color: #854d0e;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 4px;
}
.threat-title-green {
    color: #166534;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 4px;
}

.threat-desc {
    font-size: 13px;
    color: #334155;
    line-height: 1.5;
}
.threat-advice {
    background: #ffffff;
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid rgba(0,0,0,0.06);
}

/* Clean Card System */
.app-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}
.app-card-title {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}
.app-card-subtitle {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 14px;
}

/* Feature Item Row on Landing Page */
.feature-row {
    display: flex;
    gap: 14px;
    margin-bottom: 16px;
    align-items: flex-start;
}
.feature-badge {
    background: #eff6ff;
    border-radius: 8px;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: #1e3a8a;
    flex-shrink: 0;
}
.feature-title {
    font-weight: 700;
    font-size: 14px;
    color: #0f172a;
}
.feature-desc {
    font-size: 13px;
    color: #64748b;
    margin-top: 2px;
}

/* Citizen Action Boxes */
.action-box-safe {
    background: #f0fdf4;
    border: 2px solid #86efac;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.action-box-sos {
    background: #fef2f2;
    border: 2px solid #fca5a5;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}

/* Task Cards for Volunteers */
.task-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #dc2626;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
}
.task-card-welfare {
    border-left-color: #ea580c;
}

/* Badges / Pills */
.pill {
    display: inline-block;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
    border-radius: 20px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}
.pill-red { background: #fee2e2; color: #991b1b; }
.pill-orange { background: #ffedd5; color: #9a3412; }
.pill-yellow { background: #fef9c3; color: #854d0e; }
.pill-green { background: #dcfce7; color: #166534; }
.pill-blue { background: #dbeafe; color: #1e40af; }
.pill-gray { background: #f1f5f9; color: #475569; }

/* Helpline Dial Cards */
.help-dial-btn {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    margin-bottom: 6px;
}
.help-number {
    font-size: 16px;
    font-weight: 800;
    color: #1e3a8a;
}
.help-label {
    font-size: 11px;
    color: #64748b;
    font-weight: 600;
}
</style>""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None

def perform_login(email: str, raw_pass: str) -> bool:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not verify_password(raw_pass, user.password_hash):
            st.error("Incorrect email or password. Please try again.")
            return False

        if user.status == "pending":
            st.warning(
                f"Your account as a {user.role.title()} is currently awaiting verification by the Disaster Management Authority. Please check back shortly."
            )
            return False
        elif user.status == "rejected":
            st.error("Your registration was not approved. Please contact your local District Office.")
            return False

        st.session_state["auth_user"] = {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "phone": user.phone_number,
            "role": user.role,
            "state": user.state or "Assam",
            "district": user.district or "Dima Hasao",
            "village_area": user.village_area or "Central Sector",
            "latitude": user.latitude or 25.1718,
            "longitude": user.longitude or 93.1230
        }
        return True
    finally:
        db.close()

def demo_login(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if user.status == "pending":
                st.warning(
                    f"Account Verification Guard: Account '{user.full_name}' is currently PENDING review by the Authority."
                )
                return
            st.session_state["auth_user"] = {
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "phone": user.phone_number,
                "role": user.role,
                "state": user.state or "Assam",
                "district": user.district or "Dima Hasao",
                "village_area": user.village_area or "Central Sector",
                "latitude": user.latitude or 25.1718,
                "longitude": user.longitude or 93.1230
            }
            st.rerun()
    finally:
        db.close()

# ----------------- SCREEN 1: PUBLIC LANDING PAGE -----------------
if st.session_state["auth_user"] is None:
    # Clean Public Navbar
    st.markdown("""<div class="site-navbar">
<div class="brand-logo-wrap">
    <div class="brand-icon">S</div>
    <div>
        <div class="brand-name">SlopeSense AI</div>
        <div class="brand-tagline">Landslide Early Warning & Citizen Safety Network • Northeast India</div>
    </div>
</div>
<div>
    <span class="pill pill-blue">Official Safety Portal</span>
</div>
</div>""", unsafe_allow_html=True)

    # Hero Banner
    st.markdown("""<div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); border-radius: 12px; padding: 22px 24px; color: #ffffff; margin-bottom: 20px;">
<div style="font-size: 22px; font-weight: 800; margin-bottom: 6px;">Stay Safe from Landslides in Northeast India</div>
<div style="font-size: 14px; opacity: 0.92; line-height: 1.5; max-width: 780px;">
SlopeSense AI uses satellite weather telemetry and AI risk models to predict landslides before they happen.
Receive location-aware phone alerts, check in as safe, find emergency shelters, and request help from local rescue teams.
</div>
</div>""", unsafe_allow_html=True)

    c_left, c_right = st.columns([1.1, 1], gap="large")

    with c_left:
        st.markdown("""<div class="app-card">
<div class="app-card-title">How SlopeSense AI Protects Your Community</div>
<div class="app-card-subtitle">Real-time alerts, citizen safety check-ins, and local rescue coordination.</div>

<div class="feature-row">
    <div class="feature-badge">1</div>
    <div>
        <div class="feature-title">AI Landslide Risk Warnings</div>
        <div class="feature-desc">Detects dangerous hillside slope saturation and heavy monsoon rainfall in your district.</div>
    </div>
</div>

<div class="feature-row">
    <div class="feature-badge">2</div>
    <div>
        <div class="feature-title">Direct Phone Alerts (SMS & Voice Calls)</div>
        <div class="feature-desc">Citizens receive immediate SMS and automated phone calls with simple 1-click check-in options.</div>
    </div>
</div>

<div class="feature-row">
    <div class="feature-badge">3</div>
    <div>
        <div class="feature-title">Nearby Volunteer Response (SOS)</div>
        <div class="feature-desc">If you need help, the closest verified volunteer responder in your village is immediately notified.</div>
    </div>
</div>

<div class="feature-row" style="margin-bottom: 0;">
    <div class="feature-badge">4</div>
    <div>
        <div class="feature-title">Community Precursor Hazard Reporting</div>
        <div class="feature-desc">Easily report road cracks, falling boulders, or mud movements to help alert your neighbors.</div>
    </div>
</div>
</div>""", unsafe_allow_html=True)

    with c_right:
        st.markdown("""<div class="app-card">
<div class="app-card-title">Sign In / Register</div>
<div class="app-card-subtitle">Access your local safety dashboard or volunteer dispatch.</div>
""", unsafe_allow_html=True)

        tab_login, tab_register, tab_quick = st.tabs(["Sign In", "Create Account", "1-Click Demo Login"])

        with tab_login:
            with st.form("login_form"):
                email_in = st.text_input("Email Address:", placeholder="your.name@example.com")
                pass_in = st.text_input("Password:", type="password", placeholder="Enter your password")
                btn_login = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if btn_login:
                    if not email_in or not pass_in:
                        st.error("Please enter both email and password.")
                    else:
                        if perform_login(email_in, pass_in):
                            st.rerun()

        with tab_register:
            with st.form("register_form"):
                r_name = st.text_input("Full Name:", placeholder="e.g., Anisha Agrawal")
                r_phone = st.text_input("Mobile Number (for SMS Alerts):", placeholder="+91 98765 43210")
                r_email = st.text_input("Email Address:", placeholder="name@domain.com")

                c_st, c_dt = st.columns(2)
                with c_st:
                    r_state = st.selectbox("State:", ["Assam", "Meghalaya", "Nagaland", "Mizoram", "Arunachal Pradesh", "Manipur", "Tripura", "Sikkim"])
                with c_dt:
                    r_district = st.selectbox("District:", [
                        "Dima Hasao", "East Khasi Hills", "Kohima", "Aizawl", "Papum Pare", "Imphal West", "West Tripura", "East Sikkim"
                    ])

                r_area = st.text_input("Village / Neighborhood:", placeholder="e.g., Haflong Hill Sector 4")
                r_role = st.selectbox(
                    "Account Type:",
                    [
                        "Citizen (Instant Access)",
                        "Volunteer Responder (Requires Authority Verification)",
                        "Disaster Management Authority (Requires Admin Approval)"
                    ]
                )
                r_p1 = st.text_input("Create Password:", type="password")
                r_p2 = st.text_input("Confirm Password:", type="password")
                btn_reg = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if btn_reg:
                    if not r_name or not r_email or not r_phone or not r_p1:
                        st.error("Please fill in all required fields.")
                    elif r_p1 != r_p2:
                        st.error("Passwords do not match.")
                    elif len(r_p1) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        db = SessionLocal()
                        try:
                            exists = db.query(User).filter(User.email == r_email.strip().lower()).first()
                            if exists:
                                st.error("An account with this email already exists.")
                            else:
                                if "Citizen" in r_role:
                                    role_val = "citizen"
                                    status_val = "approved"
                                elif "Volunteer" in r_role:
                                    role_val = "volunteer"
                                    status_val = "pending"
                                else:
                                    role_val = "authority"
                                    status_val = "pending"

                                new_u = User(
                                    full_name=r_name.strip(),
                                    email=r_email.strip().lower(),
                                    phone_number=r_phone.strip(),
                                    password_hash=get_password_hash(r_p1),
                                    role=role_val,
                                    state=r_state,
                                    district=r_district,
                                    village_area=r_area.strip() or "General Area",
                                    status=status_val,
                                    is_active=True,
                                    latitude=25.1718,
                                    longitude=93.1230
                                )
                                db.add(new_u)
                                db.commit()

                                if status_val == "approved":
                                    st.success("Account created successfully! You can now sign in.")
                                elif role_val == "volunteer":
                                    st.info("Registration received. Your volunteer profile is awaiting verification by local authorities.")
                                else:
                                    st.info("Authority registration received. Awaiting system administrator approval.")
                        finally:
                            db.close()

        with tab_quick:
            st.caption("Click any profile below to explore the platform instantly:")
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                if st.button("Citizen (Local Resident)", use_container_width=True):
                    demo_login("citizen@slopesense.ai")
                if st.button("Authority (SDMA Officer)", use_container_width=True):
                    demo_login("authority@slopesense.ai")
            with c_d2:
                if st.button("Volunteer Responder", use_container_width=True):
                    demo_login("volunteer@slopesense.ai")
                if st.button("Super Administrator", use_container_width=True):
                    demo_login("admin@slopesense.ai")

            st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
            st.caption("Test Security Approval Guard:")
            if st.button("Test Pending Volunteer Profile", use_container_width=True):
                demo_login("pending_vol@slopesense.ai")

        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""<div style="text-align: center; color: #64748b; font-size: 13px; margin-top: 32px; padding: 16px; border-top: 1px solid #e2e8f0;">
<strong>SlopeSense AI</strong> — Disaster Intelligence & Community Safety Platform<br>
Built for State Disaster Management Authorities & Mountain Communities of Northeast India.
</div>""", unsafe_allow_html=True)
    st.stop()

# ----------------- SCREEN 2: AUTHENTICATED USER PORTAL -----------------
current_user = st.session_state["auth_user"]
role_str = current_user["role"].capitalize()

# User Navbar
st.markdown(f"""<div class="site-navbar">
<div class="brand-logo-wrap">
    <div class="brand-icon">S</div>
    <div>
        <div class="brand-name">SlopeSense AI</div>
        <div class="brand-tagline">Safety Portal • {current_user['district']}, {current_user['state']}</div>
    </div>
</div>
<div style="display: flex; align-items: center; gap: 14px;">
    <div style="text-align: right;">
        <div style="font-weight: 700; font-size: 14px; color: #0f172a;">{current_user['name']}</div>
        <span class="pill pill-blue">{role_str}</span>
    </div>
</div>
</div>""", unsafe_allow_html=True)

# Top Bar with Logout
top_info, top_out = st.columns([4, 1])
with top_info:
    st.caption(f"Logged in as: **{current_user['name']}** ({current_user['email']}) • Location: **{current_user['district']}** ({current_user.get('village_area', 'Central Sector')})")
with top_out:
    if st.button("Sign Out", type="secondary", use_container_width=True):
        st.session_state["auth_user"] = None
        st.rerun()

# ==============================================================================
# ROLE 1: CITIZEN SAFETY PORTAL
# ==============================================================================
if current_user["role"] == "citizen":
    db = SessionLocal()
    try:
        cit_lat = current_user.get("latitude", 25.1718)
        cit_lon = current_user.get("longitude", 93.1230)
        features = gee_service.get_features_for_location(
            cit_lat, cit_lon, location_name=f"{current_user['district']} Sector"
        )
        risk_pred = ml_service.predict_risk(features, db=db, save_to_db=False)
    finally:
        db.close()

    risk_lvl = risk_pred["riskLevel"]
    risk_score = risk_pred["riskScore"]

    # Status Banner
    if risk_lvl in ("CRITICAL", "HIGH"):
        st.markdown(f"""<div class="threat-banner-red">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div class="threat-title-red">High Landslide Risk in {current_user['district']}</div>
    <span class="pill pill-red">High Alert</span>
</div>
<div class="threat-desc">
    Heavy rainfall and saturated hillside soil have created dangerous ground conditions in your area. Calculated Risk Score: <strong>{risk_score:.0f}%</strong>.
</div>
<div class="threat-advice">
    <strong>What you should do:</strong> Avoid steep slope paths. Move to high ground or designated relief shelters if rain continues.
</div>
</div>""", unsafe_allow_html=True)
    elif risk_lvl == "MODERATE":
        st.markdown(f"""<div class="threat-banner-yellow">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div class="threat-title-yellow">Moderate Landslide Warning in {current_user['district']}</div>
    <span class="pill pill-yellow">Moderate Warning</span>
</div>
<div class="threat-desc">
    Moderate rainfall detected. Slope moisture levels are elevated. Calculated Risk Score: <strong>{risk_score:.0f}%</strong>.
</div>
<div class="threat-advice">
    <strong>What you should do:</strong> Stay alert, monitor local weather updates, and report any ground cracks.
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="threat-banner-green">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div class="threat-title-green">Normal / Safe Conditions in {current_user['district']}</div>
    <span class="pill pill-green">Safe</span>
</div>
<div class="threat-desc">
    No acute landslide danger detected in your sector. Weather telemetry and slope stability are within normal baseline.
</div>
<div class="threat-advice">
    <strong>Current Status:</strong> Normal conditions. No evacuation required.
</div>
</div>""", unsafe_allow_html=True)

    # Check In Actions
    st.markdown("""<div class="app-card">
<div class="app-card-title">Check In with Emergency Teams</div>
<div class="app-card-subtitle">Let authorities and local volunteers know your current safety status.</div>
""", unsafe_allow_html=True)

    col_btn_safe, col_btn_sos = st.columns(2, gap="medium")

    with col_btn_safe:
        st.markdown("""<div class="action-box-safe">
<div style="font-size: 16px; font-weight: 800; color: #166534; margin-bottom: 4px;">I AM SAFE</div>
<div style="font-size: 12px; color: #15803d; margin-bottom: 12px;">Confirm that you and your family are safe at home.</div>
</div>""", unsafe_allow_html=True)
        if st.button("Confirm: I Am Safe", type="secondary", use_container_width=True):
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == current_user["id"]).first()
                alert = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(Alert.sent_at.desc()).first()
                if user:
                    resp = AlertResponse(
                        alert_id=alert.id if alert else None,
                        user_id=user.id,
                        response_type="SAFE",
                        responded_at=datetime.utcnow()
                    )
                    db.add(resp)
                    db.commit()
                    st.success("Your status has been recorded as SAFE. Local disaster teams updated.")
            finally:
                db.close()

    with col_btn_sos:
        st.markdown("""<div class="action-box-sos">
<div style="font-size: 16px; font-weight: 800; color: #991b1b; margin-bottom: 4px;">REQUEST HELP (SOS)</div>
<div style="font-size: 12px; color: #b91c1c; margin-bottom: 12px;">Request immediate rescue assistance from nearby volunteers.</div>
</div>""", unsafe_allow_html=True)
        if st.button("Request Immediate Help (SOS)", type="primary", use_container_width=True):
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == current_user["id"]).first()
                alert = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(Alert.sent_at.desc()).first()
                if user:
                    resp = AlertResponse(
                        alert_id=alert.id if alert else None,
                        user_id=user.id,
                        response_type="NEED_HELP",
                        responded_at=datetime.utcnow()
                    )
                    db.add(resp)
                    db.commit()
                    db.refresh(resp)
                    case = escalation_service.handle_citizen_response(resp, db)
                    st.error(f"HELP REQUEST SENT: Nearest registered volunteer has been dispatched to your location in {current_user['district']}.")
            finally:
                db.close()

    st.markdown("</div>", unsafe_allow_html=True)

    # Safe Shelters & Map + Community Hazard Reporting
    c_map, c_side = st.columns([1.3, 1], gap="medium")

    with c_map:
        st.markdown("""<div class="app-card">
<div class="app-card-title">Nearby Safe Shelters & Evacuation Map</div>
<div class="app-card-subtitle">Designated relief centres and safe high-ground locations in your area.</div>
</div>""", unsafe_allow_html=True)

        m = folium.Map(location=[cit_lat, cit_lon], zoom_start=13, tiles="CartoDB positron")

        folium.Circle(
            location=[cit_lat, cit_lon],
            radius=1400,
            color="#dc2626" if risk_lvl in ("CRITICAL", "HIGH") else "#16a34a",
            fill=True,
            fill_color="#dc2626" if risk_lvl in ("CRITICAL", "HIGH") else "#16a34a",
            fill_opacity=0.2,
            popup=f"{current_user['district']} Sector"
        ).add_to(m)

        folium.Marker(
            [cit_lat + 0.009, cit_lon + 0.012],
            popup="Designated Shelter: Haflong Government Relief Centre",
            icon=folium.Icon(color="green", icon="home")
        ).add_to(m)

        folium.Marker(
            [cit_lat, cit_lon],
            popup=f"Your Location: {current_user['name']}",
            icon=folium.Icon(color="blue", icon="user")
        ).add_to(m)

        st_folium(m, width="100%", height=360)

    with c_side:
        st.markdown("""<div class="app-card">
<div class="app-card-title">Report Hazard on the Ground</div>
<div class="app-card-subtitle">See a road crack, mudslide, or fallen rocks? Warn your community.</div>
""", unsafe_allow_html=True)

        with st.form("quick_report_form"):
            rep_type = st.selectbox(
                "What did you observe?",
                ["Road Crack / Soil Crack", "Rockfall / Falling Boulders", "Active Mud Movement", "Blocked Road / Landslide", "Sudden Water Stream Change"]
            )
            rep_desc = st.text_input("Location / Description:", placeholder="e.g., Near Haflong road curve KM-12")
            rep_submit = st.form_submit_button("Submit Hazard Report", use_container_width=True, type="primary")

            if rep_submit:
                db = SessionLocal()
                try:
                    u = db.query(User).filter(User.id == current_user["id"]).first()
                    alert = db.query(Alert).filter(Alert.status == "ACTIVE").order_by(Alert.sent_at.desc()).first()
                    if u:
                        mapping = {
                            "Road Crack / Soil Crack": "ROAD_CRACK",
                            "Rockfall / Falling Boulders": "FALLING_ROCKS",
                            "Active Mud Movement": "SOIL_MOVEMENT",
                            "Blocked Road / Landslide": "ROAD_BLOCKAGE",
                            "Sudden Water Stream Change": "WATER_FLOW_CHANGE"
                        }
                        raw_obs = mapping.get(rep_type, "ROAD_CRACK")
                        r = Report(
                            user_id=u.id,
                            alert_id=alert.id if alert else None,
                            observation_type=raw_obs,
                            description=rep_desc or f"Observed {rep_type}",
                            latitude=cit_lat + 0.001,
                            longitude=cit_lon + 0.001,
                            status="PENDING",
                            created_at=datetime.utcnow()
                        )
                        db.add(r)
                        db.commit()
                        db.refresh(r)
                        validation_service.process_new_report(r, db)
                        st.success("Hazard report submitted! Logged in community monitoring.")
                finally:
                    db.close()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""<div class="app-card">
<div class="app-card-title">Emergency Helplines (1-Tap Dial)</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px;">
    <div class="help-dial-btn">
        <div class="help-number">1070</div>
        <div class="help-label">State Disaster Control</div>
    </div>
    <div class="help-dial-btn">
        <div class="help-number">1078</div>
        <div class="help-label">NDRF Rescue Team</div>
    </div>
    <div class="help-dial-btn">
        <div class="help-number">108</div>
        <div class="help-label">Ambulance Service</div>
    </div>
    <div class="help-dial-btn">
        <div class="help-number">100</div>
        <div class="help-label">Police Emergency</div>
    </div>
</div>
</div>""", unsafe_allow_html=True)

# ==============================================================================
# ROLE 2: VOLUNTEER RESPONDER PORTAL
# ==============================================================================
elif current_user["role"] == "volunteer":
    st.markdown(f"""<div class="app-card" style="margin-bottom: 16px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
        <div class="app-card-title">Volunteer Field Responder Dashboard</div>
        <div class="app-card-subtitle" style="margin-bottom:0;">Assigned Sector: <strong>{current_user['district']}</strong> • Ready for Proximity Dispatch</div>
    </div>
    <span class="pill pill-green">Active Responder</span>
</div>
</div>""", unsafe_allow_html=True)

    db = SessionLocal()
    try:
        cases = db.query(EmergencyCase).order_by(EmergencyCase.created_at.desc()).all()
        sos_cases = [c for c in cases if c.case_type == "NEED_HELP" and c.status != "RESOLVED"]
        welfare_cases = [c for c in cases if c.case_type == "NO_RESPONSE" and c.status != "RESOLVED"]
        resolved_cases = [c for c in cases if c.status == "RESOLVED"]

        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 28px; font-weight: 800; color: #dc2626;">{len(sos_cases)}</div>
<div style="font-size: 13px; font-weight: 600; color: #64748b;">Urgent SOS Requests</div>
</div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 28px; font-weight: 800; color: #ea580c;">{len(welfare_cases)}</div>
<div style="font-size: 13px; font-weight: 600; color: #64748b;">Welfare Checks</div>
</div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 28px; font-weight: 800; color: #16a34a;">{len(resolved_cases)}</div>
<div style="font-size: 13px; font-weight: 600; color: #64748b;">Completed & Safe</div>
</div>""", unsafe_allow_html=True)

        tab_tasks, tab_welfare, tab_verify = st.tabs([
            f"Urgent SOS Tasks ({len(sos_cases)})",
            f"Welfare Check Queue ({len(welfare_cases)})",
            "Submit Field Inspection"
        ])

        vol_lat = current_user.get("latitude", 25.1600)
        vol_lon = current_user.get("longitude", 93.1100)

        with tab_tasks:
            st.markdown("#### Citizens Requiring Immediate Assistance (Sorted by Distance)")
            if not sos_cases:
                st.info("No urgent SOS cases in your sector right now. All checked-in residents are safe.")
            else:
                for c in sos_cases:
                    cit = c.citizen
                    c_lat = cit.latitude if cit and cit.latitude else 25.1718
                    c_lon = cit.longitude if cit and cit.longitude else 93.1230
                    dist_km = round(haversine_distance_km(vol_lat, vol_lon, c_lat, c_lon), 1)

                    st.markdown(f"""<div class="task-card">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
        <strong style="font-size: 16px; color: #0f172a;">Resident: {cit.full_name if cit else 'Citizen'}</strong> &nbsp;
        <span class="pill pill-red">SOS RESCUE</span>
    </div>
    <span class="pill pill-blue">{dist_km} km away</span>
</div>
<div style="font-size: 13px; color: #475569; margin: 6px 0;">
    Phone: <strong>{cit.phone_number if cit else '+91 98765 43210'}</strong> &nbsp;|&nbsp;
    Area: <strong>{cit.district if cit else 'Sector'}</strong> ({cit.village_area if cit and cit.village_area else 'Locality'})
</div>
<div style="font-size: 13px; color: #334155; background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
    <strong>Situation:</strong> {c.notes or 'Resident requested urgent assistance.'}
</div>
</div>""", unsafe_allow_html=True)

                    c_b1, c_b2, c_b3 = st.columns([1, 1, 2])
                    with c_b1:
                        if st.button("Call Citizen", key=f"v_call_{c.id}"):
                            st.info(f"Connecting phone dialer to {cit.phone_number if cit else '+91 98765 43210'}...")
                    with c_b2:
                        if st.button("Get Route", key=f"v_nav_{c.id}"):
                            st.info(f"Destination Coordinates: ({c_lat:.4f}, {c_lon:.4f}) — Distance: {dist_km} km")
                    with c_b3:
                        if st.button("Mark Rescued & Safe", key=f"v_close_{c.id}", type="primary"):
                            c.status = "RESOLVED"
                            db.commit()
                            st.success("Case resolved! Citizen marked safe.")
                            st.rerun()

        with tab_welfare:
            st.markdown("#### Residents Who Have Not Responded to Warning Alerts")
            if not welfare_cases:
                st.info("No non-responsive residents recorded in your sector.")
            else:
                for c in welfare_cases:
                    cit = c.citizen
                    st.markdown(f"""<div class="task-card task-card-welfare">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <strong style="font-size: 15px; color: #0f172a;">Resident: {cit.full_name if cit else 'Resident'}</strong>
    <span class="pill pill-orange">WELFARE CHECK</span>
</div>
<div style="font-size: 13px; color: #475569; margin-top: 4px;">
    Phone: {cit.phone_number if cit else 'N/A'} &nbsp;|&nbsp; Area: {cit.district if cit else 'Sector'} ({cit.village_area if cit and cit.village_area else 'General'})
</div>
</div>""", unsafe_allow_html=True)

        with tab_verify:
            st.markdown("#### Submit Ground Inspection Findings")
            with st.form("vol_inspection_form"):
                open_c = [c for c in cases if c.status != "RESOLVED"]
                opts = {f"{c.citizen.full_name if c.citizen else 'Citizen'} ({c.case_type})": c.id for c in open_c}
                if not opts:
                    opts = {"General Sector Inspection": "general"}

                sel_case = st.selectbox("Select Case / Site:", list(opts.keys()))
                sel_id = opts[sel_case]

                finding_choice = st.selectbox(
                    "Inspection Outcome:",
                    ["Hazard Verified on Ground (Active slide / crack)", "Minor Displacement (Non-critical)", "Safe / False Alarm (Area cleared)"]
                )
                notes_in = st.text_area("Observations:", placeholder="Describe slope condition, actions taken, or resident evacuation...")
                sub_inspect = st.form_submit_button("Submit Inspection Report", use_container_width=True, type="primary")

                if sub_inspect:
                    status_code = "CONFIRMED" if "Verified" in finding_choice else ("PARTIALLY_CONFIRMED" if "Minor" in finding_choice else "FALSE_ALARM")
                    if sel_id != "general":
                        vol = db.query(User).filter(User.id == current_user["id"]).first()
                        escalation_service.submit_volunteer_verification(
                            case_id=sel_id,
                            volunteer=vol,
                            findings=notes_in or "Field inspection completed.",
                            status=status_code,
                            evidence_url=None,
                            db=db
                        )
                        st.success("Inspection submitted and synced with Authority Command Center.")
                        st.rerun()
                    else:
                        st.success("General inspection recorded.")
    finally:
        db.close()

# ==============================================================================
# ROLE 3: AUTHORITY COMMAND CENTER
# ==============================================================================
elif current_user["role"] == "authority":
    st.markdown("""<div class="app-card" style="margin-bottom: 16px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
        <div class="app-card-title">Disaster Management Authority (SDMA) Command Center</div>
        <div class="app-card-subtitle" style="margin-bottom:0;">Regional Surveillance, Warning Broadcasts & Response Coordination</div>
    </div>
    <span class="pill pill-blue">Authority Control</span>
</div>
</div>""", unsafe_allow_html=True)

    db = SessionLocal()
    try:
        alerts = db.query(Alert).order_by(Alert.sent_at.desc()).all()
        act_alert = next((a for a in alerts if a.status == "ACTIVE"), (alerts[0] if alerts else None))
        a_id = act_alert.id if act_alert else None

        total_alerted = db.query(AlertRecipient).filter(AlertRecipient.alert_id == a_id).count() if a_id else 3
        safe_cnt = db.query(AlertResponse).filter(AlertResponse.alert_id == a_id, AlertResponse.response_type == "SAFE").count() if a_id else 1
        sos_cnt = db.query(AlertResponse).filter(AlertResponse.alert_id == a_id, AlertResponse.response_type == "NEED_HELP").count() if a_id else 1
        no_resp = max(0, total_alerted - (safe_cnt + sos_cnt))

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 26px; font-weight: 800; color: #1e3a8a;">{total_alerted}</div>
<div style="font-size: 12px; font-weight: 600; color: #64748b;">Citizens Alerted</div>
</div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 26px; font-weight: 800; color: #16a34a;">{safe_cnt}</div>
<div style="font-size: 12px; font-weight: 600; color: #64748b;">Safe Check-Ins</div>
</div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 26px; font-weight: 800; color: #dc2626;">{sos_cnt}</div>
<div style="font-size: 12px; font-weight: 600; color: #64748b;">SOS Help Requests</div>
</div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="app-card" style="text-align: center;">
<div style="font-size: 26px; font-weight: 800; color: #ea580c;">{no_resp}</div>
<div style="font-size: 12px; font-weight: 600; color: #64748b;">No Response (Welfare)</div>
</div>""", unsafe_allow_html=True)

        tab_map, tab_send, tab_vols = st.tabs([
            "Regional Landslide Risk Map",
            "Send Location-Aware Phone Alert",
            "Approve Volunteer Applications"
        ])

        with tab_map:
            st.markdown("#### Northeast Monitoring Stations & Risk Predictions")
            m_auth = folium.Map(location=[25.5, 93.0], zoom_start=8, tiles="CartoDB positron")

            for p in gee_service.get_all_monitoring_points():
                pred = ml_service.predict_risk(p, db=db, save_to_db=False)
                color = "#dc2626" if pred["riskLevel"] == "CRITICAL" else ("#ea580c" if pred["riskLevel"] == "HIGH" else ("#ca8a04" if pred["riskLevel"] == "MODERATE" else "#16a34a"))

                folium.CircleMarker(
                    location=[p["latitude"], p["longitude"]],
                    radius=10,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.8,
                    popup=f"<strong>{p['location_name']}</strong><br>Risk: {pred['riskLevel']} ({pred['riskScore']:.0f}%)<br>Rainfall: {p['rainfall_mm']} mm"
                ).add_to(m_auth)

            st_folium(m_auth, width="100%", height=400)

        with tab_send:
            st.markdown("#### Broadcast SMS & Phone Call Alert to Affected Citizens")
            st.caption("Only citizens registered in the selected district will receive the alert.")

            with st.form("auth_broadcast_form"):
                dist_target = st.selectbox("Target Affected District:", [
                    "Dima Hasao", "East Khasi Hills", "Kohima", "Aizawl", "Papum Pare", "Imphal West", "West Tripura", "East Sikkim"
                ])
                risk_target = st.selectbox("Threat Level:", ["HIGH", "CRITICAL", "MODERATE"])
                msg_body = st.text_area("Advisory Message:", value=f"SlopeSense AI Alert: {risk_target} Landslide Risk in {dist_target}. Reply 1 if Safe, 2 if Help needed.")

                c1_ch, c2_ch = st.columns(2)
                with c1_ch:
                    send_sms_flag = st.checkbox("Send SMS Message", value=True)
                with c2_ch:
                    send_ivr_flag = st.checkbox("Trigger Automated Voice Phone Call", value=True)

                sub_b = st.form_submit_button("Broadcast Alert Now", use_container_width=True, type="primary")

                if sub_b:
                    al = Alert(
                        title=f"SlopeSense AI Alert: {risk_target} Risk in {dist_target}",
                        description=msg_body,
                        risk_level=risk_target,
                        status="ACTIVE",
                        sent_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(hours=24)
                    )
                    db.add(al)
                    db.commit()
                    db.refresh(al)

                    citizens = notification_service.find_affected_citizens(dist_target, dist_target, 25.1718, 93.1230, db=db)
                    if not citizens:
                        citizens = db.query(User).filter(User.role == "citizen").all()

                    res = notification_service.broadcast_alert(al, citizens, db, send_sms=send_sms_flag, send_ivr=send_ivr_flag, location_name=dist_target)
                    st.success(f"Alert broadcasted to {res['total_recipients']} citizens in {dist_target} (SMS: {res['sms_sent']}, Calls: {res['ivr_sent']}).")
                    st.rerun()

        with tab_vols:
            st.markdown("#### Pending Volunteer Applications")
            pending_v = db.query(User).filter(User.role == "volunteer", User.status == "pending").all()
            if not pending_v:
                st.info("No pending volunteer applications in queue.")
            else:
                for pv in pending_v:
                    st.markdown(f"""<div class="app-card">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
        <strong style="font-size: 15px; color: #0f172a;">{pv.full_name}</strong> &nbsp;
        <span class="pill pill-orange">PENDING APPROVAL</span>
    </div>
</div>
<div style="font-size: 13px; color: #475569; margin: 4px 0;">
    Email: {pv.email} • Mobile: {pv.phone_number} • Sector: {pv.district}, {pv.state}
</div>
</div>""", unsafe_allow_html=True)

                    c_ap, c_rj = st.columns([1, 4])
                    with c_ap:
                        if st.button("Approve", key=f"app_{pv.id}", type="primary"):
                            pv.status = "approved"
                            db.commit()
                            st.success(f"Approved {pv.full_name}.")
                            st.rerun()
                    with c_rj:
                        if st.button("Decline", key=f"dec_{pv.id}"):
                            pv.status = "rejected"
                            db.commit()
                            st.warning(f"Declined {pv.full_name}.")
                            st.rerun()
    finally:
        db.close()

# ==============================================================================
# ROLE 4: SUPER ADMIN DASHBOARD
# ==============================================================================
elif current_user["role"] == "admin":
    st.markdown("""<div class="app-card" style="margin-bottom: 16px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
        <div class="app-card-title">System Administration & Regional Governance</div>
        <div class="app-card-subtitle" style="margin-bottom:0;">Platform User Directory, ML Telemetry Diagnostics & Audit Trail</div>
    </div>
    <span class="pill pill-gray">Super Admin</span>
</div>
</div>""", unsafe_allow_html=True)

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        pending_all = [u for u in users if u.status == "pending"]

        tab_dir, tab_app, tab_ml_diag = st.tabs([
            f"User Directory ({len(users)})",
            f"Pending Authorizations ({len(pending_all)})",
            "ML Risk Model Diagnostics"
        ])

        with tab_dir:
            u_rows = [{"Name": u.full_name, "Email": u.email, "Role": u.role.upper(), "District": u.district, "Status": u.status.upper()} for u in users]
            st.dataframe(pd.DataFrame(u_rows), use_container_width=True)

        with tab_app:
            if not pending_all:
                st.info("No pending user authorizations.")
            else:
                for pu in pending_all:
                    st.markdown(f"**{pu.full_name}** ({pu.role.upper()}) — {pu.email} — District: {pu.district}")
                    if st.button("Authorize Account", key=f"sa_{pu.id}", type="primary"):
                        pu.status = "approved"
                        db.commit()
                        st.success(f"Authorized {pu.full_name}.")
                        st.rerun()

        with tab_ml_diag:
            st.markdown("#### Random Forest Landslide Risk Model (8 Features)")
            st.caption("Inspect live model output for specific environmental parameters.")

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                t_slope = st.slider("Slope Angle (°):", 0.0, 60.0, 35.0)
                t_rain = st.slider("24h Rainfall (mm):", 0.0, 250.0, 110.0)
            with c_f2:
                t_cum = st.slider("30-Day Rainfall (mm):", 0.0, 500.0, 280.0)
                t_ndvi = st.slider("NDVI Drop:", 0.0, 1.0, 0.2)

            if st.button("Run ML Model Inference", type="primary"):
                test_v = {
                    "slope": t_slope, "aspect": 180.0, "curvature": 0.5,
                    "rainfall_mm": t_rain, "cumulative_rainfall_30d": t_cum,
                    "ndvi_trend": -0.1, "ndvi_drop": t_ndvi, "distance_to_river": 150.0
                }
                pred_out = ml_service.predict_risk(test_v, db=db, save_to_db=False)
                st.success(f"Model Output: Threat Level = **{pred_out['riskLevel']}** | Risk Score = **{pred_out['riskScore']:.1f}%** | Confidence = **{pred_out['confidence']}%**")
    finally:
        db.close()

# Footer
st.markdown("""<div style="text-align: center; color: #64748b; font-size: 13px; margin-top: 32px; padding: 16px; border-top: 1px solid #e2e8f0;">
<strong>SlopeSense AI</strong> — Disaster Intelligence & Community Safety Platform<br>
Built for State Disaster Management Authorities & Mountain Communities of Northeast India.
</div>""", unsafe_allow_html=True)
