from __future__ import annotations

from datetime import date, datetime, timedelta
import math
from typing import Any


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date()
    return date.fromisoformat(text[:10])


def add_temporal_features(
    rows: list[dict[str, Any]],
    *,
    rolling_windows: dict[str, tuple[int, ...]],
) -> list[dict[str, Any]]:
    if any(window < 1 for windows in rolling_windows.values() for window in windows):
        raise ValueError("Rolling windows must contain positive day counts.")
    if not rows:
        return []

    dated_rows = [(row, _as_date(row["date_key"])) for row in rows]
    grouped: dict[str, list[tuple[dict[str, Any], date]]] = {}
    seen: set[tuple[Any, date]] = set()
    for row, observation_date in dated_rows:
        aoi_key = row.get("aoi_key")
        if aoi_key in (None, ""):
            raise ValueError("Climate serving rows must have an aoi_key.")
        aoi_key = str(aoi_key)
        grain = (aoi_key, observation_date)
        if grain in seen:
            raise ValueError(f"Duplicate climate serving row for AOI/date {grain!r}.")
        seen.add(grain)
        grouped.setdefault(aoi_key, []).append((row, observation_date))

    enriched: list[dict[str, Any]] = []
    for observations in grouped.values():
        observations.sort(key=lambda item: item[1])
        group_outputs = []
        for index, (row, observation_date) in enumerate(observations):
            output = {**row, "aoi_key": str(row["aoi_key"])}
            output["days_since_previous_observation"] = (
                (observation_date - observations[index - 1][1]).days if index else None
            )
            group_outputs.append(output)

        for field, windows in rolling_windows.items():
            prefix = field.removesuffix("_mean").removesuffix("_c")
            previous_value: float | None = None
            previous_date: date | None = None
            starts = dict.fromkeys(windows, 0)
            totals = dict.fromkeys(windows, 0.0)
            counts = dict.fromkeys(windows, 0)
            for index, (row, observation_date) in enumerate(observations):
                current = row.get(field)
                current_value = (
                    float(current)
                    if current is not None and math.isfinite(float(current))
                    else None
                )
                output = group_outputs[index]
                if current_value is None or previous_value is None or previous_date is None:
                    output[f"{prefix}_change_per_day"] = None
                else:
                    elapsed_days = (observation_date - previous_date).days
                    output[f"{prefix}_change_per_day"] = (
                        (current_value - previous_value) / elapsed_days
                        if elapsed_days > 0
                        else None
                    )

                for window_days in windows:
                    cutoff = observation_date - timedelta(days=window_days - 1)
                    while (
                        starts[window_days] <= index
                        and observations[starts[window_days]][1] < cutoff
                    ):
                        expired = observations[starts[window_days]][0].get(field)
                        if expired is not None and math.isfinite(float(expired)):
                            totals[window_days] -= float(expired)
                            counts[window_days] -= 1
                        starts[window_days] += 1

                    if current_value is not None:
                        totals[window_days] += current_value
                        counts[window_days] += 1
                    output[f"{prefix}_{window_days}d_mean"] = (
                        totals[window_days] / counts[window_days]
                        if counts[window_days]
                        else None
                    )

                if current_value is not None:
                    previous_value = current_value
                    previous_date = observation_date
        enriched.extend(group_outputs)
    return enriched
