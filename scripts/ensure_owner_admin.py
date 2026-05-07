"""Idempotently provision the project owner's permanent super-admin.

Reads ``OWNER_ADMIN_USER`` and ``OWNER_ADMIN_PASSWORD`` from the
environment and either:

* creates a new ``AdminUser`` row with role ``super_admin``, or
* resets the password / role on an existing row with that username.

Both env vars are required; the script exits with a non-zero status
otherwise. Passwords are never logged. The script is safe to re-run on
every Devin session start, every CI bootstrap, every prod deploy:
running it twice is a no-op (modulo a password rotation).

Usage::

    OWNER_ADMIN_USER=alice \\
    OWNER_ADMIN_PASSWORD=... \\
    python scripts/ensure_owner_admin.py

This is intentionally separate from ``scripts/create_e2e_admin.py``
(which provisions the dedicated ``e2e_admin`` used by the Playwright
suite). The owner admin is for humans logging into ``/admin/`` in the
deployed environment.
"""

from __future__ import annotations

import os
import sys

# Make the project root importable when invoked via ``python scripts/...``.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from models import AdminUser, db  # noqa: E402


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.stderr.write(
            f"[error] {name} is not set. Set OWNER_ADMIN_USER and "
            "OWNER_ADMIN_PASSWORD (e.g. via Devin org/user secrets) before "
            "invoking this script.\n"
        )
        sys.exit(2)
    return value


def main() -> int:
    username = _require_env("OWNER_ADMIN_USER")
    password = _require_env("OWNER_ADMIN_PASSWORD")

    app = create_app()
    with app.app_context():
        existing = AdminUser.query.filter_by(username=username).first()
        if existing is not None:
            existing.set_password(password)
            existing.role = AdminUser.ROLE_SUPER_ADMIN
            db.session.commit()
            print(f"[ok] reset password & role for owner admin: {username}")
            return 0

        user = AdminUser(username=username, role=AdminUser.ROLE_SUPER_ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"[ok] created owner super_admin: {username}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
