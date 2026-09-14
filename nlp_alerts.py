"""
nlp_alerts.py — Context-aware NLP alert message generator for Nigehbaan AI

Generates professional, actionable alert messages by analysing sensor readings,
risk scores, and zone context. No external API required — works offline.

Architecture:
  - Rule-based NLP with contextual slot-filling
  - Multi-clause sentence construction from sensor facts
  - Tone calibrated to risk level (informational → urgent → emergency)
  - Pakistan-specific place names, agencies, and protocols
"""

from __future__ import annotations
import random


# ── Tone templates by risk level ──────────────────────────────

_OPENERS = {
    "CRITICAL": [
        "🔴 EMERGENCY ALERT — {zone} ({province})",
        "🔴 CRITICAL HAZARD ACTIVE — {zone}",
        "🔴 IMMEDIATE THREAT — {zone}, {province}",
    ],
    "HIGH": [
        "🟠 HIGH RISK WARNING — {zone} ({province})",
        "🟠 ELEVATED HAZARD — {zone}",
        "🟠 URGENT ADVISORY — {zone}, {province}",
    ],
    "MODERATE": [
        "🟡 MODERATE RISK ADVISORY — {zone} ({province})",
        "🟡 PRECAUTIONARY NOTICE — {zone}",
    ],
    "LOW": [
        "🟢 ROUTINE MONITORING — {zone} ({province})",
        "🟢 LOW RISK UPDATE — {zone}",
    ],
}

_CLOSERS = {
    "CRITICAL": [
        "Rescue 1122 and NDMA teams have been notified. Immediate evacuation of low-lying areas is advised.",
        "District administration and Rescue 1122 are on standby. All residents must move to higher ground immediately.",
        "Emergency services are being mobilised. Do not wait for further instruction — evacuate now.",
    ],
    "HIGH": [
        "Rescue 1122 has been placed on high alert. Residents in vulnerable areas should prepare for possible evacuation.",
        "District administration has been informed. Residents near water bodies should move valuables to higher floors.",
        "Authorities are monitoring the situation closely. Avoid travel near rivers and steep slopes.",
    ],
    "MODERATE": [
        "Local authorities have been notified. Residents should monitor updates and avoid unnecessary travel near slopes.",
        "No immediate action required, but residents should remain alert and follow official advisories.",
    ],
    "LOW": [
        "No immediate action required. Continue to monitor official weather updates from PMD.",
        "Situation is stable. Routine monitoring continues.",
    ],
}


# ── Sensor-fact sentence builders ─────────────────────────────

def _rainfall_sentence(mm: float, mm_24h: float | None, level: str) -> str | None:
    if mm <= 0 and (mm_24h is None or mm_24h <= 0):
        return None
    if level in ("CRITICAL", "HIGH") and mm >= 50:
        return f"Rainfall of {mm} mm recorded in the last 6 hours ({mm_24h or mm_24h} mm over 24 h) — well above the {55} mm flood-trigger threshold."
    if mm >= 30:
        return f"Significant rainfall of {mm} mm in the last 6 hours has been detected by Open-Meteo weather sensors."
    if mm > 0:
        return f"Rainfall of {mm} mm recorded in the last 6 hours."
    return None


def _river_sentence(river_m: float, level: str) -> str | None:
    if river_m <= 0:
        return None
    if river_m >= 5.0:
        return f"River gauge is at {river_m} m — exceeding the critical flood level of 4.5 m. Downstream flooding is imminent."
    if river_m >= 4.0:
        return f"River level at {river_m} m is approaching the critical threshold. Conditions may deteriorate rapidly."
    if river_m >= 2.5:
        return f"River level elevated at {river_m} m. Continuous monitoring in progress."
    return None


def _soil_sentence(soil: float, level: str) -> str | None:
    if soil >= 85:
        return f"Soil saturation at {soil}% — ground is at near-maximum water capacity, sharply elevating landslide risk."
    if soil >= 70:
        return f"High soil moisture ({soil}%) indicates significant saturation, increasing slope instability."
    if soil >= 55:
        return f"Elevated soil moisture ({soil}%) detected."
    return None


def _acoustic_sentence(acoustic: float) -> str | None:
    if acoustic >= 75:
        return f"Sub-surface acoustic sensors are registering anomalies at {acoustic}% intensity — a potential precursor to slope failure or underground movement."
    if acoustic >= 55:
        return f"Acoustic anomaly detected at {acoustic}% — possible sub-surface instability."
    if acoustic >= 40:
        return f"Minor acoustic signal ({acoustic}%) is being monitored for escalation."
    return None


def _slope_sentence(slope: float, soil: float) -> str | None:
    if slope >= 40 and soil >= 65:
        return f"The terrain gradient of {slope}° combined with saturated soils creates a high probability of debris flow or landslide."
    if slope >= 30:
        return f"Steep terrain ({slope}°) amplifies hazard risk in this zone."
    return None


def _population_sentence(pop: int, level: str) -> str | None:
    if level in ("CRITICAL", "HIGH") and pop >= 3000:
        return f"Approximately {pop:,} residents are in the immediate risk perimeter."
    if pop >= 1000:
        return f"An estimated {pop:,} people may be affected."
    return None


def _confidence_sentence(confidence: float, data_source: str) -> str:
    src = "live Open-Meteo weather data" if "Open-Meteo" in data_source else "simulated sensor data"
    if confidence >= 85:
        return f"AI confidence: {confidence:.0f}% (high) — based on {src}."
    if confidence >= 65:
        return f"AI confidence: {confidence:.0f}% (moderate) — based on {src}."
    return f"AI confidence: {confidence:.0f}% (low) — based on {src}. Manual verification recommended."


# ── Main generator ────────────────────────────────────────────

def generate_alert_message(sensor: dict, risk: dict) -> str:
    """
    Generate a full, professional NLP alert message from sensor readings and
    computed risk scores.

    Parameters
    ----------
    sensor : enriched sensor dict (may contain weather_live, weather_source, etc.)
    risk   : output of calculate_risk() — must include 'level', 'confidence',
             'flood_score', 'landslide_score', 'overall_score'

    Returns
    -------
    str — multi-sentence alert message
    """
    level    = risk.get("level", "MODERATE")
    zone     = sensor.get("location", "Unknown Zone")
    province = sensor.get("province", "Pakistan")

    rainfall    = float(sensor.get("rainfall_mm", 0))
    rainfall_24 = sensor.get("rainfall_24h_mm")
    river       = float(sensor.get("river_level_m", 0))
    soil        = float(sensor.get("soil_moisture", 0))
    acoustic    = float(sensor.get("acoustic_anomaly", 0))
    slope       = float(sensor.get("slope_deg", 0))
    population  = int(sensor.get("population", 0))
    confidence  = float(risk.get("confidence", 75.0))
    data_source = sensor.get("weather_source", "Simulated")
    flood_score = risk.get("flood_score", 0)
    land_score  = risk.get("landslide_score", 0)

    # ── Build opener ──
    opener_tpl = random.choice(_OPENERS.get(level, _OPENERS["MODERATE"]))
    opener = opener_tpl.format(zone=zone, province=province)

    # ── Score summary ──
    primary_hazard = "flooding" if flood_score >= land_score else "landslide"
    score_line = (
        f"Nigehbaan AI has assigned an overall risk score of {risk['overall_score']}% "
        f"(flood: {flood_score}%, landslide: {land_score}%). "
        f"Primary hazard: {primary_hazard}."
    )

    # ── Sensor facts (only include if significant) ──
    facts = [
        _rainfall_sentence(rainfall, rainfall_24, level),
        _river_sentence(river, level),
        _soil_sentence(soil, level),
        _acoustic_sentence(acoustic),
        _slope_sentence(slope, soil),
        _population_sentence(population, level),
    ]
    facts = [f for f in facts if f]  # drop None

    # ── Recommended actions by level ──
    action_map = {
        "CRITICAL": (
            "RECOMMENDED ACTIONS: (1) Activate emergency response teams immediately. "
            "(2) Issue public evacuation orders for low-lying and slope-adjacent areas. "
            "(3) Pre-position rescue boats and medical units. "
            "(4) Coordinate with NDMA and district administration."
        ),
        "HIGH": (
            "RECOMMENDED ACTIONS: (1) Place Rescue 1122 on high alert. "
            "(2) Advise residents near rivers and slopes to be ready to evacuate. "
            "(3) Notify district emergency operations centre. "
            "(4) Inspect and reinforce vulnerable embankments."
        ),
        "MODERATE": (
            "RECOMMENDED ACTIONS: (1) Increase monitoring frequency. "
            "(2) Brief local civil defence teams. "
            "(3) Ensure evacuation routes are clear and accessible."
        ),
        "LOW": (
            "RECOMMENDED ACTIONS: Maintain routine monitoring. "
            "No immediate field action required."
        ),
    }
    actions = action_map.get(level, action_map["MODERATE"])

    # ── Closer + confidence ──
    closer = random.choice(_CLOSERS.get(level, _CLOSERS["MODERATE"]))
    conf_line = _confidence_sentence(confidence, data_source)

    # ── Assemble ──
    parts = [opener, "", score_line]
    if facts:
        parts.append(" ".join(facts))
    parts += ["", actions, "", closer, "", conf_line]

    return "\n".join(parts)


def generate_short_summary(sensor: dict, risk: dict) -> str:
    """
    One-sentence card summary shown on the dashboard card.
    """
    level    = risk.get("level", "MODERATE")
    zone     = sensor.get("location", "Zone")
    flood    = risk.get("flood_score", 0)
    land     = risk.get("landslide_score", 0)
    primary  = "flood" if flood >= land else "landslide"
    conf     = risk.get("confidence", 75)
    live     = sensor.get("weather_live", False)
    src      = "live data" if live else "simulated data"

    summaries = {
        "CRITICAL": f"Imminent {primary} threat detected. AI confidence {conf:.0f}% — based on {src}. Immediate action required.",
        "HIGH":     f"Elevated {primary} risk. AI confidence {conf:.0f}% ({src}). Prepare for possible evacuation.",
        "MODERATE": f"Moderate {primary} conditions. AI confidence {conf:.0f}% ({src}). Monitor closely.",
        "LOW":      f"Low hazard level. AI confidence {conf:.0f}% ({src}). Routine monitoring active.",
    }
    return summaries.get(level, summaries["MODERATE"])
