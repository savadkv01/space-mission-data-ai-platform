"""Serving Layer (Phase 11).

Exposes trusted Gold marts as business-ready data products for BI, APIs, ML,
and LLM/RAG consumers. The pure-Python builders in ``serving.marts`` are the
canonical serving logic (offline unit-tested); the dbt/SQL models under
``serving/dbt`` and ``serving/sql`` apply the same definitions at scale on the
DuckDB/lakehouse engine.
"""
