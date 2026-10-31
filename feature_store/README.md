# Feature Store

Feast feature definitions, PostgreSQL offline/online storage, point-in-time
training retrieval, readiness-gated materialization, and local online serving
for the Space Mission Data & AI Platform.

## Scope

- Phase 13 feature views and Phase 13b climate, dust, and air-quality views.
- PostgreSQL remains the Feast offline store, online store, and SQL registry.
- Climate inputs are read only from the four Phase 11b serving products in the
  existing read-only DuckDB file; raw Gold, Silver, and Bronze are not read here.
- Blocked data products remain registered for discovery but cannot be
  materialized or retrieved online.

## Run and validate

The feature-store Docker profile reuses PostgreSQL and mounts the built serving
database read-only. Configure the repository's normal Docker environment, then
start the existing `feature-store` profile. The API exposes readiness at
`/readiness`; protected hourly materialization is triggered by the existing
Airflow DAG.

Run unit and local integration tests from the repository root:

```powershell
python -m pytest feature_store/tests
```

The Feast integration tests require the configured PostgreSQL service.

## Documents

- [Climate / dust / air-quality feature store](../docs/feature-store/climate.md)
- [Phase 13 feature-store documentation index](../docs/feature-store/README.md)
