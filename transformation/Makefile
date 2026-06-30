# ============================================================================
# Transformation layer (Phase 9) — one-command developer workflow
# Usage: make <target>   (requires a Python 3.11+ virtual environment)
# ============================================================================
PY ?= python

.PHONY: help install install-spark test demo silver gold stream dbt-deps dbt-run dag-check

help:
	@echo "install      - install offline transformation deps (no Spark/Java needed)"
	@echo "install-spark- install PySpark + dbt-duckdb (needs Java for Spark)"
	@echo "test         - run offline unit tests (no infra)"
	@echo "demo         - run infra-free Bronze->Silver->Gold->Features demo"
	@echo "silver       - run a Spark Bronze->Silver job (needs infra up)"
	@echo "gold         - run dbt Gold marts (needs Silver Parquet)"
	@echo "stream       - run the structured streaming job (needs Kafka+Spark)"

install:
	$(PY) -m pip install -r requirements.txt

install-spark:
	$(PY) -m pip install -r requirements-spark.txt

test:
	$(PY) -m pytest

# Module entrypoints run from the repo root so the `transformation` and
# `ingestion` packages resolve without an editable install.
demo:
	cd .. && $(PY) -m transformation.scripts.run_local_demo --records 60

silver:
	cd .. && $(PY) -m transformation.batch.bronze_to_silver --entity telemetry

stream:
	cd .. && $(PY) -m transformation.streaming.spark_streaming

dbt-deps:
	cd dbt && dbt deps

dbt-run:
	cd dbt && dbt run --select gold && dbt test --select gold

dag-check:
	cd .. && $(PY) -c "from transformation.orchestration.dags.transformation_pipeline_dag import build_dag; print('DAG import OK:', build_dag())"
