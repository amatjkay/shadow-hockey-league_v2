@echo off
REM Shadow Hockey League - Database Init Script for Windows
REM Аналог 'make init-db'

echo Initializing database...
echo.
python scripts\validate_db.py --init --seed
echo.
echo Database initialized successfully!
