"""
risk_engine.py — Ensemble risk scoring engine for Nigehbaan AI

Blends two approaches:
  1. Physics formula  (hydrology + geotechnical first principles)
  2. RandomForest ML  (trained on 1,200 NDMA-calibrated synthetic records)

Final score = 60% ML prediction + 40% physics formula
Confidence  = model accuracy × channel agreement bonus

Features: rainfall_mm, river_level_m, soil_moisture,
          acoustic_anomaly, slope_deg, population
"""

from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def classify(score: float) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 60: return "HIGH"
    if score >= 35: return "MODERATE"
    return "LOW"


def _physics_score(sensor: dict) -> tuple[float, float, float]:
    """Returns (flood_score, landslide_score, overall_score) from physics formula."""
    rainfall  = float(sensor["rainfall_mm"])
    river     = float(sensor["river_level_m"])
    soil      = float(sensor["soil_moisture"])
    acoustic  = float(sensor["acoustic_anomaly"])
    slope     = float(sensor["slope_deg"])

    flood = clamp(
        rainfall * 0.78 +
        river    * 12.5 +
        max(0, soil - 50) * 0.55
    )
    landslide = clamp(
        max(0, soil - 45) * 0.65 +
        acoustic * 0.82 +
        slope    * 0.78 +
        rainfall * 0.22
    )
    overall = clamp(
        max(flood, landslide) * 0.72 +
        min(flood, landslide) * 0.28
    )
    return flood, landslide, overall


def _reasons(sensor: dict) -> list[str]:
    rainfall = float(sensor["rainfall_mm"])
    river    = float(sensor["river_level_m"])
    soil     = float(sensor["soil_moisture"])
    acoustic = float(sensor["acoustic_anomaly"])
    slope    = float(sensor["slope_deg"])

    r = []
    if rainfall >= 55:  r.append("Heavy rainfall")
    if river    >= 4.0: r.append("River level rising")
    if soil     >= 75:  r.append("Soil saturation")
    if acoustic >= 65:  r.append("Subsurface acoustic anomaly")
    if slope    >= 30:  r.append("Steep terrain")
    if not r:           r.append("No major anomaly detected")
    return r


def _confidence(sensor: dict, live: bool, ml_conf: float) -> float:
    """Blend ML confidence with channel-agreement bonus."""
    base = ml_conf if ml_conf > 0 else (78.0 if live else 62.0)

    high_signals = sum([
        float(sensor.get("rainfall_mm",     0)) >= 50,
        float(sensor.get("river_level_m",   0)) >= 3.5,
        float(sensor.get("soil_moisture",   0)) >= 70,
        float(sensor.get("acoustic_anomaly",0)) >= 55,
    ])
    if high_signals >= 3: base += 8
    elif high_signals >= 2: base += 4

    return round(clamp(base, 40.0, 97.0), 1)


def calculate_risk(sensor: dict) -> dict:
    """
    Compute ensemble risk assessment for one sensor zone.

    Uses 60% RandomForest ML + 40% physics formula blend.
    Falls back to physics-only if ML import fails.
    """
    population = int(sensor.get("population", 0))
    live       = bool(sensor.get("weather_live", False))

    # ── Physics formula ──────────────────────────────────────
    flood, landslide, phys_score = _physics_score(sensor)

    # ── ML prediction ────────────────────────────────────────
    ml_info     = {}
    ml_score    = phys_score   # default fallback
    ml_conf     = 0.0
    ml_level_str = None

    try:
        from ml_model import ml_predict, LABELS
        ml_info      = ml_predict(sensor)
        ml_level_str = ml_info["ml_level"]
        ml_conf      = ml_info["ml_confidence"]

        # Convert ML class to numeric score midpoint
        _class_scores = {"LOW": 17.5, "MODERATE": 47.5, "HIGH": 70.0, "CRITICAL": 90.0}
        ml_score = _class_scores.get(ml_level_str, phys_score)

    except Exception:
        pass   # graceful fallback — use physics only

    # ── Ensemble blend: 60% ML + 40% physics ─────────────────
    overall = clamp(ml_score * 0.60 + phys_score * 0.40)

    # ── Rescue priority ──────────────────────────────────────
    rescue_priority = clamp(overall * 0.72 + min(population / 70, 28))

    # ── Confidence ───────────────────────────────────────────
    confidence = _confidence(sensor, live, ml_conf)

    result = {
        "flood_score":      round(flood,           1),
        "landslide_score":  round(landslide,        1),
        "overall_score":    round(overall,          1),
        "level":            classify(overall),
        "reasons":          _reasons(sensor),
        "rescue_priority":  round(rescue_priority,  1),
        "confidence":       confidence,
    }

    # Attach ML metadata if available
    if ml_info:
        result["ml_level"]            = ml_level_str
        result["ml_proba"]            = ml_info.get("ml_proba", {})
        result["feature_importances"] = ml_info.get("feature_importances", {})
        result["model_accuracy"]      = ml_info.get("model_accuracy", 0)

    return result
