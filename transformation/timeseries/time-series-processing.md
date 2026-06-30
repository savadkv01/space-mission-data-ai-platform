# Time-Series Processing

> Code: [time_series.py](time_series.py) · Spec: [docs/transformation/11-time-series.md](../../docs/transformation/11-time-series.md)

## Primitives

| Function | Purpose |
| --- | --- |
| `parse_ts` | parse to UTC datetime |
| `floor_to_window` / `window_key` | align to minute/hour/day boundary |
| `resample_mean` | down-sample irregular series to fixed-window means |
| `find_gaps` | detect missing-timestamp gaps + estimate missing count |
| `interpolate_linear` | fill small gaps |
| `rolling_mean` | trailing smoothing for drift/stability features |

## Gap policy

| Gap size | Action |
| --- | --- |
| small (≤ tolerance) | `interpolate_linear` |
| large | leave as gap, flag (no fabricated data) |

## Downstream

Regularized, gap-aware series + rolling stats feed the anomaly-detection features and the cleaning-layer outlier flags — the preprocessing contract for the Phase 10+ anomaly model.
