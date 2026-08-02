"""
Application entrypoint.

24/7 design notes:
- `lifespan` loads the ML model once at startup (not per-request) and
  starts a background scheduler that keeps external-API caches warm.
- `/health` is a cheap endpoint for uptime monitors (UptimeRobot,
  Railway/Render's own health checks) to hit every minute. If this
  endpoint stops responding, your monitor should alert you.
- SlowAPI adds per-IP rate limiting so one client can't take the
  service down for everyone else.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging_config import setup_logging, logger
from app.core.database import Base, engine
from app.services import ml_service, weather_service
from app.api import auth, predict, weather_traffic, analytics, admin

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up: creating DB tables if missing, loading ML model...")

    Base.metadata.create_all(bind=engine)  # for quick start; use Alembic migrations in real prod
    ml_service.load_model_artifacts()

    scheduler.add_job(
        weather_service.refresh_all_cached_regions,
        "interval",
        seconds=settings.CACHE_REFRESH_INTERVAL_SECONDS,
        id="refresh_weather_cache",
    )
    scheduler.start()
    logger.info("Background scheduler started — service is ready for 24/7 operation")

    yield  # <-- app runs here

    logger.info("Shutting down: stopping scheduler...")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time ML-based safe driving speed recommendation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(weather_traffic.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/health", tags=["System"])
def health_check():
    """Cheap, DB-free endpoint — point your uptime monitor here."""
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/", tags=["System"])
def root():
    return {"message": f"{settings.APP_NAME} is running. See /docs for API documentation."}
