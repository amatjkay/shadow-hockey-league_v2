"""Pytest collection guard for the e2e smoke suite.

The script in this directory (``test_smoke.py``) is intended for
**manual** execution against a running dev server, not for inclusion in
``pytest`` runs (it would fail to discover any tests collectible by
pytest and, more importantly, would try to talk to a live HTTP server
that does not exist in CI).

We satisfy pytest by collecting nothing from this folder. To run the
suite explicitly, invoke the script directly:

    BASE_URL=http://127.0.0.1:5000 ./venv/bin/python tests/e2e/test_smoke.py
"""

from __future__ import annotations

collect_ignore_glob = ["*.py"]
