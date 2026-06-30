"""spark-submit launcher: run a Bronze->Silver Spark job for one entity.

Used by the full-infra run. spark-submit supplies the hadoop-aws jar via
``--packages`` and the S3A/MinIO credentials via ``--conf`` / environment, then
delegates to the shared ``run_spark`` so the cluster path uses the exact same
cleaning rules as the offline demo.

    spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4 \
        --conf spark.sql.extensions= run_silver.py telemetry
"""

import sys

from transformation.batch.bronze_to_silver import run_spark


def main() -> None:
    entity = sys.argv[1] if len(sys.argv) > 1 else "telemetry"
    print(f"[run_silver] starting Bronze->Silver for entity={entity}")
    run_spark(entity)
    print(f"[run_silver] completed Bronze->Silver for entity={entity}")


if __name__ == "__main__":
    main()
