from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.models.user import User
from app.services import weather_service, traffic_service

router = APIRouter(prefix="/api", tags=["Weather & Traffic"])


@router.get("/weather/current")
def current_weather(
    lat: float = Query(...),
    lng: float = Query(...),
    current_user: User = Depends(get_current_user),
):
    return weather_service.get_current_weather(lat, lng)


@router.get("/traffic/current")
def current_traffic(
    lat: float = Query(...),
    lng: float = Query(...),
    current_user: User = Depends(get_current_user),
):
    return traffic_service.get_current_traffic(lat, lng)
