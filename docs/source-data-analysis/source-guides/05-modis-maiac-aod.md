# 05 — MODIS MAIAC Aerosol Optical Depth (via Google Earth Engine)

## 1. Identity Card

| Attribute | Value |
| --- | --- |
| Bronze `_source` | `MODIS_AOD` |
| Data owner | **NASA** (MODIS Science Team; distributed by NASA LP DAAC) |
| Access backend | **Google Earth Engine** asset `MODIS/061/MCD19A2_GRANULES`, band `Optical_Depth_055` |
| Satellites / instrument | **Terra** (≈10:30 local) and **Aqua** (≈13:30 local) · **MODIS** (Moderate Resolution Imaging Spectroradiometer) |
| Algorithm | **MAIAC** (Multi-Angle Implementation of Atmospheric Correction), Collection 6.1, 1 km |
| Connector | [`GeeAodConnector`](../../../ingestion/api/gee_aod.py) |
| Schedule | `@daily`, 7-day window ([`modis_aod_ingest_dag.py`](../../../ingestion/batch/dags/modis_aod_ingest_dag.py)); full run 14 days |
| AOIs | UAE + dust corridors: `AOI-DXB`, `AOI-DESERT`, `AOI-ARABIA`, `AOI-ARABIA-E`, `AOI-IRAQ`, `AOI-IRAN` (redrawn partition, ADR-12) · INDIA: `IN-THAR`, `IN-GUJ-COAST`, `IN-DEL-NCR`, `IN-PB-HR` |
| Auth / licence | GEE service account · NASA open data |
| Use cases | UC-C2 dust-storm monitoring · UC-C3 PM estimation (AOD→PM regression, Phase 14b) |

## 2. What It Is (Plain Language)

**AOD measures how hazy the whole atmosphere is.** It indicates how much sunlight is blocked by
particles (dust, smoke, sea salt, pollution) between the ground and space. An AOD of 0.1 is a clear
day; 1.0 is a thick dust haze; 3+ is a severe dust storm.

## 3. How the Data Is Collected

| Aspect | Detail |
| --- | --- |
| Instrument | MODIS: 36 spectral bands, 2,330 km swath, near-daily global coverage from each satellite |
| Algorithm | MAIAC uses a **time series** of observations (up to 16 days) to separate the stable surface reflectance from the changing atmosphere. This makes it better than older algorithms over **bright deserts** |
| Wavelength | AOD reported at 470 nm and **550 nm** (we use 550 nm, the community standard) |
| Granules | Each GEE image is **one overpass** (Terra or Aqua). Our daily value averages all overpasses that touched the AOI that UTC day |
| Storage encoding | Integer × 1000 (`156` = 0.156); the connector applies `VALUE_SCALE = 0.001` |
| Aging fleet | Terra and Aqua are past their design life and orbits are drifting; NASA plans continuity with VIIRS-based products |

## 4. Why We Access It

| Reason | Detail |
| --- | --- |
| Dust is the UAE's dominant particulate source | AOD is the best free, daily, km-scale dust proxy |
| Ground stations are sparse in the Gulf | Satellite AOD fills the spatial gaps left by OpenAQ |
| Corridor AOIs (Iraq, Iran, Arabia) | Upwind AOD rising before UAE AOD gives transport signals |

## 5. How We Access It

Same GEE statistics path as doc 04: `reduceRegion` at **1,000 m** per UTC day per AOI, with
`bestEffort` coarsening for very large AOIs (`AOI-ARABIA` is ~1.4 M km²).

## 6–7. Format at Source and What We Store

Real record:

```json
{"_source": "MODIS_AOD", "_event_ts": "2026-11-06T00:00:00Z",
 "payload": {"interval": {"from": "2026-11-06T00:00:00Z", "to": "2026-11-07T00:00:00Z"},
   "outputs": {"index": {"bands": {"B0": {"stats": {"mean": 0.1564, "min": 0.0, "max": 2.233,
       "stDev": 0.1079, "sampleCount": 236785, "noDataCount": 15783}}}}},
   "product": "AOD", "aoi_id": "AOI-DXB", "bbox": [54.9, 24.8, 55.6, 25.4],
   "collection": "MODIS/061/MCD19A2_GRANULES", "sensor": "MODIS", "unit": "unitless"}}
```

*Interpretation:* national mean 0.16 (fairly clear), 94 % valid pixels, but a local maximum of 2.2
points to a dust or smoke patch somewhere in the AOI.

| Decision | Why | Alternative | Trade-off |
| --- | --- | --- | --- |
| MAIAC 1 km via GEE | Free, already scaled, best desert performance | MOD04 Dark Target/Deep Blue 10 km (coarser); VIIRS Deep Blue (6 km); CAMS AOD (model, NetCDF; deferred) | Granule-level QA not applied (SG-03) |
| Scale applied at ingest | Downstream always sees physical AOD | Land raw integers | Bronze is not the raw integer |

## 8. Field Dictionary

| Field | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `…stats.mean` | double | unitless | AOI-mean AOD at 550 nm |
| `…stats.min` / `max` | double | unitless | Pixel extremes (already scaled) |
| `…stats.stDev` | double | unitless | Spatial heterogeneity (high = plume or edge) |
| `…stats.sampleCount` / `noDataCount` | int | pixels @ 1 km | Valid vs missing retrievals |
| `product` | `AOD` | — | Fixed |
| `sensor` | `MODIS` | — | Stamped by the connector (README SG-03: `VIIRS` would still query MODIS) |
| `collection` | string | — | GEE asset |
| `unit` | `unitless` | — | — |

## 9. How to Read & Interpret

| AOD (550 nm) | Typical condition |
| --- | --- |
| < 0.1 | Very clean |
| 0.1 – 0.3 | Normal Gulf background |
| 0.3 – 0.7 | Hazy or elevated dust |
| 0.7 – 1.5 | Dust event |
| > 1.5 | Severe dust storm |

*Indicative bands for orientation only. The platform's dust-event thresholds are defined in
[climate/03](../climate/03-derived-indicators.md) and the Phase 6b KPI-threshold contract.*

AOD is **column-integrated**. A high-altitude dust layer can produce high AOD while surface PM is
moderate, so corroborate with OpenAQ PM₁₀ and TROPOMI `AER_AI`.

## 10. Quality, Limitations & Gotchas

| Gotcha | Mitigation |
| --- | --- |
| No per-pixel QA mask before averaging (SG-03) | Silver flags `valid_fraction < 0.5` as `suspect`; consider adding an `AOD_QA` mask |
| Thick dust can be misclassified as cloud, removing the strongest events | Check `noDataCount` spikes on suspected dust days |
| Bright-surface bias over sand | Silver `bright_surface_flag` → `suspect` |
| Daily mean merges Terra (morning) and Aqua (afternoon) | Diurnal dust cycles are blurred |
| Huge AOIs (`AOI-ARABIA`) get `bestEffort` coarsening | Compare corridors by trend, not absolute pixel counts |

## 11. Downstream Lineage

`Bronze MODIS_AOD` → `silver_aerosol` (`obs_aerosol`, AOD range [0, 5], quality flag) → Gold
`fact_dust_event_daily` → `serving_dust_event_daily` → Air-Quality & Dust dashboard; feature view
*Dust*.

## 12. References

- GEE catalog: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES
- MCD19A2 product page (LP DAAC): https://lpdaac.usgs.gov/products/mcd19a2v061/
- Lyapustin et al. (2018), *MODIS Collection 6 MAIAC algorithm*, Atmospheric Measurement Techniques
