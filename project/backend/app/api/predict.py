from datetime import datetime
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import logger
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionRequest, PredictionResponse, ScenarioRequest, ScenarioResponse
from app.api.deps import get_current_user
from app.services import weather_service, traffic_service, ml_service, xai_service
from app.services.connection_manager import manager

router = APIRouter(prefix="/api", tags=["Prediction"])


def _run_prediction_pipeline(lat: float, lng: float, current_speed: float) -> tuple[dict, dict]:
    weather = weather_service.get_current_weather(lat, lng)
    traffic = traffic_service.get_current_traffic(lat, lng)

    features = {
        "temperature": weather["temperature"],
        "humidity": weather["humidity"],
        "rainfall": weather["rainfall"],
        "visibility": weather["visibility"],
        "wind_speed": weather["wind_speed"],
        "road_condition": "wet" if weather["rainfall"] > 0.5 else "dry",
        "traffic_density": traffic["traffic_density"],
        "current_speed": current_speed,
        "hour_of_day": datetime.utcnow().hour,
    }

    prediction = ml_service.predict(features)
    explanation = xai_service.build_explanation(features, prediction)
    prediction["explanation"] = explanation
    return features, prediction


@router.post("/predict", response_model=PredictionResponse)
def predict(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    features, prediction = _run_prediction_pipeline(
        payload.latitude, payload.longitude, payload.current_speed
    )

    record = Prediction(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        temperature=features["temperature"],
        humidity=features["humidity"],
        rainfall=features["rainfall"],
        visibility=features["visibility"],
        wind_speed=features["wind_speed"],
        road_condition=features["road_condition"],
        traffic_density=features["traffic_density"],
        current_speed=payload.current_speed,
        recommended_speed=prediction["recommended_speed"],
        risk_level=prediction["risk_level"],
        confidence_score=prediction["confidence_score"],
        explanation=prediction["explanation"],
        shap_values=prediction["shap_values"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Prediction stored for user {current_user.id}: {prediction['recommended_speed']} km/h")
    return record


@router.post("/predict/scenario", response_model=ScenarioResponse)
def predict_scenario(
    payload: ScenarioRequest,
    current_user: User = Depends(get_current_user),
):
    features = {
        "temperature": payload.temperature,
        "humidity": payload.humidity,
        "rainfall": payload.rainfall,
        "visibility": payload.visibility,
        "wind_speed": payload.wind_speed,
        "road_condition": payload.road_condition,
        "traffic_density": payload.traffic_density,
        "current_speed": payload.current_speed,
        "hour_of_day": datetime.utcnow().hour,
    }
    prediction = ml_service.predict(features)
    prediction["explanation"] = xai_service.build_explanation(features, prediction)
    return prediction


@router.get("/predictions", response_model=list[PredictionResponse])
def list_predictions(
    skip: int = 0,
    limit: int = 20,
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Prediction).filter(Prediction.user_id == current_user.id)
    if risk_level:
        query = query.filter(Prediction.risk_level == risk_level)
    return (
        query.order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.websocket("/ws/predict")
async def websocket_predict(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            lat = data["latitude"]
            lng = data["longitude"]
            speed = data.get("current_speed", 0)

            features, prediction = _run_prediction_pipeline(lat, lng, speed)
            await websocket.send_json(
                {
                    "recommended_speed": prediction["recommended_speed"],
                    "risk_level": prediction["risk_level"],
                    "confidence_score": prediction["confidence_score"],
                    "explanation": prediction["explanation"],
                }
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
        manager.disconnect(websocket)