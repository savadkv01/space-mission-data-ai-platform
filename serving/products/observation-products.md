# Earth Observation Data Products (MVP)

> Primary serving surface. Real open data (FIRMS, Sentinel, GFW, Copernicus EMS).
> These products back the six MVP use cases and are the platform's core value.

Every product below is built by a pure-Python builder in
[../marts/serving_marts.py](../marts/serving_marts.py) and a mirrored dbt model in
[../dbt/models/serving/](../dbt/models/serving/).

**Analysis regions:** every AOI-grained product carries `region`
(`UAE-GULF`, `INDIA`, `US-LEGACY`) from `dim_aoi`. Always filter or group by
region; never add values across regions. `mv_kpi_platform_daily` is keyed by
`(date_key, region)`, and vessel KPIs use `region = 'GLOBAL'` because GFW
identity records carry no position. See
[02-aoi-strategy.md](../../docs/source-data-analysis/climate/02-aoi-strategy.md#analysis-regions).

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
| Source | `kpi_wildfire_aoi_daily`, `ref_aoi`, `kpi_aoi_validation`, `fire_aoi_attribution` (freshness) |
| Grain | 1 row / AOI / day |
| KPIs | detections, mean_frp, max_frp, severity band, EMS corroboration, freshness_status, publication_status |

**Publication gate:** every row carries its **region's** FIRMS event-time
freshness from `serving_wildfire_freshness` (exactly one row per analysis
region; regions are judged independently, so a fresh INDIA feed never makes
UAE-GULF rows look current).
`publication_status = 'blocked'` unless the latest *acquired* detection is
≤ 6 h old (`freshness_status = 'current'`). A fresh landing of zero or old
records does not advance freshness, and a non-CSV FIRMS response fails the
source instead of reading as "no fires". While blocked/stale, absent AOI/day
rows are **not** a current negative. The Superset dataset re-evaluates age at
query time so a materialized table cannot look current after it ages.
Detections are VIIRS S-NPP through 2026-11-02 and VIIRS NOAA-20 from
2026-11-03 (the S-NPP NRT feed ended at FIRMS); one sensor per day, so counts
are not double counted, but day-to-day counts across the switch are not
strictly comparable.

**Release restriction:** exploratory only; not certified for public-safety
decisions. Use the [fire readiness contract](../../docs/source-data-analysis/16-live-readiness-and-fire-contract.md)
and its [live evidence snapshot](../../docs/source-data-analysis/live-readiness-snapshot.json).
The snapshot exposes field completeness, lineage, event freshness, and every
matched/unmatched detection. Overlapping AOIs are intentionally non-additive.
The curated reference seed is not independent EMS activation ground truth;
`ems_corroborated` must not be interpreted as externally verified fire evidence.
The source freshness objective remains six hours; the daily product SLA above
does not waive that upstream requirement.

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

## Maritime Activity — Area-based (UC-18)

| Attribute | Value |
| --- | --- |
| Product | `serving_maritime_activity_daily` |
| Purpose | Daily fishing, vessel presence, and radar-detected vessel activity inside each maritime AOI |
| Owner | Maritime Intelligence team |
| Consumers | Maritime analysts, executive dashboard, REST API |
| Refresh | Daily (30-day GFW look-back; recent days are revised) |
| SLA | Fishing effort ~96 h behind, SAR ~5 days behind (GFW publication latency) |
| Source | `fact_maritime_activity_daily` ← GFW 4Wings (`public-global-fishing-effort`, `public-global-presence`, `public-global-sar-presence`), `ref_aoi` |
| Grain | 1 row / maritime AOI / UTC day (`AOI-GULF`, `AOI-COAST`, `IN-GUJ-COAST`, `IN-MUM`) |
| KPIs | fishing_hours, fishing_vessels, presence_hours, presence_vessels, sar_detections, sar_unmatched_detections, sar_dark_fraction, `*_status` |

**Interpretation:**
- **Unpublished days:** a null measure with `*_status = 'not_published'` means GFW has not released that day; it is not zero.
- **Unmatched radar detections:** `sar_unmatched_detections` are Sentinel-1 detections with no matching AIS broadcast. They are review candidates (small craft, non-AIS vessels, platforms, AIS gaps), not confirmed illegal or "dark" activity.
- **Overlapping AOIs:** `AOI-COAST` lies inside `AOI-GULF`, so values are not additive across AOIs; the product is deliberately not rolled up into `mv_kpi_platform_daily`.
- **Licence:** GFW data is free for non-commercial use only.

---

## Maritime Vessel Activity (UC-18) — DEMONSTRATOR

> Identity-search sample (fixed GFW name query), not regional traffic. Use
> `serving_maritime_activity_daily` for real AOI activity (SG-05).

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
| KPIs | transmissions, suspicious_flag, review_priority, active_span_days, signal_basis, domain_review_status |

**Triage only:** `suspicious_flag` / `review_priority` come from an
identity-completeness heuristic (missing flag state or IMO). They are triage
signals for analyst review, not verified illegal-fishing alerts;
`domain_review_status` stays `pending` until the heuristic is approved.
`transmissions` counts retained identity records, not AIS pings.

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
