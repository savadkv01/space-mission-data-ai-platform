# 15 - Data Governance Model

> **Phase 6 - Data Modeling** · Document 15 of 18

## Ownership

| Domain | Owner |
| --- | --- |
| EO | EO data steward |
| Telemetry | Ops steward |
| Catalog/metadata | Platform team |

## Lineage

- Captured per transition (Bronze→Silver→Gold) with batch_id; any Gold figure traces to source.

## Metadata

- Inventory, provenance, quality, freshness, ownership in PostgreSQL catalog.

## Data Catalog (Concept)

- Searchable dataset registry; classification + sensitivity tags; API-exposed.

## Cross References

- [13-data-lifecycle.md](13-data-lifecycle.md) · [02-bronze-layer.md](02-bronze-layer.md)
