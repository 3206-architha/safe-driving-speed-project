"""
ML Inference Service.

Loads the trained model + SHAP explainer ONCE at process startup
(see main.py's lifespan handler) and keeps them in memory — for a
24/7 service, re-loading a joblib file from disk on every request
would be both slow and pointless.

The actual training pipeline lives in ml_model/train.py (Phase 3).
This module only does inference.
"""
import joblib
import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

FEATURE_ORDER = [
    "temperature", "humidity", "rainfall", "visibility", "wind_speed",
    "road_condition_code", "traffic_density_code", "current_speed", "hour_of_day",
]

ROAD_CONDITION_MAP = {"dry": 0, "wet": 1, "snow": 2, "ice": 3}
TRAFFIC_DENSITY_MAP = {"low": 0, "medium": 1, "high": 2}

_model = None
_explainer = None


def load_model_artifacts() -> None:
    global _model, _explainer
    try:
        _model = joblib.load(settings.MODEL_ARTIFACT_PATH)
        _explainer = joblib.load(settings.SHAP_EXPLAINER_PATH)
        logger.info("ML model and SHAP explainer loaded successfully")
    except FileNotFoundError:
        logger.warning(
            "Model artifacts not found — run ml_model/train.py first. "
            "Predictions will use a rule-based fallback until then."
        )
        _model = None
        _explainer = None


def _build_feature_row(features: dict) -> pd.DataFrame:
    row = {
        "temperature": features["temperature"],
        "humidity": features["humidity"],
        "rainfall": features["rainfall"],
        "visibility": features["visibility"],
        "wind_speed": features["wind_speed"],
        "road_condition_code": ROAD_CONDITION_MAP.get(features["road_condition"], 0),
        "traffic_density_code": TRAFFIC_DENSITY_MAP.get(features["traffic_density"], 1),
        "current_speed": features["current_speed"],
        "hour_of_day": features["hour_of_day"],
    }
    return pd.DataFrame([row], columns=FEATURE_ORDER)


def _rule_based_fallback(features: dict) -> dict:
    """
    Used only if the trained model isn't loaded yet. Keeps the API
    functional end-to-end during initial setup/demo, and as a safety
    net if model loading ever fails in production.
    """
    base = 60.0
    if features["rainfall"] > 0:
        base -= min(features["rainfall"] * 4, 20)
    if features["visibility"] < 5:
        base -= (5 - features["visibility"]) * 3
    if features["road_condition"] in ("wet", "snow", "ice"):
        base -= {"wet": 8, "snow": 15, "ice": 20}[features["road_condition"]]
    if features["traffic_density"] == "high":
        base -= 10
    speed = max(15.0, round(base, 1))

    risk = "Low" if speed >= 45 else "Medium" if speed >= 30 else "High"
    return {
        "recommended_speed": speed,
        "risk_level": risk,
        "confidence_score": 0.55,  # deliberately marked low-confidence
        "shap_values": {},
    }


def predict(features: dict) -> dict:
    if _model is None:
        return _rule_based_fallback(features)

    row = _build_feature_row(features)
    predicted_speed = float(_model.predict(row)[0])

    # risk classification derived from how far below the "safe baseline" we are
    if predicted_speed >= 45:
        risk = "Low"
    elif predicted_speed >= 25:
        risk = "Medium"
    else:
        risk = "High"

    # confidence: for tree ensembles, use agreement across estimators when available
    confidence = 0.85
    if hasattr(_model, "estimators_"):
        raw_estimators = _model.estimators_
        trees = raw_estimators.ravel() if hasattr(raw_estimators, "ravel") else raw_estimators
        preds = np.array([tree.predict(row)[0] for tree in trees])
        spread = preds.std()
        confidence = float(max(0.5, min(0.99, 1 - (spread / max(predicted_speed, 1)))))

    shap_values = {}
    if _explainer is not None:
        shap_out = _explainer.shap_values(row)
        shap_row = shap_out[0] if isinstance(shap_out, list) else shap_out[0]
        shap_values = {
            feat: round(float(val), 3) for feat, val in zip(FEATURE_ORDER, shap_row)
        }

    return {
        "recommended_speed": round(predicted_speed, 1),
        "risk_level": risk,
        "confidence_score": round(confidence, 2),
        "shap_values": shap_values,
    }
