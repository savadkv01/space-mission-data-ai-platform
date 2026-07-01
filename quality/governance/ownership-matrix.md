# Ownership Matrix

> Authoritative dataset-to-owner mapping, including source, steward, freshness
> SLA and certification status. This is the reference used during incidents and
> certification reviews.

---

## 1. Silver entities

| Entity | Track | Source | Owner | Steward | Freshness SLA | Status |
|--------|-------|--------|-------|---------|---------------|--------|
| `silver_fire` | MVP | NASA FIRMS | EO Ops Lead | Analytics Eng | ≤ 6 h | CERTIFIED |
| `silver_index` | MVP | Sentinel Hub Statistical | EO Ops Lead | Analytics Eng | ≤ 48 h | CERTIFIED |
| `silver_vessel` | MVP | Global Fishing Watch | Maritime Lead | Analytics Eng | ≤ 24 h | CERTIFIED |
| `silver_scene` | MVP | Sentinel Hub / Landsat / Earthdata | Data Product Lead | Analytics Eng | ≤ 12 h | CERTIFIED |
| `ref_aoi` | MVP | Copernicus EMS (manual) | Data Product Lead | Analytics Eng | on activation | VALIDATED |
| `silver_telemetry` | Sim | Synthetic generator | Platform Lead | Platform Eng | ≤ 5 min | VALIDATED |
| `silver_orbit` | Sim | Synthetic / TLE | Platform Lead | Platform Eng | ≤ 5 min | VALIDATED |
| `silver_space_weather` | Sim | NOAA SWPC-shaped | Platform Lead | Platform Eng | ≤ 30 min | VALIDATED |

---

## 2. Gold marts

| Mart | Grain | Owner | Steward | Feeds | Status |
|------|-------|-------|---------|-------|--------|
| `kpi_eo_daily` | geo_key / day | EO Ops Lead | Analytics Eng | UC-15 dashboards | CERTIFIED |
| `kpi_wildfire_aoi_daily` | aoi / day | EO Ops Lead | Analytics Eng | UC-15 AOI view | CERTIFIED |
| `kpi_flood_aoi_daily` | aoi / day | EO Ops Lead | Analytics Eng | UC-16 flood view | CERTIFIED |
| `fact_vessel_activity` | vessel / day | Maritime Lead | Analytics Eng | UC-18 triage | CERTIFIED |
| `fact_scene_catalog` | scene | Data Product Lead | Analytics Eng | UC-25 catalog | CERTIFIED |
| `kpi_aoi_validation` | EMS AOI | Data Product Lead | Analytics Eng | recall/precision | VALIDATED |
| `fact_sat_health` | sat / day | Platform Lead | Platform Eng | Sim demo | VALIDATED |
| `fact_weather_impact` | day | Platform Lead | Platform Eng | Sim demo | VALIDATED |
| `kpi_launch_monthly` | provider / month | Platform Lead | Platform Eng | Sim demo | VALIDATED |

---

## 3. Source connector ownership

| Connector | Dataset | Owner | Auth/secret | Notes |
|-----------|---------|-------|-------------|-------|
| `nasa_firms` | active fire | EO Ops Lead | API key | near-real-time |
| `sentinelhub` / `sentinelhub_stats` | imagery + indices | EO Ops Lead | OAuth secret | rate-limited |
| `gfw` | vessel identity | Maritime Lead | API token | slow-changing |
| `earthdata` | CMR granules | Data Product Lead | Earthdata login | metadata |
| `landsat` | Landsat STAC | Data Product Lead | none/public | metadata |
| `nasa_power` | climate grids | Platform Lead | none/public | supplementary |
| `noaa_swpc` | space weather | Platform Lead | none/public | Sim |
| `celestrak` | TLE | Platform Lead | none/public | Sim |

Secrets must be gitignored and injected via `infrastructure/env`; never committed.

---

## 4. Escalation contacts

| Severity | First responder | Escalation |
|----------|-----------------|------------|
| Critical | Data on-call (Platform Eng) | Owner |
| High | Steward | Platform Eng |
| Medium / Low | Steward | backlog review |

Roles are functional, not headcount — a single engineer may hold multiple roles
on this project. The matrix exists so accountability is unambiguous during
incidents and certification.
