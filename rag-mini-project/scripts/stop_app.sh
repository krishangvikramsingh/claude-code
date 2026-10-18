#!/usr/bin/env bash
# Shutdown procedure: stop the Streamlit process started by start_app.sh.
cd "$(dirname "$0")/.."
if [ -f artifacts/streamlit.pid ]; then kill "$(cat artifacts/streamlit.pid)" 2>/dev/null && echo "stopped" || echo "process not running"; rm -f artifacts/streamlit.pid
else echo "no PID file; if running in a terminal, press Ctrl+C there"; fi
