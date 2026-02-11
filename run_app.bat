@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Spoustim webovou aplikaci...
start "" "http://127.0.0.1:8080"
python ui_app.py

endlocal
