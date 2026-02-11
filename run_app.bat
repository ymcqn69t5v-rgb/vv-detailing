@echo off
setlocal
cd /d "%~dp0"

set PORT=8765
echo [INFO] Spoustim webovou aplikaci na portu %PORT%...
echo [INFO] Pockej 2 sekundy, pak se otevre prohlizec na http://127.0.0.1:%PORT%
start "" cmd /c "timeout /t 2 >nul && start "" "http://127.0.0.1:%PORT%""
python ui_app.py --host 127.0.0.1 --port %PORT%

endlocal
