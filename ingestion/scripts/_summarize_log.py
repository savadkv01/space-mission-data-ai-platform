import json
import re

with open("/tmp/full_batch_ingest.log", encoding="utf-8", errors="replace") as f:
    text = f.read()

# The JSON result dict is printed last (after all log lines); find its start.
start = text.rindex("\n{\n")
data = json.loads(text[start + 1:])
for k, v in data.items():
    print(k, "->", v.get("records", v.get("error")))
