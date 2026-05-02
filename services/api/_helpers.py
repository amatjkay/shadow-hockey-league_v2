"""Shared helpers for the :mod:`services.api` package.

Contains pagination + field-projection utilities used by every list endpoint.
Kept module-private to avoid coupling, but re-exported via
``services.api.__init__`` for backwards compatibility.
"""

from __future__ import annotations

import math

from flask import request
from sqlalchemy.orm import Session

from models import db


def get_session() -> Session:
    """Return the current Flask-SQLAlchemy session."""
    return db.session


def _parse_fields_param() -> set[str] | None:
    """Parse the optional ``?fields=`` query parameter.

    Clients can request a subset of fields to minimise response size, e.g.
    ``GET /api/managers?fields=id,name,country_code``. ``id`` is always kept
    so callers can correlate items.

    Returns:
        Set of field names (lower-case, ``id`` injected) or ``None`` when the
        parameter is absent / empty (in which case the caller emits the full
        record).
    """
    raw = request.args.get("fields", "").strip()
    if not raw:
        return None
    parts = {p.strip() for p in raw.split(",") if p.strip()}
    if not parts:
        return None
    parts.add("id")
    return parts


def _project(record: dict, fields: set[str] | None) -> dict:
    """Return ``record`` projected onto ``fields`` (no-op when ``fields`` is None)."""
    if fields is None:
        return record
    return {k: v for k, v in record.items() if k in fields}


def paginate_query(query, schema, default_per_page: int = 20, max_per_page: int = 100):
    """Apply offset/limit pagination to a query.

    Honours the optional ``?fields=`` query parameter (see ``_parse_fields_param``)
    so clients can request a slim subset of the schema and pay fewer response
    bytes / parse fewer fields.

    Args:
        query: SQLAlchemy query object.
        schema: Schema function to serialise results (must return a ``dict``).
        default_per_page: Default items per page.
        max_per_page: Maximum allowed items per page.

    Returns:
        Tuple of (response_dict, status_code).
    """
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=default_per_page, type=int)

    page = max(1, page)
    per_page = min(max(per_page, 1), max_per_page)

    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 0

    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    fields = _parse_fields_param()

    return {
        "data": [_project(schema(item), fields) for item in items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }, 200
