"""
Trains Random Forest, XGBoost, Gradient Boosting, and Decision Tree
regressors on the driving-conditions dataset, evaluates each with
cross-validation, picks the best by R^2 / MAE, and saves:
  - model_artifacts/best_model.joblib
  - model_artifacts/explainer.joblib   (SHAP TreeExplainer for the winner)
  - model_artifacts/comparison_report.json

Run: python train.py
"""
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from generate_data import generate_dataset

ARTIFACT_DIR = Path("model_artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)

FEATURE_COLUMNS = [
    "temperature", "humidity", "rainfall", "visibility", "wind_speed",
    "road_condition_code", "traffic_density_code", "current_speed", "hour_of_day",
]
TARGET_COLUMN = "recommended_speed"


def load_or_generate_data() -> pd.DataFrame:
    data_path = Path("data/driving_conditions.csv")
    if data_path.exists():
        return pd.read_csv(data_path)
    df = generate_dataset(20000)
    df.to_csv(data_path, index=False)
    return df


def build_models() -> dict:
    return {
        "decision_tree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "random_forest": RandomForestRegressor(
            n_estimators=200, max_depth=14, min_samples_leaf=3,
            n_jobs=-1, random_state=42,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42,
        ),
        "xgboost": xgb.XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=-1,
        ),
    }


def evaluate_model(name: str, model, X_train, X_test, y_train, y_test) -> dict:
    start = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)

    # feature importance (works for all four tree-based models here)
    importance = {}
    if hasattr(model, "feature_importances_"):
        importance = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in model.feature_importances_]))

    print(f"[{name}] MAE={mae:.3f} km/h  RMSE={rmse:.3f}  R2={r2:.4f}  "
          f"CV R2={cv_scores.mean():.4f}(+/-{cv_scores.std():.4f})  train_time={train_time:.1f}s")

    return {
        "model_name": name,
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "r2": round(float(r2), 4),
        "cv_r2_mean": round(float(cv_scores.mean()), 4),
        "cv_r2_std": round(float(cv_scores.std()), 4),
        "train_time_seconds": round(train_time, 2),
        "feature_importance": importance,
    }


def main():
    print("Loading dataset...")
    df = load_or_generate_data()
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows\n")

    models = build_models()
    trained_models = {}
    results = []

    for name, model in models.items():
        result = evaluate_model(name, model, X_train, X_test, y_train, y_test)
        results.append(result)
        trained_models[name] = model

    # pick the best by R^2 on the held-out test set (ties broken by lower MAE)
    best = sorted(results, key=lambda r: (-r["r2"], r["mae"]))[0]
    best_name = best["model_name"]
    best_model = trained_models[best_name]
    print(f"\nBest model: {best_name} (R2={best['r2']}, MAE={best['mae']} km/h)")

    joblib.dump(best_model, ARTIFACT_DIR / "best_model.joblib")

    print("Building SHAP TreeExplainer for the winning model...")
    explainer = shap.TreeExplainer(best_model)
    joblib.dump(explainer, ARTIFACT_DIR / "explainer.joblib")

    report = {
        "best_model": best_name,
        "trained_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "dataset_size": len(df),
        "feature_columns": FEATURE_COLUMNS,
        "all_models": results,
    }
    with open(ARTIFACT_DIR / "comparison_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved: {ARTIFACT_DIR}/best_model.joblib")
    print(f"Saved: {ARTIFACT_DIR}/explainer.joblib")
    print(f"Saved: {ARTIFACT_DIR}/comparison_report.json")


if __name__ == "__main__":
    main()
