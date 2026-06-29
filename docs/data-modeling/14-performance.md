# 14 - Performance Considerations

> **Phase 6 - Data Modeling** · Document 14 of 18

## Query Optimization

- Star schemas + partition pruning; broadcast small dims; DuckDB vectorized scans.

## Pre-Aggregation

- Daily/AOI KPI marts; incremental refresh; avoid runtime fan-out joins.

## Indexing (Conceptual)

| Element | Index |
| --- | --- |
| Date | partition |
| Geo | H3/geohash |
| Keys | sorted clustering |

## Storage Optimization

- Parquet/Iceberg compaction; 128–512 MB files; ZSTD; column pruning.

## Cross References

- [12-partitioning.md](12-partitioning.md) · [05-star-schemas.md](05-star-schemas.md)
