"""API authentication middleware.

Provides decorator-based authentication for API endpoints using API keys.
Supports three scopes: read, write, admin with hierarchy (admin > write > read).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable

from flask import jsonify, request

from models import ApiKey, db


def generate_api_key() -> str:
    """Generate a new random API key.

    Returns:
        Random API key string (64 characters)
    """
    return f"shl_{secrets.token_hex(32)}"


def hash_api_key(key: str) -> str:
    """Hash an API key for storage.

    Args:
        key: Plain text API key

    Returns:
        SHA-256 hash of the key
    """
    return hashlib.sha256(key.encode()).hexdigest()


def authenticate_api_key(required_scope: str = "read") -> Callable:
    """Decorator to authenticate API requests using API key.

    Checks:
    1. API key is present in X-API-Key header
    2. API key exists and is not revoked
    3. API key is not expired
    4. API key has required scope

    Args:
        required_scope: Minimum required scope (read/write/admin)

    Returns:
        Decorated function or error response
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            api_key_header = request.headers.get("X-API-Key")

            if not api_key_header:
                return jsonify({"error": "Missing API key. Provide X-API-Key header."}), 401

            # Hash the provided key and look it up
            key_hash = hash_api_key(api_key_header)
            api_key = db.session.query(ApiKey).filter_by(key_hash=key_hash).first()

            if not api_key:
                return jsonify({"error": "Invalid API key."}), 401

            if not api_key.is_active:
                if api_key.revoked:
                    return jsonify({"error": "API key has been revoked."}), 401
                return jsonify({"error": "API key has expired."}), 401

            if not api_key.has_scope(required_scope):
                return (
                    jsonify(
                        {
                            "error": f"Insufficient scope. Required: {required_scope}, has: {api_key.scope}"
                        }
                    ),
                    403,
                )

            # Update last used timestamp
            api_key.last_used_at = datetime.now(timezone.utc)
            db.session.commit()

            # Store key info in request context for logging/auditing
            request.api_key_id = api_key.id
            request.api_key_scope = api_key.scope

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def create_api_key(
    name: str, scope: str = "read", expires_in_days: int | None = None
) -> tuple[str, ApiKey]:
    """Create a new API key.

    Args:
        name: Human-readable name for the key
        scope: Key scope (read/write/admin)
        expires_in_days: Number of days until expiration (None = no expiration)

    Returns:
        Tuple of (plain_text_key, ApiKey_model)
    """
    if scope not in ApiKey.VALID_SCOPES:
        raise ValueError(f"Invalid scope: {scope}. Must be one of {ApiKey.VALID_SCOPES}")

    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)

    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    api_key = ApiKey(
        key_hash=key_hash,
        name=name,
        scope=scope,
        expires_at=expires_at,
    )
    db.session.add(api_key)
    db.session.commit()

    return plain_key, api_key


def revoke_api_key(key_id: int) -> bool:
    """Revoke an API key.

    Args:
        key_id: API key ID

    Returns:
        True if key was revoked, False if not found
    """
    api_key = db.session.query(ApiKey).filter_by(id=key_id).first()
    if not api_key:
        return False

    api_key.revoked = True
    db.session.commit()
    return True
