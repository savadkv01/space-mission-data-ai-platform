# Climate / Dust / Air-Quality — Data Quality Rules

> **Phase 10b** validation rules for the climate expansion entities (Phase 9b).
> Extends the Phase-10 [`quality/` framework](../../README.md); no new engine.
> Executable form: [`transformation/quality/climate_suites.py`](../../../transformation/quality/climate_suites.py),
> tested by [`transformation/tests/test_climate_rules.py`](../../../transformation/tests/test_climate_rules.py).

Every rule below is realized as an `Expectation` in a `*_suite()` and run through
`run_checkpoint` at the Silver/Gold gate — identical mechanics to the EO suites.

## In-scope entities

| Layer | Entity | Grain | Rules doc |
|-------|--------|-------|-----------|
| Silver | `obs_air_quality` | station / pollutant / reading | [air-quality-rules.md](air-quality-rules.md) |
| Silver | `obs_aerosol` | AOI / sensor / day | [aerosol-dust-rules.md](aerosol-dust-rules.md) |
| Silver | `obs_atmos_column` | AOI / gas / day | [atmospheric-column-rules.md](atmospheric-column-rules.md) |
| Gold | `fact_air_quality_daily` | AOI / day | [air-quality-rules.md](air-quality-rules.md) |
| Gold | `fact_dust_event_daily` | AOI / day | [aerosol-dust-rules.md](aerosol-dust-rules.md) |
| Gold | `fact_climate_indicator_daily` | AOI / day | [climate-indicator-rules.md](climate-indicator-rules.md) |
| Gold | `fact_vegetation_health_daily` | AOI / day | [climate-indicator-rules.md](climate-indicator-rules.md) |

## Rule categories (all entities)

| Category | Intent | Severity |
|----------|--------|----------|
| **Range** | Physical / plausibility bounds (pollutants, AOD, LST/SST, indices) | critical (hard bounds), warn (plausibility caps) |
| **Unit** | Standardized canonical units (µg/m³, mg/m³, mol/m², ppb, unitless, °C) | critical |
| **Enum** | Controlled vocabularies (pollutant/gas codes, quality flags, bands) | critical |
| **Grain / uniqueness** | One row per natural key / per AOI-date | critical |
| **Completeness** | Station coverage, valid-pixel fraction floors | warn |
| **Consistency** | Derived-column agreement (AQI needs a station, etc.) | critical |

## Controlled vocabularies

| Vocabulary | Values |
|------------|--------|
| `pollutant_code` | `PM25`, `PM10`, `NO2`, `SO2`, `CO`, `O3`, `BC` |
| `gas_code` | `NO2`, `SO2`, `CO`, `O3`, `CH4`, `AER_AI` |
| `unit_std` (column) | `mol/m2`, `ppb`, `unitless` |
| `quality_flag` | `valid`, `suspect`, `low_coverage` |
| `aqi_band` | `Good`, `Moderate`, `Unhealthy (sensitive)`, `Unhealthy`, `Very Unhealthy`, `Hazardous` (US EPA, UAE-GULF); `Good`, `Satisfactory`, `Moderate`, `Poor`, `Very Poor`, `Severe` (CPCB NAQI, INDIA) |
| `dust_severity_band` | `0`, `1`, `2`, `3`, `4` |
| `lst_anomaly_band` | `-1`, `0`, `1`, `2`, `3` |
| `ndvi_health_band` | `0`, `1`, `2`, `3`, `4` |

Bands and breakpoints are single-sourced from
[docs/data-modeling/climate/05-kpi-thresholds.md](../../../docs/data-modeling/climate/05-kpi-thresholds.md).

## Cross references

- Freshness SLAs & alerts: [../../monitoring/monitoring-strategy.md](../../monitoring/monitoring-strategy.md), [../../monitoring/quality-kpis.md](../../monitoring/quality-kpis.md)
- Profiling: [../../profiling/climate/](../../profiling/climate/README.md)
- Governance & certification: [../../governance/governance-model.md](../../governance/governance-model.md)
- Incidents: [../../incidents/production-incidents.md](../../incidents/production-incidents.md)
- Narrative: [docs/data-quality/climate.md](../../../docs/data-quality/climate.md)
