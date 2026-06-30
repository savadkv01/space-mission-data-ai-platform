#!/bin/sh
# Inspect Spark Structured Streaming progress from the job log.
echo "== progress reports =="
grep -ac 'made progress' /tmp/stream.log
echo "== numInputRows per batch =="
grep -ao 'numInputRows" : [0-9]*' /tmp/stream.log
echo "== latest watermarks =="
grep -ao 'watermark" : "[^"]*"' /tmp/stream.log | tail -5
echo "== errors =="
grep -ac 'STREAM_FAILED\|No resolvable bootstrap' /tmp/stream.log
