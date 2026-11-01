#!/bin/bash
# Starts the MK1300 V2 app locally and opens it in Chrome (or Edge).
cd "$(dirname "$0")" || exit 1
PORT=8080
URL="http://localhost:$PORT"

if ! command -v node >/dev/null 2>&1; then
  osascript -e 'display dialog "Node.js is needed to run this app. Install it from nodejs.org, then open this file again." buttons {"OK"} default button "OK" with icon caution'
  exit 1
fi

# Start the server only if nothing is already listening on the port.
if ! lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  node scripts/serve.mjs "$PORT" >/dev/null 2>&1 &
  sleep 1
fi

if [ -d "/Applications/Google Chrome.app" ]; then
  open -a "Google Chrome" "$URL"
elif [ -d "/Applications/Microsoft Edge.app" ]; then
  open -a "Microsoft Edge" "$URL"
else
  osascript -e 'display dialog "Please install Google Chrome or Microsoft Edge. Safari cannot connect to keyboards." buttons {"OK"} default button "OK" with icon caution'
  exit 1
fi

echo "MK1300 V2 is running at $URL. Close this window to stop the server."
wait
