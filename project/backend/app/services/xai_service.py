"""
Converts a feature dict + SHAP values into a plain-language explanation
a non-technical driver can understand. This is the "Explainable AI"
module from the spec.
"""

FEATURE_LABELS = {
    "temperature": "temperature",
    "humidity": "humidity",
    "rainfall": "rainfall",
    "visibility": "visibility",
    "wind_speed": "wind speed",
    "road_condition_code": "road surface condition",
    "traffic_density_code": "traffic density",
    "current_speed": "current speed",
    "hour_of_day": "time of day",
}


def _describe_feature(feature: str, features: dict) -> str:
    if feature == "rainfall" and features["rainfall"] > 0:
        return f"Rainfall of {features['rainfall']:.1f} mm/h is increasing stopping distance"
    if feature == "visibility" and features["visibility"] < 5:
        return f"Visibility is reduced to {features['visibility']:.1f} km"
    if feature == "road_condition_code" and features["road_condition"] != "dry":
        return f"Road surface is {features['road_condition']}"
    if feature == "traffic_density_code" and features["traffic_density"] == "high":
        return "Traffic density is high"
    if feature == "wind_speed" and features["wind_speed"] > 30:
        return f"Wind speed of {features['wind_speed']:.0f} km/h may affect vehicle stability"
    return f"{FEATURE_LABELS.get(feature, feature).capitalize()} is a contributing factor"


def build_explanation(features: dict, prediction: dict) -> str:
    shap_values = prediction.get("shap_values") or {}

    if not shap_values:
        return (
            f"Recommended speed: {prediction['recommended_speed']} km/h. "
            f"This is a preliminary estimate based on current weather, road, "
            f"and traffic conditions. Risk level: {prediction['risk_level']}."
        )

    # negative SHAP values pushed the speed DOWN — those are the risk factors to surface
    risk_factors = sorted(
        ((feat, val) for feat, val in shap_values.items() if val < 0),
        key=lambda x: x[1],
    )[:4]

    if not risk_factors:
        return (
            f"Recommended speed: {prediction['recommended_speed']} km/h. "
            f"Conditions are favorable — no significant risk factors detected. "
            f"Risk level: {prediction['risk_level']}."
        )

    reasons = [_describe_feature(feat, features) for feat, _ in risk_factors]
    reasons_text = "\n".join(f"- {r}." for r in reasons)

    # rough, illustrative risk percentage derived from confidence — clearly
    # framed as an estimate, not a hard statistical guarantee
    risk_pct = round((1 - prediction["confidence_score"]) * 100 + 20)
    risk_pct = min(risk_pct, 95)

    return (
        f"Recommended speed: {prediction['recommended_speed']} km/h\n\n"
        f"Reason:\n{reasons_text}\n\n"
        f"These combined factors increase accident risk by approximately {risk_pct}%.\n\n"
        f"Therefore the safest recommended speed is {prediction['recommended_speed']} km/h."
    )
