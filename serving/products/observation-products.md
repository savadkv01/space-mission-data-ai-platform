# Earth Observation Data Products (MVP)

> Primary serving surface. Real open data (FIRMS, Sentinel, GFW, Copernicus EMS).
> These products back the six MVP use cases and are the platform's core value.

Every product below is built by a pure-Python builder in
[../marts/serving_marts.py](../marts/serving_marts.py) and a mirrored dbt model in
[../dbt/models/serving/](../dbt/models/serving/).

---

## Wildfire Activity (UC-15)

| Attribute | Value |
| --- | --- |
| Product | `serving_wildfire_daily` |
| Purpose | Per-AOI daily wildfire detections + intensity for public-safety alerting |
| Owner | EO Analytics team |
| Consumers | EO analysts, emergency management, executive dashboard, RAG |
| Refresh | Daily (batch, after Gold rebuild) |
| SLA | Data freshness ≤ 24 h; dashboard read p95 ≤ 3 s |
| Source | `kpi_wildfire_aoi_daily`, `ref_aoi`, `kpi_aoi_validation` |
| Grain | 1 row / AOI / day |
| KPIs | detections, mean_frp, max_frp, severity band, EMS corroboration |

---

## Flood Extent (UC-16)

| Attribute | Value |
| --- | --- |
| Product | `serving_flood_daily` |
| Purpose | Per-AOI daily open-water (NDWI) extent for disaster response |
| Owner | EO Analytics team |
| Consumers | EO analysts, emergency management, executive dashboard |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h; dashboard read p95 ≤ 3 s |
| Source | `kpi_flood_aoi_daily`, `ref_aoi`, `kpi_aoi_validation` |
| Grain | 1 row / AOI / day |
| KPIs | ndwi_mean, ndwi_max, valid_pixel_fraction, flood_flag, EMS corroboration |

---

## Maritime Vessel Activity (UC-18)

| Attribute | Value |
| --- | --- |
| Product | `serving_vessel_activity` |
| Purpose | Daily vessel activity + suspicious-identity triage for illegal-fishing review |
| Owner | Maritime Intelligence team |
| Consumers | Maritime analysts, REST API |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h; API p95 ≤ 400 ms |
| Source | `fact_vessel_activity` |
| Grain | 1 row / vessel / day |
| KPIs | transmissions, suspicious_flag, review_priority, active_span_days |

---

## Imagery Catalog (UC-25)

| Attribute | Value |
| --- | --- |
| Product | `serving_scene_catalog` |
| Purpose | Searchable imagery catalog + metadata-quality banding |
| Owner | Data Stewardship team |
| Consumers | Data stewards, analysts, REST API search |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h; search API p95 ≤ 500 ms |
| Source | `fact_scene_catalog` |
| Grain | 1 row / scene |
| KPIs | is_searchable, completeness_score, quality_band, cloud_cover |

---

## Detection Validation (UC-27)

| Attribute | Value |
| --- | --- |
| Product | `serving_aoi_validation` |
| Purpose | EMS ground-truth corroboration for damage-assessment prioritization + QA |
| Owner | EO Analytics / QA |
| Consumers | Analysts, QA, executive dashboard, RAG |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h |
| Source | `kpi_aoi_validation` |
| Grain | 1 row / EMS AOI |
| KPIs | corroborated, trust, evidence_days, area_km2 |

---

## Platform Daily KPI Rollup (cross-product)

| Attribute | Value |
| --- | --- |
| Product | `mv_kpi_platform_daily` (materialized aggregate) |
| Purpose | One-row-per-day executive summary across all EO products |
| Owner | Platform team |
| Consumers | Program leadership (executive dashboard) |
| Refresh | Daily, after data products rebuild |
| SLA | Dashboard read p95 ≤ 2 s |
| Source | serving wildfire/flood/vessel products |
| Grain | 1 row / day |
| KPIs | fire_detections, peak_frp, flood_aoi_days, suspicious_vessels |

---

## Change Detection (UC-14)

Change detection is served analytically from `kpi_eo_daily` (per grid-cell daily
detection deltas) rather than as a standalone wide table; it is a reusable
analytical foundation consumed by the wildfire and flood products above. A
dedicated `serving_change_daily` product is a roadmap item once multi-date scene
differencing lands in Gold.
