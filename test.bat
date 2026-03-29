@echo off
REM Shadow Hockey League - Test Script for Windows
REM Аналог 'make test'

echo Running tests...
echo.
python -m unittest discover -v
