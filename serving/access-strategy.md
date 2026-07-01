# Data Access Strategy (Task 9)

Access to serving datasets is governed by classification + RBAC. The serving
layer is **read-only** to all consumers; writes happen only via the serving
refresh job.

## Consumers

| Type | Consumer | Access |
| --- | --- | --- |
| Internal | EO analysts, maritime analysts, stewards, leadership | RBAC role per dashboard/dataset |
| Internal | ML pipelines, RAG assistant | service accounts, scoped read |
| External | partner apps / public portal | public datasets only, via API |

## Dataset Classification

| Class | Meaning | Examples | Access |
| --- | --- | --- | --- |
| Public | shareable externally | `mv_kpi_platform_daily` (aggregated), `serving_scene_catalog` (metadata) | anonymous read scope |
| Internal | staff only | `serving_wildfire_daily`, `serving_flood_daily`, `serving_aoi_validation` | authenticated role |
| Sensitive | restricted | `serving_vessel_activity` (maritime/defence-adjacent) | `ops_maritime` only |
| Demo | synthetic (sim) | satellite/launch/weather products | `demo` scope, labelled synthetic |

## RBAC Model

```mermaid
flowchart LR
    U["User / service account"] --> R["Role (exec/ops_eo/ops_maritime/steward/ai/demo)"]
    R --> P["Dataset permissions (read)"]
    P --> D["Serving datasets (classified)"]
```

| Role | Public | Internal EO | Maritime (sensitive) | Catalog | Sim (demo) |
| --- | --- | --- | --- | --- | --- |
| `exec` | ✅ | ✅ | ✅ | ✅ | — |
| `ops_eo` | ✅ | ✅ | — | ✅ | — |
| `ops_maritime` | ✅ | — | ✅ | — | — |
| `steward` | ✅ | — | — | ✅ | — |
| `ai` (svc) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `demo` | ✅ | — | — | — | ✅ |
| anonymous | ✅ | — | — | — | — |

## Read-Only Guarantee

- Consumers connect with read-only credentials; no consumer can mutate serving
  tables.
- The serving refresh service account is the **only** writer, isolated from
  consumer roles.

## Enforcement Points

- **Superset**: role-based dashboard access + row-level security.
- **API**: OIDC scope → role mapping in middleware (Phase 16).
- **RAG**: classification metadata filter at retrieval time.
- **Warehouse**: read-only grants per schema (`serving`, `serving_agg`).
