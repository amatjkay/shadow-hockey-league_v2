"""Shared Flask extension instances.

Putting extension singletons in their own module avoids the two-Limiter problem
where ``app.py`` and ``services/api.py`` would each create their own
``Flask-Limiter`` instance and the second ``init_app`` call silently overwrites
the first in ``app.extensions``.

The single ``limiter`` defined here is bound to the Flask app once in
``app.register_extensions`` and is reused for both global default limits
and per-route ``@limiter.limit(...)`` decorators on the REST API.
"""

from __future__ import annotations

from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _api_key_or_ip() -> str:
    """Pick a rate-limit key.

    Falls back to the client IP address for unauthenticated/non-API traffic
    so the global ``200 per day, 50 per hour`` defaults still apply.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api-key:{api_key}"
    return get_remote_address()


limiter = Limiter(
    key_func=_api_key_or_ip,
    default_limits=["200 per day", "50 per hour"],
    headers_enabled=True,
)
