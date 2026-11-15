# 08 Climate / Air-Quality Freshness & Risk

> Classifies each IN-scope source by update cadence and documents adoption risks (rate limits, auth/quota, licensing, retrieval gaps, duplication). Extends Phase 5 [`08-freshness-strategy.md`](../08-freshness-strategy.md) and [`09-data-risks.md`](../09-data-risks.md).

## Executive Summary

The atmospheric column is **near-real-time to daily** — no true streaming source. OpenAQ is the freshest (hourly); satellite products (TROPOMI, AOD) are once-daily per overpass; derived indicators inherit their source cadence. The dominant risks are **Google Earth Engine compute quota**, **cloud/retrieval gaps**, and **auth management** (two credential systems: an OpenAQ API key + a Google Earth Engine service account). All risks are mitigable within the free tier via AOI clipping and QA filtering.

## Freshness Classification

| Source | Class | Native Cadence | Effective Freshness (AOI) | Notes |
| --- | --- | --- | --- | --- |
| OpenAQ | Near-real-time | Hourly (station-dependent) | ~1 hour lag | Freshest; but sparse spatially |
| TROPOMI (SH Stats) | Daily batch | 1 overpass/day | Same-day to +1 day | Cloud can drop a day |
| MODIS/VIIRS AOD | Daily batch | Daily (Terra/Aqua/VIIRS) | ~+3 days measured on GEE `MODIS/061/MCD19A2_GRANULES` (2026-11-15) | Feature freshness objective 96 h (domain decision 2026-11-15) |
| Derived indicators | Daily → periodic | Inherits source | Source cadence | Anomalies need baseline history |

> No real-time / streaming atmospheric source in scope. Ingestion cadence should be **scheduled batch** (daily) for satellite sources and **frequent polling** (hourly) for OpenAQ.

## Risk Register

| ID | Source | Risk | Severity | Mitigation |
| --- | --- | --- | --- | --- |
| R-C1 | TROPOMI/AOD (GEE) | Earth Engine compute-quota / rate-limit exhaustion | High | AOI clipping + coarse `reduceRegion` scale; one request per AOI-day; schedule sparingly; cache stats |
| R-C2 | All satellite | Cloud / retrieval gaps → missing AOI-days | Medium | QA filter + `noDataCount` completeness flag; interpolate/carry-forward flagged as estimated |
| R-C3 | OpenAQ | Sparse Gulf station coverage | Medium | Use as ground-truth/calibration, not area estimate; pair with satellite columns |
| R-C4 | OpenAQ | Duplicate / re-reported station values | Low | Dedup on `sensor_id` + `datetime_utc` |
| R-C5 | AOD | Desert bright-surface positive bias | Medium | Prefer MAIAC; corroborate with `AER_AI`; flag high-brightness |
| R-C6 | AOD | MODIS vs VIIRS cross-calibration drift | Low-Med | Keep sensor as dimension; harmonize before blending |
| R-C7 | All | Two auth systems (OpenAQ API key, GEE service account) | Low-Med | Centralize secrets in `infrastructure/env/.env`; service-account JSON key mounted on the runner |
| R-C8 | TROPOMI/OpenAQ | Semantic mismatch: column density (mol/m²) vs surface (µg/m³) | Medium | Never equate; document conversion/assumption explicitly |
| R-C9 | All | Licensing / attribution obligations | Low | All free/open; record attribution (Copernicus, NASA, OpenAQ) in governance |
| R-C10 | AOD (AppEEARS) | Async job latency / task quota | Low-Med | Batch-schedule; tolerate +1 day; retry with backoff |

## Licensing & Attribution Summary

| Source | License / Terms | Attribution |
| --- | --- | --- |
| OpenAQ | Open (CC BY 4.0 typical) | "Air quality data from OpenAQ" |
| Sentinel-5P / TROPOMI | Copernicus open data | ESA / Copernicus Sentinel data |
| MODIS / VIIRS AOD | NASA open (Earthdata) | NASA LP DAAC / LAADS |
| Derived indicators | Inherits source licenses | Carry upstream attribution |

## Duplication & Overlap

- **AOD vs AER_AI** both signal aerosol/dust — keep both (AER_AI robust over bright desert; AOD gives concentration). Not redundant; complementary.
- **TROPOMI CO/SO₂ vs FIRMS smoke** overlap on fire events — treated as corroborating signals, not duplicates.
- **OpenAQ PM vs AOD-derived PM** — OpenAQ is truth, AOD is estimate; join, don't dedup.

## Cross References

- AOI strategy (PU/quota driver): [`02-aoi-strategy.md`](./02-aoi-strategy.md)
- Quality: [`04-climate-data-quality.md`](./04-climate-data-quality.md)
- MVP & deferred: [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md)
- Phase 5 risks: [`../09-data-risks.md`](../09-data-risks.md)
