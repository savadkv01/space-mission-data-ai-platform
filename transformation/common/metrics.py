"""Transformation metrics -> Prometheus mapping (Task 16).

We keep an in-process counter/gauge registry that mirrors the Prometheus metric
names used by the platform's monitoring stack. When ``prometheus_client`` is
installed and a job runs under infrastructure, the same names are exported; for
offline runs the registry is a plain dict so tests stay dependency-free.

Metric catalogue (see docs/transformation/16-observability.md):
- ``transform_rows_in_total{job,layer}``
- ``transform_rows_out_total{job,layer}``
- ``transform_rows_rejected_total{job,layer}``
- ``transform_duration_seconds{job}``
- ``transform_data_freshness_seconds{dataset}``
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsSink:
    """A minimal counter/gauge sink, keyed by ``metric{label=value,...}``."""

    values: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def _key(name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        rendered = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{rendered}}}"

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = self._key(name, labels)
        self.values[key] = self.values.get(key, 0.0) + value

    def gauge(self, name: str, value: float, **labels: str) -> None:
        self.values[self._key(name, labels)] = value

    def snapshot(self) -> dict[str, Any]:
        return dict(self.values)


# Canonical metric names referenced by Grafana dashboards.
ROWS_IN = "transform_rows_in_total"
ROWS_OUT = "transform_rows_out_total"
ROWS_REJECTED = "transform_rows_rejected_total"
DURATION = "transform_duration_seconds"
FRESHNESS = "transform_data_freshness_seconds"
