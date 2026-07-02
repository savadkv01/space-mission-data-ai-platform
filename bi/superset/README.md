# Superset Assets-as-Code

> Phase 12 — BI implementation. Superset dashboards, charts, datasets and the
> database connection are version-controlled here as YAML (the Superset
> import/export bundle format) so BI is reproducible from `git` + `docker compose`.

## Layout

```
superset/
├── databases/            connection definitions (no secrets — env-substituted)
│   └── serving_duckdb.yaml
├── datasets/             physical/virtual dataset definitions (certified SQL)
│   └── serving_duckdb/*.yaml
├── charts/               chart (slice) definitions
│   └── *.yaml
├── dashboards/           dashboard definitions + layout
│   └── *.yaml
└── metadata.yaml         bundle version marker
```

The certified SQL bodies are the single source in
[`../datasets/sql/`](../datasets/sql/); the dataset YAML embeds the same SQL so an
import is self-contained. Keep them in sync via the `make bi-export` workflow.

## Prerequisite — build the serving DuckDB file

Superset reads a **pre-built** DuckDB file produced by the serving dbt project
(it materialises the Gold parquet in `s3://gold` into the `semantic` / `serving`
/ `serving_agg` schemas). Build it before starting the BI stack:

```bash
cd serving/dbt
DBT_PROFILES_DIR=$PWD SERVING_DUCKDB_PATH=$PWD/serving.duckdb \
  DUCKDB_S3_ENDPOINT=minio:9000 \
  dbt deps && dbt run   # produces serving/dbt/serving.duckdb (git-ignored)
```

The [`macros/generate_schema_name.sql`](../../serving/dbt/macros/generate_schema_name.sql)
override forces **bare** schema names (`serving`, not the dbt-default
`main_serving`) so the dataset SQL resolves.

## Import (into a running Superset)

```bash
# 1. bring up storage + BI (Superset depends on postgres, which lives in the
#    storage profile — BOTH profiles are required or Compose errors)
docker compose --env-file infrastructure/env/.env \
  -f infrastructure/docker/docker-compose.yml \
  -f infrastructure/docker/docker-compose.bi.yml \
  --profile storage --profile bi up -d superset

# 2. first-boot init runs automatically (see the service `command:` in
#    docker-compose.bi.yml — db upgrade + create-admin + init)

# 3. import the assets bundle via the v1 REST API (NOT the `superset
#    import-dashboards` CLI — that dispatches to the legacy v0 JSON importer
#    and fails on these YAML assets). Log in for an access token + CSRF token,
#    then POST the zip to /api/v1/dashboard/import/ with overwrite=true.
```

> **Bundle gotchas (verified):**
> - The zip must use **forward-slash** entry names under a **single root folder**
>   (e.g. `bundle/metadata.yaml`). Windows `Compress-Archive` writes backslash
>   separators, which the importer's POSIX path-stripping cannot handle — build
>   the zip with `System.IO.Compression` (forward slashes) or `zip` on Linux.
> - Every `CHART` node in a dashboard's `position` needs both `uuid` **and**
>   `chartId` (int) in its `meta`, or the importer raises `KeyError: 'chartId'`.
> - `${...}` placeholders in `databases/serving_duckdb.yaml` (S3 endpoint/creds)
>   are substituted with real values at import time; secrets are never committed.

## Export (after editing in the UI)

```bash
docker compose ... exec superset \
  superset export-dashboards -f /tmp/bi_assets.zip
# unzip into bi/superset/ and commit — the UI is NEVER the source of truth
```

## Connection & Secrets

- `databases/serving_duckdb.yaml` references the read-only serving DuckDB file
  mounted into the Superset container at
  `duckdb:////opt/serving/serving_products.duckdb`. The file is bind-mounted
  read-only in `docker-compose.bi.yml` from `serving/dbt/serving.duckdb`. The
  container basename **deliberately differs** (`serving_products` vs `serving`):
  a DuckDB attached-database takes its catalog name from the file basename, so a
  file named `serving.duckdb` would create a catalog `serving` that collides with
  the `serving` *schema* ("Ambiguous reference to catalog or schema serving").
- S3/MinIO credentials for the `sim` datasets' `httpfs` reads are provided via the
  connection's `engine_params.connect_args.config` from environment variables —
  **no secrets are committed** (placeholders use `${...}`).
- RBAC roles (`exec`, `ops_eo`, `ops_maritime`, `steward`, `ai`, `demo`) and RLS
  filters are defined in [`../../serving/security.md`](../../serving/security.md)
  and applied post-import via `superset` CLI (documented in
  [`../docs/bi/10-security.md`](../docs/bi/10-security.md)).

## Coverage

This bundle imports live end-to-end: the connection, all 10 certified datasets,
8 charts, and the Executive + Earth Observation dashboards (with layout). Verified
via `POST /api/v1/chart/data` — both the baked `serving_*` tables and the
`s3://gold` httpfs `sim` datasets return rows. The remaining dashboards (Platform,
Satellite `sim`, Launch `sim`, Weather `sim`) follow the identical pattern
documented per-dashboard in [`../dashboards/`](../dashboards/) and are generated
with the same export workflow.
