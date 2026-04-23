"""Server time utilities."""

from datetime import datetime, timezone


def get_server_time() -> str:
    """Return current UTC time in ISO 8601 format.

    Returns:
        Current UTC time string (e.g., '2026-04-08T12:00:00+00:00').
    """
    return datetime.now(timezone.utc).isoformat()
