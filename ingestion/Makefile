# ============================================================================
# Ingestion layer — one-command developer workflow
# Usage: make <target>   (requires a Python 3.11+ virtual environment)
# ============================================================================
PY ?= python

.PHONY: help install test demo topics produce consume validate dags lint

help:
	@echo "install  - install ingestion dependencies"
	@echo "test     - run offline unit tests (no infra)"
	@echo "demo     - run infra-free end-to-end pipeline demo"
	@echo "topics   - create Kafka topics (needs infra up)"
	@echo "produce  - run synthetic telemetry producer (needs infra up)"
	@echo "consume  - run raw Bronze writer consumer (needs infra up)"
	@echo "validate - run validation consumer -> cleaned/DLQ (needs infra up)"

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest

demo:
	$(PY) -m ingestion.scripts.run_local_demo --records 30

topics:
	$(PY) -m ingestion.scripts.create_topics

produce:
	$(PY) -m ingestion.streaming.producers.telemetry_producer --max 1000 --rate 50

consume:
	$(PY) -m ingestion.streaming.consumers.raw_ingest_consumer

validate:
	$(PY) -m ingestion.streaming.consumers.validation_consumer
