# Data Quality Runbooks

> Step-by-step operational procedures for the on-call data engineer. Each runbook
> is triggered by an alert defined in
> [../monitoring/monitoring-strategy.md](../monitoring/monitoring-strategy.md) and
> references the incident catalog in [production-incidents.md](production-incidents.md).

---

## Response principles

1. **Never drop data.** Failing records go to quarantine, never `/dev/null`.
2. **Bronze is truth.** Recovery reprocesses from immutable Bronze, not source,
   whenever the raw landing is intact.
3. **Contain, then fix.** Stop bad data from reaching Gold/BI before root-causing.
4. **Record everything.** Every incident produces a timestamped record for
   MTTD/MTTR measurement.

---

## RB-01 — Freshness breach (INC-01, INC-07)

**Trigger:** `FreshnessBreach` / `dq_freshness_lag_seconds > SLA`.

1. Confirm the affected `entity` and current lag in Grafana.
2. Check source availability (connector logs, provider status).
3. If source is healthy → re-trigger the ingestion DAG in Airflow (`:8082`).
4. If source is down → open INC-02 path, hold pipeline, do **not** publish empty
   Silver.
5. Once data lands, backfill the missed window from Bronze and re-run Silver/Gold.
6. Verify `dq_freshness_lag_seconds` returns below SLA; close incident.

---

## RB-02 — API unavailable (INC-02)

**Trigger:** error-rate spike / zero-volume batch.

1. Classify: outage vs auth (`401/403`) vs rate-limit (`429`).
2. Auth → rotate credential in `infrastructure/env`, redeploy connector.
3. Rate-limit → enable backoff, reduce fetch frequency.
4. Outage → pause the DAG, set maintenance note, poll for recovery.
5. On recovery, resume and backfill; verify volume returns to baseline.

---

## RB-03 — Schema change (INC-03)

**Trigger:** `SchemaChanged` / schema-registry diff.

1. Retrieve the schema diff from the Bronze gate.
2. Quarantine the affected batch (records preserved).
3. Update the `Schema` in [ingestion/common/schemas.py](../../ingestion/common/schemas.py)
   and the cleaner mapping; bump schema `version`.
4. Add/adjust a contract test with the new sample payload.
5. Re-profile, re-run the batch, confirm checkpoint passes.
6. Request Owner + Platform Eng approval; re-certify the dataset.

---

## RB-04 — Duplicate spike (INC-04)

**Trigger:** `DuplicateSpike` / `dq_duplicate_ratio > 0.05`.

1. Identify the entity and natural key (`fire_key`, `vessel_key`, `scene_key`,
   `launch_id`).
2. Confirm whether the source re-sent or fetch windows overlapped.
3. Re-run Silver dedup for the window; verify unique-key checkpoint passes.
4. Recompute affected Gold marts; confirm counts corrected.
5. Adjust fetch watermark to prevent window overlap.

---

## RB-05 — Corrupted / unreadable files (INC-05, INC-09)

**Trigger:** file-integrity failure / Parquet read error / checksum mismatch.

1. Locate the object and compare stored `_checksum` to recomputed checksum.
2. Quarantine the corrupt object.
3. If Bronze raw is intact → reprocess Silver/Gold from Bronze.
4. If Bronze is corrupt → re-fetch from source, re-land, verify checksum.
5. Run an integrity sweep on neighbouring partitions.
6. Verify downstream checkpoints pass; close incident.

---

## RB-06 — Missing partitions (INC-06)

**Trigger:** reconciliation mismatch / volume drop.

1. Compare expected-partition manifest to actual partitions per day.
2. Identify the missing window and its cause (failed task vs source gap).
3. Backfill from Bronze/source for the window.
4. Re-run Silver and Gold for affected partitions.
5. Re-run reconciliation; confirm counts align across layers.

---

## RB-07 — Timestamp / time-sync issues (INC-08)

**Trigger:** timestamp validation failures / `dq_late_arrival_pct` spike.

1. Inspect quarantined rows for future/implausible timestamps.
2. Confirm UTC normalization is applied at Silver.
3. Fix timezone/parse handling if a source format changed.
4. Reprocess; reorder by event time; verify monotonicity checkpoint.

---

## RB-08 — Geospatial corruption (INC-10)

**Trigger:** geospatial validation failures / AOI join returns zero.

1. Inspect out-of-range lat/lon and `geo_key` mismatches.
2. Check for swapped lat/lon or non-WGS84 input; fix `normalize_lon`/bbox parse.
3. Re-derive `geo_key`; re-run AOI marts (`kpi_wildfire_aoi_daily`,
   `kpi_flood_aoi_daily`, `kpi_aoi_validation`).
4. Verify AOI-attribution reconciliation is non-zero where expected.

---

## RB-09 — Quarantine release (general)

**Trigger:** steward decides quarantined records are recoverable.

1. Review quarantine payloads at
   `staging/quarantine/<source>/ingest_date=<date>/` and the `_quarantine_reasons`.
2. Apply the fix (mapping/parse/threshold) at the appropriate layer.
3. Replay quarantined records through validation.
4. Records that now pass promote to Silver; the rest stay quarantined with an
   updated reason.
5. Record the release in the incident log (audit trail).

---

## Escalation & closure

| Step | Owner | SLA |
|------|-------|-----|
| Acknowledge alert | Data on-call | ≤ 30 min |
| Contain (quarantine/hold) | Data on-call | ≤ 1 h |
| Root cause + fix | Steward / Platform Eng | severity-based (see KPIs) |
| Re-certify | Owner | before republish |
| Retro (critical only) | all involved | within 3 days |

Each closed incident updates MTTD/MTTR metrics reported on the Grafana
**Quality Overview** dashboard.
