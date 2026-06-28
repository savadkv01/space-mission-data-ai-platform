# MinIO Configuration

> Phase 4 Infrastructure Blueprint — see [../../../docs/infrastructure/06-storage-design.md](../../../docs/infrastructure/06-storage-design.md)

MinIO is configured entirely via environment variables in
`docker/docker-compose.storage.yml` (`MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`,
`MINIO_PROMETHEUS_AUTH_TYPE`). No server config file is required.

## Buckets (created by `scripts/bootstrap.sh`)

| Bucket | Purpose |
| --- | --- |
| `bronze` | Raw immutable ingested objects |
| `silver` | Validated, standardized data |
| `gold` | Business-ready aggregates/marts |
| `warehouse` | Iceberg-managed table data + metadata |
| `mlflow-artifacts` | MLflow model artifacts |
| `staging` | Transient landing area |

## Bucket Policy Strategy (lightweight RBAC)

| Service account | Access |
| --- | --- |
| ingestion | write `bronze`, `staging` |
| processing (Spark/dbt) | read/write `bronze`,`silver`,`gold`,`warehouse` |
| mlflow | read/write `mlflow-artifacts` |
| analyst/superset | read `gold` |

Service accounts and scoped policies are created with `mc admin user`/`mc admin policy`
during a later implementation phase; the design is documented here.
