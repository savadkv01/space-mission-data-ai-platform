"""Spark Structured Streaming transformation (Task 5).

Near-real-time Silver enrichment of the cleaned telemetry topic:

    Kafka(telemetry.satellite.cleaned) -> parse -> windowed aggregation
        -> watermark(late data) -> Silver streaming sink (Parquet + checkpoint)

PySpark is optional: this module only imports it inside :func:`run` so the rest
of the package (and the test suite) import cleanly without Spark. The windowing
parameters come from :data:`settings.streaming` so batch and streaming share one
configuration source.
"""

from __future__ import annotations

from transformation.common.logging_setup import get_logger
from transformation.config.settings import settings

log = get_logger("streaming")


def run() -> None:  # pragma: no cover - requires Spark + Kafka
    """Start the structured streaming telemetry aggregation job.

    Windowing strategy (see docs/transformation/05-streaming-processing.md):
    - tumbling/ sliding window of ``window_duration`` / ``slide_duration``
    - event-time watermark of ``watermark_delay`` bounds state + drops late data
    - micro-batch trigger every ``trigger_interval``; ``update`` output mode
    - checkpointing to ``spark.checkpoint_dir`` for exactly-once state recovery
    """
    from pyspark.sql import functions as F
    from pyspark.sql.types import (
        BooleanType,
        StringType,
        StructField,
        StructType,
        TimestampType,
    )

    from transformation.common.spark import build_spark_session

    st = settings.streaming
    spark = build_spark_session("telemetry-stream")
    spark.sparkContext.setLogLevel("WARN")

    schema = StructType([
        StructField("timestamp", StringType()),
        StructField("satellite_id", StringType()),
        StructField("sensor_type", StringType()),
        StructField("health", StringType()),
        StructField("label_anomaly", BooleanType()),
    ])

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", st.bootstrap_servers)
        .option("subscribe", st.topic_telemetry_cleaned)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = (
        raw.select(F.from_json(F.col("value").cast("string"), schema).alias("r"))
        .select("r.*")
        .withColumn("event_time", F.to_timestamp("timestamp"))
    )

    windowed = (
        parsed.withWatermark("event_time", st.watermark_delay)
        .groupBy(
            F.window("event_time", st.window_duration, st.slide_duration),
            F.col("satellite_id"),
        )
        .agg(
            F.count("*").alias("samples"),
            F.sum(F.when(F.col("label_anomaly"), 1).otherwise(0)).alias("anomaly_samples"),
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "satellite_id",
            "samples",
            "anomaly_samples",
        )
    )

    query = (
        windowed.writeStream.format("parquet")
        .option("path", settings.lake.path("silver", "stream_sat_health_1m"))
        .option("checkpointLocation", f"{settings.spark.checkpoint_dir}/sat_health_1m")
        .outputMode("append")
        .trigger(processingTime=st.trigger_interval)
        .start()
    )
    log.info("streaming query started: %s", query.id)
    query.awaitTermination()


if __name__ == "__main__":  # pragma: no cover
    run()
