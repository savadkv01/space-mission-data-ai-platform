-- Certified dataset: climate_indicator_daily  (Superset virtual dataset)  [CLIMATE-EXT 12b]
-- Owner: Climate Analytics Lead  |  Layer: serving  |  Grain: 1 row / AOI / day
-- Source of truth: serving.serving_climate_indicator_daily (Phase 11b data product).
-- Land/sea-surface temperature + anomalies, water availability (NDWI), tree-cover
-- loss, and the composite desertification proxy. Anomaly bands pre-computed upstream.
--
-- Superset database connection: `serving_duckdb`
-- Refresh: rebuilt by the `serving_refresh` DAG; cache TTL 1h.
select
    aoi_key,
    aoi_name,
    cast(date_key as date)          as event_date,
    lst_c,
    lst_anomaly_c,
    sst_c,
    sst_anomaly_c,
    ndwi_mean,
    tree_cover_loss_ha,
    desertification_proxy,
    lst_anomaly_band,
    lst_anomaly_label,
    warming_flag,
    desertification_flag,
    area_km2
from serving.serving_climate_indicator_daily
