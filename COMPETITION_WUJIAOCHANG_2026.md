# Nigehbaan AI — Wujiaochang 2026 Competition Brief

## One-line pitch
**Nigehbaan AI is a decision-support platform that combines environmental signals, machine-learning risk scoring, population exposure and automated alerts to help emergency coordinators identify which locations need attention first.**

## Problem
Floods and landslides can affect many locations at once. Emergency teams need more than a weather bulletin: they need a zone-level view that combines hazard indicators with the number of people potentially exposed and turns those signals into a prioritized response list.

## Solution
Nigehbaan AI converts multi-source environmental readings into:
- flood and landslide risk scores;
- LOW / MODERATE / HIGH / CRITICAL classifications;
- a rescue-priority score incorporating population exposure;
- an interactive map and analytics dashboard;
- context-aware alert drafts and recommended actions;
- an auditable alert history.

## What works in the current prototype
- Flask web application with authenticated dashboard and APIs.
- 26 demonstration zones across Pakistan.
- Live rainfall and surface-soil-moisture enrichment through Open-Meteo where available.
- Ensemble risk engine combining a deterministic hazard formula with a lightweight Random-Forest-style classifier.
- Rescue-priority ranking using hazard score and population.
- NLP-based alert drafting.
- Interactive map, analytics and alert history.
- Rate limiting, security headers, payload validation and automated tests.

## Validation status — important
The current machine-learning classifier is trained and tested on **synthetically generated sensor records whose ranges and thresholds were designed around disaster-domain assumptions**. Its internal test accuracy therefore measures performance on that synthetic dataset; it is **not a claim of field accuracy or independently validated disaster-prediction performance**.

The acoustic-anomaly channel is also simulated in the present prototype. Before operational use, Nigehbaan requires field sensor calibration, historical-event back-testing, expert review and pilot validation.

## Innovation
Nigehbaan is not positioned as a replacement for meteorological or disaster-management agencies. Its proposed value is the **decision layer between incoming hazard data and local response**: fusing multiple indicators, estimating zone risk, incorporating population exposure, ranking locations and converting results into actionable response information.

## Initial customer / user segment
**Beachhead users:** district emergency operations centres, university/campus safety teams, industrial sites and NGOs operating in flood- or landslide-prone regions.

**Primary users:** emergency coordinators and field-response managers.

## Business model hypothesis
A B2B/B2G model:
1. annual software subscription for dashboard, analytics, alert workflows and reporting;
2. implementation/integration fee for customer data sources and deployment;
3. optional sensor/edge-device package delivered with hardware partners;
4. enterprise support and multi-site plans.

Pricing will be validated through customer discovery and pilot discussions rather than claimed before evidence exists.

## Go-to-market
**Stage 1 — Pilot:** one bounded site or district with existing weather/environmental feeds; establish baseline metrics and run historical-event back-tests.

**Stage 2 — Validate:** compare alerts and risk rankings with historical ground truth and expert assessments; measure false alarms, missed events, lead time and operator usefulness.

**Stage 3 — Integrate:** connect approved local data sources and real notification/dispatch providers.

**Stage 4 — Scale:** expand to multi-district deployments and additional hazards/data channels.

## 2026–2027 roadmap
### Q4 2026 — Competition-ready MVP
- Complete current dashboard, ensemble scoring, live-weather enrichment and transparent data-source labeling.
- Historical-event evaluation protocol.
- Customer discovery with emergency-management, campus-safety or NGO stakeholders.
- Deployment documentation and demo scenario.

### Q1–Q2 2027 — Pilot validation
- Run historical-event back-testing using authoritative datasets where licensing/access permits.
- Partner with domain experts for threshold review.
- Pilot a small number of physical/environmental sensors.
- Measure precision/recall, false-alarm rate, lead time and usability.

### Q3–Q4 2027 — Operational integration
- PostgreSQL-backed multi-user deployment.
- Role-based access and audit controls.
- Approved SMS/notification provider integration.
- Customer-specific data connectors and reporting.

## Competitive positioning
Nigehbaan's differentiator is intended to be **multi-signal local prioritization**, not raw weather forecasting. Existing weather and hazard feeds can become inputs; Nigehbaan focuses on turning them into a ranked operational picture for responders.

## Success metrics
A pilot should be judged on measurable outcomes:
- hazard classification precision/recall against historical ground truth;
- false-alarm and missed-event rates;
- alert lead time;
- time required for an operator to identify the highest-priority zone;
- percentage of alerts with traceable supporting signals;
- operator usability and trust scores.

## Responsible deployment
Nigehbaan is a decision-support prototype, not an autonomous evacuation authority. High-stakes public alerts should require authorized human review. Every dashboard output should clearly label whether each input is live, stored, estimated or simulated.

## Team
**Team Lead:** Eeman e Fatima Awan  
**University:** Institute of Space Technology, Islamabad, Pakistan  
**Program:** BS Data Science

## 60-second pitch
When floods or landslides threaten multiple communities, responders face a prioritization problem: where should limited attention and resources go first? Nigehbaan AI is a multi-hazard decision-support platform designed to turn environmental signals into a ranked operational picture. The prototype combines rainfall, river level, soil moisture, terrain and an experimental acoustic channel with population exposure to generate zone-level risk and rescue-priority scores. It then presents the results on an interactive dashboard and drafts context-aware alerts for human review. The current system already includes live weather enrichment, analytics, APIs and a working risk engine, while clearly labeling simulated and experimental inputs. Our next step is not to claim production readiness; it is to validate the system against historical events and run a bounded pilot with domain partners. Our goal is to help emergency teams move from scattered data to faster, explainable and better-prioritized decisions.
