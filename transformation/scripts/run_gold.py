"""spark-submit launcher: build every Gold mart to ``s3://gold`` (Task 9).

Delegates to :func:`transformation.batch.gold_lakehouse.run_gold_spark`, which
reuses the pure-Python Gold rules so the cluster path is identical to the
offline demo. Run after the Bronze->Silver jobs:

    spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4 \
        transformation/scripts/run_gold.py
"""

from transformation.batch.gold_lakehouse import run_gold_spark


def main() -> None:
    print("[run_gold] starting Silver->Gold lakehouse materialisation")
    run_gold_spark()
    print("[run_gold] completed Silver->Gold lakehouse materialisation")


if __name__ == "__main__":
    main()
