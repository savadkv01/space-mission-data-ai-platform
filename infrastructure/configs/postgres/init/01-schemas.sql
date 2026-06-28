-- ============================================================================
-- PostgreSQL bootstrap — Phase 4 Infrastructure Blueprint
-- Runs automatically on first container init (mounted to
-- /docker-entrypoint-initdb.d). Creates the logical schemas that isolate
-- each service within a single PostgreSQL instance (ADR-007).
-- bootstrap.sh also creates these idempotently for already-initialized DBs.
-- See docs/infrastructure/06-storage-design.md
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS metadata;          -- dataset inventory, lineage, quality
CREATE SCHEMA IF NOT EXISTS gold;              -- business-ready serving tables
CREATE SCHEMA IF NOT EXISTS iceberg_catalog;   -- Iceberg JDBC catalog
CREATE SCHEMA IF NOT EXISTS airflow;           -- Airflow metadata DB
CREATE SCHEMA IF NOT EXISTS mlflow;            -- MLflow tracking store
CREATE SCHEMA IF NOT EXISTS superset;          -- Superset metadata DB
CREATE SCHEMA IF NOT EXISTS feast;             -- Feast registry / online store

-- Lightweight RBAC simulation: a read-only analyst role scoped to gold.
-- (Password/login roles are created out-of-band; this defines privileges.)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analyst_ro') THEN
    CREATE ROLE analyst_ro NOLOGIN;
  END IF;
END
$$;

GRANT USAGE ON SCHEMA gold TO analyst_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO analyst_ro;
