"""
Synthetic Dataset Generator — Safe Driving Speed

WHY SYNTHETIC DATA:
There is no public dataset that maps (weather, road, traffic) conditions
directly to a "correct" safe speed — that's not something anyone has
labeled at scale. Rather than faking numbers, we derive the target speed
from a real physics formula (braking distance), then add realistic noise
and edge cases. This is defensible in a project review: you can point to
the exact formula used, and it's the same approach commonly used in
ADAS (Advanced Driver Assistance Systems) research when ground-truth
labels aren't available.

PHYSICS:
Braking distance:  d = v^2 / (2 * mu * g)
  where v = speed (m/s), mu = coefficient of friction, g = 9.81 m/s^2

We invert this: given a "required safe stopping distance" for the
current conditions, solve for the maximum safe speed v.

  v_max = sqrt(2 * mu_effective * g * d_required)

mu_effective drops with rain/snow/ice (less tire grip).
d_required drops with poor visibility and heavy traffic (you need to
react and stop within a shorter distance you can actually see or
before hitting the car in front).
"""
import numpy as np
import pandas as pd

np.random.seed(42)
G = 9.81  # m/s^2

FRICTION_BY_ROAD = {
    "dry": 0.80,
    "wet": 0.55,
    "snow": 0.30,
    "ice": 0.15,
}


def _sample_row(rng: np.random.Generator) -> dict:
    road_condition = rng.choice(list(FRICTION_BY_ROAD.keys()), p=[0.55, 0.25, 0.12, 0.08])
    traffic_density = rng.choice(["low", "medium", "high"], p=[0.4, 0.4, 0.2])

    temperature = rng.uniform(-5, 45)
    humidity = rng.uniform(20, 100)

    # rainfall correlates with wet/snow/ice road condition, not fully independent
    if road_condition == "dry":
        rainfall = max(0, rng.normal(0, 0.3))
    elif road_condition == "wet":
        rainfall = rng.uniform(0.5, 15)
    else:
        rainfall = rng.uniform(0, 5)  # snow/ice: precipitation may have stopped, ground still frozen/wet

    visibility = np.clip(rng.normal(8 if rainfall < 2 else 3, 3), 0.2, 10)
    wind_speed = np.clip(rng.normal(15, 10), 0, 80)
    hour_of_day = rng.integers(0, 24)
    current_speed_intent = np.clip(rng.normal(55, 20), 10, 140)  # what the driver WANTS to drive at

    # --- physics-derived label ---
    mu = FRICTION_BY_ROAD[road_condition]
    # crosswind reduces effective grip slightly at higher wind speeds
    mu_effective = mu * (1 - min(wind_speed / 300, 0.1))

    base_required_distance = 45.0  # metres, a generic urban/highway baseline
    visibility_factor = np.clip(visibility / 10, 0.25, 1.0)  # poor visibility -> shorter usable distance
    traffic_factor = {"low": 1.0, "medium": 0.85, "high": 0.65}[traffic_density]
    d_required = base_required_distance * visibility_factor * traffic_factor

    v_max_ms = np.sqrt(max(2 * mu_effective * G * d_required, 1))
    v_max_kmh = v_max_ms * 3.6

    # realistic noise + human/measurement variability
    v_max_kmh = v_max_kmh + rng.normal(0, 3)
    recommended_speed = float(np.clip(v_max_kmh, 10, 130))

    return {
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
        "rainfall": round(rainfall, 2),
        "visibility": round(visibility, 2),
        "wind_speed": round(wind_speed, 1),
        "road_condition": road_condition,
        "traffic_density": traffic_density,
        "current_speed": round(current_speed_intent, 1),
        "hour_of_day": int(hour_of_day),
        "recommended_speed": round(recommended_speed, 1),
    }


def generate_dataset(n_rows: int = 20000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = [_sample_row(rng) for _ in range(n_rows)]
    df = pd.DataFrame(rows)

    # encode categoricals the same way ml_service.py expects at inference time
    df["road_condition_code"] = df["road_condition"].map({"dry": 0, "wet": 1, "snow": 2, "ice": 3})
    df["traffic_density_code"] = df["traffic_density"].map({"low": 0, "medium": 1, "high": 2})
    return df


if __name__ == "__main__":
    df = generate_dataset(20000)
    df.to_csv("data/driving_conditions.csv", index=False)
    print(f"Generated {len(df)} rows -> data/driving_conditions.csv")
    print(df.describe(include="all").T)
