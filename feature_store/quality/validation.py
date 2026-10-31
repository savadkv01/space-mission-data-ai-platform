from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def profile_rows(
    rows: Sequence[Mapping[str, Any]],
    critical_fields: Iterable[str],
) -> dict[str, Any]:
    null_rates = {
        field: (
            sum(row.get(field) is None for row in rows) / len(rows) if rows else None
        )
        for field in critical_fields
    }
    return {
        "row_count": len(rows),
        "null_rates": null_rates,
    }


def validate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    entity_field: str,
    event_timestamp_field: str = "event_timestamp",
    critical_fields: Iterable[str] = (),
    max_null_rate: float = 0.0,
) -> list[str]:
    errors: list[str] = []
    if not 0 <= max_null_rate <= 1:
        raise ValueError("max_null_rate must be between 0 and 1.")
    if not rows:
        return ["required feature source has no rows"]

    profile = profile_rows(rows, critical_fields)
    if any(row.get(entity_field) in (None, "") for row in rows):
        errors.append(f"{entity_field} contains null or empty entity keys")
    if any(row.get(event_timestamp_field) is None for row in rows):
        errors.append(f"{event_timestamp_field} contains null event times")
    for field, null_rate in profile["null_rates"].items():
        if null_rate is not None and null_rate > max_null_rate:
            errors.append(f"{field} null rate {null_rate:.4f} exceeds {max_null_rate:.4f}")
    return errors


def validate_numeric_bounds(
    rows: Sequence[Mapping[str, Any]],
    bounds: Mapping[str, tuple[float, float]],
) -> list[str]:
    errors: list[str] = []
    for field, (minimum, maximum) in bounds.items():
        for index, row in enumerate(rows):
            value = row.get(field)
            if value is None:
                continue
            number = float(value)
            if not math.isfinite(number) or not minimum <= number <= maximum:
                errors.append(
                    f"{field} at row {index} is outside [{minimum}, {maximum}]: {value!r}"
                )
    return errors
