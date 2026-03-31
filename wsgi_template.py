"""WSGI configuration template for PythonAnywhere deployment.

COPY THIS FILE TO: /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py

REPLACE 'YOUR_USERNAME' WITH YOUR PYTHONANYWHERE USERNAME!

This template uses absolute paths to avoid database path issues.
"""

import sys
import os

# ==============================================================================
# CONFIGURATION - EDIT THESE VALUES
# ==============================================================================

# Your PythonAnywhere username
USERNAME = 'YOUR_USERNAME'  # ← ЗАМЕНИ НА СВОЙ ЛОГИН!

# Project paths (absolute - always use absolute paths on server!)
project_home = f'/home/{USERNAME}/shadow-hockey-league_v2'

# ==============================================================================
# DO NOT EDIT BELOW THIS LINE (обычно не нужно менять)
# ==============================================================================

# Add project to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables for Flask
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = f'sqlite:///{project_home}/dev.db'
os.environ['LOG_LEVEL'] = 'INFO'

# IMPORTANT: Generate a unique SECRET_KEY for production!
# Run this command to generate:
#   python -c "import secrets; print(secrets.token_hex(32))"
# Then paste the result below:
os.environ['SECRET_KEY'] = 'GENERATE_AND_PASTE_SECRET_KEY_HERE'

# Import Flask application
from app import create_app
application = create_app()
