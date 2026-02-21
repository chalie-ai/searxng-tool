#!/bin/sh
set -e

echo "[ENTRYPOINT] Starting SearXNG..." >&2

# Generate settings.yml in /tmp (rootfs is read-only, /tmp is tmpfs)
SETTINGS=/tmp/searxng-settings.yml
TEMPLATE=/usr/local/searxng/searx/settings.yml

echo "[ENTRYPOINT] Creating settings from template..." >&2
cp "$TEMPLATE" "$SETTINGS"
SECRET=$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')
sed -i "s/ultrasecretkey/$SECRET/g" "$SETTINGS"

# Ensure json format is enabled (required by handler.py)
if ! grep -q '    - json' "$SETTINGS"; then
    sed -i 's/^    - html$/    - html\n    - json/' "$SETTINGS"
fi

# Point SearXNG to the tmp settings
export SEARXNG_SETTINGS_PATH="$SETTINGS"

# Start granian from SearXNG's directory so it can resolve the local 'searx' module
cd /usr/local/searxng
/usr/local/searxng/.venv/bin/granian searx.webapp:app > /tmp/searxng.log 2>&1 &
SEARXNG_PID=$!
echo "[ENTRYPOINT] Granian PID: $SEARXNG_PID" >&2

# Wait for SearXNG to be ready
python3 << 'PYEOF'
import time, sys
from urllib.request import urlopen

max_attempts = 40
for i in range(max_attempts):
    try:
        resp = urlopen("http://localhost:8080/", timeout=2)
        if resp.status == 200:
            print("[ENTRYPOINT] SearXNG is ready!", file=sys.stderr, flush=True)
            sys.exit(0)
    except Exception as e:
        if i == max_attempts - 1:
            print(f"[ENTRYPOINT] SearXNG not ready after {max_attempts} attempts: {e}", file=sys.stderr, flush=True)
            try:
                with open("/tmp/searxng.log") as f:
                    print("[ENTRYPOINT] Granian log:", file=sys.stderr)
                    print(f.read(), file=sys.stderr, flush=True)
            except Exception:
                pass
            sys.exit(1)
        time.sleep(1)
PYEOF

echo "[ENTRYPOINT] Running handler..." >&2
exec python3 /tool/runner.py "$@"
