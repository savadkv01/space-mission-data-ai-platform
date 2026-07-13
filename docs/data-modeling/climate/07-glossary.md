# 07 - Glossary (Climate / Dust / Air-Quality Data Modeling)

> **Phase 6b - Data Modeling (Climate Extension)** · Document 07 of 07
>
> Modeling terms specific to this extension. Extends Phase 6 [`../18-glossary.md`](../18-glossary.md).

| Term | Definition |
| --- | --- |
| `obs_air_quality_raw` | Bronze payload for OpenAQ station readings (source `OPENAQ`). |
| `obs_atmos_raw` | Bronze payload for TROPOMI per-AOI statistical buckets (source `TROPOMI`, via Sentinel Hub Statistical API). |
| `obs_aerosol_raw` | Bronze payload for MODIS/VIIRS AOD (source `MODIS_AOD`). |
| `obs_air_quality` | Silver — harmonized, unit-standardized surface pollutant readings, AOI-tagged. |
| `obs_atmos_column` | Silver — trace-gas column densities per AOI per day (mol/m²). |
| `obs_aerosol` | Silver — AOD + UV aerosol index per AOI per day. |
| `fact_air_quality_daily` | Gold — pollutant means/maxes, AQI bands, exceedance flags at AOI-date grain. |
| `fact_dust_event_daily` | Gold — AOD, dust-index, wind-transport context, dust flag at AOI-date grain. |
| `fact_climate_indicator_daily` | Gold — LST/SST/NDWI + anomalies, deforestation, desertification proxy. |
| `fact_vegetation_health_daily` | Gold — NDVI/EVI trend + crop-stress proxy. |
| `dim_pollutant` | Conformed dimension: pollutants/AOD with units, AQI breakpoints, thresholds. |
| `dim_climate_indicator` | Conformed dimension: indicator code, unit, normal range, anomaly bands. |
| `dim_aoi` | Shared AOI dimension (EMS + Phase 5b climate AOIs); universal join key `aoi_key`. |
| AOD | Aerosol Optical Depth (unitless, 550 nm); dust/haze proxy. |
| AER_AI | TROPOMI UV Aerosol Index; absorbing-aerosol signal robust over bright desert. |
| AQI | Air Quality Index; banded scale derived from pollutant breakpoints. |
| Column density | Vertically integrated gas amount over unit area (mol/m²); not surface concentration. |
| Surface concentration | Near-ground breathable concentration (µg/m³); OpenAQ measure. |
| LST / SST anomaly | Temperature departure from a same-day-of-year climatological baseline (°C). |
| Desertification proxy | Composite flag from multi-year NDVI decline + rising LST in desert-margin AOIs. |
| `valid_pixel_fraction` | sample_count / (sample_count + no_data_count); coverage/completeness measure. |
| Exceedance flag | 1 when a pollutant daily mean exceeds the WHO/local guideline. |
| BronzeEnvelope | Standard JSONL provenance wrapper (`ingestion/common/envelope.py`) all raw records use. |

## Cross References

- Phase 6 glossary: [`../18-glossary.md`](../18-glossary.md)
- Bronze contracts: [`01-bronze-contracts.md`](./01-bronze-contracts.md)
