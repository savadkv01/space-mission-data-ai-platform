"""Spark session factory tuned for a 16 GB laptop (Task 14).

PySpark is an *optional* dependency. The pure-Python transformation rules in this
package never import this module, so unit tests and the offline demo run without
Java/Spark installed. Spark job entrypoints call :func:`build_spark_session`
only when infrastructure is available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from transformation.config.settings import settings

if TYPE_CHECKING:  # pragma: no cover
    from pyspark.sql import SparkSession


def build_spark_session(app_suffix: str = "") -> "SparkSession":
    """Create a local-mode SparkSession with laptop-friendly tuning.

    Tuning rationale (see docs/transformation/14-performance.md):
    - ``local[*]`` uses all cores but a single JVM (low overhead).
    - small shuffle partition count avoids many tiny tasks on a laptop.
    - adaptive query execution coalesces shuffle partitions automatically.
    - Kryo serialization + Snappy Parquet for compact, fast IO.
    """
    from pyspark.sql import SparkSession  # local import: optional dependency

    cfg = settings.spark
    name = f"{cfg.app_name}{('-' + app_suffix) if app_suffix else ''}"
    builder = (
        SparkSession.builder.appName(name)
        .master(cfg.master)
        .config("spark.driver.memory", cfg.driver_memory)
        .config("spark.executor.memory", cfg.executor_memory)
        .config("spark.sql.shuffle.partitions", str(cfg.shuffle_partitions))
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.session.timeZone", "UTC")
    )
    # S3A / MinIO wiring (only used when reading/writing the object store).
    lake = settings.lake
    builder = (
        builder.config("spark.hadoop.fs.s3a.endpoint", lake.endpoint)
        .config("spark.hadoop.fs.s3a.access.key", lake.access_key)
        .config("spark.hadoop.fs.s3a.secret.key", lake.secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    )
    return builder.getOrCreate()
