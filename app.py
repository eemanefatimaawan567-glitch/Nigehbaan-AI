"""
app.py — Nigehbaan AI Flask application

Routes:
  GET/POST /login          — auth
  POST     /logout         — clear session
  GET      /               — main dashboard
  GET      /api/status     — live sensor + risk JSON (simulated jitter)
  GET      /api/weather    — live Open-Meteo enriched sensor data
  POST     /api/alerts     — dispatch & store an alert
  GET      /api/alerts     — fetch recent alerts
  POST     /api/sensors    — add a new sensor zone
  GET      /health         — health check
"""

import json, os, random, tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from risk_engine import calculate_risk
from security import login_required, valid_credentials, validate_sensor_payload
from weather_service import enrich_sensor_with_live_weather
from nlp_alerts import generate_alert_message, generate_short_summary

load_dotenv()

BASE_DIR   = Path(__file__).resolve().parent
DATA_FILE  = BASE_DIR / "data" / "sensors.json"
ALERT_FILE = BASE_DIR / "data" / "alerts.json"

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
    MAX_CONTENT_LENGTH=64 * 1024,
)

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "60 per hour"])


# ── Data helpers ──────────────────────────────────────────────

def _atomic_write(path: Path, data):
    """Write JSON atomically — no partial-write corruption on crash."""
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

def load_sensors():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_sensors(items):
    _atomic_write(DATA_FILE, items)

def load_alerts():
    if not ALERT_FILE.exists():
        return []
    return json.loads(ALERT_FILE.read_text(encoding="utf-8"))

def save_alerts(items):
    _atomic_write(ALERT_FILE, items)


def build_dashboard_data(simulate: bool = False, live_weather: bool = False) -> list:
    """
    Build the full dashboard payload.
    - simulate:     adds random jitter to sensor values (for demo refresh)
    - live_weather: enriches rainfall + soil moisture from Open-Meteo API
    """
    results = []
    for sensor in load_sensors():
        current = dict(sensor)

        if simulate:
            current["rainfall_mm"]      = round(max(0, current["rainfall_mm"]      + random.uniform(-5,  7)),  1)
            current["river_level_m"]    = round(max(0, current["river_level_m"]    + random.uniform(-0.2, 0.3)), 2)
            current["soil_moisture"]    = round(max(0, min(100, current["soil_moisture"]    + random.uniform(-3, 4))),  1)
            current["acoustic_anomaly"] = round(max(0, min(100, current["acoustic_anomaly"] + random.uniform(-7, 9))),  1)

        if live_weather:
            current = enrich_sensor_with_live_weather(current)

        risk = calculate_risk(current)
        current["risk"] = risk

        # AI short summary for card display
        current["ai_summary"] = generate_short_summary(current, risk)

        results.append(current)

    return sorted(results, key=lambda x: x["risk"]["rescue_priority"], reverse=True)


# ── Security headers ──────────────────────────────────────────

@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"]  = "nosniff"
    resp.headers["X-Frame-Options"]         = "DENY"
    resp.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"]      = "geolocation=(), microphone=(), camera=()"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://unpkg.com https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "script-src 'self' https://unpkg.com 'unsafe-inline'; "
        "img-src 'self' data: https://*.tile.openstreetmap.org; "
        "connect-src 'self' https://api.open-meteo.com;"
    )
    return resp


# ── Auth ──────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        username = request.form.get("username", "")[:100]
        password = request.form.get("password", "")[:200]
        if valid_credentials(username, password):
            session.clear()
            session["authenticated"] = True
            next_url = request.args.get("next", "")
            # validate next is a relative path to prevent open redirect
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    sensors = build_dashboard_data()
    alerts  = load_alerts()[-20:][::-1]
    return render_template("index.html", sensors=sensors, alerts=alerts)


# ── API: simulated live refresh ───────────────────────────────

@app.get("/api/status")
@login_required
@limiter.limit("60 per minute")
def api_status():
    return jsonify(build_dashboard_data(simulate=True))


# ── API: live Open-Meteo weather ──────────────────────────────

@app.get("/api/weather")
@login_required
@limiter.limit("10 per minute")
def api_weather():
    """
    Returns sensor data enriched with live Open-Meteo rainfall and soil moisture.
    Cached for 10 minutes per zone to avoid API rate limits.
    Attribution: Open-Meteo.com (open-source weather API, free for non-commercial use)
    """
    data = build_dashboard_data(live_weather=True)
    live_count = sum(1 for s in data if s.get("weather_live", False))
    return jsonify({
        "zones":      data,
        "live_count": live_count,
        "total":      len(data),
        "source":     "Open-Meteo.com / ECMWF",
        "note":       "Rainfall and soil moisture from live Open-Meteo API where available.",
    })


# ── API: alert dispatch ───────────────────────────────────────

@app.post("/api/alerts")
@login_required
@limiter.limit("20 per minute")
def send_alert():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 415

    body     = request.get_json(silent=True) or {}
    zone     = str(body.get("zone",    ""))[:120].strip()
    level    = str(body.get("level",   ""))[:20].strip().upper()
    message  = str(body.get("message", ""))[:500].strip()
    channels = body.get("channels", [])
    sensor   = body.get("sensor_data")   # optional — used for NLP generation
    risk     = body.get("risk_data")     # optional — used for NLP generation

    if not zone or not level:
        return jsonify({"error": "zone and level are required"}), 400
    if level not in {"CRITICAL", "HIGH", "MODERATE", "LOW"}:
        return jsonify({"error": "invalid level"}), 400
    if not isinstance(channels, list):
        channels = []
    channels = [str(c)[:40] for c in channels[:5]]

    # ── NLP message generation ──
    if not message:
        if sensor and risk:
            message = generate_alert_message(sensor, risk)
        else:
            # Minimal fallback without full sensor context
            _s = {"location": zone, "province": "", "rainfall_mm": 0,
                  "river_level_m": 0, "soil_moisture": 0, "acoustic_anomaly": 0,
                  "slope_deg": 0, "population": 0, "weather_live": False,
                  "weather_source": "Simulated"}
            _r = {"level": level, "flood_score": 0, "landslide_score": 0,
                  "overall_score": 0, "confidence": 70}
            message = generate_alert_message(_s, _r)

    alert = {
        "id":       f"ALT-{int(datetime.now(timezone.utc).timestamp()*1000) % 100000:05d}",
        "zone":     zone,
        "level":    level,
        "message":  message,
        "channels": channels,
        "sent_at":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sent_by":  "Command Centre",
    }

    alerts = load_alerts()
    alerts.append(alert)
    if len(alerts) > 200:
        alerts = alerts[-200:]
    save_alerts(alerts)

    return jsonify({"ok": True, "alert": alert}), 201


# ── API: get alerts ───────────────────────────────────────────

@app.get("/api/alerts")
@login_required
@limiter.limit("30 per minute")
def get_alerts():
    return jsonify(load_alerts()[-50:][::-1])


# ── API: analytics ───────────────────────────────────────────

@app.get("/api/analytics")
@login_required
@limiter.limit("30 per minute")
def api_analytics():
    """
    Aggregated analytics for Chart.js dashboard charts.
    Returns: risk distribution, province breakdown, feature importance,
             model accuracy, population at risk by level.
    """
    from collections import Counter
    from ml_model import get_model, get_accuracy, FEATURE_NAMES

    data = build_dashboard_data()

    # Risk level distribution
    level_counts = Counter(s["risk"]["level"] for s in data)
    risk_dist = {lvl: level_counts.get(lvl, 0)
                 for lvl in ["CRITICAL", "HIGH", "MODERATE", "LOW"]}

    # Province breakdown
    prov_risk: dict = {}
    for s in data:
        prov = s.get("province", "Other")
        lvl  = s["risk"]["level"]
        if prov not in prov_risk:
            prov_risk[prov] = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0, "total": 0}
        prov_risk[prov][lvl]    += 1
        prov_risk[prov]["total"] += 1

    # Population at risk by level
    pop_by_level: dict = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
    for s in data:
        pop_by_level[s["risk"]["level"]] += s.get("population", 0)

    # Feature importances from ML model
    try:
        model = get_model()
        feat_imp = {FEATURE_NAMES[i]: round(model.feature_importances_[i] * 100, 1)
                    for i in range(len(FEATURE_NAMES))}
        model_acc = get_accuracy()
    except Exception:
        feat_imp  = {}
        model_acc = 0

    # Average confidence per level
    conf_by_level: dict = {}
    for lvl in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
        zones = [s["risk"]["confidence"] for s in data if s["risk"]["level"] == lvl]
        conf_by_level[lvl] = round(sum(zones) / len(zones), 1) if zones else 0

    return jsonify({
        "risk_distribution":  risk_dist,
        "province_breakdown": prov_risk,
        "pop_at_risk":        pop_by_level,
        "feature_importance": feat_imp,
        "model_accuracy":     model_acc,
        "confidence_by_level":conf_by_level,
        "total_zones":        len(data),
        "total_population":   sum(s.get("population", 0) for s in data),
    })


# ── API: add sensor ───────────────────────────────────────────

@app.post("/api/sensors")
@login_required
@limiter.limit("10 per minute")
def add_sensor():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 415
    payload = validate_sensor_payload(request.get_json())
    sensors = load_sensors()
    if any(x["id"] == payload["id"] for x in sensors):
        return jsonify({"error": "Sensor ID already exists"}), 409
    sensors.append(payload)
    save_sensors(sensors)
    return jsonify({"ok": True, "sensor": payload}), 201


# ── Health ────────────────────────────────────────────────────

@app.get("/health")
def health():
    return jsonify({
        "status":  "ok",
        "service": "nigehbaan-ai",
        "zones":   len(load_sensors()),
        "version": "2.0",
    })


# ── Error handlers ────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(err):
    return jsonify({"error": str(err.description)}), 400

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(429)
def rate_limited(_):
    return jsonify({"error": "Too many requests"}), 429


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=os.getenv("FLASK_ENV") == "development")
