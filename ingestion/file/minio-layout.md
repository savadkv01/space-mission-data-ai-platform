# MinIO Layout

Narrative: [docs/ingestion/07-landing-zone.md](../../docs/ingestion/07-landing-zone.md). Code: [common/minio_io.py](../common/minio_io.py).

```
s3://bronze/<source>/ingest_date=YYYY-MM-DD/<batch_id>/<part|filename>
s3://staging/quarantine/<source>/ingest_date=YYYY-MM-DD/<batch_id>.jsonl
```

| Bucket | Use |
| --- | --- |
| `bronze` | immutable raw landing (NDJSON envelopes + raw files) |
| `staging` | quarantine + transient work |

Buckets are created by [infrastructure/scripts/bootstrap.sh](../../infrastructure/scripts/bootstrap.sh). Key builder: `bronze_key(source, batch_id, part)`.
