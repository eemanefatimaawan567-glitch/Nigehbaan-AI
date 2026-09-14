
import os
os.environ["ADMIN_USERNAME"]="admin"
os.environ["ADMIN_PASSWORD"]="secret"
os.environ["SECRET_KEY"]="test-secret"

from app import app

def client():
    app.config.update(TESTING=True)
    return app.test_client()

def login(c):
    return c.post("/login", data={"username":"admin","password":"secret"}, follow_redirects=False)

def test_health():
    c=client()
    r=c.get("/health")
    assert r.status_code==200
    assert r.get_json()["status"]=="ok"

def test_dashboard_requires_login():
    c=client()
    r=c.get("/")
    assert r.status_code in (301,302)

def test_login_and_dashboard():
    c=client()
    r=login(c)
    assert r.status_code in (301,302)
    r=c.get("/")
    assert r.status_code==200
    assert b"Nigehbaan AI" in r.data

def test_bad_sensor_payload_rejected():
    c=client()
    login(c)
    r=c.post("/api/sensors", json={"id":"X"})
    assert r.status_code==400
