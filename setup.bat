@echo off
REM Shadow Hockey League - Setup Script for Windows
REM Аналог 'make setup'

echo ==========================================
echo Shadow Hockey League - Setup
echo ==========================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo.

echo [2/3] Checking database state...
python seed_db.py --check
if errorlevel 1 (
    echo [WARN] Could not check database state, attempting seed anyway...
)
echo.

echo [3/3] Seeding database (safe mode)...
python seed_db.py
if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    exit /b 1
)

echo.
echo ==========================================
echo Setup complete!
echo ==========================================
echo.
echo To start the server, run:
echo   run.bat
echo.
echo To force reseed (WARNING: deletes all data), run:
echo   python seed_db.py --force
echo.
