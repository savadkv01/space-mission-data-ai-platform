# 05 Climate / Air-Quality Use-Case Mapping

> Maps each IN-scope source to the new use cases: climate-change monitoring, dust-storm monitoring, and air-quality monitoring. Extends Phase 5 [`05-use-case-mapping.md`](../05-use-case-mapping.md).

## Executive Summary

The atmospheric expansion unlocks the highest-value UAE use cases the platform previously could not serve. TROPOMI supplies the pollutant column, MODIS/VIIRS AOD supplies the aerosol/dust signal, OpenAQ supplies ground-truth for calibration, and the derived indicators supply the climate-change baseline — all keyed by `aoi_id` for cross-domain fusion with existing weather (NASA POWER wind) and fire (FIRMS) data.

## New Use Cases

| UC ID | Use Case | Question Answered |
| --- | --- | --- |
| UC-C1 | Climate-change monitoring | Is the AOI warming, drying, greening, or degrading over time? |
| UC-C2 | Dust-storm monitoring | Where is dust, how concentrated, and where is it heading? |
| UC-C3 | Air-quality monitoring | What are NO₂/SO₂/CO/O₃/CH₄ levels and are they rising? |

## Source → Use-Case Matrix

| Source | UC-C1 Climate | UC-C2 Dust | UC-C3 Air Quality | Primary Role |
| --- | --- | --- | --- | --- |
| OpenAQ | ○ | ◐ (PM) | ● | PM ground-truth, model calibration |
| TROPOMI (NO₂/SO₂/CO/O₃/CH₄) | ◐ (CH₄ carbon proxy) | ◐ (smoke/SO₂) | ● | Air-quality pollutant column, carbon proxy |
| TROPOMI UV Aerosol Index (`AER_AI`) | ○ | ● | ◐ | Dust/smoke plume proxy (bright-surface robust) |
| MODIS/VIIRS AOD | ○ | ● | ◐ (PM proxy) | Aerosol concentration, dust plume, PM estimation |
| Derived LST / LST anomaly | ● | ○ | ○ | Warming / urban-heat indicator |
| Derived NDVI / EVI | ● | ○ | ○ | Vegetation health, desertification |
| Derived SST / SST anomaly | ● | ○ | ○ | Ocean-warming indicator |
| Derived NDWI | ● | ○ | ○ | Water availability |
| Global Forest Watch (existing) | ● | ○ | ○ | Deforestation / carbon |

Legend: ● primary · ◐ supporting · ○ not applicable

## Use-Case Detail

### UC-C1 · Climate-Change Monitoring
- **Inputs:** derived LST/SST/NDVI/EVI/NDWI anomalies + GFW tree-cover loss + desertification proxy.
- **Signal:** multi-year trend and same-DOY anomaly per AOI (warming, greening/browning, drying, degradation).
- **Cross-domain:** urban heat validated against AUH/DXB AOIs; coastal warming from `AOI-COAST` SST.

### UC-C2 · Dust-Storm Monitoring
- **Inputs:** MODIS/VIIRS AOD (concentration) + TROPOMI `AER_AI` (plume proxy) + NASA POWER wind (transport) + secondary corridor AOIs (source).
- **Signal:** elevated AOD/AER_AI over source corridors advecting toward UAE with wind vector; PM estimation from AOD calibrated by OpenAQ.
- **Cross-domain:** `smoke/dust = source(corridor AOD) + wind(POWER) + destination(UAE AOI)`.

### UC-C3 · Air-Quality Monitoring
- **Inputs:** TROPOMI columns (NO₂ traffic/industry, SO₂ industry/volcanic, CO combustion, O₃, CH₄) + OpenAQ surface concentrations.
- **Signal:** pollutant levels and trend per urban AOI; OpenAQ calibrates/validates satellite columns.
- **Cross-domain:** NO₂ elevation co-located with urban AOIs; SO₂/CO smoke linked to FIRMS fire events.

## Smoke Fusion Example (cross-domain)

> Demonstrates fusion with **existing** platform data (fire + weather):

`Smoke event = FIRMS fire detection (source) + AOD/AER_AI elevation (aerosol) + POWER wind (transport direction)` — all joined on AOI + day. Detailed graph in [`07-climate-data-relationships.md`](./07-climate-data-relationships.md).

## Alignment to Phase 1 Business Problems

| Business Theme | Served By |
| --- | --- |
| Environmental & disaster monitoring | UC-C2 dust, UC-C3 air quality |
| Climate & sustainability | UC-C1 climate-change indicators |
| Public-health / urban planning | UC-C3 urban air quality (AUH/DXB) |

## Cross References

- Inventory: [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md)
- Relationships: [`07-climate-data-relationships.md`](./07-climate-data-relationships.md)
- MVP: [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md)
- Phase 5 use-case baseline: [`../05-use-case-mapping.md`](../05-use-case-mapping.md)
