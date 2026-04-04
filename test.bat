@echo off
REM Shadow Hockey League - Test Script for Windows
REM Аналог 'make test'

echo ==========================================
echo Shadow Hockey League - Running Tests
echo ==========================================
echo.

echo [INFO] Running pytest...
python -m pytest tests/ -v --tb=short

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Some tests failed!
    echo ==========================================
    exit /b 1
)

echo.
echo ==========================================
echo All tests passed!
echo ==========================================
echo.
