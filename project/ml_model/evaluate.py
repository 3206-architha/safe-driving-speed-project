"""
Additional evaluation on top of train.py's regression metrics.

The core task is regression (predict a speed in km/h), but the product
spec also wants classification-style metrics (accuracy, precision,
recall, F1, confusion matrix) for the derived Risk Level (Low/Medium/
High), since that's the categorical output users actually see as a
colored badge. This script buckets both true and predicted speeds into
risk levels using the same thresholds as ml_service.py, then reports
classification metrics on that.

Run: python evaluate.py   (after train.py has produced best_model.joblib)
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report,
)

from generate_data import generate_dataset

ARTIFACT_DIR = Path("model_artifacts")
FEATURE_COLUMNS = [
    "temperature", "humidity", "rainfall", "visibility", "wind_speed",
    "road_condition_code", "traffic_density_code", "current_speed", "hour_of_day",
]
TARGET_COLUMN = "recommended_speed"


def speed_to_risk(speed: float) -> str:
    # must match app/services/ml_service.py's risk thresholds exactly
    if speed >= 45:
        return "Low"
    if speed >= 25:
        return "Medium"
    return "High"


def main():
    data_path = Path("data/driving_conditions.csv")
    df = pd.read_csv(data_path) if data_path.exists() else generate_dataset(20000)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = joblib.load(ARTIFACT_DIR / "best_model.joblib")
    y_pred = model.predict(X_test)

    true_risk = y_test.apply(speed_to_risk)
    pred_risk = pd.Series(y_pred).apply(speed_to_risk)

    labels = ["Low", "Medium", "High"]
    acc = accuracy_score(true_risk, pred_risk)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_risk, pred_risk, labels=labels, average="weighted", zero_division=0
    )
    cm = confusion_matrix(true_risk, pred_risk, labels=labels)

    print("Risk-Level Classification (derived from regression output)")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}\n")
    print("Confusion Matrix (rows=true, cols=predicted), order = Low, Medium, High")
    print(cm)
    print()
    print(classification_report(true_risk, pred_risk, labels=labels, zero_division=0))

    report = {
        "risk_classification": {
            "accuracy": round(float(acc), 4),
            "precision_weighted": round(float(precision), 4),
            "recall_weighted": round(float(recall), 4),
            "f1_weighted": round(float(f1), 4),
            "confusion_matrix": cm.tolist(),
            "labels_order": labels,
        }
    }
    with open(ARTIFACT_DIR / "risk_classification_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved: {ARTIFACT_DIR}/risk_classification_report.json")


if __name__ == "__main__":
    main()
