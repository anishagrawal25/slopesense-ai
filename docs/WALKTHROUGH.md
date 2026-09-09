# SlopeSense AI — Disaster Intelligence & Emergency Response Platform

## Executive Summary

**SlopeSense AI** has been redesigned as a **government-grade disaster intelligence platform** tailored for State Disaster Management Authorities (SDMAs) and regional response coordination in Northeast India (Dima Hasao, Meghalaya, Nagaland, Mizoram, Arunachal Pradesh).

The machine learning landslide risk prediction engine is the centerpiece of the platform, driving early warning broadcasts, bi-directional citizen safety validation, proximity-based volunteer dispatch, and strategic authority response coordination.

---

## Key Redesign Highlights

### 1. Clean Light Theme UI
- Replaced previous dark theme with a clean light palette:
  - Neutral canvas: `#f8fafc`
  - Crisp cards: `#ffffff` with subtle borders (`#e2e8f0`)
  - Primary text: Deep Slate (`#0f172a`) and Navy accents (`#1e3a8a`, `#2563eb`)
  - Standardized threat color system: Green (`#16a34a`), Yellow (`#ca8a04`), Orange (`#ea580c`), Red (`#dc2626`).

### 2. Serious Professional Tone (Zero Emojis)
- Removed all casual emojis from all titles, buttons, headers, tables, and notifications.
- Replaced with formal government badges: `[CRITICAL]`, `[HIGH]`, `[MODERATE]`, `[LOW]`, `[SAFE]`, `[SOS]`, `[PENDING]`, `[VERIFIED]`.

### 3. Removed Prototype Clutter
- Eliminated persona switchers and prototype dropdowns from production screens.
- Implemented real authentication with dedicated role-based portals for **Citizen**, **Volunteer**, **Authority**, and **Super Admin**.

### 4. Registration & Approval Workflow
- **Public Landing Page**: Sign In, Register Account, and Quick Access Demo Credentials.
- **Role Approval Rules**:
  - **Citizen**: Automatically approved (`status="approved"`) for immediate access.
  - **Volunteer**: Registered with `status="pending"`; requires SDMA Authority approval before accessing the field dispatch queue.
  - **Authority Official**: Registered with `status="pending"`; requires Super Admin approval.
- **Verification Guard**: If a pending user attempts login, an official notice informs them that authorization is pending review.

---

## Role-Based Operational Portals

### Role 1: Citizen Safety & Early Warning Portal
- **ML Landslide Threat Card**:
  - Displays real-time landslide risk probability score (%) and model confidence (%).
  - Environmental breakdown: Slope angle, 30-day cumulative precipitation, NDVI vegetation trend, distance to river drainage.
  - Actionable safety advisory.
- **Multi-Channel Alert Delivery**:
  - Exact Twilio SMS template delivered to the citizen's mobile number:
    ```
    SlopeSense AI Alert
    [HIGH] Landslide Risk detected in Dima Hasao.
    Risk Score: 87%
    Reply:
    1 = I AM SAFE
    2 = NEED HELP
    ```
  - Automated Voice IVR emergency call script preview.
- **Emergency Safety Check-In**:
  - `[ I AM SAFE (Option 1) ]`: Records `SAFE` status in the response registry.
  - `[ REQUEST HELP / SOS (Option 2) ]`: Automatically registers a `CRITICAL` emergency rescue case and triggers proximity dispatch of the nearest volunteer.
- **Safe Zone & Evacuation Map**:
  - CartoDB Positron light GIS map showing risk radius, citizen coordinates, and designated relief shelters.
- **Community Ground Hazard Reporting**:
  - Precursor reporting form (cracks, falling rocks, soil movement) with photo upload.

### Role 2: Volunteer Operations & Proximity Dispatch
- **Proximity-Ranked Rescue Queue (SOS)**:
  - Lists open `NEED_HELP` emergency cases sorted by physical GPS distance (Haversine calculation in km).
  - Shows citizen details, mobile phone, coordinates, and dispatch notes.
  - Actions: Automated citizen dialer, GPS navigation route coordinates, and `Mark In-Progress`.
- **Non-Responsive Welfare Queue**:
  - Lists non-responsive residents for door-to-door welfare verification.
- **Ground Truth Field Verification**:
  - Form to record physical site inspection findings (`CONFIRMED`, `PARTIALLY_CONFIRMED`, `FALSE_ALARM`).
  - Resolves emergency cases and synchronizes with the SDMA Command Center in real-time.

### Role 3: Authority Command & Strategic Response Center
- **Executive KPI Strip**:
  - Affected Sector, Citizens Alerted, Safe Responses, Need Help SOS, No Response, Active Volunteer Tasks, Response Rate %.
- **Strategic GIS Surveillance Heatmap**:
  - Interactive map of Northeast monitoring points with color-coded risk markers and precipitation data.
- **Location-Aware Early Warning Broadcast Console**:
  - Targeted district selection (only citizens in that district receive the alert).
  - Broadcast via Twilio SMS and Voice IVR.
- **Community Response Analytics**:
  - Plotly donut chart of citizen check-in status and district vulnerability index.
- **Volunteer Approvals Tab**:
  - Review pending volunteer applications with `[ Approve ]` / `[ Reject ]` actions.

### Role 4: Super Admin Dashboard
- **User Directory & Authorization Queue**:
  - Manage all users and authorize pending Authority and Volunteer accounts.
- **ML Diagnostic Console**:
  - 8-feature contract table and real-time interactive inference test tool.
- **System Audit Logs**:
  - Full operational timeline of alerts, responses, escalations, and authorization events.

---

## Verification & Test Results

All integration tests and UI workflows have been automated and verified:

```bash
PYTHONPATH=. pytest tests/ -v
```

### Test Results Summary
- `test_user_registration_and_login`: **PASSED**
- `test_alert_lifecycle_and_citizen_response`: **PASSED**
- `test_community_hazard_report`: **PASSED**
- `test_volunteer_operations`: **PASSED**
- `test_authority_analytics`: **PASSED**
- `test_location_aware_alert_filtering`: **PASSED**
- `test_ml_risk_prediction`: **PASSED**
- `test_gee_telemetry_integration`: **PASSED**
- `test_rbac_permissions`: **PASSED**
- `test_login_and_pending_approval_guard`: **PASSED**
- `test_registration_approval_workflow`: **PASSED**
- `test_ml_landslide_prediction_centerpiece`: **PASSED**
- `test_haversine_proximity_ranking`: **PASSED**
- `test_sos_response_and_volunteer_verification`: **PASSED**

**Total: 17 Passed, 0 Failed (100% Success)**

---

## How to Run & Access

1. **Start the FastAPI Backend**:
   ```bash
   source .venv/bin/activate
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
   - API Docs: `http://localhost:8000/docs`

2. **Start the Streamlit Platform**:
   ```bash
   source .venv/bin/activate
   streamlit run app.py --server.port 8501
   ```
   - Web Platform: `http://localhost:8501`

3. **Demo Credentials for Evaluation**:
   - **Citizen**: `citizen@slopesense.ai` / `password123`
   - **Volunteer**: `volunteer@slopesense.ai` / `password123`
   - **Authority**: `authority@slopesense.ai` / `password123`
   - **Super Admin**: `admin@slopesense.ai` / `password123`
   - **Pending Volunteer (Verification Guard Test)**: `pending_vol@slopesense.ai` / `password123`
