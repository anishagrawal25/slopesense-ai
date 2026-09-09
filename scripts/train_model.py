"""
Trains a Random Forest classifier on the balanced Dima Hasao landslide dataset.
Run this ONCE before starting the live Streamlit system.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def train_model():
    df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'dima_hasao_landslides_balanced.csv'))

    print("Class distribution:\n", df['label'].value_counts())
    if df['label'].nunique() < 2:
        raise ValueError("Dataset must contain both label=1 and label=0 rows before training.")

    synthetic_negatives = df[
        (df['label'] == 0) & df['source'].str.contains('synthetic', case=False, na=False)
    ]
    if len(synthetic_negatives) > 0:
        print(
            f"\nWARNING: {len(synthetic_negatives)} negative samples are synthetic and "
            "not field-verified. The holdout score below is prototype-only and must "
            "not be presented as real-world model accuracy."
        )

    feature_cols = ['slope', 'aspect', 'curvature', 'rainfall_mm',
                     'cumulative_rainfall_30d', 'ndvi_trend', 'ndvi_drop',
                     'distance_to_river']
    X = df[feature_cols]
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=2,
        class_weight='balanced', random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("\n--- Prototype Holdout Performance (not real-world validation) ---")
    print(classification_report(y_test, preds))
    print("Confusion Matrix:\n", confusion_matrix(y_test, preds))

    print("\n--- Feature Importances ---")
    for feat, imp in sorted(zip(feature_cols, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.3f}")

    os.makedirs(os.path.join(BASE_DIR, 'models'), exist_ok=True)
    joblib.dump(model, os.path.join(BASE_DIR, 'models', 'rf_model.pkl'))
    joblib.dump(feature_cols, os.path.join(BASE_DIR, 'models', 'feature_cols.pkl'))
    print(f"\nModel saved to {os.path.join(BASE_DIR, 'models', 'rf_model.pkl')}")
    return model, feature_cols

if __name__ == "__main__":
    train_model()
