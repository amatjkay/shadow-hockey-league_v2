.PHONY: install dev test lint format clean clean-db run validate init-db seed-db setup

# ==============================================================================
# INSTALLATION
# ==============================================================================

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
dev: install
	pip install flake8 black isort pytest pytest-cov

# ==============================================================================
# TESTING
# ==============================================================================

# Run tests
test:
	python -m pytest tests -v -n auto

# Run tests with coverage
coverage:
	python -m unittest discover --coverage

# ==============================================================================
# CODE QUALITY
# ==============================================================================

# Lint code
lint:
	flake8 . --count --show-source --statistics

# Format code
format:
	black .
	isort .

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
