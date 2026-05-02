"""Admin API package for Select2 dropdowns and bulk operations.

Implements API-001 through API-006 from requirements.json. All endpoints
require admin authentication (see :func:`admin_required`).

Routes are registered across submodules:

* ``blueprints.admin_api.lookups`` — countries, managers, seasons, leagues,
  achievement types, single-row points calc.
* ``blueprints.admin_api.achievements`` — bulk-create / bulk-add /
  per-manager listing / delete.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from flask import Blueprint, jsonify
from flask_login import current_user

admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/admin/api")

api_logger = logging.getLogger("shleague.admin_api")


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Ensure the current user has admin privileges."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if not getattr(current_user, "is_admin", False):
            return jsonify({"error": "Access denied"}), 403
        return func(*args, **kwargs)

    return wrapper


# Importing submodules registers their routes on ``admin_api_bp``.
from blueprints.admin_api import achievements, lookups  # noqa: E402,F401

__all__ = ["admin_api_bp", "admin_required", "api_logger"]
