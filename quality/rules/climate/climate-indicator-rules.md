# Climate Indicators & Vegetation Health — Data Quality Rules

> Entities: Gold `fact_climate_indicator_daily` (LST/SST anomalies, NDWI,
> desertification proxy) and `fact_vegetation_health_daily` (NDVI/EVI health).
> Both derive from the `obs_index` Silver mart — zero new connectors. Suites:
> `gold_climate_indicator_daily_suite()`, `gold_vegetation_health_daily_suite()`.

---

## Gold `fact_climate_indicator_daily`

Grain: **1 row / AOI / day** (`aoi_key`, `date_key` unique).

| Category | Rule | Severity |
|----------|------|----------|
| Keys | `aoi_key`, `date_key` non-null; `(aoi_key, date_key)` unique | critical |
| Range | `lst_c ∈ [-90, 70]` °C (land-surface physical bound) | critical |
| Range | `sst_c ∈ [-2, 40]` °C (sea-surface physical bound) | critical |
| Range | `ndwi_mean ∈ [-1, 1]` (normalized index) | critical |
| Range | `lst_anomaly_c ∈ [-40, 40]` °C (bounded delta) | warn |
| Range | `sst_anomaly_c ∈ [-20, 20]` °C (bounded delta) | warn |
| Enum | `lst_anomaly_band ∈ {-1, 0, 1, 2, 3}` | critical |

**LST anomaly bands** (°C above same-DOY baseline): `-1` Cooler (< −1) · `0`
Normal (−1…+1) · `1` Warm (+1…+3) · `2` Hot (+3…+5) · `3` Extreme (> +5).

---

## Gold `fact_vegetation_health_daily`

Grain: **1 row / AOI / day** (`aoi_key`, `date_key` unique).

| Category | Rule | Severity |
|----------|------|----------|
| Keys | `aoi_key`, `date_key` non-null; `(aoi_key, date_key)` unique | critical |
| Range | `ndvi_mean`, `ndvi_max`, `evi_mean` `∈ [-1, 1]` | critical |
| Range | `valid_pixel_fraction ∈ [0, 1]` | critical |
| Range | `valid_pixel_fraction ≥ 0.3` cloud-free floor (below → NDVI KPI estimated) | warn |
| Enum | `ndvi_health_band ∈ {0, 1, 2, 3, 4}` | critical |

**NDVI health bands:** `0` Bare/water (< 0.1) · `1` Sparse (0.1–0.3) · `2`
Moderate (0.3–0.5) · `3` Healthy (0.5–0.7) · `4` Dense (0.7–1.0).

**Business impact of failure:** out-of-range indices or wrong health/anomaly
bands corrupt the desertification proxy, crop-stress flag, and the heatwave /
desertification climate KPIs that feed the Climate-Indicators dashboard and the
LST-anomaly-forecast model (14b).
