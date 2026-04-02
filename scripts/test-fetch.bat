@echo off
REM Test Fetch MCP Script for Shadow Hockey League

echo ========================================
echo Testing Fetch MCP Server
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv is not installed
    echo Installing uv...
    pip install uv -q
)

echo [INFO] uv found: 
uv --version
echo.

REM Test fetch server
echo [INFO] Testing mcp-server-fetch...
echo.

REM Test local health endpoint (if app is running)
echo [TEST 1] Checking local health endpoint...
curl -s http://localhost:5000/health 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Health endpoint accessible
) else (
    echo [SKIP] Application not running on localhost:5000
)
echo.

REM Test production endpoint
echo [TEST 2] Checking production endpoint...
curl -s -o nul -w "HTTP Status: %%{http_code}\n" https://shadow-hockey-league.ru/health 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Production endpoint accessible
) else (
    echo [ERROR] Production endpoint not accessible
)
echo.

REM Test fetch MCP server directly
echo [TEST 3] Testing fetch MCP server...
uvx mcp-server-fetch --help >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] mcp-server-fetch is working
) else (
    echo [ERROR] mcp-server-fetch failed
)
echo.

echo ========================================
echo Testing complete!
echo ========================================
echo.
echo To use Fetch MCP in AI assistant:
echo   1. Make sure .qwen/mcp.json has fetch enabled
echo   2. Ask AI: "Check http://localhost:5000/health"
echo   3. Or: "Get metrics from https://shadow-hockey-league.ru/metrics"
