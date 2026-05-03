"""Idempotently provision the dedicated admin user used by the e2e smoke suite.

The Playwright script in ``tests/e2e/test_smoke.py`` logs in as a dedicated
super-admin so it can exercise every Flask-Admin model view. CI calls this
helper before launching the dev server so the credentials always exist.

Usage::

    E2E_ADMIN_USER=e2e_admin \\
    E2E_ADMIN_PASS=e2e-pass-1234 \\
    python scripts/create_e2e_admin.py

The defaults match the defaults baked into ``tests/e2e/test_smoke.py``;
override via env vars if you need different credentials.
"""

from __future__ import annotations

import os
import sys

# Make the project root importable when invoked via `python scripts/...`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from models import AdminUser, db  # noqa: E402


def main() -> int:
    username = os.environ.get("E2E_ADMIN_USER", "e2e_admin")
    password = os.environ.get("E2E_ADMIN_PASS", "e2e-pass-1234")

    app = create_app()
    with app.app_context():
        existing = AdminUser.query.filter_by(username=username).first()
        if existing is not None:
            # Re-set the password so a stale row from a previous CI run
            # cannot block a re-run with rotated credentials.
            existing.set_password(password)
            existing.role = AdminUser.ROLE_SUPER_ADMIN
            db.session.commit()
            print(f"[ok] reset password for existing e2e admin: {username}")
            return 0

        user = AdminUser(
            username=username,
            role=AdminUser.ROLE_SUPER_ADMIN,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"[ok] created e2e admin: {username}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
