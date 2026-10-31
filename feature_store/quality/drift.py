from __future__ import annotations

import math
from collections.abc import Sequence


def population_stability_index(
    expected: Sequence[float],
    actual: Sequence[float],
    *,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    if bins < 2:
        raise ValueError("bins must be at least 2.")
    if not expected or not actual:
        raise ValueError("Expected and actual samples must both be non-empty.")
    if any(not math.isfinite(value) for value in (*expected, *actual)):
        raise ValueError("Drift samples must contain only finite numbers.")

    sorted_expected = sorted(expected)
    edges = [
        sorted_expected[min(int(len(sorted_expected) * index / bins), len(sorted_expected) - 1)]
        for index in range(1, bins)
    ]
    expected_counts = [0] * bins
    actual_counts = [0] * bins
    for value in expected:
        expected_counts[sum(value > edge for edge in edges)] += 1
    for value in actual:
        actual_counts[sum(value > edge for edge in edges)] += 1

    expected_total = len(expected)
    actual_total = len(actual)
    score = 0.0
    for expected_count, actual_count in zip(expected_counts, actual_counts, strict=True):
        expected_share = max(expected_count / expected_total, epsilon)
        actual_share = max(actual_count / actual_total, epsilon)
        score += (actual_share - expected_share) * math.log(actual_share / expected_share)
    return score


def drift_status(score: float, *, warning_threshold: float = 0.2) -> str:
    if warning_threshold <= 0:
        raise ValueError("warning_threshold must be positive.")
    return "warn" if score >= warning_threshold else "pass"
