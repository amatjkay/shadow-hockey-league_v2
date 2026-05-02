"""REST API package for manager management.

Provides the :data:`api` Flask Blueprint registering CRUD endpoints for
countries, managers, and achievements. Routes are split across submodules:

* ``services.api.countries`` — country CRUD
* ``services.api.managers`` — manager CRUD
* ``services.api.achievements`` — achievement CRUD (incl. PATCH helpers)

Public helpers ``paginate_query`` / ``get_session`` are re-exported here for
backwards compatibility with code that imported them from ``services.api``.
"""

from __future__ import annotations

from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")

# Importing submodules registers their routes on the ``api`` Blueprint above.
from services.api import achievements, countries, managers  # noqa: E402,F401

# Re-export helpers used historically as ``from services.api import …``.
from services.api._helpers import (  # noqa: E402
    _parse_fields_param,
    _project,
    get_session,
    paginate_query,
)

__all__ = [
    "api",
    "paginate_query",
    "get_session",
    "_parse_fields_param",
    "_project",
]
