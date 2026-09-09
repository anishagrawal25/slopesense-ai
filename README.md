# NER Landslide Risk Dashboard — Developer Handoff

This ZIP contains a prototype Random Forest landslide-risk dashboard and the
integration contract needed to replace its precompiled terrain/NDVI data with
Google Earth Engine (GEE) exports.

## Handoff contents

- `app.py`: Streamlit dashboard and risk scoring workflow.
- `models/`: trained model and feature-column order.
- `data/`: prototype training and monitoring CSVs.
- `scripts/train_model.py`: retrains the model.
- `scripts/gee_export_features.py`: optional GEE terrain/NDVI export template.
- `requirements-gee.txt`: optional dependency for the GEE export script.
- `package_project.ps1`: creates the developer handoff ZIP.

## Model input contract

The model must receive these columns in this order:

```text
slope, aspect, curvature, rainfall_mm, cumulative_rainfall_30d,
ndvi_trend, ndvi_drop, distance_to_river
```

GEE supplies terrain and NDVI features. Open-Meteo supplies rainfall at runtime.
The application currently reads terrain/NDVI from `data/monitoring_points.csv`.
After a GEE export, validate the CSV and replace those feature columns while
preserving `location_id`, `latitude`, and `longitude`.

## What was tested here (in a restricted sandbox)
- ✅ Model trains successfully (train_model.py)
- ✅ Streamlit app launches and serves (HTTP 200 confirmed)
- ✅ Risk scoring pipeline runs end-to-end
- ✅ Offline fallback for rainfall API confirmed working (sandbox blocks
     open-meteo.com; on your machine with normal internet, it will use LIVE data)
- ⚠️ NOT tested here: actual live Open-Meteo response (blocked in sandbox),
     Google Earth Engine integration (not built into this version — see below)

## Before you run this on your machine

1. Install dependencies:
   pip install -r requirements.txt

2. Train the model (creates models/rf_model.pkl):
   python scripts/train_model.py

3. Run the app:
   streamlit run app.py

4. Open the browser link it gives you (usually http://localhost:8501)

## Optional GEE integration

Install the additional dependency only on the machine that will run GEE:

```bash
python -m pip install -r requirements-gee.txt
python scripts/gee_export_features.py --project YOUR_GCP_PROJECT_ID
```

The first run opens Earth Engine authentication. The Google Cloud project must
have Earth Engine enabled. The script exports a CSV to Google Drive; it does not
place credentials in this project or download the file automatically.

Before connecting the export to the app, verify that the CSV contains numeric
values for `slope`, `aspect`, `curvature`, `ndvi_trend`, `ndvi_drop`, and
`distance_to_river`. Keep `rainfall_mm` and `cumulative_rainfall_30d` for the
runtime Open-Meteo step. A developer may need to compute `distance_to_river`
from a verified hydrography dataset if it is not present in the export.

## Creating the ZIP for handoff

From the project directory, run PowerShell:

```powershell
.\package_project.ps1
```

This creates `NER_Landslide_Project-developer-handoff.zip` beside the project
folder. Do not include GEE service-account keys, `.env` files, or personal
credentials in the ZIP.

## IMPORTANT — things to fix before final presentation

1. **Negative points are SYNTHETIC** (randomly generated, not real verified
   safe locations). Replace data/dima_hasao_landslides_balanced.csv's NEG*
   rows with real QGIS/GEE-verified safe points before claiming real accuracy.

2. **Do not present the current 100% test accuracy as model skill.** It is a
   prototype holdout result caused by the clean separation between the real
   landslide records and synthetic negatives, not a real-world validation score.
   Replace the negatives first, then evaluate with a geographically and
   temporally representative validation design and report those results.

3. **GEE satellite live-refresh is NOT wired into app.py yet** — this version
   uses pre-computed terrain/NDVI from your dataset (the "slow track" is
   simulated as static, not actually re-fetched every few days). To add real
   GEE integration, see the separate satellite_update.py pattern discussed
   earlier — this requires `earthengine-api` + a GEE account, and must be run
   on a machine with GEE access (not tested in this sandbox).

4. **Twilio alerts are simulated only** (shown as warning boxes in the UI,
   not actual SMS/calls). Wire in real Twilio credentials via .env if you want
   live alert sending for the demo.
