# Bronze Zone

Narrative: [docs/ingestion/07-landing-zone.md](../../docs/ingestion/07-landing-zone.md). Code: [common/minio_io.py](../common/minio_io.py), [common/envelope.py](../common/envelope.py).

- Bucket `bronze`; append-only, immutable, replayable.
- Records wrapped in the **Bronze envelope** (provenance: `_ingest_id`, `_source`, `_checksum`, `_batch_id`, …).
- Layout: `s3://bronze/<source>/ingest_date=YYYY-MM-DD/<batch_id>/part-0000.jsonl`.
- Retention: long-term (audit + full Silver/Gold rebuild).
- Aligns with [docs/data-modeling/02-bronze-layer.md](../../docs/data-modeling/02-bronze-layer.md).
