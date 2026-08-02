from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class PredictionRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    current_speed: float = Field(ge=0, le=300, description="km/h, from device or manual entry")


class ScenarioRequest(BaseModel):
    road_condition: str = Field(description="dry | wet | snow | ice")
    rainfall: float = Field(ge=0, le=100, default=0)
    visibility: float = Field(ge=0.1, le=10, default=10)
    traffic_density: str = Field(description="low | medium | high")
    wind_speed: float = Field(ge=0, le=150, default=10)
    temperature: float = Field(ge=-20, le=55, default=25)
    humidity: float = Field(ge=0, le=100, default=50)
    current_speed: float = Field(ge=0, le=300, default=50)


class ScenarioResponse(BaseModel):
    recommended_speed: float
    risk_level: str
    confidence_score: float
    explanation: str
    shap_values: dict


class PredictionResponse(BaseModel):
    id: UUID
    latitude: float
    longitude: float
    temperature: Optional[float]
    humidity: Optional[float]
    rainfall: Optional[float]
    visibility: Optional[float]
    wind_speed: Optional[float]
    road_condition: Optional[str]
    traffic_density: Optional[str]
    current_speed: Optional[float]
    recommended_speed: float
    risk_level: str
    confidence_score: float
    explanation: str
    shap_values: dict
    created_at: datetime

    class Config:
        from_attributes = True