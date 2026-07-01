# 08 - Feature Store Design

> **Phase 6 - Data Modeling** · Document 08 of 18

## Scope

Conceptual feature store sourcing from Silver/Gold; Feast-style offline+online split.

## Feature Groups

| Group | Features |
| --- | --- |
| Satellite health | temp_mean, voltage_var, anomaly_7d, uptime |
| Orbit stability | alt_drift, vel_var, decay_rate |
| Weather impact | kp_lag, flux_max, exposure_hr |
| EO fire risk | ndvi, dryness, frp_trend, weather_idx |
| EO spectral index | ndvi_mean, ndwi_mean, nbr_mean, valid_pixel_fraction (from Silver `obs_index`) |

## Online vs Offline

| Store | Source | Latency | Use |
| --- | --- | --- | --- |
| Offline | Parquet/DuckDB Gold (Iceberg at scale) | minutes | training, backfill |
| Online | PostgreSQL/Redis | ms | inference serving |

## Reuse Strategy

- Entity keys = `sat_key`, `geo_key`; point-in-time joins prevent leakage; features versioned + documented for reuse across models.

## Cross References

- [04-gold-layer.md](04-gold-layer.md) · [09-vector-model.md](09-vector-model.md)
