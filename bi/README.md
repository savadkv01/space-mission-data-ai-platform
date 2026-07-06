# Business Intelligence & Analytics Layer

> **Phase 12 — Business Intelligence & Analytics** · Space Mission Data & AI Platform

The BI layer turns trusted **Gold**/serving data into executive dashboards,
operational monitoring, engineering analytics, and decision-support reports using
**Apache Superset** (open-source, 16 GB-laptop viable). Everything here is
**assets-as-code**: certified dataset SQL, Superset YAML exports, and governance
docs are version-controlled and load against the serving layer.

## Design Principles

- **One source of truth** — KPIs come from the serving semantic layer, never
  re-derived in BI (BI = human-facing projection of serving).
- **Certified datasets only** — no ad-hoc SQL in charts; one dataset per serving
  product.
- **Audience-first** — dashboards grouped by persona, each mapped to an RBAC role.
- **MVP-aligned** — Earth Observation / maritime is primary; spacecraft
  satellite/launch/weather are clearly-labelled `sim` demonstrators (ADR-09).

## Folder Map

| Path | Contents |
| --- | --- |
| [`datasets/sql/`](./datasets/sql/) | Certified dataset SQL (10 datasets) |
| [`datasets/certified-datasets.md`](./datasets/certified-datasets.md) | Dataset catalog + tiers + lifecycle |
| [`datasets/dataset-governance.md`](./datasets/dataset-governance.md) | Governance rules + certification checklist |
| [`dashboards/`](./dashboards/) | 6 dashboard specs (wireframes, KPI tiles, drill-down) |
| [`kpis/kpi-catalog.md`](./kpis/kpi-catalog.md) | Full KPI catalog (definition→threshold→impact) |
| [`reports/reporting-strategy.md`](./reports/reporting-strategy.md) | Scheduled + real-time reporting |
| [`alerts/alert-strategy.md`](./alerts/alert-strategy.md) | Decision + infra alert catalog + flow |
| [`superset/`](./superset/) | Assets-as-code: databases, datasets, charts, dashboards (YAML) |

Governance narrative lives in [`../docs/bi/`](../docs/bi/) (14 documents).

## Certified Datasets

| Dataset | Source | Track |
| --- | --- | --- |
| `wildfire_daily`, `flood_daily`, `vessel_activity`, `scene_catalog`, `aoi_validation` | `serving.serving_*` | MVP |
| `platform_daily` | `serving_agg.mv_kpi_platform_daily` | MVP (materialized) |
| `catalog_quality` | `serving.serving_scene_catalog` (aggregate) | MVP |
| `sat_health`, `launch_monthly`, `weather_impact` | `gold.*` via httpfs | Sim (`demo`) |

## Dashboards

Executive · Earth Observation (MVP-primary) · Imagery & Catalog Quality · Simulation
Track (Satellite/Launch/Weather `sim`, tabbed). Executive and Earth Observation each
have an **Overview** tab and a **Details** tab with raw drill-down tables (fire
detections, flood extent, suspicious vessels). Platform Operations remains a
markdown-only spec (Prometheus/Airflow metrics aren't queryable via the Superset
DuckDB connection). See [`docs/bi/02-dashboard-catalog.md`](../docs/bi/02-dashboard-catalog.md).

## Run It

```bash
# 0. build the serving DuckDB file the dashboards read (see serving/dbt)
#    -> produces serving/dbt/serving.duckdb
# 1. storage first, then BI stack (Superset depends on postgres in `storage`)
docker compose --env-file infrastructure/env/.env \
  -f infrastructure/docker/docker-compose.yml \
  -f infrastructure/docker/docker-compose.bi.yml \
  --profile storage --profile bi up -d superset
# 2. init + import assets via the v1 REST API — see bi/superset/README.md
```

## Alignment

- MVP: [`docs/business/05-mvp-definition.md`](../docs/business/05-mvp-definition.md)
- KPIs: [`docs/business/08-kpis.md`](../docs/business/08-kpis.md)
- Serving contract: [`serving/`](../serving/) (ADR-SV-01, semantic layer)
- Architecture: [`architecture/`](../architecture/) (observability, security)
