"""spark-submit launcher: run the Kafka -> Silver structured streaming job.

Mirrors ``run_silver.py`` for the streaming path. spark-submit supplies both the
Kafka and hadoop-aws connectors via ``--packages``; the job reads the cleaned
telemetry topic, windows it, and writes windowed Silver aggregates to MinIO.

    spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4 \
        --conf spark.sql.extensions= run_stream.py
"""

from transformation.streaming.spark_streaming import run


def main() -> None:
    print("[run_stream] starting Kafka -> Silver streaming job")
    run()


if __name__ == "__main__":
    main()
