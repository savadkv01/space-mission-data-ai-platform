# 11 MVP Dataset Definition

## Executive Summary

The MVP dataset set is the minimum required to build the Phase 6 ingestion system for Earth Observation Operations Intelligence. It draws from Tier 1 plus two early Tier 2 additions, balancing coverage, feasibility, and laptop constraints.

## MVP Set

| Dataset | Use Cases | Why Included |
| --- | --- | --- |
| NASA FIRMS | UC-15 | Backbone NRT fire alerts, low cost |
| VIIRS | UC-15 | Higher-res fire precision |
| Sentinel-2 | UC-14/15/16/27 | Primary optical imagery |
| Sentinel-1 SAR | UC-16/27 | Cloud-penetrating flood mapping |
| Sentinel Hub | UC-14/15 | Index extraction without full scenes |
| Copernicus EMS | UC-16/27 | Reference/eval labels |
| Global Fishing Watch | UC-18 | Maritime fishing effort |
| NASA POWER | UC-15/16 | Lightweight weather context |
| NASA Earthdata (early T2) | UC-14/25 | Catalog + metadata |
| Landsat 8/9 (early T2) | UC-14 | Historical baseline |

## Exclusions

| Excluded | Reason |
| --- | --- |
| ERA5/CAMS | High volume, queue lag; deferred |
| Space weather | UC-21 expansion only |
| Launch/astro | No MVP use case |
| Live AIS | Batch GFW first; streaming later |
| Orbital catalogs | Not needed for first release |

## Trade-offs

- Coverage over volume; laptop feasibility first; SAR for weather independence; built-in validation via EMS.

## Cross References

- Prioritization: [10-data-prioritization.md](./10-data-prioritization.md)
- Phase 2 MVP: [../domain-research/07-mvp-datasets.md](../domain-research/07-mvp-datasets.md)
