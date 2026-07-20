-- ============================================================================
-- Pipeline run-logging tables (Airflow orchestration observability)
-- Runs automatically on first container init (mounted to
-- /docker-entrypoint-initdb.d). bootstrap.sh / apply-run-logging.sh also
-- apply this idempotently to already-initialized volumes.
--
-- Lives in the existing `metadata` schema (ADR-007: reserved for dataset
-- inventory, lineage, quality — nothing else used it yet).
--
-- Shape: every pipeline stage gets a "run" header table (one row per DAG
-- run, one row per stage) plus a "run_detail" table (one row per
-- source/entity/model/dataset processed in that run). `master_run` and
-- `batch_run` are header-only roll-ups (their "detail" is the child stage/
-- pipeline run rows themselves, already logged elsewhere).
--
-- run_id is the Airflow dag_run_id (unique per trigger); parent_run_id links
-- a child run back to whatever triggered it (master -> batch/streaming,
-- batch -> its own stages), giving full trigger-chain traceability.
-- All writes are idempotent: INSERT ... ON CONFLICT DO UPDATE, keyed on the
-- primary key, so task retries under the same run_id never duplicate rows.
-- See docs/infrastructure/06-storage-design.md, OPERATIONS.md.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- master_run — top-level "run everything" rollup (platform_master_pipeline).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.master_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,       -- unused (master is the top of the chain); kept for a uniform header schema
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    batch_run_id      TEXT NULL,
    streaming_run_id  TEXT NULL,
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- batch_run — top-level rollup for one platform_batch_pipeline run
-- (ingestion -> transformation -> serving -> bi).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.batch_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    total_rows        BIGINT NULL,
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- streaming_run — top-level rollup for one platform_streaming_pipeline run
-- (streaming ingestion -> streaming transform).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.streaming_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    total_units       INTEGER NULL,
    total_rows        BIGINT NULL,
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS metadata.streaming_run_detail (
    run_id            TEXT NOT NULL REFERENCES metadata.streaming_run(run_id) ON DELETE CASCADE,
    unit_name         TEXT NOT NULL,   -- e.g. telemetry_produce, raw_ingest_consumer, validation_consumer, stream_sat_health_1m
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    rows              BIGINT NULL,
    error_message     TEXT NULL,
    details           JSONB NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, unit_name)
);

-- ---------------------------------------------------------------------------
-- ingestion_run / ingestion_run_detail — batch ingestion stage (one detail
-- row per API source per run).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.ingestion_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    total_units       INTEGER NULL,
    total_rows        BIGINT NULL,
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS metadata.ingestion_run_detail (
    run_id            TEXT NOT NULL REFERENCES metadata.ingestion_run(run_id) ON DELETE CASCADE,
    unit_name         TEXT NOT NULL,   -- source code, e.g. SWPC, FIRMS, OPENAQ
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    rows              BIGINT NULL,
    error_message     TEXT NULL,
    details           JSONB NULL,      -- e.g. {"batch_id": "...", "bronze_key": "..."}
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, unit_name)
);

-- ---------------------------------------------------------------------------
-- transformation_run / transformation_run_detail — Bronze->Silver->Gold
-- (one detail row per Silver entity / Gold mart / dbt demonstrator run).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.transformation_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    total_units       INTEGER NULL,
    total_rows        BIGINT NULL,
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS metadata.transformation_run_detail (
    run_id            TEXT NOT NULL REFERENCES metadata.transformation_run(run_id) ON DELETE CASCADE,
    unit_name         TEXT NOT NULL,   -- e.g. silver_fire, gold_kpi_wildfire_aoi_daily, gold_dbt_demonstrator
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    rows              BIGINT NULL,
    error_message     TEXT NULL,
    details           JSONB NULL,      -- e.g. {"layer": "silver"|"gold", "path": "s3://..."}
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, unit_name)
);

-- ---------------------------------------------------------------------------
-- serving_run / serving_run_detail — Gold -> dbt data products
-- (one detail row per serving dbt model).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.serving_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    total_units       INTEGER NULL,
    total_rows        BIGINT NULL,
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS metadata.serving_run_detail (
    run_id            TEXT NOT NULL REFERENCES metadata.serving_run(run_id) ON DELETE CASCADE,
    unit_name         TEXT NOT NULL,   -- serving dbt model name, e.g. serving_wildfire_daily
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    rows              BIGINT NULL,
    error_message     TEXT NULL,
    details           JSONB NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, unit_name)
);

-- ---------------------------------------------------------------------------
-- bi_run / bi_run_detail — Superset dataset refresh
-- (one detail row per certified dataset).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.bi_run (
    run_id            TEXT PRIMARY KEY,
    parent_run_id     TEXT NULL,
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    triggered_by      TEXT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    total_units       INTEGER NULL,
    total_rows        BIGINT NULL,    -- unused for BI (kept for a uniform header schema); always NULL
    error_message     TEXT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS metadata.bi_run_detail (
    run_id            TEXT NOT NULL REFERENCES metadata.bi_run(run_id) ON DELETE CASCADE,
    unit_name         TEXT NOT NULL,   -- Superset dataset name, e.g. wildfire_daily
    status            TEXT NOT NULL DEFAULT 'RUNNING',
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NULL,
    duration_seconds  NUMERIC NULL,
    rows              BIGINT NULL,     -- unused for BI (kept for a uniform detail schema); always NULL
    error_message     TEXT NULL,
    details           JSONB NULL,      -- e.g. {"dataset_id": 11}
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, unit_name)
);

CREATE INDEX IF NOT EXISTS ix_ingestion_run_detail_run_id       ON metadata.ingestion_run_detail (run_id);
CREATE INDEX IF NOT EXISTS ix_transformation_run_detail_run_id  ON metadata.transformation_run_detail (run_id);
CREATE INDEX IF NOT EXISTS ix_serving_run_detail_run_id         ON metadata.serving_run_detail (run_id);
CREATE INDEX IF NOT EXISTS ix_bi_run_detail_run_id              ON metadata.bi_run_detail (run_id);
CREATE INDEX IF NOT EXISTS ix_streaming_run_detail_run_id       ON metadata.streaming_run_detail (run_id);
