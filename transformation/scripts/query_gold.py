"""Ad-hoc Gold layer verification query (DuckDB warehouse)."""
import duckdb

con = duckdb.connect("/tmp/space.duckdb")

tables = [
    r[0]
    for r in con.execute(
        "select table_schema || '.' || table_name "
        "from information_schema.tables "
        "where table_schema in ('main_gold', 'main_staging')"
    ).fetchall()
]
print("TABLES:", tables)
print()

for tbl in ("main_gold.fact_sat_health", "main_gold.fact_weather_impact"):
    n = con.execute(f"select count(*) from {tbl}").fetchone()[0]
    cur = con.execute(f"select * from {tbl} limit 5")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(f"=== {tbl}  ({n} rows) ===")
    print(" | ".join(cols))
    print("-" * 80)
    for row in rows:
        print(" | ".join(str(v) for v in row))
    print()
