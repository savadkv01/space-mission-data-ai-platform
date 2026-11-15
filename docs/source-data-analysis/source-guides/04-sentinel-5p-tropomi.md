# 04 — Sentinel-5P TROPOMI Trace Gases (via Google Earth Engine)

## 1. Identity Card

| Attribute | Value |
| --- | --- |
| Bronze `_source` | `TROPOMI` |
| Data owner | **ESA / European Commission Copernicus**; instrument co-developed by the Netherlands (KNMI, SRON, Airbus NL) |
| Access backend | **Google Earth Engine** L3 assets `COPERNICUS/S5P/{NRTI,OFFL}/L3_*` |
| Satellite / instrument | **Sentinel-5 Precursor** (launched Oct 2017) · **TROPOMI** (TROPOspheric Monitoring Instrument) |
| Connector | [`GeeS5pConnector`](../../../ingestion/api/gee_s5p.py) (base [`gee.py`](../../../ingestion/api/gee.py)) |
| Schedule | `@daily` ([`tropomi_ingest_dag.py`](../../../ingestion/batch/dags/tropomi_ingest_dag.py)); full run uses a 14-day window |
| AOIs × products | UAE: `AOI-UAE-NAT`, `AOI-AUH`, `AOI-DXB` × 6 products · INDIA: `IN-DEL-NCR`, `IN-PB-HR` |
| Auth / licence | GEE service account · Copernicus free and open |
| Use cases | UC-C3 air-quality monitoring · UC-C2 dust (aerosol index) · UC-C1 climate (CH₄) |

> **Why GEE and not Sentinel Hub?** The `sentinel-5p-l2` collection is **not entitled** on the
> free/CDSE Sentinel Hub plan. GEE is free for non-commercial use, and `reduceRegion` maps 1:1 to
> the AOI-statistics design. Full decision: [climate/01](../climate/01-climate-dataset-inventory.md).

## 2. What It Is (Plain Language)

Once a day, around **13:30 local time**, the satellite measures how much of each gas sits in the
air column above every ~3.5 × 5.5 km patch of Earth. We receive the **average over each AOI per UTC
day**. A bigger number means more of that gas between the ground and the top of the troposphere or
atmosphere. It is **not** what a person breathes at street level (primer §9).

## 3. How the Data Is Collected

| Aspect | Detail |
| --- | --- |
| Orbit | Sun-synchronous, 824 km, ascending node ≈ 13:30 local |
| Swath / coverage | 2,600 km wide, giving **daily global coverage** |
| Instrument | Push-broom imaging **spectrometer** (UV, visible, NIR, SWIR) |
| Retrieval principle | Each gas absorbs sunlight at characteristic wavelengths. Comparing measured spectra with the known solar spectrum (e.g., **DOAS** for NO₂/SO₂) gives a **slant column**, converted to a **vertical column** with an air-mass factor (accounting for geometry, clouds and surface) |
| Pixel | ~3.5 × 5.5 km at nadir (since Aug 2019) |
| L2 → L3 (by GEE) | GEE re-grids L2 swaths to a 0.01° (~1.1 km) grid with `harpconvert` and **removes low-QA pixels** (product-specific `qa_value` thresholds; see the GEE catalog page) |
| Latency | **NRTI** ≈ 3 h after sensing; **OFFL** ≈ 1–5 days; GEE ingestion adds hours to days |

## 4. Why We Access It

| Product | Why it matters for the UAE/India |
| --- | --- |
| NO₂ | Traffic, power plants, shipping and ports; urban air-quality proxy |
| SO₂ | Refineries, oil and gas, smelters, volcanic plumes |
| CO | Combustion and biomass burning (India stubble burning) |
| O₃ | Total ozone (mostly stratospheric); context, not surface ozone |
| CH₄ | Greenhouse gas; oil and gas leaks, landfills, rice paddies |
| AER_AI | UV-absorbing aerosols, i.e., **dust and smoke**; pairs with MODIS AOD for dust events |

## 5. How We Access It

| Item | Value |
| --- | --- |
| Method | GEE SDK `ImageCollection(asset).filterDate(day).filterBounds(bbox).select(band).mean().reduceRegion(...)` at **1,113.2 m** |
| NO₂ fallback | Tries `NRTI/L3_NO2` first; for any UTC day without NRTI data, retries `OFFL/L3_NO2` |
| Products → assets/bands | See §8 |
| Requests | 6 products × 3 UAE AOIs × N days (+ INDIA) per run; 2 calls per bucket |

## 6. Format at Source

GEE `reduceRegion` dict → reshaped into the common statistics bucket (primer §6). No raw L2
NetCDF is ever downloaded.

## 7. What We Store in Bronze (and Why)

Real record (AER_AI over Punjab/Haryana):

```json
{"_source": "TROPOMI", "_event_ts": "2026-10-15T00:00:00Z",
 "payload": {"interval": {"from": "2026-10-15T00:00:00Z", "to": "2026-10-16T00:00:00Z"},
   "outputs": {"index": {"bands": {"B0": {"stats": {"mean": 0.00247, "min": -2.616, "max": 1.980,
       "stDev": 0.699, "sampleCount": 126238, "noDataCount": 0}}}}},
   "product": "AER_AI", "aoi_id": "IN-PB-HR", "bbox": [73.8, 29.0, 77.4, 32.5],
   "collection": "COPERNICUS/S5P/OFFL/L3_AER_AI", "unit": "unitless"}}
```

Observed NO₂ means on 2026-11-12/13 (from the verified DuckDB recipe): `AOI-DXB` ≈ **6.1 × 10⁻⁵**
mol/m² vs `AOI-UAE-NAT` ≈ **2.4 × 10⁻⁵** mol/m². The city is about 2.5× the national average, as
expected.

Enrichment added by the connector: `product`, `aoi_id`, `bbox`, `collection` (actual asset,
records NRTI vs OFFL), `unit`.

## 8. Field Dictionary

| `product` | GEE asset | Band | `unit` | Typical range (UAE) | Reading |
| --- | --- | --- | --- | --- | --- |
| `NO2` | `NRTI/L3_NO2` (fallback `OFFL`) | `tropospheric_NO2_column_number_density` | mol/m² | 1e-5 rural … 2e-4 urban/industrial | Higher = more combustion pollution |
| `SO2` | `OFFL/L3_SO2` | `SO2_column_number_density` | mol/m² | ~0 ± 5e-4 (noisy) | Only strong sources stand out; **negative values are normal noise** |
| `CO` | `OFFL/L3_CO` | `CO_column_number_density` | mol/m² | ~0.02–0.05 | Fire/combustion plumes |
| `O3` | `OFFL/L3_O3` | `O3_column_number_density` | mol/m² | ~0.11–0.14 | Total column; 1 DU = 4.4615 × 10⁻⁴ mol/m² (≈ 250–320 DU) |
| `CH4` | `OFFL/L3_CH4` | `CH4_column_volume_mixing_ratio_dry_air` | ppb | ~1,850–1,990 | Small anomalies (+10–30 ppb) matter; sparse over bright or cloudy scenes |
| `AER_AI` | `OFFL/L3_AER_AI` | `absorbing_aerosol_index` | unitless | −2 … +3 | > ~1 = absorbing aerosol (dust/smoke); < 0 = non-absorbing aerosol or cloud |

Statistics fields (`mean`, `min`, `max`, `stDev`, `sampleCount`, `noDataCount`, `interval`) are
defined in primer §6.

**Unit conversion:** 1 mol/m² = 6.022 × 10¹⁹ molecules/cm². Scientific papers often quote NO₂ in
10¹⁵ molec/cm², and 6 × 10⁻⁵ mol/m² ≈ 3.6 × 10¹⁵ molec/cm².

## 9. How to Read & Interpret

- Compare **relative** levels (city vs region, this week vs last month); absolute satellite columns
  cannot be compared with WHO µg/m³ limits.
- Weekly or monthly averages are far more robust than single days (noise and cloud gaps).
- NO₂ has a strong **weekday cycle** (traffic). In the UAE, Friday/Saturday are lower.
- Pair `AER_AI` (absorbing, height-sensitive) with MODIS AOD (total particle load) for dust events.

## 10. Quality, Limitations & Gotchas

| Gotcha | Mitigation |
| --- | --- |
| Clouds remove pixels (GEE QA filter) | Use `sampleCount`/valid fraction; prefer multi-day means |
| NRTI vs OFFL differ slightly | `collection` field shows which was used; avoid mixing in trend studies |
| SO₂ and CH₄ are noisy and sparse | Long averaging windows; treat single-day spikes cautiously |
| Bright desert surfaces affect CH₄ and aerosol retrievals | Silver flags suspicious records |
| 13:30 snapshot | Misses morning and evening rush-hour peaks |
| Very small numbers (1e-5) | Use scientific notation; never round to 4 decimals |

## 11. Downstream Lineage

`Bronze TROPOMI` → `silver_atmos_column` (`obs_atmos_column`) → Gold `fact_air_quality_daily`
(satellite columns), `fact_dust_event_daily` (AER_AI) → `serving_air_quality_daily`,
`serving_dust_event_daily` → Air-Quality & Dust dashboard.

## 12. References

- GEE catalog (NO₂ OFFL, includes QA-filter notes): https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2
- Sentinel-5P mission: https://sentiwiki.copernicus.eu/web/s5p-mission
- TROPOMI products and processing: https://sentiwiki.copernicus.eu/web/s5p-products
