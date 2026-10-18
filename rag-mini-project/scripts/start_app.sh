#!/usr/bin/env bash
# Start procedure: build the index if missing/stale, then launch Streamlit in the background (PID in artifacts/streamlit.pid).
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8501}"
python scripts/build_index.py > /dev/null 2>&1
nohup streamlit run app.py --server.headless true --server.port "$PORT" --browser.gatherUsageStats false > artifacts/streamlit.log 2>&1 &
echo $! > artifacts/streamlit.pid
echo "App starting on http://localhost:$PORT  (log: artifacts/streamlit.log, stop with scripts/stop_app.sh)"
