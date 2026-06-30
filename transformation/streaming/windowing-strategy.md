# Design — Windowing Strategy

> Spec: [docs/transformation/05-streaming-processing.md](../../docs/transformation/05-streaming-processing.md)

## Windows

| Window | Duration | Slide | Use |
| --- | --- | --- | --- |
| Live health | 1 min | 30 s | overlapping sliding windows for smooth live trend |
| Hourly rollup | 1 hour | tumbling | batch reconciliation |
| Daily KPI | 1 day | tumbling | Gold marts |

## Watermark

`watermark = max(event_time) − 2 min`. Window state retained until watermark passes `window.end`, then result emitted (append mode) and state evicted — bounds memory.

## Late data

| Lateness | Action |
| --- | --- |
| ≤ watermark | included in window |
| > watermark | dropped from streaming state; counted in a metric; recovered by nightly batch |

## Tumbling vs sliding

- **Sliding** (1 min / 30 s) for live dashboards: smoother, overlapping.
- **Tumbling** for KPI rollups: non-overlapping, exact daily/hourly buckets.
