"""WSGI configuration for PythonAnywhere deployment.

This file is used by PythonAnywhere to serve the Flask application.
"""
import sys
import os

# Add project root to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Load environment variables from .env file (if exists)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_home, '.env'))
except ImportError:
    pass  # python-dotenv not installed, use system env vars only

# Create Flask application
from app import create_app

application = create_app()
