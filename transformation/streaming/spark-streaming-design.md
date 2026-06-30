# Design — Spark Structured Streaming

> Code: [spark_streaming.py](spark_streaming.py) · Spec: [docs/transformation/05-streaming-processing.md](../../docs/transformation/05-streaming-processing.md)

## Pipeline

`Kafka(telemetry.satellite.cleaned)` → `from_json` → `withWatermark(2 min)` → `window(1 min, slide 30 s) groupBy satellite_id` → `agg(samples, anomaly_samples)` → `writeStream` Parquet (append) + checkpoint.

## Config (from `settings.streaming`)

| Param | Default |
| --- | --- |
| watermark_delay | 2 minutes |
| window_duration | 1 minute |
| slide_duration | 30 seconds |
| trigger_interval | 30 seconds |
| output mode | append |

## Guarantees

- Exactly-once via checkpoint dir (offsets + window state).
- Bounded state via watermark → laptop-safe.
- Late events beyond watermark dropped from state (kept in Bronze for batch).

PySpark is imported only inside `run()`, so the module imports cleanly without Spark.
