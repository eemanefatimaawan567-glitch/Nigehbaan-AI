# 🛡 Nigehbaan AI — Guardian of Lives · نگہبان

> **Multi-hazard early warning and rescue prioritization for Pakistan's most vulnerable communities.**

---

## The Problem

Pakistan faces catastrophic annual flood and landslide seasons.

- **$30B+** in flood damage in the 2022 monsoon season alone
- **33 million** people displaced in 2022 — the worst flooding in Pakistan's recorded history
- Current NDMA warning systems operate on a **72-hour lead time** using coarse national-level data
- Local rescue coordinators have **no real-time, zone-level risk score** to prioritize response

No platform exists that fuses multi-sensor environmental data with population density to give rescue coordinators a ranked priority list — **until now.**

---

## What Nigehbaan Does

Nigehbaan AI ingests four environmental channels per monitored zone:

| Channel | What it measures |
|---------|-----------------|
| 🌧 Rainfall intensity | Precipitation accumulation at the zone level |
| 🌊 River gauge level | Live river height vs. flood thresholds |
| 💧 Soil saturation | Moisture content indicating slope instability |
| 🔊 Acoustic anomaly | Sub-surface micro-fracture signature (landslide precursor) |

It produces:
- A **flood score** and **landslide score** per zone (0–100)
- An **overall risk level** (LOW / MODERATE / HIGH / CRITICAL)
- A **rescue priority rank** — weighted by risk AND population density
- A **human-readable reason list** (e.g. "Heavy rainfall · Soil saturation · Steep terrain")

Rescue coordinators can use the prototype to **prepare and log alert-dispatch actions** for channels such as SMS broadcast, Rescue 1122, NDMA, or district administration. These external channels are demonstration targets in the current MVP; production deployment requires approved integrations.

---

## Live Dashboard

- **26 monitored zones** across KPK, Punjab, AJK, Sindh, Balochistan, Gilgit-Baltistan
- Interactive **Leaflet / OpenStreetMap** hazard map with color-coded risk markers
- Real-time simulated sensor updates (production: replaces simulation with live PMD/SUPARCO feeds)
- Filter zones by risk level
- Alert dispatch with multi-channel selection
- Full alert history log

---

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open: [http://127.0.0.1:5002](http://127.0.0.1:5002)

Default demo credentials (from `.env.example`):
- **Username:** `admin`
- **Password:** `ChangeMe123!`

Change both before any public deployment.

```bash
# Run tests
pytest -q
```

---

## API Reference

### `GET /health`
Unauthenticated health check. Returns zone count.

### `GET /api/weather`
Authenticated. Returns all 26 zones enriched with live rainfall and soil moisture from Open-Meteo (ECMWF model). Cached 10 minutes per zone. Falls back to stored values if API is unreachable.

### `GET /api/status`
Authenticated. Returns all zones with current simulated sensor readings and computed risk scores.

### `POST /api/alerts`
Authenticated. Dispatches an alert and logs it.

```json
{
  "zone":     "Swat Valley — Mingora",
  "level":    "CRITICAL",
  "message":  "Immediate evacuation advised. River at 5.8m.",
  "channels": ["SMS Broadcast", "Rescue 1122", "NDMA"]
}
```

### `GET /api/alerts`
Authenticated. Returns the last 50 dispatched alerts.

### `POST /api/sensors`
Authenticated. Adds a new sensor zone.

```json
{
  "id": "NG-25", "location": "Demo Valley", "province": "KPK",
  "lat": 33.8, "lng": 73.2,
  "rainfall_mm": 65, "river_level_m": 3.4,
  "soil_moisture": 81, "acoustic_anomaly": 72,
  "slope_deg": 31, "population": 750
}
```

---

## Competition / Commercialization

For the 2026 Wujiaochang competition, see **[Competition Brief](COMPETITION_WUJIAOCHANG_2026.md)** for the customer, business-model, validation and commercialization plan.

## Data Roadmap

### Phase 1 · MVP (Complete ✓)
- Physics-based sensor simulation with realistic Pakistani geography
- Risk-scoring prototype designed around disaster-domain thresholds; field validation still required
- Full dashboard, alert dispatch, and API layer
- 24 zones across 6 provinces

### Phase 2 · Pilot (Q2 2025)
- **PMD** (Pakistan Meteorological Department) — live rainfall and river gauge feeds
- **SUPARCO** — satellite-derived soil moisture via SAR imagery
- **NDMA** — historical disaster event ground truth for model calibration
- 5-zone KPK pilot with IoT acoustic sensors (Swat, Mansehra, Abbottabad corridor)

### Phase 3 · Scale (Q4 2025)
- 100+ sensor zones nationwide
- ML model trained on labeled PMD + NDMA event data
- SMS alerts via Jazz/Zong emergency broadcast integration
- Rescue 1122 dispatch system API integration
- Multi-user role-based access (field officers, district admins, NDMA)

---

## Security

| Feature | Status |
|---------|--------|
| HMAC constant-time credential comparison | ✓ |
| Rate limiting (login: 10/min, API: 60/min) | ✓ |
| HttpOnly, SameSite, Secure session cookies | ✓ |
| Content-Security-Policy headers | ✓ |
| X-Frame-Options, Referrer-Policy, Permissions-Policy | ✓ |
| 64KB request body cap | ✓ |
| Input type + range validation on all API endpoints | ✓ |
| Atomic JSON file writes (no partial-write corruption) | ✓ |
| No secrets committed to source control | ✓ |
| CSRF protection | Production upgrade |

---

## Validation & Honesty Note

This prototype uses **simulated acoustic anomaly data**, and its ML classifier is trained/tested on **synthetic sensor records**. Any model accuracy shown in the dashboard is therefore internal synthetic-test performance, **not field-validated disaster-prediction accuracy**. A production deployment requires calibrated field sensors, authoritative historical-event back-testing, labeled real-world data, domain-expert review and a bounded pilot. Live rainfall and surface-soil-moisture enrichment is currently available through Open-Meteo; other operational feeds and agency integrations remain future work.

---

## Stack

- **Backend:** Python / Flask 3.1
- **Risk engine:** Pure Python (no ML dependency — deterministic formula, swappable for ML model in Phase 3)
- **Frontend:** Vanilla JS + Leaflet.js / OpenStreetMap
- **Storage:** JSON file (Phase 2: PostgreSQL / Firestore)
- **Auth:** Session-based with HMAC credential verification

---

## Why Nigehbaan

> نگہبان — *Niga-hbaan* — means "Guardian" in Urdu.

Pakistan loses billions every monsoon season to disasters that are increasingly predictable with the right data infrastructure. Nigehbaan's goal is to give local rescue coordinators the information they need **5 minutes after a threshold is crossed** — not 72 hours later when national agencies issue bulletins.

The people most affected by Pakistan's floods are in the areas with the least data coverage. Nigehbaan is built to change that.
