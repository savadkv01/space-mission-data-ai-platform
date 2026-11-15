# INDIA Regional Tier — End-to-End Validation (2026-11-14)

Evidence for adding India as a separate analysis region, backfilling it, and
running the full platform end to end under Airflow orchestration.

> **Scope.** New `region` model, INDIA AOIs and sources, a 30-day backfill, and
> two orchestrated `platform_batch_pipeline` runs. The design decision is
> [ADR-11](../data-modeling/17-adr.md); AOI and source definitions are in
> [02-aoi-strategy.md](../source-data-analysis/climate/02-aoi-strategy.md#analysis-regions).
> Domain certification is still pending for every product.

---

## 1. What Changed

| Layer | Change |
|---|---|
| Reference data | Six INDIA AOIs added to the [AOI seed](../../transformation/seeds/aoi_reference.geojson); every feature carries `region` (`UAE-GULF`, `INDIA`, `US-LEGACY`). |
| Ingestion | [`regional_ingest.py`](../../ingestion/scripts/regional_ingest.py) per-region source plan (daily + backfill). FIRMS per AOI box with a 10,000-detection cap, OpenAQ PM-only with station/page caps, TROPOMI, MODIS AOD, NDVI/NDWI. Truncation is returned and logged as `coverage = capped`. The [hourly FIRMS DAG](../../ingestion/batch/dags/nasa_firms_ingest_dag.py) also requests the INDIA boxes. |
| Gold | `fire_aoi_attribution.region` (regional envelope, matched or not); `aqi_standard` per region (`US_EPA_PRE2024` / `IN_CPCB_NAQI_2014`); dust corridors restricted to the same region; `ref_aoi.region`. |
| Serving | `region` on `dim_aoi` and every AOI-grained product. `serving_wildfire_freshness` has one row per region, and wildfire rows join their own region's gate. Both rollups are keyed `(date_key, region)`; vessels use `GLOBAL`. |
| BI | Superset datasets expose `region` (and `aqi_standard`); rollup dataset descriptions require filtering or grouping by region. |

## 2. Issues Found During the Run and How They Were Resolved

| # | Finding | Evidence | Resolution |
|---|---|---|---|
| R1 | **VIIRS S-NPP NRT feed ended at FIRMS on 2026-11-02.** This was the real cause of the persistent UAE fire staleness. | FIRMS `data_availability`: `VIIRS_SNPP_NRT` max date 2026-11-02; `VIIRS_NOAA20_NRT` current to 2026-11-14. Backfill windows after Nov 3 returned 0 rows for every AOI. | `FIRMS_SOURCE` setting (default `VIIRS_NOAA20_NRT`) used by the daily driver, the regional plan and the hourly DAG. The Nov 3–13 gap was backfilled with NOAA-20 only, so there is one sensor per day; the satellite is part of the Silver fire key, so mixing sensors on a day would double count. |
| R2 | The broad UAE FIRMS box (30–60°E, 10–40°N, including East Africa) exceeds 10,000 detections per 5-day window. | Gap backfill `uae_gulf` windows: 10,000 (capped), 10,000 (capped). | Recorded as capped. The UAE-GULF region envelope (42–57°E, 18–36°N) was also requested and stayed under the cap (4,111 / 4,935 / 1,218), so region coverage is complete. |
| R3 | **GEE NDVI/NDWI were sign-inverted** (open finding SG-01). | Before fix: Punjab NDVI mean −0.39; Assam NDWI mean +0.60 → 26/26 false Assam flood flags. | Band order fixed; records stamped `formula_version = 2`; Silver quarantines unversioned GEE index records (`superseded:gee_index_sign_v1`); Oct 15–Nov 14 re-ingested. After fix: Punjab NDVI +0.39, Assam NDWI −0.60, Assam flood flags 0/26. |

## 3. Backfill

`python -m ingestion.scripts.regional_ingest --region INDIA --days 30`
(2026-10-15 → 2026-11-13), plus the FIRMS NOAA-20 gap fill (2026-11-03 → 11-13).

| Source | Records | Notes |
|---|---:|---|
| FIRMS (S-NPP, Oct 15–Nov 2) | 5,299 | PB-HR 2,951 · THAR 1,137 · GUJ-COAST 907 · ASSAM 249 · DEL-NCR 55 |
| FIRMS (NOAA-20, Nov 3–13) | 4,997 | PB-HR 3,398 · THAR 749 · GUJ-COAST 580 · ASSAM 242 · DEL-NCR 28 |
| OpenAQ (PM only) | 31,749 | DEL-NCR 14,400 · MUM 17,349; both **capped** (25 stations, 3 pages per sensor) |
| TROPOMI (6 products) | 323 | DEL-NCR, PB-HR |
| MODIS AOD | 110 | THAR, GUJ-COAST, DEL-NCR, PB-HR |
| Sentinel-2 NDVI / NDWI | 20 / 26 (+ v2 re-ingest) | PB-HR / ASSAM |
| **Total** | 37,527 (main backfill) | 50 units, 0 errors |

## 4. Orchestrated End-to-End Runs

| Run | Result | Duration | Purpose |
|---|---|---|---|
| `manual__2026-11-14_india_regional_e2e` | ✅ success | 35.7 min | First regional run (exposed R3) |
| `manual__2026-11-14_india_regional_e2e_v2` | ✅ success | 28.6 min | Final run after the index fix (evidence below) |

**Final run (`…_v2`) stage metadata (`metadata.*_run_detail`):**

| Stage | Units | Rows | Notes |
|---|---:|---:|---|
| Ingestion | 72 success · 1 failed | 37,518 | `OPENAQ:AOI-UAE-NAT` HTTP 429 (pre-existing V06). `FIRMS:IN-DEL-NCR` 0 rows → `data_availability = unavailable`. OpenAQ INDIA → `capped`. |
| Transformation | 26 success | 122,600 | `silver_fire` 38,363 · `silver_air_quality` 71,369 · `silver_index` 72 · `gold_kpi_launch_monthly` 0 (unavailable) |
| Serving dbt | 15 models · **95/95 tests** | 1,644 | Includes region, freshness-per-region, NAQI and rollup-grain tests |
| Gold dbt demonstrator | 5 models · 18/18 tests | — | — |
| BI refresh | 15 datasets | — | All 15 dataset SQLs verified against the rebuilt warehouse; columns match |

## 5. Results by Region (final run)

| Product | UAE-GULF | INDIA | US-LEGACY |
|---|---|---|---|
| Wildfire rows (AOIs, dates) | 111 (10, Oct 31 → Nov 14) | 147 (5, Oct 15 → Nov 14) | 3 (legacy) |
| Wildfire freshness | `stale` / `blocked` (10.1 h) | `stale` / `blocked` (11.8 h) | `stale` (346.6 h) |
| Air quality rows · standard | 185 · `US_EPA_PRE2024` | 91 · `IN_CPCB_NAQI_2014` | — |
| Dust rows · max corridor AOD | 176 · 0.333 | 110 · 4.621 | — |
| Flood rows · flags | 65 · 65 (see §6 L1) | 26 · 0 | — |
| Vegetation rows | 65 | 20 | — |
| `mv_kpi_platform_daily` duplicate `(date, region)` keys | 0 | 0 | 0 |

**INDIA highlights:**
- **Fire:** Punjab–Haryana 6,451 detections (crop-residue season), Thar 1,894, Gujarat coast 1,570, Assam 521, Delhi NCR 83.
- **Air quality:**
  - Delhi NCR mean PM2.5 134.9 µg/m³ (max 257.3); Mumbai 59.2.
  - NAQI bands: 12 Satisfactory, 23 Moderate, 6 Poor, 13 Very Poor, 2 Severe.
  - 35 AOI-days have no surface PM (TROPOMI-only rows) and are `not_evaluated`, not "Good".
- **Isolation:** the UAE dust corridor maximum fell to 0.333 because Indian AOD can no longer leak into UAE corridors.

## 6. Known Limitations and Follow-ups

| ID | Item | Owner |
|---|---|---|
| L1 | **UAE flood flags reflect permanent sea water.** The Dubai index box is mostly Arabian Gulf. With the corrected sign, NDWI (+0.15) trips the flood rule on 13/13 days, and centroid attribution copies it to 5 overlapping AOIs (65 rows). A permanent-water baseline (e.g. JRC Global Surface Water) is required before flood flags are meaningful. | EO analytics |
| L2 | The 6 h event-time freshness objective is unattainable with one polar-orbiting VIIRS sensor (about 2 overpasses a day). Both regions are `blocked` at 10–12 h. The objective needs a domain decision (e.g. 12–14 h for single-sensor VIIRS, or multi-sensor). | Domain / EO ops |
| L3 | Fire counts are S-NPP up to 2026-11-02 and NOAA-20 afterwards. Day-to-day counts across the switch are not strictly comparable. | EO analytics |
| L4 | OpenAQ caps in Delhi and Mumbai: per-sensor pages fill even in the 14-day window, so coverage is a capped sample (recorded per sensor). | Data engineering |
| L5 | Dust flags in Punjab/Delhi during crop-burning season can reflect smoke aerosol, not mineral dust (AOD up to 4.6). | Climate analytics |
| L6 | Daily grain is the UTC day; IST evening burning can split across dates. The NAQI "Severe" ceiling (PM2.5 500 / PM10 600) is a platform assumption. | Domain |
| L7 | The Gold dbt demonstrator still computes EPA AQI only; the canonical Spark Gold path is region-aware. | Data engineering |
| L8 | Power BI model not regenerated from the updated Superset YAMLs; Superset charts that sum rollups must add a region filter or group-by. | BI |
| L9 | Evidence in [2026-11-14-priority-remediation.md](./2026-11-14-priority-remediation.md) for vegetation, flood and climate was computed on sign-inverted indices (R3) and is superseded by this report. | — |

## 7. Addendum (2026-11-15): Aerosol QA Mask and POWER UTC Days

| Item | Change | Live result |
|---|---|---|
| MODIS MAIAC AOD (SG-03) | Per-pixel `AOD_QA` mask: cloud mask = clear and AOD QA = best. Records are stamped `qa_mask`; Silver prefers masked records and flags legacy unmasked MAIAC rows `suspect`. | Oct 15 → Nov 14 re-ingested for 9 AOIs (259 records). In this dry period the mask removes 2–11 % of pixels and shifts AOI means by ≤ ~0.03, so the high Punjab/Delhi AOD (0.8–1.5) is real aerosol (crop-burning smoke), not cloud artefacts. 46 legacy rows remain as `suspect` (2024 history, plus AOI-days where no clear pixel survived the mask). |
| NASA POWER (SG-04) | `time-standard=UTC`; `silver_wind.time_standard`; UTC preferred on key collision. | 15 AOIs re-ingested (2,325 records); `silver_wind` is now 900/900 UTC rows. |

Serving rebuilt: 15/15 models, 95/95 tests. INDIA dust flags (from Oct 15) went from 5 to 7 positive; UAE-GULF stays 156 negative.

**Remaining:** the mask does not separate smoke from dust (L5). MAIAC's `AOD_QA` bits 13–14 (aerosol model: background/smoke/dust) could, as a follow-up. Gold dust still uses `suspect` rows.

## 8. Addendum (2026-11-15): Area-based Maritime Activity (GFW 4Wings)

New `GFW_4WINGS` source (ADR-08-08) replaces the identity-search sample for regional analysis. Orchestrated run `manual__2026-11-15_gfw_maritime_e2e`: ✅ success (31.6 min). 12 GFW units, 9,456 records, all `coverage = complete`. `silver_maritime` 9,456 rows → `fact_maritime_activity_daily` / `serving_maritime_activity_daily` 108 rows.

| Region | AOI | Days | Mean fishing h/day (vessels) | Mean AIS vessels/day | Mean SAR detections/day | SAR share without AIS match |
|---|---|---:|---|---:|---:|---:|
| UAE-GULF | AOI-GULF | 27 | 5,586 (408) | 5,490 | 849 | 0.52 |
| UAE-GULF | AOI-COAST | 27 | 113 (11) | 2,288 | 257 | 0.41 |
| INDIA | IN-GUJ-COAST | 27 | 7.3 (1.3) | 763 | 51 | 0.47 |
| INDIA | IN-MUM | 27 | 4.1 (0.4) | 368 | 3 | 0.21 |

All three datasets are published through 2026-11-11. The unmatched SAR share is high in the Gulf partly because Sentinel-1 also detects fixed offshore oil and gas infrastructure, small craft, and vessels in AIS reception gaps. The share is a review signal, not a count of illegal "dark" vessels. A fixed-infrastructure exclusion layer is a follow-up.

**dbt partial-parse finding:** the orchestrated serving step ran **80 of 112** contract tests because dbt's partial-parse cache missed YAML edits made through the Windows bind mount (models such as `serving_wildfire_daily` silently had no tests). The batch DAG now runs `dbt run/test --no-partial-parse` for both dbt projects. A full parse passes 108/108 serving data tests and 18/18 Gold demonstrator tests. The earlier counts in §4 and §7 (81 → 83 → 95) rose exactly with each added test, consistent with full parses; the stale cache affected this run.

## 9. Glossary

| Term | Definition |
|---|---|
| Analysis region | Group of AOIs analysed together (`UAE-GULF`, `INDIA`, `US-LEGACY`); never combined in rollups, corridors, AQI or freshness. |
| Region envelope | Union bounding box of a region's AOIs; assigns every fire detection (matched or not) to a region. |
| Capped coverage | A request truncated by a fixed budget cap; recorded as `coverage = capped` with notes, never silent. |
| NAQI | India's CPCB National Air Quality Index (2014): Good, Satisfactory, Moderate, Poor, Very Poor, Severe. |
| Formula version | Version stamp on GEE index records; v2 = corrected band order. Earlier records are quarantined as superseded. |
