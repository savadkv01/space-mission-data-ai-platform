"""Read the streaming windowed Silver output from MinIO via DuckDB httpfs."""
import os

import duckdb

con = duckdb.connect()
con.execute("install httpfs; load httpfs;")
con.execute("set s3_endpoint='minio:9000';")
con.execute("set s3_use_ssl=false;")
con.execute("set s3_url_style='path';")
con.execute(f"set s3_access_key_id='{os.environ['MINIO_ROOT_USER']}';")
con.execute(f"set s3_secret_access_key='{os.environ['MINIO_ROOT_PASSWORD']}';")

q = (
    "select window_start, window_end, satellite_id, samples, anomaly_samples "
    "from read_parquet('s3://silver/stream_sat_health_1m/*.parquet') "
    "order by window_start, satellite_id"
)
cur = con.execute(q)
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("stream_sat_health_1m rows:", len(rows))
print(" | ".join(cols))
print("-" * 80)
for r in rows:
    print(" | ".join(str(v) for v in r))
