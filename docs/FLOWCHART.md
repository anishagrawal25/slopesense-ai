# SlopeSense AI — Main System Flowchart

Here is the complete visual flowchart showing how **SlopeSense AI** works from satellite telemetry ingestion all the way to citizen check-in and volunteer rescue dispatch.

---

```mermaid
flowchart TD
    %% STAGE 1: TELEMETRY
    A["🛰️ Google Earth Engine & Weather Data<br>• SRTM 30m DEM (Slope, Aspect, Curvature)<br>• Sentinel-2 MSI (NDVI Trend, NDVI Drop)<br>• Open-Meteo (24h & 30-Day Cumulative Rainfall)"]
    
    %% STAGE 2: ML PREDICTION
    B["🧠 Random Forest AI Risk Model<br>Calculates Landslide Probability (0-100%) & Threat Level"]
    
    A --> B
    
    %% STAGE 3: THREAT EVALUATION
    C{"Threat Level Assessment"}
    B --> C
    
    C -->|Low / Normal| D["🟢 Baseline Normal Monitoring<br>GIS Map Updated with Green Status"]
    C -->|High / Critical| E["🚨 Location-Aware Warning Triggered<br>Spatial Filter isolates citizens in affected district"]
    
    %% STAGE 4: ALERT BROADCAST
    E --> F1["📱 Location-Aware SMS Alert<br>'Reply 1 = Safe, 2 = Need Help'"]
    E --> F2["📞 Automated Voice IVR Phone Call<br>'Press 1 if Safe, 2 for Help'"]
    
    %% STAGE 5: CITIZEN RESPONSE
    G{"Citizen Response"}
    F1 --> G
    F2 --> G
    
    G -->|Reply '1'| H["✅ Citizen Marked SAFE<br>Logged in State Disaster Registry"]
    G -->|No Response| I["⚠️ Welfare Check Required<br>Flagged for non-responsive resident check"]
    G -->|Reply '2'| J["🆘 EMERGENCY SOS TRIGGERED<br>Critical Rescue Case Created"]
    
    %% STAGE 6: PROXIMITY DISPATCH
    J --> K["📍 Haversine GPS Distance Calculation<br>System locates and ranks closest active volunteers"]
    
    K --> L["👷 Nearest Volunteer Dispatched<br>Receives citizen name, GPS route & phone dialer"]
    I --> L
    
    %% STAGE 7: FIELD VERIFICATION & RESOLUTION
    L --> M["📝 Volunteer On-Ground Inspection<br>Verifies physical slope status & resident safety"]
    
    M --> N["🏛️ SDMA Authority Command Center<br>Live GIS Heatmap updated & Emergency Case Resolved"]
```

---

### Step-by-Step Flow Explanation (For Your Pitch)

1. **Step 1: Environmental Telemetry**: Satellites and weather APIs continuously feed terrain slope, vegetation loss, and 30-day cumulative rainfall into the system.
2. **Step 2: AI Risk Prediction**: The Random Forest model computes a real-time landslide risk score and threat level (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
3. **Step 3: Location-Filtered Alert**: If risk is High or Critical, the spatial filter targets *only* citizens registered in the affected district.
4. **Step 4: Dual-Channel Delivery**: SMS and automated voice phone calls are broadcast to residents' phones without requiring mobile internet.
5. **Step 5: Citizen Check-In**:
   - `1 = Safe`: Automatically marked safe in the government registry.
   - `2 = Need Help (SOS)`: Instantly creates a Critical Emergency Case.
   - `No Response`: Automatically added to the welfare check queue.
6. **Step 6: Proximity Volunteer Dispatch**: The Haversine GPS algorithm automatically assigns the closest verified local responder in the village (e.g. *1.4 km away*).
7. **Step 7: Ground Truth Verification & Resolution**: The volunteer confirms the site on the ground and resolves the case, synchronizing with the State Disaster Management Authority dashboard in real time.
