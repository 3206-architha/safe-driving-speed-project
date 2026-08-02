"""
Traffic Service — wraps TomTom's Traffic Flow API.
Same retry + cache + fallback pattern as weather_service.py — see that
file's docstring for the 24/7 reasoning.
"""
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

_traffic_cache: dict[str, tuple[float, dict]] = {}


def _region_key(lat: float, lng: float) -> str:
    return f"{round(lat, 2)}:{round(lng, 2)}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    reraise=True,
)
def _fetch_from_tomtom(lat: float, lng: float) -> dict:
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {"point": f"{lat},{lng}", "key": settings.TOMTOM_API_KEY}
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _classify_density(current_speed: float, free_flow_speed: float) -> str:
    if free_flow_speed <= 0:
        return "unknown"
    ratio = current_speed / free_flow_speed
    if ratio > 0.75:
        return "low"
    if ratio > 0.4:
        return "medium"
    return "high"


def get_current_traffic(lat: float, lng: float) -> dict:
    key = _region_key(lat, lng)
    cached = _traffic_cache.get(key)
    if cached and (time.time() - cached[0]) < settings.TRAFFIC_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        raw = _fetch_from_tomtom(lat, lng)
        seg = raw["flowSegmentData"]
        data = {
            "current_speed": seg["currentSpeed"],
            "free_flow_speed": seg["freeFlowSpeed"],
            "traffic_density": _classify_density(seg["currentSpeed"], seg["freeFlowSpeed"]),
            "confidence": seg.get("confidence", 1.0),
        }
        _traffic_cache[key] = (time.time(), data)
        return data
    except Exception as exc:
        logger.error(f"Traffic fetch failed for {key}: {exc}")
        if cached:
            logger.info(f"Serving stale traffic cache for {key}")
            return cached[1]
        return {
            "current_speed": 40.0, "free_flow_speed": 50.0,
            "traffic_density": "medium", "confidence": 0.0, "_fallback": True,
        }
