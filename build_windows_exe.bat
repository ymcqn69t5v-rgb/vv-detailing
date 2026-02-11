@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Build Windows EXE (bez nutnosti Pythonu na cilovem PC)
where py >nul 2>&1
if %errorlevel% neq 0 (
  echo [CHYBA] Nenalezen prikaz 'py'. Nainstaluj Python z https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

py -3 -m pip install --upgrade pip pyinstaller
if %errorlevel% neq 0 (
  echo [CHYBA] Instalace PyInstaller selhala.
  pause
  exit /b 1
)

py -3 -m PyInstaller --noconfirm --onefile --name VyhledavacKontaktu --add-data "ui;ui" ui_app.py
if %errorlevel% neq 0 (
  echo [CHYBA] Build EXE selhal.
  pause
  exit /b 1
)

echo.
echo [HOTOVO] EXE je zde:
echo %cd%\dist\VyhledavacKontaktu.exe
echo.
echo Tento .exe muzes poslat dalsim lidem. Spusti appku dvojklikem.
pause
endlocal
