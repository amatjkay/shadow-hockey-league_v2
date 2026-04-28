"""WSGI configuration for PythonAnywhere deployment.

This file is used by PythonAnywhere to serve the Flask application.
"""

import os
import sys

# Add project root to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Create Flask application
from app import create_app

application = create_app()
