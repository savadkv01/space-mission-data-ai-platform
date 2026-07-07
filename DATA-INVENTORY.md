# Data Inventory — Operational Reference (Data Engineer View)

A single, consolidated inventory of every physical/logical data object across the platform's
medallion layers and serving surfaces — Bronze → Silver → Gold → Serving → BI, plus Feature Store,
ML, and Vector/RAG. Use this as the day-to-day map of "what tables/products/reports exist and what
each contains."

For operator commands (start/stop, querying Postgres/MinIO), see [OPERATIONS.md](OPERATIONS.md).
For phase status, see [README.md](README.md).

---

## Legend

| Marker | Meaning |
| --- | --- |
| ✅ Built | Implemented (code + offline tests) |
| 📐 Design | Specified in design docs, not yet implemented |
| 🔄 Sim | Simulation track — synthetic data, post-MVP demonstrator (ADR-09) |
| ⭐ MVP | Core MVP (real open data) |

Grain = one row per … . All facts/products conform to `dim_date` (UTC) and, where spatial, `dim_aoi`/`dim_geo`.

---

## 1. Bronze — Raw Landing (schema-on-read)

Bronze has **no per-source table names**; every raw record is wrapped in a standard envelope and
partitioned by `_source` + `ingest_date`. Object layout: `s3://bronze/<source>/ingest_date=YYYY-MM-DD/<batch_id>/part-*.jsonl`.

**Envelope columns (all sources):** `_ingest_id`, `_source`, `_ingest_ts`, `_event_ts`, `_batch_id`, `_format`, `_checksum`, `_source_uri`, `payload`.

| Source code | Contains | Status |
| --- | --- | --- |
| `FIRMS` / `VIIRS` | Near-real-time active-fire alerts (lat/lon, brightness, FRP, confidence) | ✅ ⭐ |
| `S2` / `SENTINELHUB` / `EARTHDATA` / `LANDSAT` | Imagery scene metadata (tile/scene id, acquisition, cloud cover, bands) | ✅ ⭐ |
| `SENTINELHUB_STATS` | Per-AOI spectral-index statistics (NDVI/NDWI/NBR buckets) | ✅ ⭐ |
| `GFW` | Global Fishing Watch vessel transmissions (MMSI, position, speed, flag) | ✅ ⭐ |
| `POWER` | NASA POWER daily weather (T2M, RH2M, WS2M, precipitation) per grid cell | ✅ ⭐ |
| `EMS` | Copernicus EMS activation footprints (file upload) | ✅ ⭐ |
| `SWPC` | NOAA space-weather indices (Kp, Dst, solar wind) | ✅ 🔄 |
| `CELESTRAK` | Orbital TLE/GP elements | ✅ 🔄 |
| `TELEMETRY` | Synthetic spacecraft telemetry stream | 📐 🔄 |

---

## 2. Silver — Conformed / Cleaned Entities

Cleaned, deduplicated, unit-standardized, AOI-tagged. Source: `docs/data-modeling/03-silver-layer.md`.

### Earth Observation & Maritime ⭐

| Entity | Grain | Contains |
| --- | --- | --- |
| `obs_fire` | 1 / fire detection | Normalized FIRMS/VIIRS detections, canonical units + confidence |
| `obs_flood` | 1 / scene / AOI | Cleaned flood-scene metadata (NDWI context) |
| `obs_vessel` | 1 / vessel identity | Normalized maritime registry (MMSI/IMO/flag) |
| `obs_scene` | 1 / scene granule | Normalized imagery metadata (Sentinel/Landsat/Earthdata) |
| `obs_index` | 1 / AOI / index / date | Spectral-index stats (NDVI, NDWI, NBR) + valid-pixel fraction |
| `ref_aoi` | 1 / EMS footprint | Copernicus EMS activation areas (reference dimension) |

### Simulation Track 🔄

| Entity | Grain | Contains |
| --- | --- | --- |
| `dim_satellite` | 1 / satellite | Normalized spacecraft identity |
| `dim_sensor` | 1 / sensor | Standardized sensor registry |
| `dim_mission` | 1 / mission | Mission metadata |
| `fact_launch_event` | 1 / launch | Launch event facts |
| `orbit_trajectory` | 1 / sat / timestamp | Orbital position time series |
| `dim_ground_station` | 1 / station | Ground-station registry |

---

## 3. Gold — Star Schema (facts, dimensions, KPI aggregates)

Source: `docs/data-modeling/04-gold-layer.md`, `05-star-schemas.md`.

### Facts

| Fact | Grain | Contains | Status |
| --- | --- | --- | --- |
| `fact_fire_detection` | 1 / detection / AOI / day | FRP + confidence (UC-15) | ✅ ⭐ |
| `fact_flood_extent` | 1 / AOI / scene | Open-water (NDWI) aggregates (UC-16) | ✅ ⭐ |
| `fact_vessel_activity` | 1 / vessel / day | Activity + suspicious flag (UC-18) | ✅ ⭐ |
| `fact_scene_catalog` | 1 / scene | Imagery metadata + searchability score (UC-25) | ✅ ⭐ |
| `fact_launch` | 1 / launch | Launch success/delay metrics | 🔄 |
| `fact_sat_health` | 1 / sat / day | Health score + anomaly count | 🔄 |
| `fact_weather_impact` | 1 / sat / storm window | Geomagnetic-to-anomaly correlation | 🔄 |

### Dimensions

| Dimension | Grain | Contains |
| --- | --- | --- |
| `dim_date` | 1 / calendar day (UTC) | Conformed date key |
| `dim_geo` | 1 / grid cell | Quantized lat/lon tile for spatial joins |
| `dim_aoi` | 1 / EMS AOI | Copernicus activation footprint |
| `dim_vessel` | 1 / vessel identity | Maritime vessel registry |
| `dim_provider` | 1 / provider | Data/launch provider registry |
| `dim_satellite` 🔄 | 1 / spacecraft | Satellite/mission identity |
| `dim_mission` 🔄 | 1 / mission | Mission metadata |

### KPI / Aggregate tables

| Table | Contains | Status |
| --- | --- | --- |
| `kpi_eo_daily` | Daily EO KPIs per grid cell (fires, burned area, flood km², revisit gap) | ✅ ⭐ |
| `kpi_wildfire_aoi_daily` | Daily wildfire detections + FRP stats per AOI | ✅ ⭐ |
| `kpi_flood_aoi_daily` | Daily NDWI statistics per AOI | ✅ ⭐ |
| `kpi_fishing_daily` | Daily maritime KPIs (vessels, suspicious events, fishing hours) | ✅ ⭐ |
| `kpi_catalog_quality` | Scene metadata completeness % + searchable count per collection | ✅ ⭐ |
| `kpi_aoi_validation` | EMS ground-truth corroboration + evidence days per AOI | ✅ ⭐ |
| `kpi_launch_monthly` | Monthly launch performance per provider | 🔄 |
| `kpi_mission` | Mission success metrics (objective %, uptime) | 🔄 |

---

## 4. Serving — Data Products, Aggregates, Semantic

Pre-denormalized, contract-tested (dbt schema tests + Python unit tests). Source: `serving/serving-models.md`, `serving/products/`.

### MVP data products ⭐

| Product | Grain | Contains |
| --- | --- | --- |
| `serving_wildfire_daily` | 1 / AOI / day | Wildfire detections + intensity + EMS corroboration (UC-15) |
| `serving_flood_daily` | 1 / AOI / day | Open-water extent (NDWI) + valid-pixel fraction (UC-16) |
| `serving_vessel_activity` | 1 / vessel / day | Vessel activity + suspicious-identity triage (UC-18, RLS) |
| `serving_scene_catalog` | 1 / scene | Searchable imagery catalog + metadata-quality band (UC-25) |
| `serving_aoi_validation` | 1 / EMS AOI | EMS ground-truth corroboration for damage prioritization (UC-27) |

### Materialized aggregates

| Object | Grain | Contains |
| --- | --- | --- |
| `mv_kpi_platform_daily` | 1 / day | Executive rollup across all EO products (detections, peak FRP, flood AOI-days, suspicious vessels) |
| `mv_catalog_quality` | 1 / collection | Catalog quality rollup (searchable rate, mean completeness, mean cloud cover) |

### Semantic layer

| Object | Contains |
| --- | --- |
| `dim_aoi` | Business-named AOI dimension (aoi_key, aoi_name, event_type, area_km2, geo_key) |
| `dim_vessel` | Business-named vessel dimension (registry attributes) |
| Metric registry (`semantic.METRICS`) | Canonical KPI definitions shared by BI, API, RAG |

### Simulation track products 🔄

| Product | Grain | Contains |
| --- | --- | --- |
| `serving_sat_health` | 1 / satellite / day | Daily health score + status band (nominal/degraded/critical) |
| `stream_sat_health_1m` | 1 / satellite / minute | Near-real-time telemetry aggregates + anomaly rate (1-min window) |
| `serving_launch_monthly` | 1 / provider / month | Monthly launch performance (success rate, delays) |
| `serving_weather_impact` | 1 / day | Geomagnetic activity (Kp, storms) + telemetry anomaly correlation |

---

## 5. BI — Dashboards & Certified Datasets

Apache Superset. Source: `bi/dashboards/`, `bi/datasets/certified-datasets.md`.

### Dashboards / reports

| Dashboard | Audience | Primary datasets | Status |
| --- | --- | --- | --- |
| Executive | Leadership | `platform_daily`, `aoi_validation` | ✅ ⭐ |
| Earth Observation | EO / Maritime ops (RLS) | `wildfire_daily`, `flood_daily`, `scene_catalog`, `vessel_activity` | ✅ ⭐ |
| Platform Operations | Engineers / Stewards | `catalog_quality` + observability metrics | ✅ ⭐ |
| Satellite Operations | Demo | `sat_health` | 🔄 |
| Launch Operations | Demo | `launch_monthly` | 🔄 |
| Space Weather | Demo | `weather_impact` | 🔄 |

### Certified datasets (BI semantic datasets)

| Dataset | Source | Grain | TTL | Status |
| --- | --- | --- | --- | --- |
| `wildfire_daily` | `serving.serving_wildfire_daily` | AOI/day | 1h | ✅ ⭐ |
| `flood_daily` | `serving.serving_flood_daily` | AOI/day | 1h | ✅ ⭐ |
| `vessel_activity` | `serving.serving_vessel_activity` | vessel/day | 1h | ✅ ⭐ |
| `scene_catalog` | `serving.serving_scene_catalog` | scene | 1h | ✅ ⭐ |
| `aoi_validation` | `serving.serving_aoi_validation` | AOI | 1h | ✅ ⭐ |
| `platform_daily` | `serving_agg.mv_kpi_platform_daily` | day | 15m | ✅ ⭐ |
| `catalog_quality` | `serving.serving_scene_catalog` | collection | 1h | ✅ ⭐ |
| `sat_health` | `gold.fact_sat_health` (DuckDB httpfs) | sat/day | — | 🔄 |
| `launch_monthly` | `gold.kpi_launch_monthly` (DuckDB httpfs) | provider/month | — | 🔄 |
| `weather_impact` | `gold.fact_weather_impact` (DuckDB httpfs) | day | — | 🔄 |

---

## 6. Feature Store — Feature Groups 📐

Design-only (Feast + Postgres offline/online planned in Phase 13). Source: `docs/data-modeling/08-feature-store.md`.
Entity keys: `sat_key` (satellite), `geo_key` (grid cell). Point-in-time joins enforce no label leakage.

| Feature group | Example features | Source | Status |
| --- | --- | --- | --- |
| EO fire risk | `ndvi`, `dryness`, `frp_trend`, `weather_idx` | Silver `obs_index` + Gold | 📐 ⭐ |
| EO spectral index | `ndvi_mean`, `ndwi_mean`, `nbr_mean`, `valid_pixel_fraction` | Silver `obs_index` | 📐 ⭐ |
| Satellite health | `temp_mean`, `voltage_var`, `anomaly_7d`, `uptime` | Silver + Gold telemetry | 📐 🔄 |
| Orbit stability | `alt_drift`, `vel_var`, `decay_rate` | Silver `orbit_trajectory` | 📐 🔄 |
| Weather impact | `kp_lag`, `flux_max`, `exposure_hr` | Gold `fact_weather_impact` | 📐 🔄 |

Storage split: **offline** = versioned Parquet snapshots (training/batch); **online** = Redis/Postgres KV (inference).

---

## 7. ML — Datasets & Artifacts 📐

Design-only (Phase 14). Source: `serving/ai-data-serving.md`, `architecture/07-ai-ml-architecture.md`.

| Artifact | Type | Contains |
| --- | --- | --- |
| Wildfire escalation training set | Training | Labeled from `serving_wildfire_daily` + `serving_aoi_validation` (EMS labels) |
| Vessel-anomaly training set | Training | Labeled from `serving_vessel_activity` |
| Daily flood-risk scoring input | Inference | Feature vectors from `serving_flood_daily` |
| AOI feature vector | Inference | Quality-checked offline features promoted to online KV |
| MLflow model registry | Registry | Experiments, params, metrics, versions, stage transitions |
| Model serving API | Serving | FastAPI exposing prediction endpoints from approved MLflow version |

Monitoring hooks: prediction latency/throughput, input feature drift, output distribution, feature data quality.

---

## 8. Vector / RAG — Collections 📐

Design-only (Qdrant + Ollama, Phase 15). Source: `docs/data-modeling/09-vector-model.md`.
Chunk schema: `chunk_id`, `embedding`, `source_ref` (grounding key), `text`, `metadata`.

| Collection | Embedding source | Use | Status |
| --- | --- | --- | --- |
| Mission knowledge base | Mission docs, ADRs, reports, specs | Analyst Q&A RAG | 📐 ⭐ |
| Geo-event cards | Fire/flood/change-detection event cards | Situational Q&A over events | 📐 ⭐ |
| Telemetry anomaly summaries | Anomaly descriptions + context | Semantic search on telemetry events | 📐 🔄 |

---

## Lineage (end-to-end)

```mermaid
flowchart LR
    B[Bronze<br/>raw JSONL envelopes] --> S[Silver<br/>obs_* / ref_aoi]
    S --> G[Gold<br/>fact_* / dim_* / kpi_*]
    G --> SV[Serving<br/>serving_* / mv_*]
    SV --> BI[BI datasets<br/>+ dashboards]
    G --> FS[Feature Store 📐]
    SV --> FS
    FS --> ML[ML 📐]
    G --> RAG[Vector/RAG 📐]
    ML --> API[Platform API 📐]
    RAG --> API
```

---

## Planned Additions — Climate / Dust / Air-Quality (authored, not built)

Delivered via extension prompts `05b`–`16b` (see [README.md](README.md#planned-expansion--climate-dust--air-quality-monitoring)). New objects will follow the same patterns and AOI-date grain:

| Layer | Planned objects |
| --- | --- |
| Bronze | `OPENAQ`, `TROPOMI`, `MODIS_AOD` source classes (JSONL) |
| Silver | `obs_air_quality`, `obs_aerosol`, `obs_atmos_column` |
| Gold | `fact_air_quality_daily`, `fact_dust_event_daily`, `fact_climate_indicator_daily`, `fact_vegetation_health_daily`; dims `dim_pollutant`, `dim_climate_indicator` |
| Serving | `serving_air_quality_daily`, `serving_dust_event_daily`, `serving_climate_indicator_daily`, `serving_vegetation_health_daily` |
| BI | Air-Quality/Dust dashboard, Climate-Indicators dashboard, Weather dashboard (sim → real) |
| Feature/ML | AQ/dust/climate feature views; AOD→PM regression, dust & heatwave forecast models |
| RAG | Environmental-report / climate-summary corpus over new Gold products |
