# Climate Profiling Configs

> **Phase 10b** profiling for the climate expansion entities, using the existing
> profiling approach in [../profiling-strategy.md](../profiling-strategy.md) and
> [../statistics-framework.md](../statistics-framework.md). Profiles run at each
> Silver/Gold promotion so thresholds, drift baselines and anomaly-rate alerts
> are grounded in observed distributions rather than guessed.

Machine-readable config: [profiles.yml](profiles.yml).

## Profiled entities & columns

| Entity | Key numeric columns | Categorical columns | Focus |
|--------|---------------------|---------------------|-------|
| `obs_air_quality` | `value_std`, `value_raw`, `latitude`, `longitude` | `pollutant_code`, `quality_flag`, `unit_raw` | pollutant distributions, station coverage, unit drift |
| `obs_aerosol` | `aod_550nm`, `valid_fraction`, `angstrom_exponent`, `uv_aerosol_index` | `sensor`, `quality_flag`, `bright_surface_flag` | AOD distribution, retrieval completeness |
| `obs_atmos_column` | `mean`, `valid_pixel_fraction`, `min`, `max`, `stddev` | `gas_code`, `unit_std`, `quality_flag` | per-gas column density, coverage |
| `fact_air_quality_daily` | `pm25_mean`, `pm10_mean`, `aqi_pm25`, `station_count`, `column_valid_fraction` | `aqi_band`, `exceedance_flag` | AQI stability, exceedance rate |
| `fact_dust_event_daily` | `aod_mean`, `aod_max`, `uv_aerosol_index_mean`, `corridor_aod_max` | `dust_severity_band`, `dust_flag`, `transport_flag` | dust-event rate, severity mix |
| `fact_climate_indicator_daily` | `lst_c`, `lst_anomaly_c`, `sst_c`, `sst_anomaly_c`, `ndwi_mean`, `desertification_proxy` | `lst_anomaly_band`, `warming_flag`, `desertification_flag` | anomaly distributions, warming rate |
| `fact_vegetation_health_daily` | `ndvi_mean`, `evi_mean`, `ndvi_trend_30d`, `valid_pixel_fraction` | `ndvi_health_band`, `crop_stress_flag` | vegetation health, crop-stress rate |

## Dimensions computed (per profiling-strategy §3)

- **Column statistics** — count, min, max, mean, median, stddev.
- **Null percentage** — per column, tracked over time (e.g. `station_count == 0`
  days for `fact_air_quality_daily`).
- **Cardinality** — distinct values for enums; detects `pollutant_code` /
  `gas_code` vocabulary drift.
- **Distribution** — histogram / quantiles (p05, p25, p50, p75, p95) for
  `aod_550nm`, `value_std`, `lst_anomaly_c`, `ndvi_mean`.
- **Anomaly rate** — share of rows flagged (`quality_flag != valid`,
  `dust_flag`, `warming_flag`, `crop_stress_flag`) vs the rolling baseline.
- **Drift** — PSI (`dq_psi`) vs the rolling baseline; categorical share shift for
  `pollutant_code`, `gas_code`, `sensor`, `*_band`.

## Emitted metrics

Profiles emit the standard `dq_*` metrics (see
[../../monitoring/monitoring-strategy.md](../../monitoring/monitoring-strategy.md)):
`dq_null_pct{entity,column}`, `dq_psi{entity,column}`,
`dq_completeness_score{entity}`, and an anomaly-rate gauge per flag column.
