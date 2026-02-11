@echo off
setlocal
cd /d "%~dp0"

set PORT=8765
echo [INFO] Spoustim webovou aplikaci na portu %PORT%...
echo [INFO] Pockej 2 sekundy, pak se otevre prohlizec na http://127.0.0.1:%PORT%
start "" cmd /c "timeout /t 2 >nul && start \"\" \"http://127.0.0.1:%PORT%\""

where py >nul 2>&1
if %errorlevel%==0 (
  py -3 ui_app.py --host 127.0.0.1 --port %PORT%
  goto :end
)

where python >nul 2>&1
if %errorlevel%==0 (
  python ui_app.py --host 127.0.0.1 --port %PORT%
  goto :end
)

echo.
echo [CHYBA] Python neni nainstalovany nebo neni v PATH.
echo [TIP] Nainstaluj Python z https://www.python.org/downloads/windows/
echo [TIP] Pri instalaci zatrhni "Add python.exe to PATH".
echo [TIP] Pak spust znovu tento soubor.
pause

:end
endlocal
