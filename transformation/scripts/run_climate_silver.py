"""spark-submit launcher: run a climate Bronze->Silver Spark job for one entity.

Companion to ``run_silver.py`` for the atmospheric domain (Phase 9b). Delegates
to :func:`transformation.batch.climate_bronze_to_silver.run_spark`, so the
cluster path uses the exact same cleaning rules as the offline unit tests.

    spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4 \
        --conf spark.sql.extensions= run_climate_silver.py air_quality
"""

import sys

from transformation.batch.climate_bronze_to_silver import run_spark


def main() -> None:
    entity = sys.argv[1] if len(sys.argv) > 1 else "air_quality"
    print(f"[run_climate_silver] starting Bronze->Silver for entity={entity}")
    run_spark(entity)
    print(f"[run_climate_silver] completed Bronze->Silver for entity={entity}")


if __name__ == "__main__":
    main()
