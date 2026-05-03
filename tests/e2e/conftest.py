"""Pytest collection guard for the e2e smoke suite.

The script in this directory (``test_smoke.py``) is *not* a pytest
module - it talks to a live HTTP server via Playwright and writes its
own report under ``$E2E_ARTIFACTS``. We exclude it from the unit-test
``pytest`` collection here; CI runs it as a dedicated job (see
``.github/workflows/deploy.yml`` ``e2e-smoke``).

To run the suite locally, boot the dev server in one shell and call the
``e2e`` make target in another:

    # shell 1
    make run

    # shell 2
    ./venv/bin/python scripts/create_e2e_admin.py
    make e2e
"""

from __future__ import annotations

collect_ignore_glob = ["*.py"]
