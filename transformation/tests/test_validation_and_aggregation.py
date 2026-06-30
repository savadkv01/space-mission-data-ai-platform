from __future__ import annotations

from transformation.batch.aggregation_jobs import aggregate_time
from transformation.cleaning.validation_framework import (
    expect_not_null,
    expect_unique,
    expect_value_in_range,
    run_checkpoint,
)


def test_checkpoint_passes_clean_batch():
    rows = [{"id": 1, "ts": "t1", "v": 5}, {"id": 2, "ts": "t2", "v": 7}]
    result = run_checkpoint(rows, [
        expect_not_null("id"),
        expect_unique(["id"]),
        expect_value_in_range("v", 0, 10),
    ])
    assert result.passed
    assert not result.failures


def test_checkpoint_detects_failures():
    rows = [{"id": 1, "v": 99}, {"id": 1, "v": None}]
    result = run_checkpoint(rows, [
        expect_unique(["id"]),
        expect_value_in_range("v", 0, 10),
        expect_not_null("v", severity="warn"),
    ])
    assert not result.passed
    assert any("unique" in f for f in result.failures)
    assert result.warnings  # null v is a warning, not critical


def test_aggregate_time_mean_per_entity():
    rows = [
        {"satellite_id": "S1", "event_ts": "2026-06-01T00:00:10Z", "snr": 10},
        {"satellite_id": "S1", "event_ts": "2026-06-01T00:00:50Z", "snr": 20},
        {"satellite_id": "S2", "event_ts": "2026-06-01T00:00:10Z", "snr": 5},
    ]
    out = aggregate_time(rows, "snr", grain="minute", key_fields=["satellite_id"])
    by_sat = {r["satellite_id"]: r for r in out}
    assert by_sat["S1"]["snr_mean"] == 15.0
    assert by_sat["S1"]["count"] == 2
    assert by_sat["S2"]["snr_mean"] == 5.0
