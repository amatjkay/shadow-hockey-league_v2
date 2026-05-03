"""Shared type aliases used across the services package.

Kept in a separate module to avoid circular imports between services and to
provide a single place to evolve the project's typing conventions.
"""

from __future__ import annotations

from typing import Union

from sqlalchemy.orm import Session, scoped_session

# Flask-SQLAlchemy exposes ``db.session`` as a ``scoped_session`` proxy that forwards
# every call to a thread-local ``Session``. Validators / helpers that take a session
# should accept either, since callers may pass the bare ``Session`` (e.g. in tests
# that build their own session) or the Flask-SQLAlchemy proxy (in request handlers).
SessionLike = Union[Session, scoped_session]
