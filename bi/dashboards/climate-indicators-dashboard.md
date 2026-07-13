# Climate Indicators Dashboard

> Phase 12b · Task 2 — Dashboard Catalog · Audience: **Climate Analysts,
> Environmental & Agriculture teams** · Superset slug: `climate-indicators`
> Roles: `ops_climate` (+ `exec` read) · **Real-data (11b climate products)**

## Purpose

Monitoring surface for land/sea climate change signals: land-surface-temperature
(LST) and sea-surface-temperature (SST) anomalies, vegetation health and
desertification, water availability (NDWI), and deforestation. Reuses the
existing certified-dataset and deck.gl AOI-map conventions.

## Data Sources (certified 11b products)

| Dataset | Certified SQL | Source product | Grain |
| --- | --- | --- | --- |
| `climate_indicator_daily` | [climate_indicator_daily.sql](../datasets/sql/climate_indicator_daily.sql) | `serving.serving_climate_indicator_daily` | AOI/day |
| `vegetation_health_daily` | [vegetation_health_daily.sql](../datasets/sql/vegetation_health_daily.sql) | `serving.serving_vegetation_health_daily` | AOI/day |

## Tabs & Charts

### Tab 1 — Temperature & Water (dataset `climate_indicator_daily`)

| Chart | Type | Columns / Metric |
| --- | --- | --- |
| LST + anomaly map | deck.gl / geo | `aoi_key`, `lst_anomaly_c`, `lst_anomaly_label` |
| Mean LST Anomaly | big number | `mean_lst_anomaly` |
| LST & Anomaly Trend | line | `event_date`, `lst_c`, `lst_anomaly_c` |
| SST & Anomaly Trend (coastal) | line | `event_date`, `sst_c`, `sst_anomaly_c` |
| NDWI water availability | geo / line | `aoi_key`, `ndwi_mean` |

### Tab 2 — Vegetation & Land (dataset `vegetation_health_daily` + climate)

| Chart | Type | Columns / Metric |
| --- | --- | --- |
| NDVI / EVI vegetation-health map | deck.gl / geo | `aoi_key`, `ndvi_mean`, `ndvi_health_label` |
| Vegetation Health Distribution | pie | `ndvi_health_label` |
| NDVI Vegetation Trend | line | `event_date`, `mean_ndvi` |
| Tree-cover Loss by AOI (deforestation) | bar | `event_date`, `aoi_name`, `tree_cover_loss_ha` |
| Desertification proxy | geo / KPI | `desertification_proxy`, `desertification_flag` |

### Tab 3 — Details (drill-down)

| Chart | Type | Columns |
| --- | --- | --- |
| Climate Indicator Details | table | `aoi_name`, `event_date`, `lst_c`, `lst_anomaly_c`, `lst_anomaly_label`, `sst_c`, `sst_anomaly_c`, `ndwi_mean`, `tree_cover_loss_ha`, `desertification_flag` |
| Vegetation Health Details | table | `aoi_name`, `event_date`, `ndvi_mean`, `evi_mean`, `ndvi_trend_30d`, `ndvi_trend_dir`, `ndvi_health_label`, `crop_stress_flag` |

## Layout (wireframe — Temperature & Water tab)

```
+---------------------------------------------------------------+
| CLIMATE INDICATORS  [Temp & Water][Veg & Land][Details]  [ ▾ ]|
+------------------------+--------------------------------------+
| Mean LST Anomaly       |                                      |
|      +1.8 °C           |                                      |
+------------------------+--------------------------------------+
| LST & Anomaly Trend (line)     | SST & Anomaly Trend (line)   |
+-------------------------------+-------------------------------+
```

```
+---------------------------------------------------------------+
| … [Veg & Land]                                                |
+---------------------------------------------------------------+
| Vegetation Health Distribution (pie)                          |
+-------------------------------+-------------------------------+
| NDVI Vegetation Trend (line)   | Tree-cover Loss by AOI (bar) |
+-------------------------------+-------------------------------+
```

## Filters & Cross-filtering

- Global time range (default 90 days) + AOI selector (`aoi_name`).
- Vegetation-health slice cross-filters the NDVI trend and detail table.

## Alerts (see [../alerts/alert-strategy.md](../alerts/alert-strategy.md))

- **Extreme LST anomaly** — `climate_indicator_daily.lst_anomaly_c` in the
  extreme band, or `warming_flag = true` sustained.
- **Desertification onset** — new `desertification_flag = true`.

## Alignment

- Certified 11b products only; anomaly / vegetation bands pre-computed upstream.
- Same certified-dataset + deck.gl pattern as
  [earth-observation-dashboard.md](./earth-observation-dashboard.md).
- KPIs single-sourced in [../kpis/kpi-catalog.md](../kpis/kpi-catalog.md).
