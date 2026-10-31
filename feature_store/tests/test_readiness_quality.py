from datetime import datetime, timezone

import pytest

from feature_store.quality.drift import drift_status, population_stability_index
from feature_store.quality.validation import (
    profile_rows,
    validate_numeric_bounds,
    validate_rows,
)
from feature_store.readiness import FEATURE_READINESS, may_materialize


def test_readiness_blocks_unreconciled_and_empty_domains():
    assert FEATURE_READINESS["wildfire_aoi_daily"].status == "blocked"
    assert "45 of 98" in FEATURE_READINESS["wildfire_aoi_daily"].blocker
    assert FEATURE_READINESS["spectral_index_daily"].status == "blocked"
    assert "zero rows" in FEATURE_READINESS["spectral_index_daily"].blocker
    assert not may_materialize(
        FEATURE_READINESS["wildfire_aoi_daily"].status,
        allow_demo=True,
        allow_restricted=True,
    )


def test_demo_and_catalog_feature_views_require_explicit_scope():
    assert not may_materialize("demo_only", allow_demo=False, allow_restricted=True)
    assert may_materialize("demo_only", allow_demo=True, allow_restricted=False)
    assert not may_materialize("restricted", allow_demo=True, allow_restricted=False)
    assert may_materialize("restricted", allow_demo=False, allow_restricted=True)


def test_quality_profile_and_contract_validation_report_missing_critical_values():
    rows = [
        {
            "sat_key": "SIM-SAT-001",
            "event_timestamp": datetime(2026, 10, 31, tzinfo=timezone.utc),
            "health_score": 0.8,
        },
        {
            "sat_key": "SIM-SAT-002",
            "event_timestamp": datetime(2026, 10, 31, tzinfo=timezone.utc),
            "health_score": None,
        },
    ]

    profile = profile_rows(rows, ["health_score"])
    assert profile["row_count"] == 2
    assert profile["null_rates"]["health_score"] == 0.5
    assert validate_rows(
        rows,
        entity_field="sat_key",
        critical_fields=["health_score"],
        max_null_rate=0.1,
    ) == ["health_score null rate 0.5000 exceeds 0.1000"]


def test_numeric_bounds_and_drift_checks():
    assert validate_numeric_bounds(
        [{"health_score": 0.8}, {"health_score": 1.2}],
        {"health_score": (0.0, 1.0)},
    ) == ["health_score at row 1 is outside [0.0, 1.0]: 1.2"]
    score = population_stability_index([1, 1, 2, 2, 3, 3], [10, 10, 11, 11, 12, 12])
    assert score > 0.2
    assert drift_status(score) == "warn"
    assert drift_status(0.01) == "pass"
    with pytest.raises(ValueError, match="non-empty"):
        population_stability_index([], [1.0])
