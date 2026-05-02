"""Shared helpers for the :mod:`blueprints.admin_api` package."""

from __future__ import annotations

from typing import Any


def paginate_query(query, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Paginate query results for Select2-style endpoints.

    ``page_size`` is clamped to ``[1, 100]``.
    """
    page_size = min(max(page_size, 1), 100)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_more": page * page_size < total,
        },
    }
