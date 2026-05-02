"""Internal rate-limit helpers for the admin login flow.

Module-level state is intentional: ``_login_attempts`` is a process-local
sliding-window bucket, scoped per-IP. Tests reach into it via
``services.admin._login_attempts`` (re-exported through ``services.admin``).
"""

from __future__ import annotations

import time

from flask import request

_login_attempts: dict[str, list[float]] = {}


def _get_client_ip() -> str:
    """Return the client IP for rate-limit bucketing.

    `request.remote_addr` has already been resolved to the real client IP
    by the ProxyFix middleware wired up in :func:`app.create_app` (see
    `app.py` and `docs/ARCHITECTURE.md` § Production deployment), which
    walks `X-Forwarded-For` from the right using the configured trusted-
    proxy count.

    We must **not** re-parse `X-Forwarded-For` ourselves. The leftmost
    entry of that header is user-controllable, so trusting it would let
    an attacker rotate the apparent IP on every login attempt and bypass
    the per-IP rate-limit entirely.

    For deployments that don't sit behind a proxy, set ``PROXY_FIX_X_FOR=0``
    and ``request.remote_addr`` is the raw socket address, which is also
    the correct rate-limit key.
    """
    return request.remote_addr or "unknown"


def _is_login_rate_limit_ok(max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Return True iff the caller is *under* the failed-login budget.

    Does NOT record an attempt - successful logins should not consume
    the budget. Pair with :func:`_record_failed_login_attempt` on the
    failure branch.
    """
    ip = _get_client_ip()
    now = time.time()

    bucket = _login_attempts.setdefault(ip, [])
    # Drop attempts that have aged out of the window.
    bucket[:] = [t for t in bucket if now - t < window_seconds]

    return len(bucket) < max_attempts


def _record_failed_login_attempt() -> None:
    """Record a failed login for rate-limiting purposes."""
    ip = _get_client_ip()
    _login_attempts.setdefault(ip, []).append(time.time())


def _check_login_rate_limit(max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Backward-compatible combined check + record.

    Kept for any external callers; the admin login flow now uses the
    split :func:`_is_login_rate_limit_ok` /
    :func:`_record_failed_login_attempt` API so successful logins don't
    consume the budget.
    """
    if not _is_login_rate_limit_ok(max_attempts, window_seconds):
        return False
    _record_failed_login_attempt()
    return True
