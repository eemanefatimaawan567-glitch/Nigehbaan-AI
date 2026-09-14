
import hmac
import os
from functools import wraps
from flask import session, redirect, url_for, request, abort

def constant_time_equal(a, b):
    return hmac.compare_digest(str(a), str(b))

def valid_credentials(username, password):
    expected_user = os.getenv("ADMIN_USERNAME", "admin")
    expected_pass = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
    return constant_time_equal(username, expected_user) and constant_time_equal(password, expected_pass)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def validate_sensor_payload(payload):
    required = {
        "id": str, "location": str, "lat": (int,float), "lng": (int,float),
        "rainfall_mm": (int,float), "river_level_m": (int,float),
        "soil_moisture": (int,float), "acoustic_anomaly": (int,float),
        "slope_deg": (int,float), "population": int
    }
    if not isinstance(payload, dict):
        abort(400, "Invalid payload")
    for key, typ in required.items():
        if key not in payload or not isinstance(payload[key], typ):
            abort(400, f"Invalid or missing field: {key}")
    if not (-90 <= payload["lat"] <= 90 and -180 <= payload["lng"] <= 180):
        abort(400, "Invalid coordinates")
    for key in ["soil_moisture","acoustic_anomaly"]:
        if not (0 <= payload[key] <= 100):
            abort(400, f"{key} must be between 0 and 100")
    if payload["rainfall_mm"] < 0 or payload["river_level_m"] < 0 or payload["population"] < 0:
        abort(400, "Negative values are not allowed")
    return payload
