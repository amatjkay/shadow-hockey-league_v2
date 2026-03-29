.PHONY: install dev test lint format clean run

# Install dependencies
install:
pip install -r requirements.txt

# Install development dependencies
dev: install
pip install flake8 black isort pytest pytest-cov

# Run tests
test:
python -m unittest discover -v

# Run tests with coverage
coverage:
python -m unittest discover --coverage

# Lint code
lint:
flake8 . --count --show-source --statistics

# Format code
format:
black .
isort .

# Clean up
clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

# Run development server
run:
python app.py

# Run production server with gunicorn
prod:
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"

# Initialize database
init-db:
python init_db.py

# Seed database
seed-db:
python seed_db.py
