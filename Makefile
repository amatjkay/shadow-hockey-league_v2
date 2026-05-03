.PHONY: install dev test lint format clean clean-db run validate init-db seed-db setup mcp-install audit-deps

# ==============================================================================
# INSTALLATION
# ==============================================================================

# Use venv binaries if available
VENV_BIN = venv/bin/

# Install dependencies
install:
	$(VENV_BIN)pip install -r requirements.txt

# Install development dependencies
dev: install
	$(VENV_BIN)pip install -r requirements-dev.txt

# Install MCP server packages locally (replaces vendored mcp-servers/ that used to be tracked)
mcp-install:
	@if [ ! -f mcp-servers/package.json ]; then \
		echo "mcp-servers/package.json not found; skipping (run npm init -y in mcp-servers/ first)"; \
		exit 0; \
	fi
	cd mcp-servers && npm install --no-audit --no-fund

# ==============================================================================
# TESTING
# ==============================================================================

# Run tests
test:
	$(VENV_BIN)pytest tests -v -n auto

# Run tests with coverage
coverage:
	$(VENV_BIN)pytest --cov=services --cov=blueprints --cov=app --cov=models tests/

# ==============================================================================
# CODE QUALITY
# ==============================================================================

# Lint code
lint:
	$(VENV_BIN)flake8 . --count --show-source --statistics

# Format code
format:
	$(VENV_BIN)black .
	$(VENV_BIN)isort .

# Run all quality checks
check:
	$(VENV_BIN)black --check .
	$(VENV_BIN)isort --check-only .
	$(VENV_BIN)flake8 . --count --show-source --statistics
	@echo "[skip] mypy currently disabled in CI; tracked as type-debt cleanup"

# Performance benchmark
benchmark:
	PYTHONPATH=. $(VENV_BIN)python scripts/benchmark.py

# Data integrity audit
audit:
	PYTHONPATH=. $(VENV_BIN)python scripts/audit_data.py

# Dependency security audit (scans installed packages for known CVEs).
audit-deps:
	$(VENV_BIN)pip-audit -r requirements.txt -r requirements-dev.txt

# ==============================================================================
# DATABASE
# ==============================================================================

# Validate database setup
validate:
	python seed_db.py

# Initialize database (create tables + seed)
init-db:
	python seed_db.py

# Seed database with initial data
seed-db:
	python seed_db.py

# Clean database (remove all data)
clean-db:
	python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.drop_all(); db.create_all(); print('Database cleaned')"

# Full setup (install + init-db)
setup: install init-db
	@echo ""
	@echo "=========================================="
	@echo "Setup complete!"
	@echo "=========================================="
	@echo ""
	@echo "To start the server:"
	@echo "  make run"
	@echo "  # or"
	@echo "  python app.py"
	@echo ""

# ==============================================================================
# CLEANUP
# ==============================================================================

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

# ==============================================================================
# RUNNING
# ==============================================================================

# Run development server
run:
	python app.py

# Run production server with gunicorn
prod:
	gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
