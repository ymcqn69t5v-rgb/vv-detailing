@echo off
setlocal
cd /d "%~dp0"

set APP_DIR=
if exist "ui_app.py" (
  set APP_DIR=%CD%
) else if exist "vv-detailing\ui_app.py" (
  set APP_DIR=%CD%\vv-detailing
)

if "%APP_DIR%"=="" (
  echo [CHYBA] Nenasel jsem soubor ui_app.py.
  echo.
  echo Tento build script musi byt ve stejne slozce jako projektove soubory,
  echo nebo o uroven vys vedle slozky vv-detailing.
  echo.
  echo Ocekavane soubory:
  echo   - ui_app.py
  echo   - company_lookup.py
  echo   - ui\index.html
  echo.
  echo Aktualni slozka: %CD%
  pause
  exit /b 1
)

cd /d "%APP_DIR%"

echo [INFO] Build Windows EXE (bez nutnosti Pythonu na cilovem PC)
echo [INFO] Projektova slozka: %CD%

if not exist "ui_app.py" (
  echo [CHYBA] Chybi ui_app.py v projektove slozce.
  pause
  exit /b 1
)

if not exist "ui\index.html" (
  echo [CHYBA] Chybi slozka ui nebo soubor ui\index.html.
  pause
  exit /b 1
)

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

py -3 -m PyInstaller --noconfirm --onefile --name VyhledavacKontaktu --add-data "ui;ui" "ui_app.py"
if %errorlevel% neq 0 (
  echo [CHYBA] Build EXE selhal.
  pause
  exit /b 1
)

echo.
echo [HOTOVO] EXE je zde:
echo %CD%\dist\VyhledavacKontaktu.exe
echo.
echo Tento .exe muzes poslat dalsim lidem. Spusti appku dvojklikem.
pause
endlocal
