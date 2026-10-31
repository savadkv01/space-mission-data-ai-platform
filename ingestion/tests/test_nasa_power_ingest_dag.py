from __future__ import annotations

from types import SimpleNamespace

import pytest

from ingestion.batch.dags import nasa_power_ingest_dag


def _capture_ingest(monkeypatch):
    calls = []

    def capture(connector, **kwargs):
        calls.append(kwargs)
        return {"status": "ok"}

    monkeypatch.setattr(nasa_power_ingest_dag, "run_connector_to_bronze", capture)
    return calls


def test_power_dag_uses_default_trailing_window(monkeypatch):
    calls = _capture_ingest(monkeypatch)

    result = nasa_power_ingest_dag._ingest(
        "AOI-DXB", 25.1, 55.2, ds_nodash="20261031"
    )

    assert result == {"status": "ok"}
    assert calls[0]["start"] == "20261024"
    assert calls[0]["end"] == "20261031"
    assert calls[0]["aoi_id"] == "AOI-DXB"


def test_power_dag_accepts_historical_backfill_window(monkeypatch):
    calls = _capture_ingest(monkeypatch)

    nasa_power_ingest_dag._ingest(
        "AOI-DXB", 25.1, 55.2,
        dag_run=SimpleNamespace(conf={"start": "2024-06-01", "end": "20240630"}),
    )

    assert calls[0]["start"] == "20240601"
    assert calls[0]["end"] == "20240630"


def test_power_dag_rejects_reversed_window(monkeypatch):
    calls = _capture_ingest(monkeypatch)

    with pytest.raises(ValueError, match="start date .* is after end date"):
        nasa_power_ingest_dag._ingest(
            "AOI-DXB", 25.1, 55.2,
            dag_run=SimpleNamespace(conf={"start": "2024-07-01", "end": "2024-06-30"}),
        )

    assert calls == []
