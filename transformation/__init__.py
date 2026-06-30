"""Transformation layer (Phase 9) — Bronze -> Silver -> Gold lakehouse processing.

This package implements the Medallion transformation pipeline for the Space
Mission Data & AI Platform. The pure-Python transformation *rules* (cleaning,
Silver conformance, Gold aggregation, feature engineering, geospatial and
time-series processing) are infra-free and fully unit-tested so they run on any
laptop with no Spark/Kafka/Java. Thin PySpark and dbt entrypoints apply the same
rules at scale once infrastructure is available.
"""
