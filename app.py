"""
NER Landslide Risk Dashboard
Combines cached satellite/terrain features + live rainfall (Open-Meteo) into a
Random Forest risk score. Falls back to simulated rainfall if the live API is
unreachable (e.g. no internet, or running in a restricted sandbox) so the app
never breaks during a demo.

Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import joblib
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="NER Landslide Risk Monitor", layout="wide")
st.title("🏔️ NER Landslide Early Warning Dashboard")
st.caption("Dima Hasao, Assam — Prototype for Smart India Hackathon")

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_model():
    model = joblib.load(os.path.join(BASE_DIR, 'models', 'rf_model.pkl'))
    feature_cols = joblib.load(os.path.join(BASE_DIR, 'models', 'feature_cols.pkl'))
    return model, feature_cols

try:
    model, feature_cols = load_model()
except FileNotFoundError:
    st.error("Model not found. Run `python scripts/train_model.py` first.")
    st.stop()

# ---------- LOAD MONITORING POINTS ----------
@st.cache_data
def load_points():
    return pd.read_csv(os.path.join(BASE_DIR, 'data', 'monitoring_points.csv'))

points_df = load_points()

training_data = pd.read_csv(os.path.join(BASE_DIR, 'data', 'dima_hasao_landslides_balanced.csv'))
synthetic_negative_count = training_data[
    (training_data['label'] == 0) &
    training_data['source'].str.contains('synthetic', case=False, na=False)
].shape[0]
if synthetic_negative_count:
    st.warning(
        f"Prototype data warning: {synthetic_negative_count} negative training points are "
        "synthetically generated and not field-verified. Model risk scores and the "
        "reported holdout score are not evidence of real-world accuracy."
    )

# ---------- FETCH LIVE RAINFALL (Open-Meteo, free, no API key needed) ----------
def fetch_rainfall(lat, lon):
    """
    Attempts to fetch live rainfall from Open-Meteo.
    Falls back to a simulated plausible value if the API is unreachable
    (e.g. offline testing, sandboxed environment) so the demo never breaks.
    """
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={lat}&longitude={lon}&hourly=precipitation&past_days=2")
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data = response.json()
        precip = data['hourly']['precipitation']
        current_rainfall = precip[-1] if precip else 0
        cumulative_30d = sum(precip[-30:]) if len(precip) >= 30 else sum(precip)
        return round(current_rainfall, 2), round(cumulative_30d, 2), "live"
    except Exception:
        # Fallback: simulated rainfall (clearly flagged as such in the UI)
        sim_rainfall = round(random.uniform(5, 130), 2)
        sim_cumulative = round(sim_rainfall * random.uniform(2, 5), 2)
        return sim_rainfall, sim_cumulative, "simulated (offline fallback)"

# ---------- REFRESH BUTTON (simulates the scheduled 3-hour cycle) ----------
st.info("In production this refresh runs automatically every 3 hours via a "
        "scheduled job. Click below to trigger it manually for this demo.")

if st.button("🔄 Refresh Risk Data Now", type="primary"):
    results = []
    data_mode_used = set()
    with st.spinner("Fetching rainfall and calculating risk..."):
        for idx, row in points_df.iterrows():
            rainfall_now, cum_rainfall, mode = fetch_rainfall(row['latitude'], row['longitude'])
            data_mode_used.add(mode)

            feature_row = pd.DataFrame([{
                'slope': row['slope'],
                'aspect': row['aspect'],
                'curvature': row['curvature'],
                'rainfall_mm': rainfall_now,
                'cumulative_rainfall_30d': cum_rainfall,
                'ndvi_trend': row['ndvi_trend'],
                'ndvi_drop': row['ndvi_drop'],
                'distance_to_river': row['distance_to_river']
            }])[feature_cols]

            risk_score = model.predict_proba(feature_row)[0][1]

            if risk_score > 0.75:
                category = 'Red'
            elif risk_score > 0.40:
                category = 'Orange'
            else:
                category = 'Green'

            results.append({
                'location_id': row['location_id'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'rainfall_mm': rainfall_now,
                'cumulative_rainfall_30d': cum_rainfall,
                'risk_score': round(risk_score, 3),
                'risk_category': category,
                'data_source': mode,
                'timestamp': datetime.now().isoformat()
            })

    risk_df = pd.DataFrame(results)
    risk_df.to_csv(os.path.join(BASE_DIR, 'data', 'current_risk_scores.csv'), index=False)
    st.session_state['risk_df'] = risk_df

    if "simulated (offline fallback)" in data_mode_used:
        st.warning("⚠️ Live rainfall API unreachable — using simulated fallback "
                    "values for this run (flagged per-row in the data table below).")
    st.success(f"Updated {len(risk_df)} locations at {datetime.now().strftime('%H:%M:%S')}")

# ---------- LOAD LAST SAVED RESULTS IF NO REFRESH YET ----------
if 'risk_df' not in st.session_state:
    csv_path = os.path.join(BASE_DIR, 'data', 'current_risk_scores.csv')
    if os.path.exists(csv_path):
        st.session_state['risk_df'] = pd.read_csv(csv_path)
    else:
        st.info("Click 'Refresh Risk Data Now' to run the first risk calculation.")
        st.stop()

risk_df = st.session_state['risk_df']

# ---------- SUMMARY METRICS ----------
col1, col2, col3 = st.columns(3)
col1.metric("🔴 High Risk", len(risk_df[risk_df['risk_category'] == 'Red']))
col2.metric("🟠 Moderate Risk", len(risk_df[risk_df['risk_category'] == 'Orange']))
col3.metric("🟢 Low Risk", len(risk_df[risk_df['risk_category'] == 'Green']))

# ---------- MAP ----------
st.subheader("Risk Map")
color_map = {'Red': 'red', 'Orange': 'orange', 'Green': 'green'}
m = folium.Map(location=[risk_df['latitude'].mean(), risk_df['longitude'].mean()], zoom_start=9)

for idx, row in risk_df.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=10, color=color_map[row['risk_category']], fill=True, fill_opacity=0.7,
        popup=(f"ID: {row['location_id']}<br>Risk: {row['risk_score']:.2f}"
               f"<br>Category: {row['risk_category']}"
               f"<br>Rainfall: {row['rainfall_mm']}mm")
    ).add_to(m)

st_folium(m, width=1000, height=500)

# ---------- ALERT SIMULATION ----------
st.subheader("🚨 Alert Dispatch (Simulated)")
high_risk = risk_df[risk_df['risk_category'].isin(['Red', 'Orange'])]
if len(high_risk) > 0:
    for idx, row in high_risk.iterrows():
        st.warning(f"ALERT SENT (simulated SMS + Voice Call) → Location "
                    f"{row['location_id']}: {row['risk_category']} risk "
                    f"({row['risk_score']:.2f})")
else:
    st.success("No alerts required — all locations currently Green.")

# ---------- VOLUNTEER GROUND-TRUTH FEEDBACK ----------
st.subheader("📋 Volunteer Ground-Truth Feedback")
with st.form("feedback_form"):
    loc_id = st.selectbox("Location ID", risk_df['location_id'].tolist())
    observed = st.selectbox("What did you observe?",
                              ["No landslide", "Minor slope movement",
                               "Active landslide", "Debris/blocked road"])
    notes = st.text_area("Additional notes")
    submitted = st.form_submit_button("Submit Feedback")
    if submitted:
        feedback_row = pd.DataFrame([{
            'location_id': loc_id, 'observed': observed, 'notes': notes,
            'timestamp': datetime.now().isoformat()
        }])
        feedback_file = os.path.join(BASE_DIR, 'data', 'ground_truth_feedback.csv')
        feedback_row.to_csv(feedback_file, mode='a',
                             header=not os.path.exists(feedback_file), index=False)
        st.success("Feedback logged. Thank you!")

# ---------- RAW DATA TABLE ----------
with st.expander("View Raw Risk Data"):
    st.dataframe(risk_df)

with st.expander("⚠️ Data Source Notes (read before presenting)"):
    st.markdown("""
    - **Terrain/NDVI features** (slope, aspect, curvature, NDVI trend) are from the
      pre-compiled dataset — verify these were extracted via real QGIS/GEE processing,
      not fabricated placeholders, before presenting as production-ready.
    - **Rainfall** is fetched live from Open-Meteo where possible; if unreachable,
      a clearly-flagged simulated value is used instead.
    - **Negative (safe) points** in the current training set are synthetically
      generated for prototype purposes — replace with real verified safe locations
      before claiming production accuracy.
    """)
