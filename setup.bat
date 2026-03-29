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
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo.

echo [2/3] Initializing database...
python scripts\validate_db.py --init --seed
if errorlevel 1 (
    echo ERROR: Failed to initialize database
    exit /b 1
)
echo.

echo [3/3] Setup complete!
echo.
echo ==========================================
echo To start the server, run:
echo   python app.py
echo ==========================================
echo.
