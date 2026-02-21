#!/bin/bash
set -e

# Start SearXNG in background
python -m searxng.server > /tmp/searxng.log 2>&1 &
SEARXNG_PID=$!

# Wait for SearXNG to be ready using Python (max 10 seconds)
python << 'EOF'
import time
import requests

for i in range(20):
    try:
        requests.get("http://localhost:8080/", timeout=1)
        print("SearXNG is ready", flush=True)
        break
    except Exception:
        time.sleep(0.5)
EOF

# Run the handler
exec python runner.py "$@"
