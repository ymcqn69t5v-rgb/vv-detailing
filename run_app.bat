@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Spoustim webovou aplikaci...
echo [INFO] Pockej 2 sekundy, pak se otevre prohlizec na http://127.0.0.1:8080
start "" cmd /c "timeout /t 2 >nul && start "" "http://127.0.0.1:8080""
python ui_app.py

endlocal
