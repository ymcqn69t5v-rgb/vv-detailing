#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "[INFO] Spouštím webovou aplikaci..."
echo "[INFO] Za 2 sekundy se zkusí otevřít: http://127.0.0.1:8080"
(
  sleep 2
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:8080" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:8080" >/dev/null 2>&1 || true
  fi
) &

python3 ui_app.py
