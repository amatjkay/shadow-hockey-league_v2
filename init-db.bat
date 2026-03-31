@echo off
REM Shadow Hockey League - Database Init Script for Windows
REM Аналог 'make init-db'

echo Initializing database...
echo.
python seed_db.py
echo.
echo Database initialized successfully!
