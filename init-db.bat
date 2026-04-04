@echo off
REM Shadow Hockey League - Database Init Script for Windows
REM Аналог 'make init-db'
REM
REM This script checks the database state before seeding.
REM - If database has data, it will skip seeding (safe mode).
REM - Use 'python seed_db.py --force' to force reseed.

echo ==========================================
echo Shadow Hockey League - Database Init
echo ==========================================
echo.

echo [INFO] Checking database state...
python seed_db.py --check
if errorlevel 1 (
    echo [ERROR] Failed to check database state
    exit /b 1
)

echo.
echo [INFO] Seeding database (safe mode - will skip existing data)...
python seed_db.py
if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    exit /b 1
)

echo.
echo ==========================================
echo Database initialized successfully!
echo ==========================================
echo.
echo To force reseed (WARNING: deletes all data), run:
echo   python seed_db.py --force
echo.
