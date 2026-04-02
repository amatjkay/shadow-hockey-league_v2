#!/bin/bash
# Redis Management Script for Shadow Hockey League

case "$1" in
    start)
        echo "[INFO] Starting Redis container..."
        docker start shadow-redis
        if [ $? -eq 0 ]; then
            echo "[OK] Redis started successfully"
            docker exec shadow-redis redis-cli ping
        else
            echo "[ERROR] Failed to start Redis"
        fi
        ;;
    stop)
        echo "[INFO] Stopping Redis container..."
        docker stop shadow-redis
        if [ $? -eq 0 ]; then
            echo "[OK] Redis stopped"
        else
            echo "[ERROR] Failed to stop Redis"
        fi
        ;;
    restart)
        echo "[INFO] Restarting Redis container..."
        docker restart shadow-redis
        if [ $? -eq 0 ]; then
            echo "[OK] Redis restarted"
            docker exec shadow-redis redis-cli ping
        else
            echo "[ERROR] Failed to restart Redis"
        fi
        ;;
    status)
        echo "[INFO] Redis container status:"
        docker ps --filter "name=shadow-redis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "[INFO] Redis ping:"
        docker exec shadow-redis redis-cli ping
        ;;
    logs)
        docker logs shadow-redis
        ;;
    cli)
        echo "[INFO] Connecting to Redis CLI..."
        docker exec -it shadow-redis redis-cli
        ;;
    install)
        echo "[INFO] Installing Redis container..."
        docker run -d --name shadow-redis -p 6379:6379 --restart unless-stopped redis:7-alpine
        if [ $? -eq 0 ]; then
            echo "[OK] Redis installed and started"
            docker exec shadow-redis redis-cli ping
        else
            echo "[ERROR] Failed to install Redis"
        fi
        ;;
    remove)
        echo "[WARNING] This will remove the Redis container and all data!"
        read -p "Are you sure? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker stop shadow-redis
            docker rm shadow-redis
            echo "[OK] Redis container removed"
        else
            echo "[INFO] Operation cancelled"
        fi
        ;;
    *)
        echo "Redis Management Script"
        echo ""
        echo "Usage: ./redis.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start Redis container"
        echo "  stop     - Stop Redis container"
        echo "  restart  - Restart Redis container"
        echo "  status   - Show Redis status and ping"
        echo "  logs     - Show Redis logs"
        echo "  cli      - Open Redis CLI"
        echo "  install  - Install and start Redis container"
        echo "  remove   - Remove Redis container"
        echo "  help     - Show this help message"
        echo ""
        ;;
esac
