"""Ingestion-time data quality (Task 9)."""

from ingestion.quality.validators import ValidationOutcome, validate_record
from ingestion.quality.quarantine import Quarantine

__all__ = ["ValidationOutcome", "validate_record", "Quarantine"]
