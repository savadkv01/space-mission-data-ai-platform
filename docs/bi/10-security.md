# 10 — BI Security

> Phase 12 · Task 10 — BI Security

BI security inherits the platform access model
([`serving/security.md`](../../serving/security.md),
[`serving/access-strategy.md`](../../serving/access-strategy.md),
[`architecture/09-security-architecture.md`](../../architecture/09-security-architecture.md))
and applies it inside Superset.

## RBAC

| Superset role | Dashboards | Datasets | Notes |
| --- | --- | --- | --- |
| `exec` | Executive | `platform_daily`, `aoi_validation` | aggregates only |
| `ops_eo` | Earth Observation (EO tabs) | `wildfire_daily`,`flood_daily`,`aoi_validation`,`scene_catalog` | EO event types |
| `ops_maritime` | EO (Maritime tab) | `vessel_activity` | RLS: maritime only |
| `steward` | Platform Operations | `catalog_quality`,`scene_catalog`, observability | eng view |
| `ai` | AI / feature view | feature/offline, sim marts | training inputs |
| `demo` | Sim dashboards | `sat_health`,`launch_monthly`,`weather_impact` | labelled sim |
| `analyst` | SQL Lab (personal) | certified datasets (read) | cannot publish ad-hoc SQL |

Roles are created post-import via the `superset` CLI; grants map to the datasets
above.

## Row-Level Security (RLS)

| RLS policy | Role | Filter |
| --- | --- | --- |
| Maritime scope | `ops_maritime` | `vessel_activity` only (dataset-level grant) |
| EO event scope | `ops_eo` | `event_type in ('fire','flood')` on validation |
| Sim isolation | `demo` | sim datasets only; excluded from MVP datasets |

RLS is applied both as **dataset grants** (a role can't see a dataset it isn't
granted) and **row filters** where a shared dataset carries mixed audiences.

## Dataset & Dashboard Permissions

- Datasets: grant per role (default deny).
- Dashboards: `published` + role grant required to view.
- Personal (SQL Lab) content is never auto-shared.

## Audit Logging

| Event | Captured by |
| --- | --- |
| Login / role change | Superset security log |
| Query executed | Superset query log + `logs/` |
| Dashboard/asset export/import | Git history + Superset log |
| RLS filter applied | Superset query log (filter appended) |

## Secrets

- No secrets in `bi/superset/` YAML — DB creds and MinIO keys are env-substituted
  at import (`${...}` placeholders), consistent with
  [../../docs/infrastructure/09-security.md](../../docs/infrastructure/09-security.md).
- Superset secret key from `.env` (`SUPERSET_SECRET_KEY`).

## OWASP Alignment

| Risk | Control |
| --- | --- |
| Broken access control | default-deny RBAC + RLS + read-only DB connection |
| Injection | no ad-hoc chart SQL; parameterised certified datasets; `allow_dml: false` |
| Sensitive data exposure | aggregates for exec; RLS for row-level; no secrets in git |
| Security misconfig | read-only serving DuckDB; least-privilege MinIO analyst key |
