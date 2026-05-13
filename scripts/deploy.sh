#!/usr/bin/env bash
# =============================================================================
# Shadow Hockey League - Deployment Script
# =============================================================================
# This script is executed on the production server via SSH by GitHub Actions.
# It is scp'd to the server before execution.
# =============================================================================
set -euo pipefail

APP_DIR="/home/shleague/shadow-hockey-league_v2"
SERVICE_NAME="shadow-hockey-league"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="$APP_DIR/backups"
ENV_FILE="$APP_DIR/.env"
HEALTH_URL="http://127.0.0.1:8000/health"

log_info()  { echo "[INFO]  $1"; }
log_warn()  { echo "[WARN]  $1"; }
log_error() { echo "[ERROR] $1"; }

ROLLBACK_COMMIT=""

rollback() {
    log_warn "=== ROLLING BACK to: $ROLLBACK_COMMIT ==="
    cd "$APP_DIR" || exit 1
    if [ -n "$ROLLBACK_COMMIT" ]; then
        git checkout "$ROLLBACK_COMMIT" 2>&1 || true
    fi
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/dev.db.*.pre-deploy* 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        DB_FILE="$APP_DIR/instance/dev.db"
        log_info "Restoring database from: $LATEST_BACKUP"
        cp "$LATEST_BACKUP" "$DB_FILE" 2>&1 || true
    fi
    # Restart service (with sudo if available)
    if command -v sudo &> /dev/null; then
        sudo systemctl restart "$SERVICE_NAME" 2>&1 || systemctl restart "$SERVICE_NAME" 2>&1 || true
    else
        systemctl restart "$SERVICE_NAME" 2>&1 || true
    fi
    log_warn "Rollback completed."
    return 1
}

trap 'rollback' ERR

cd "$APP_DIR" || exit 1
log_info "=========================================="
log_info "Starting deployment"
log_info "=========================================="

# Record current commit
ROLLBACK_COMMIT=$(git rev-parse HEAD)
log_info "Current commit (for rollback): $ROLLBACK_COMMIT"

# Fetch latest code
log_info "=== Fetching latest code ==="
git fetch origin main 2>&1
git reset --hard origin/main 2>&1
log_info "Deployed commit: $(git log --oneline -1)"

# Clean Python cache
log_info "=== Cleaning Python cache ==="
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create backup dir
mkdir -p "$BACKUP_DIR"

# Backup database
DB_FILE="$APP_DIR/instance/dev.db"
if [ -f "$DB_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/dev.db.$(date +%Y%m%d%H%M%S).pre-deploy"
    cp "$DB_FILE" "$BACKUP_FILE"
    log_info "Database backed up to: $BACKUP_FILE"
else
    log_warn "No database file found, skipping backup"
fi

# Install dependencies
log_info "=== Installing dependencies ==="
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt --quiet --upgrade 2>&1
log_info "Dependencies installed"

# Run migrations
log_info "=== Running database migrations ==="
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    log_info "Loaded .env"
fi

# Validate DATABASE_URL - fix Windows paths if they somehow got into .env
if [ -n "${DATABASE_URL:-}" ]; then
    # Check for Windows-style paths (c:/, d:/, etc.) and replace with correct Linux path
    if echo "$DATABASE_URL" | grep -qiE 'sqlite:///[a-z]:'; then
        log_warn "Detected Windows path in DATABASE_URL, fixing..."
        
        # Ensure .env is writable by current user
        chmod u+w "$ENV_FILE" 2>/dev/null || true
        
        # Fix the .env file permanently
        sed -i "s|DATABASE_URL=sqlite:///.*|DATABASE_URL=sqlite:///${APP_DIR}/instance/dev.db|" "$ENV_FILE"
        log_info "Fixed .env file permanently"
        
        # Reload .env with the fixed path
        set -a
        source "$ENV_FILE"
        set +a
        DATABASE_URL="sqlite:///${APP_DIR}/instance/dev.db"
        log_info "Fixed DATABASE_URL: $DATABASE_URL"
    fi
    
    log_info "Using DATABASE_URL: $DATABASE_URL"
    
    # Check if alembic_version is empty but tables exist (common after restore)
    VERSION=$(python3 -c "
import sqlite3, sys
try:
    c=sqlite3.connect('${APP_DIR}/instance/dev.db')
    v=c.execute('SELECT version_num FROM alembic_version').fetchone()
    tables=[r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]
    c.close()
    if v and v[0]:
        print(v[0])
    elif 'countries' in tables:
        print('NEEDS_STAMP')
    else:
        print('EMPTY')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    print('EMPTY')
" 2>&1)
    
    if [ "$VERSION" = "NEEDS_STAMP" ]; then
        log_warn "Tables exist but alembic_version is empty - stamping to head..."
        DATABASE_URL="$DATABASE_URL" alembic stamp head 2>&1
        log_info "Alembic stamped to head"
    else
        log_info "Running alembic upgrade (version: $VERSION)"
        DATABASE_URL="$DATABASE_URL" alembic upgrade head 2>&1
    fi
else
    log_warn "DATABASE_URL not set, using alembic default"
    alembic upgrade head 2>&1
fi
log_info "Migrations complete"

# Provision/refresh owner admin from .env (idempotent; no-op if vars unset).
# Without this step a fresh prod DB ends up with an empty admin_users table —
# see docs/progress.md (2026-05-08, "Production admin доступ восстановлен").
log_info "=== Ensuring owner admin ==="
if [ -n "${OWNER_ADMIN_USER:-}" ] && [ -n "${OWNER_ADMIN_PASSWORD:-}" ]; then
    DATABASE_URL="${DATABASE_URL:-}" python scripts/ensure_owner_admin.py 2>&1 \
        || log_warn "ensure_owner_admin.py failed; continuing deploy"
else
    log_info "OWNER_ADMIN_USER/OWNER_ADMIN_PASSWORD not set in .env — skipping"
fi

# Wait for Redis before restarting Gunicorn so every worker resolves the
# Redis backend on startup. Without this loop, a slow-starting Redis (or
# a node-local Redis restarted in the same window) lets a worker fall
# back to per-process SimpleCache and produces the TIK-100 season-tab
# hang: cached pages live in one worker's heap, every other worker
# computes the leaderboard from scratch.
log_info "=== Waiting for Redis (max 30s) ==="
REDIS_OK=0
for i in $(seq 1 30); do
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping 2>/dev/null | grep -q '^PONG$'; then
            REDIS_OK=1
            log_info "Redis ping OK via redis-cli (attempt $i)"
            break
        fi
    elif python3 -c "import redis; r=redis.Redis(host='localhost',port=6379,socket_connect_timeout=2); r.ping(); print('ok')" 2>/dev/null | grep -q '^ok$'; then
        REDIS_OK=1
        log_info "Redis ping OK via python (attempt $i)"
        break
    fi
    sleep 1
done
if [ "$REDIS_OK" != "1" ]; then
    log_warn "Redis ping did not succeed within 30s — continuing anyway (Gunicorn workers will fall back to SimpleCache and /health will report cache_backend_type=SimpleCache)"
fi

# Restart service
log_info "=== Restarting $SERVICE_NAME ==="

# Try systemctl with sudo first, fallback to regular systemctl
if command -v sudo &> /dev/null; then
    sudo systemctl restart "$SERVICE_NAME" 2>&1 || systemctl restart "$SERVICE_NAME" 2>&1
else
    systemctl restart "$SERVICE_NAME" 2>&1
fi
sleep 2

# Verify service is active
SERVICE_STATUS=$(systemctl is-active "$SERVICE_NAME" 2>&1)
if [ "$SERVICE_STATUS" = "active" ]; then
    log_info "Service is active"
else
    log_error "Service status: $SERVICE_STATUS"
    exit 1
fi

# Health check
log_info "=== Running health check ==="
for i in 1 2 3 4 5; do
    HEALTH_RESPONSE=$(curl -sf --max-time 10 "$HEALTH_URL" 2>&1) || true
    if [ -n "$HEALTH_RESPONSE" ]; then
        STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'unknown'))
except Exception:
    print('invalid_json')
" 2>/dev/null) || STATUS="parse_error"

        if [ "$STATUS" = "healthy" ]; then
            log_info "Health check PASSED (status: $STATUS)"
            # Warm the leaderboard cache on every Gunicorn worker so the
            # first real user does not pay the cold-cache cost (TIK-100:
            # serial curls observed 18.7s → 27.8s → 5.8s on prod). We hit
            # ``/`` plus one URL per season so each ``_leaderboard_cache_key``
            # variant lands in Redis. ``--max-time 30`` guards against a
            # wedged worker; failures here are logged but non-fatal — the
            # deploy already passed the health check above.
            log_info "=== Warming leaderboard cache ==="
            for url in "http://127.0.0.1:8000/" \
                       "http://127.0.0.1:8000/?season=1" \
                       "http://127.0.0.1:8000/?season=2" \
                       "http://127.0.0.1:8000/?season=3" \
                       "http://127.0.0.1:8000/?season=4" \
                       "http://127.0.0.1:8000/?season=5"; do
                curl -sf -o /dev/null -w "warmup %{url}: %{time_total}s\n" --max-time 30 "$url" \
                    || log_warn "warmup failed for $url (non-fatal)"
            done
            log_info "=========================================="
            log_info "Deployment completed successfully!"
            log_info "Commit: $(git log --oneline -1)"
            log_info "=========================================="
            trap - ERR
            exit 0
        else
            log_warn "Health check attempt $i: status=$STATUS"
        fi
    else
        log_warn "Health check attempt $i: no response"
    fi
    sleep 3
done

log_error "Health check failed after 5 attempts"
exit 1
