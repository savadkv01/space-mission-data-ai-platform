from __future__ import annotations

from transformation.scripts.run_local_demo import run


def test_demo_runs_offline_end_to_end():
    summary = run(records=40)
    assert summary["silver"]["telemetry"] > 0
    assert summary["gold"]["satellite_health_rows"] > 0
    assert summary["features"]["sat_health"] > 0
    assert summary["checkpoint_passed"] is True
