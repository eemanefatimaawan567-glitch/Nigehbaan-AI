
from risk_engine import calculate_risk

def test_critical_landslide_case():
    s={"rainfall_mm":80,"river_level_m":2,"soil_moisture":90,"acoustic_anomaly":90,"slope_deg":40,"population":1000}
    r=calculate_risk(s)
    assert r["landslide_score"] >= 80
    assert r["level"] in {"HIGH","CRITICAL"}

def test_low_case():
    s={"rainfall_mm":0,"river_level_m":0.5,"soil_moisture":20,"acoustic_anomaly":5,"slope_deg":5,"population":10}
    r=calculate_risk(s)
    assert r["overall_score"] < 35
    assert r["level"] == "LOW"
