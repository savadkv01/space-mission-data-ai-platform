# Prompt 12b - Climate & Air-Quality BI (Extension, Implementation)

# Enterprise Space Mission Data & AI Platform

> **Phase 12b - Business Intelligence (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 12 (`bi/`).

---

# Objective

You are acting as:

* BI Engineer
* Analytics Engineer
* Data Visualization Specialist

Your task is to **deliver dashboards for climate, dust, and air-quality monitoring** on Apache Superset, reusing the existing BI patterns.

This is an **IMPLEMENTATION phase**: dashboard specs + Superset assets + certified datasets.

---

# Scope Guardrails

* Build only on the certified serving products from Phase 11b.
* Reuse the existing Superset stack and conventions (`bi/superset/`, `bi/dashboards/`, deck.gl maps, certified datasets, RLS approach).
* Promote the existing **Weather** dashboard from synthetic → real using the new climate/air-quality products.
* Do NOT introduce new BI tooling.

---

# Context

Existing dashboards (Executive, Earth Observation) use certified `*_daily` datasets and deck.gl AOI maps. New dashboards must reuse the same dataset-certification and chart patterns.

---

# Task 1 - Air Quality & Dust Dashboard

Design + build a new dashboard sourced from `serving_air_quality_daily` + `serving_dust_event_daily`:

* AOI pollutant maps (deck.gl), AQI heat layers
* Dust plume/AOD map + dust-flag calendar
* PM2.5/PM10 trend lines, exceedance counts
* Wind-transport context panel (NASA POWER)
* Audience: air-quality / smart-city / aviation / ports teams

---

# Task 2 - Climate Indicators Dashboard

Design + build a dashboard sourced from `serving_climate_indicator_daily` + `serving_vegetation_health_daily`:

* LST + LST-anomaly map and trend
* NDVI/EVI vegetation-health map, desertification proxy
* SST + anomaly (coastal), NDWI water availability
* Deforestation / tree-cover-loss panel

---

# Task 3 - Promote Weather Dashboard (Sim → Real)

Repoint the existing Weather dashboard from synthetic `weather_impact` to real climate/air-quality products; keep layout, update datasets and KPIs.

---

# Task 4 - Executive Dashboard Update

Add climate/dust/air-quality KPIs to the Executive dashboard via the extended materialized aggregate from 11b (AQI exceedances, active dust days, LST anomaly).

---

# Task 5 - Certified Datasets & Governance

* Register new Superset datasets as **certified** (extend `bi/datasets/certified-datasets.md`).
* Update KPI catalog (`bi/kpis/`) and alert strategy (`bi/alerts/`) with air-quality/dust thresholds.
* Update dataset governance docs.

---

# Task 6 - Alerts

Define BI alerts: AQI exceedance, high-AOD dust events, extreme LST anomaly — using the existing alert-strategy pattern.

---

# Deliverables

```text
bi/dashboards/air-quality-dust-dashboard.md
bi/dashboards/climate-indicators-dashboard.md
bi/dashboards/weather-dashboard.md          (update: sim → real)
bi/dashboards/executive-dashboard.md        (update: add climate KPIs)
bi/superset/datasets/                        (new certified datasets)
bi/superset/dashboards/                       (new dashboard exports)
bi/superset/charts/                           (new charts)
bi/datasets/certified-datasets.md            (extend)
bi/kpis/kpi-catalog.md                       (extend)
bi/alerts/alert-strategy.md                  (extend)
docs/bi/climate-dashboards.md
```

---

# Critical Rules

* Implementation phase: dashboards/datasets defined and importable to Superset.
* Reuse existing BI stack and certification; no new tooling.
* Source only from certified 11b products.

---

# Acceptance Criteria

Complete only if:

* Air-Quality/Dust and Climate-Indicators dashboards delivered
* Weather dashboard promoted to real data; Executive KPIs updated
* New datasets certified; KPIs + alerts documented

---

# Definition of Done

> Analysts and executives can monitor climate, dust, and air quality on certified Superset dashboards backed by governed data products.

Stop after this phase. The remaining forward phases (13 feature store, 14 ML, 15 RAG, 16 API) should be authored to include the climate scope; phases 17-25 run once and cover the new components automatically.
