# 13 - Data Lifecycle Management

> **Phase 6 - Data Modeling** · Document 13 of 18

## Retention

| Layer | Retention |
| --- | --- |
| Bronze raw | 90 days hot, archive after |
| Silver | 1–2 years |
| Gold KPI | 5 years |
| Vectors | rebuildable from source |

## Archival

- Cold data to MinIO compressed Parquet; metadata retained in catalog.

## Versioning

- Iceberg snapshots enable time-travel; feature/vector sets versioned.

## Historical Reprocessing

- Replay Bronze → Silver → Gold by batch_id; deterministic transforms.

## Cross References

- [02-bronze-layer.md](02-bronze-layer.md) · [15-governance.md](15-governance.md)
