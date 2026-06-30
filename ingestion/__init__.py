"""Ingestion layer package.

A modular, open-source ingestion implementation for the Space Mission Data &
AI Platform. Components:

- ``config``      — environment-driven settings
- ``common``      — Bronze envelope, HTTP/Kafka/MinIO IO, schema registry
- ``simulation``  — synthetic telemetry / orbit / space-weather generators
- ``api``         — pull connectors for NASA/NOAA/CelesTrak
- ``streaming``   — Kafka producers and consumers
- ``quality``     — ingestion-time validation and quarantine
- ``batch``       — Airflow DAGs for scheduled batch ingestion
"""

__version__ = "0.1.0"
