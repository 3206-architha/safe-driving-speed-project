import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    visibility = Column(Float)
    wind_speed = Column(Float)
    road_condition = Column(String(20))
    traffic_density = Column(String(20))
    current_speed = Column(Float)

    recommended_speed = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)       # Low | Medium | High
    confidence_score = Column(Float, nullable=False)
    explanation = Column(String)                           # plain-language XAI text
    shap_values = Column(JSON)                              # {feature: contribution}

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="predictions")
