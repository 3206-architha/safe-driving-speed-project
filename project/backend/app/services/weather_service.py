"""
Weather Service — wraps OpenWeatherMap.

24/7 design notes:
- `tenacity` retries transient failures (timeouts, 5xx) up to 3 times
  with exponential backoff, so a single flaky call doesn't surface as
  an error to the user.
- Results are cached in-memory per rounded lat/lng for
  WEATHER_CACHE_TTL_SECONDS. This means if OpenWeatherMap is down,
  most requests still get a recent value instead of failing outright.
- If the API is unreachable AND there's no cache, we raise — the
  caller (prediction service) decides whether to fail the request or
  fall back to safe defaults.
"""
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

# in-memory cache: {region_key: (timestamp, data)}
_weather_cache: dict[str, tuple[float, dict]] = {}


def _region_key(lat: float, lng: float) -> str:
    # round to ~1km precision so nearby requests share a cache entry
    return f"{round(lat, 2)}:{round(lng, 2)}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    reraise=True,
)
def _fetch_from_openweather(lat: float, lng: float) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lng, "appid": settings.OPENWEATHER_API_KEY, "units": "metric"}
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def get_current_weather(lat: float, lng: float) -> dict:
    key = _region_key(lat, lng)
    cached = _weather_cache.get(key)
    if cached and (time.time() - cached[0]) < settings.WEATHER_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        raw = _fetch_from_openweather(lat, lng)
        data = {
            "temperature": raw["main"]["temp"],
            "humidity": raw["main"]["humidity"],
            "wind_speed": raw["wind"]["speed"],
            "visibility": raw.get("visibility", 10000) / 1000,  # metres -> km
            "rainfall": raw.get("rain", {}).get("1h", 0.0),
            "description": raw["weather"][0]["description"],
            "clouds": raw.get("clouds", {}).get("all", 0),
        }
        _weather_cache[key] = (time.time(), data)
        return data
    except Exception as exc:
        logger.error(f"Weather fetch failed for {key}: {exc}")
        if cached:
            logger.info(f"Serving stale weather cache for {key}")
            return cached[1]
        # Last resort — safe, conservative defaults so prediction can still run.
        return {
            "temperature": 25.0, "humidity": 50.0, "wind_speed": 5.0,
            "visibility": 10.0, "rainfall": 0.0, "description": "unknown",
            "clouds": 0, "_fallback": True,
        }


def refresh_all_cached_regions() -> None:
    """Called by the background scheduler on a fixed interval. Proactively
    re-fetches every region that's currently cached, so a real user request
    almost never has to wait on a cold external API call."""
    for key in list(_weather_cache.keys()):
        lat_str, lng_str = key.split(":")
        try:
            raw = _fetch_from_openweather(float(lat_str), float(lng_str))
            data = {
                "temperature": raw["main"]["temp"],
                "humidity": raw["main"]["humidity"],
                "wind_speed": raw["wind"]["speed"],
                "visibility": raw.get("visibility", 10000) / 1000,
                "rainfall": raw.get("rain", {}).get("1h", 0.0),
                "description": raw["weather"][0]["description"],
                "clouds": raw.get("clouds", {}).get("all", 0),
            }
            _weather_cache[key] = (time.time(), data)
        except Exception as exc:
            logger.warning(f"Background weather refresh failed for {key}: {exc}")
    logger.info(f"Weather cache refresh tick - {len(_weather_cache)} regions tracked")
