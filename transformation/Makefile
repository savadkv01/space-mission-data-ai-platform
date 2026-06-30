# ============================================================================
# Transformation layer (Phase 9) — one-command developer workflow
# Usage: make <target>   (requires a Python 3.11+ virtual environment)
# ============================================================================
PY ?= python

# In-container runner (hardened spark-master). Override if your project name
# or container differs: make pipeline-infra SPARK_C=<container>
SPARK_C ?= space-platform-spark-master-1
ENTITY  ?= telemetry

.PHONY: help install install-spark test demo silver gold stream dbt-deps dbt-run dag-check \
        pipeline-infra silver-infra gold-infra stream-infra

help:
	@echo "install      - install offline transformation deps (no Spark/Java needed)"
	@echo "install-spark- install PySpark + dbt-duckdb (needs Java for Spark)"
	@echo "test         - run offline unit tests (no infra)"
	@echo "demo         - run infra-free Bronze->Silver->Gold->Features demo"
	@echo "silver       - run a Spark Bronze->Silver job (needs infra up)"
	@echo "gold         - run dbt Gold marts (needs Silver Parquet)"
	@echo "stream       - run the structured streaming job (needs Kafka+Spark)"
	@echo "--- in-container (hardened spark-master; needs 'docker compose up') ---"
	@echo "pipeline-infra - Bronze->Silver->Gold end-to-end inside spark-master"
	@echo "stream-infra   - run the Kafka->Silver streaming job inside spark-master"

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

# --- In-container targets (run against the live, hardened spark-master) ------
# These exec into the container, which already has the code mount, dbt-duckdb,
# cached jars and MinIO/Kafka env — no docker cp / pip / network-connect needed.
pipeline-infra:
	docker exec -u root $(SPARK_C) bash /opt/spark/work-dir/transformation/scripts/run_pipeline.sh

silver-infra:
	docker exec -u root $(SPARK_C) /opt/spark/bin/spark-submit \
		--packages org.apache.hadoop:hadoop-aws:3.3.4 \
		--conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions= \
		/opt/spark/work-dir/transformation/scripts/run_silver.py $(ENTITY)

gold-infra:
	docker exec -u root -w /opt/spark/work-dir/transformation/dbt $(SPARK_C) \
		bash -c "dbt deps && dbt run && dbt test"

stream-infra:
	docker exec -u root $(SPARK_C) /opt/spark/bin/spark-submit \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4 \
		--conf spark.jars.ivy=/tmp/.ivy2 --conf spark.sql.extensions= \
		--conf spark.driver.host=localhost --conf spark.driver.bindAddress=127.0.0.1 \
		/opt/spark/work-dir/transformation/scripts/run_stream.py
