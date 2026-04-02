@echo off
REM Redis Management Script for Shadow Hockey League

if "%1"=="" goto help

if "%1"=="start" (
    echo [INFO] Starting Redis container...
    docker start shadow-redis
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Redis started successfully
        docker exec shadow-redis redis-cli ping
    ) else (
        echo [ERROR] Failed to start Redis
    )
    goto end
)

if "%1"=="stop" (
    echo [INFO] Stopping Redis container...
    docker stop shadow-redis
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Redis stopped
    ) else (
        echo [ERROR] Failed to stop Redis
    )
    goto end
)

if "%1"=="restart" (
    echo [INFO] Restarting Redis container...
    docker restart shadow-redis
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Redis restarted
        docker exec shadow-redis redis-cli ping
    ) else (
        echo [ERROR] Failed to restart Redis
    )
    goto end
)

if "%1"=="status" (
    echo [INFO] Redis container status:
    docker ps --filter "name=shadow-redis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo.
    echo [INFO] Redis ping:
    docker exec shadow-redis redis-cli ping
    goto end
)

if "%1"=="logs" (
    docker logs shadow-redis
    goto end
)

if "%1"=="cli" (
    echo [INFO] Connecting to Redis CLI...
    docker exec -it shadow-redis redis-cli
    goto end
)

if "%1"=="install" (
    echo [INFO] Installing Redis container...
    docker run -d --name shadow-redis -p 6379:6379 --restart unless-stopped redis:7-alpine
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Redis installed and started
        docker exec shadow-redis redis-cli ping
    ) else (
        echo [ERROR] Failed to install Redis
    )
    goto end
)

if "%1"=="remove" (
    echo [WARNING] This will remove the Redis container and all data!
    set /p confirm="Are you sure? (y/N): "
    if /i "%confirm%"=="y" (
        docker stop shadow-redis
        docker rm shadow-redis
        echo [OK] Redis container removed
    ) else (
        echo [INFO] Operation cancelled
    )
    goto end
)

:help
echo Redis Management Script
echo.
echo Usage: redis.bat [command]
echo.
echo Commands:
echo   start    - Start Redis container
echo   stop     - Stop Redis container
echo   restart  - Restart Redis container
echo   status   - Show Redis status and ping
echo   logs     - Show Redis logs
echo   cli      - Open Redis CLI
echo   install  - Install and start Redis container
echo   remove   - Remove Redis container
echo   help     - Show this help message
echo.

:end
