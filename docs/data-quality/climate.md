# Data Quality — Climate / Dust / Air-Quality Extension (Phase 10b)

> Narrative companion to the operational artifacts under [`quality/`](../../quality/README.md).
> Extends the Phase-10 framework to quality-gate and certify the climate expansion
> entities (Phase 9b). **No new quality engine** — the same declarative
> expectation framework
> ([`transformation/cleaning/validation_framework.py`](../../transformation/cleaning/validation_framework.py))
> and checkpoint runner are reused.

## 1. Scope

In-scope entities (Phase 6b/9b) — air quality, aerosol/dust, atmospheric columns,
and derived climate indicators:

| Layer | Entities |
|-------|----------|
| Silver | `obs_air_quality`, `obs_aerosol`, `obs_atmos_column` |
| Gold | `fact_air_quality_daily`, `fact_dust_event_daily`, `fact_climate_indicator_daily`, `fact_vegetation_health_daily` |

Out of scope (later phases): serving/API (11b/16b), RAG (15b), ML (14b).

## 2. Executable gates

| Artifact | Path |
|----------|------|
| Quality suites (rules) | [`transformation/quality/climate_suites.py`](../../transformation/quality/climate_suites.py) |
| Unit tests | [`transformation/tests/test_climate_rules.py`](../../transformation/tests/test_climate_rules.py) |
| Rule docs | [`quality/rules/climate/`](../../quality/rules/climate/README.md) |
| Profiling | [`quality/profiling/climate/`](../../quality/profiling/climate/README.md) |
| Freshness SLAs / alerts | [`quality/monitoring/`](../../quality/monitoring/monitoring-strategy.md) |
| Governance / certification | [`quality/governance/`](../../quality/governance/governance-model.md) |
| Incidents | [`quality/incidents/`](../../quality/incidents/production-incidents.md) |

> **Location note.** Consistent with the Phase-10 pattern (see the *Executable
> gates* table in [`quality/README.md`](../../quality/README.md)), the runnable
> suite + tests live inside the `transformation` package so they are collected by
> `cd transformation && make test`. The `quality/` tree holds the governing
> documentation, rules, profiling configs, SLAs, and incident records.

```powershell
cd transformation
make test        # includes test_climate_rules.py (pure-Python, offline)
```

## 3. Rule coverage matrix

| Category | `obs_air_quality` | `obs_aerosol` | `obs_atmos_column` | Gold marts |
|----------|:-----------------:|:-------------:|:------------------:|:----------:|
| Range (physical/plausibility) | ✅ value_std, PM caps | ✅ AOD [0,5] | ✅ column ≥ 0 | ✅ AQI, AOD, LST/SST, NDVI/NDWI |
| Unit (canonical) | ✅ µg/m³ · mg/m³ | — | ✅ mol/m² · ppb · unitless | ✅ °C, index |
| Enum (vocabulary) | ✅ pollutant_code | ✅ quality_flag | ✅ gas_code, unit_std | ✅ bands, aqi_band |
| Grain / uniqueness | ✅ air_quality_key | ✅ aoi/sensor/day | ✅ aoi/gas/day | ✅ aoi/day |
| Completeness | ✅ station coverage | ✅ valid_fraction | ✅ valid_pixel_fraction | ✅ station/coverage floors |
| Consistency | — | — | AER_AI sign exempt | ✅ AQI needs a station |

Full breakpoints and bands are single-sourced from
[`docs/data-modeling/climate/05-kpi-thresholds.md`](../data-modeling/climate/05-kpi-thresholds.md).

## 4. Freshness & availability

OpenAQ (≤ 3 h) and TROPOMI (≤ 24 h) are treated as near-real-time feeds; MODIS
AOD is daily (≤ 24 h); the derived AQ/dust marts refresh ≤ 6 h after sources,
and the slow-moving climate/vegetation marts ≤ 48 h. Lag is measured as
`dq_freshness_lag_seconds = now − max(event_ts)` and reuses the existing
`FreshnessBreach` alerting. See
[`quality/monitoring/quality-kpis.md §2.1`](../../quality/monitoring/quality-kpis.md).

## 5. Certification

A climate Gold mart becomes **`CERTIFIED`** only when criteria C1–C7 hold
(critical rules pass, grain unique, ranges/enums valid, freshness within SLA,
coverage met, no open critical incident, drift within band). A WARN-level
shortfall (e.g. low coverage) yields **`VALIDATED`** (usable with a caveat); a
CRITICAL failure holds the mart at **`DRAFT`**. See
[`quality/governance/governance-model.md §5`](../../quality/governance/governance-model.md).

## 6. Design decisions

| Decision | Chosen | Alternatives | Trade-off |
|----------|--------|--------------|-----------|
| Engine | Reuse `validation_framework` expectations | Great Expectations, Soda | Zero new deps, laptop-friendly; fewer built-in checks |
| Suite location | `transformation/quality/` | new `quality/` Python pkg | Matches Phase-10 pattern & test runner; docs stay in `quality/` |
| AER_AI negativity | Exempt from `≥ 0` gate | reject negatives | UV aerosol index is legitimately signed; avoids false rejects |
| Coverage / station floors | WARN, not CRITICAL | hard-fail | Gaps are expected in NRT feeds; keeps marts flowing, flags trust |
| Plausibility PM caps | WARN | hard bound | Extreme dust events are real; avoid dropping true outliers |

## 7. Glossary

| Term | Meaning |
|------|---------|
| AOD | Aerosol Optical Depth (unitless, 550 nm) — column aerosol loading |
| AQI | Air Quality Index (US EPA scale, 0–500) |
| LST / SST | Land- / Sea-Surface Temperature (°C) |
| NDVI / NDWI / EVI | Normalized vegetation / water / enhanced-vegetation indices ([-1, 1]) |
| TROPOMI | Sentinel-5P trace-gas spectrometer (column densities) |
| `valid_pixel_fraction` | Share of valid pixels in a raster aggregate (coverage) |
| Certification status | `DRAFT → VALIDATED → CERTIFIED → (DEPRECATED)` |
