# syntax=docker/dockerfile:1
# ============================================================================
# Apache Superset + platform DB drivers
# ----------------------------------------------------------------------------
# The stock apache/superset:latest image is lean and ships NO database drivers,
# so it cannot reach either its own metadata store or the serving data layer.
# This image bakes in only what the BI stack needs (mirrors the
# airflow.Dockerfile / spark-transform.Dockerfile pattern: build once, no
# per-run pip):
#   * psycopg2-binary -> PostgreSQL metadata DB (superset schema/database)
#   * duckdb-engine   -> read-only serving DuckDB datasource (Gold via httpfs)
#
# Superset assets-as-code (bi/superset/**) and first-boot init (db upgrade +
# create-admin + init) are driven from docker-compose.bi.yml.
# ============================================================================
FROM apache/superset:latest

# The base image manages its runtime with `uv` inside the venv at /app/.venv,
# whose site-packages (NOT the system python) is what Superset imports from.
# Installing with plain `pip` lands in system site-packages and is invisible to
# Superset, so drivers must go through `uv` targeting the venv explicitly.
USER root
RUN VIRTUAL_ENV=/app/.venv uv pip install --no-cache \
      "psycopg2-binary==2.9.9" \
      "duckdb-engine==0.13.2"

USER superset
