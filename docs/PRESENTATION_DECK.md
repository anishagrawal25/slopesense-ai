# SlopeSense AI — Smart India Hackathon Presentation Deck

A complete 9-slide presentation guide with slide content, bullet points, visual layout suggestions, and a live demo script for judging.

---

## Slide 1: Title & Overview
- **Title**: **SLOPESENSE AI**
- **Subtitle**: AI-Powered Landslide Disaster Intelligence & Emergency Response Platform
- **Target Region**: Northeast India (Assam, Meghalaya, Nagaland, Mizoram, Arunachal Pradesh)
- **Tagline**: *"From Satellite Telemetry to Last-Mile Community Rescue"*
- **Team**: SlopeSense AI Team
- **Visual**: Platform logo with clean GIS map graphic of Northeast India mountain corridors.

---

## Slide 2: The Problem (Crisis in Mountainous Northeast India)
- **Extreme Monsoonal Rainfall**: Steep Himalayan slopes become saturated during cloudbursts, causing sudden catastrophic landslides.
- **Failures of Current Warning Systems**:
  1. **Generic Broad Warnings**: Entire states get alerted at once, causing warning fatigue and ignored advisories.
  2. **No Citizen Feedback Loop**: Disaster authorities don't know who is safe at home vs. who is trapped under debris.
  3. **Poor Cellular Data in Hills**: Smartphone apps fail in remote mountain villages where 4G/5G is unavailable.
  4. **Uncoordinated Response**: Rescue teams are dispatched blindly without proximity distance ranking.

---

## Slide 3: Our Solution — Closed-Loop Disaster Intelligence Lifecycle
- **Step 1: Environmental Telemetry**: Google Earth Engine (SRTM 30m DEM + Sentinel-2 NDVI) + Open-Meteo precipitation.
- **Step 2: AI Landslide Prediction**: 8-feature Random Forest probability model predicting landslide risk score & confidence %.
- **Step 3: Location-Aware Warning**: SMS & Automated Voice IVR delivered *exclusively* to citizens inside the affected risk zone.
- **Step 4: Bi-Directional Check-In**: Citizens reply `1 = Safe` or `2 = Need Help (SOS)` on basic 2G phones.
- **Step 5: Proximity Volunteer Dispatch**: Nearest verified local responder assigned via GPS Haversine distance.
- **Step 6: Authority Strategic Command**: SDMA dashboard tracks real-time check-in rates and ground truth verification.

---

## Slide 4: AI & Earth Observation Architecture (Centerpiece)
- **Model**: Scikit-Learn Random Forest Classifier (`models/rf_model.pkl`).
- **Standard 8-Feature Contract**:
  1. `slope`: Terrain slope gradient in degrees (SRTM 30m DEM).
  2. `aspect`: Compass orientation of the hillside.
  3. `curvature`: Surface curvature index.
  4. `rainfall_mm`: 24-hour precipitation accumulation.
  5. `cumulative_rainfall_30d`: Antecedent 30-day soil moisture saturation.
  6. `ndvi_trend`: Multi-month vegetation health trend (Sentinel-2).
  7. `ndvi_drop`: Rapid canopy loss / deforestation indicator.
  8. `distance_to_river`: Proximity to nearest drainage river basin.
- **Model Outputs**: Risk Level (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), Risk Probability Score %, Model Confidence %, and Actionable Safety Advisories.

---

## Slide 5: Multi-Channel Last-Mile Communications (Twilio SMS & Voice IVR)
- **Why It Works in Rural Areas**: Functions over basic 2G cellular networks without mobile data or app installation.
- **Automated SMS Template**:
  ```text
  SlopeSense AI Alert
  [HIGH] Landslide Risk detected in Dima Hasao.
  Risk Score: 87%
  Reply:
  1 = I AM SAFE
  2 = NEED HELP
  ```
- **Automated Voice IVR Call**: Phone call in natural language asking the resident to press `1` for Safe or `2` for Emergency Help.

---

## Slide 6: Proximity-Based Volunteer Dispatch & Ground Verification
- **Haversine Distance Prioritization**: SOS emergency cases are ranked and dispatched to the nearest active responder (e.g. *Tenzing Norgay — 1.4 km away*).
- **Non-Responsive Welfare Queue**: Automatic list of citizens who haven't responded to alerts for door-to-door welfare checks.
- **Ground Truth Field Verification**: Volunteers submit inspection findings (`CONFIRMED`, `PARTIALLY_CONFIRMED`, `FALSE_ALARM`) to confirm site conditions and resolve cases in real-time.

---

## Slide 7: State Disaster Management Authority (SDMA) Command Center
- **Role-Based Security & Approvals**:
  - **Citizen**: Instant registration for early warnings.
  - **Volunteer**: Requires SDMA verification before receiving field dispatch cases.
  - **Authority Official**: Comprehensive command for broadcast and regional surveillance.
- **Strategic Command Features**:
  - Regional GIS surveillance heatmap with real-time risk markers.
  - Location-filtered warning broadcast console.
  - Citizen safety response analytics (Safe vs SOS vs No-Response).

---

## Slide 8: Technical Architecture & System Robustness
- **Web Portal / UX**: Streamlit, Custom Light Theme Design System, Folium/Leaflet GIS, Plotly Analytics.
- **Backend & APIs**: FastAPI, Uvicorn, Pydantic V2.
- **Data Layer**: SQLite with WAL (Write-Ahead Logging) Mode for non-blocking concurrent reads/writes.
- **Security & RBAC**: Bcrypt password hashing, PyJWT authentication tokens.
- **Quality Assurance**: 17/17 automated integration & UI workflow tests passing (`pytest`).

---

## Slide 9: Impact, Scalability & Roadmap
- **Immediate Impact**: Reduces evacuation warning and rescue dispatch times from hours to under 2 minutes.
- **Future Roadmap**:
  - Multi-lingual voice alerts in regional languages (Assamese, Khasi, Nagamese, Mizo).
  - Integration with acoustic & soil-moisture IoT sensors along mountain highways (NH-54).
  - Interoperability with the National Disaster Management Authority (NDMA) national portal.

---

## 3-Minute Live Hackathon Demo Script

1. **Minute 1: The Citizen Experience (`citizen@slopesense.ai`)**
   - Show the **Citizen Portal**: Look at the High Landslide Warning card for Dima Hasao, showing 87% risk score and safety recommendations.
   - Click `[ REQUEST HELP (SOS) ]` — demonstrate an instant emergency escalation case being created.

2. **Minute 2: The Volunteer Dispatch (`volunteer@slopesense.ai`)**
   - Switch to the **Volunteer Portal**: Show the SOS rescue task appearing at the top of the queue ranked by distance (**1.4 km away**).
   - Click `[ Submit Field Inspection ]`, choose `CONFIRMED`, and resolve the case.

3. **Minute 3: The SDMA Command Center (`authority@slopesense.ai`)**
   - Open the **Authority Command Center**: Show the GIS surveillance map and the 7-metric KPI strip updating in real time.
   - Demonstrate the **Location-Aware Broadcast Console**, showing that alerts are only sent to citizens registered in the selected district.
