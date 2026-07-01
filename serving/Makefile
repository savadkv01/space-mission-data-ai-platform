# Serving Layer (Phase 11) — developer tasks.
# Mirrors the transformation/ingestion Makefile conventions. The offline targets
# (test) need no infrastructure; dbt/sql targets activate once MinIO + Gold land.

PY ?= ../ingestion/.venv/Scripts/python.exe

.PHONY: help test dbt-deps dbt-run dbt-test sql-build

help:
	@echo "test       - run offline serving unit tests (no infra)"
	@echo "dbt-deps   - install dbt packages (needs dbt-duckdb)"
	@echo "dbt-run    - build serving models on DuckDB (needs Gold Parquet)"
	@echo "dbt-test   - run dbt data-product contract tests"
	@echo "sql-build  - build serving tables via raw DuckDB SQL"

test:
	"$(PY)" -m pytest -q

dbt-deps:
	cd dbt && dbt deps

dbt-run:
	cd dbt && dbt run

dbt-test:
	cd dbt && dbt test

sql-build:
	duckdb serving.duckdb < sql/01_serving_tables.sql
	duckdb serving.duckdb < sql/02_materialized_views.sql
