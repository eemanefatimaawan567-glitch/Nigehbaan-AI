"""
weather_service.py — Live weather from Open-Meteo (free, no API key)
Source: open-meteo.com — integrates ECMWF, NOAA, DWD models
"""

import time, threading, urllib.request, urllib.parse, json, logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_cache: dict = {}
_cache_lock  = threading.Lock()
CACHE_TTL    = 600  # 10 minutes

BASE_URL = "https://api.open-meteo.com/v1/forecast"


def _fetch(lat: float, lng: float) -> dict | None:
    params = urllib.parse.urlencode({
        "latitude": lat, "longitude": lng,
        "hourly":   "precipitation,soil_moisture_0_to_1cm",
        "daily":    "precipitation_sum",
        "past_days": 1, "forecast_days": 1,
        "timezone": "Asia/Karachi",
    })
    try:
        req = urllib.request.Request(
            f"{BASE_URL}?{params}",
            headers={"User-Agent": "NigehbaanAI/2.0"},
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        logger.warning("Open-Meteo failed (%.4f,%.4f): %s", lat, lng, e)
        return None


def get_live_weather(lat: float, lng: float) -> dict | None:
    key = f"{lat:.4f},{lng:.4f}"
    with _cache_lock:
        c = _cache.get(key)
        if c and (time.monotonic() - c["ts"]) < CACHE_TTL:
            return c["data"]

    raw = _fetch(lat, lng)
    if not raw:
        return None

    hourly = raw.get("hourly", {})
    daily  = raw.get("daily",  {})

    def last6(lst):
        vals = [x for x in lst if x is not None]
        return vals[-6:] if len(vals) >= 6 else vals

    precip_6h  = round(sum(last6(hourly.get("precipitation", []))), 1)
    precip_24h = round(sum(x for x in daily.get("precipitation_sum", []) if x), 1)
    soil_raw   = (last6(hourly.get("soil_moisture_0_to_1cm", [])) or [None])[-1]
    soil_pct   = round(min(100.0, (soil_raw or 0) / 0.5 * 100), 1) if soil_raw else None

    data = {
        "rainfall_mm":       precip_6h,
        "rainfall_24h_mm":   precip_24h,
        "soil_moisture_pct": soil_pct,
        "source":            "open-meteo.com",
        "fetched_at":        datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.monotonic()}
    return data


def enrich_sensor_with_live_weather(sensor: dict) -> dict:
    enriched = dict(sensor)
    live = get_live_weather(sensor["lat"], sensor["lng"])
    if live:
        if live["rainfall_mm"] is not None:
            enriched["rainfall_mm"] = live["rainfall_mm"]
        if live["soil_moisture_pct"] is not None:
            enriched["soil_moisture"] = live["soil_moisture_pct"]
        enriched["weather_live"]    = True
        enriched["weather_source"]  = "Open-Meteo / ECMWF"
        enriched["rainfall_24h_mm"] = live.get("rainfall_24h_mm")
        enriched["weather_fetched"] = live.get("fetched_at")
    else:
        enriched["weather_live"]   = False
        enriched["weather_source"] = "Simulated (Open-Meteo unavailable)"
    return enriched
