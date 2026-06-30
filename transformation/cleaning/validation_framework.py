"""Inter-layer validation checkpoints (Task 12).

A checkpoint runs a set of declarative expectations against a batch of records
*after* a transform and *before* the output is published. If a critical
expectation fails, the batch is held (the orchestrator fails the task); warnings
are logged but allow promotion. This is a tiny, dependency-free analogue of
Great Expectations suited to a laptop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Expectation:
    name: str
    predicate: Callable[[list[dict[str, Any]]], bool]
    severity: str = "critical"  # "critical" | "warn"
    description: str = ""


@dataclass
class CheckpointResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


def expect_row_count_min(minimum: int) -> Expectation:
    return Expectation(
        name=f"row_count>={minimum}",
        predicate=lambda rows: len(rows) >= minimum,
        description="Batch is not unexpectedly empty.",
    )


def expect_not_null(field_name: str, severity: str = "critical") -> Expectation:
    return Expectation(
        name=f"not_null:{field_name}",
        predicate=lambda rows: all(r.get(field_name) not in (None, "") for r in rows),
        severity=severity,
        description=f"{field_name} is populated on every row.",
    )


def expect_unique(key_fields: list[str]) -> Expectation:
    def _unique(rows: list[dict[str, Any]]) -> bool:
        seen = set()
        for r in rows:
            k = tuple(r.get(f) for f in key_fields)
            if k in seen:
                return False
            seen.add(k)
        return True

    return Expectation(
        name=f"unique:{'+'.join(key_fields)}",
        predicate=_unique,
        description="Natural key is unique after dedup.",
    )


def expect_value_in_range(field_name: str, lo: float, hi: float,
                          severity: str = "critical") -> Expectation:
    def _ranged(rows: list[dict[str, Any]]) -> bool:
        for r in rows:
            v = r.get(field_name)
            if v is None:
                continue
            try:
                if not (lo <= float(v) <= hi):
                    return False
            except (TypeError, ValueError):
                return False
        return True

    return Expectation(
        name=f"range:{field_name}[{lo},{hi}]",
        predicate=_ranged,
        severity=severity,
        description=f"{field_name} within [{lo}, {hi}].",
    )


def run_checkpoint(rows: list[dict[str, Any]], expectations: list[Expectation],
                   name: str = "checkpoint") -> CheckpointResult:
    failures: list[str] = []
    warnings: list[str] = []
    for exp in expectations:
        try:
            ok = exp.predicate(rows)
        except Exception as exc:  # noqa: BLE001 — a broken expectation is a failure
            ok = False
            exp_msg = f"{exp.name}: error {exc}"
        else:
            exp_msg = exp.name
        if not ok:
            (failures if exp.severity == "critical" else warnings).append(exp_msg)
    return CheckpointResult(
        passed=not failures,
        failures=failures,
        warnings=warnings,
        stats={"checkpoint": name, "rows": len(rows), "expectations": len(expectations)},
    )
