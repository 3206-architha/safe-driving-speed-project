"""
Central application configuration.
All values are loaded from environment variables (.env file locally,
or dashboard-set env vars on Railway/Render/Vercel in production).
Never hardcode secrets here.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Safe Driving Speed API"
    ENV: str = "development"  # "development" | "production"
    DEBUG: bool = True

    # --- Security / JWT ---
    SECRET_KEY: str  # required, no default — set in .env, min 32 random chars
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Database ---
    DATABASE_URL: str  # postgresql+psycopg2://user:pass@host:port/dbname

    # --- External APIs ---
    OPENWEATHER_API_KEY: str = ""
    TOMTOM_API_KEY: str = ""

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Caching / background jobs ---
    WEATHER_CACHE_TTL_SECONDS: int = 300      # 5 minutes
    TRAFFIC_CACHE_TTL_SECONDS: int = 180      # 3 minutes
    CACHE_REFRESH_INTERVAL_SECONDS: int = 240  # background job cadence

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- ML ---
    MODEL_ARTIFACT_PATH: str = "ml_model/model_artifacts/best_model.joblib"
    SHAP_EXPLAINER_PATH: str = "ml_model/model_artifacts/explainer.joblib"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    # lru_cache means the .env file is parsed only once per process,
    # which matters when this app runs under multiple gunicorn workers.
    return Settings()
