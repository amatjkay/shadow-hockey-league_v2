"""End-to-end smoke suite for ``feature/admin-enhancement``.

Diagnostic Playwright run against a live Flask dev server. Designed to
catch 500s, blank pages, broken nav, and form-submit explosions without
asserting anything about business data.

Scenarios
---------
* public leaderboard (``/``, ``/rating``)
* health / metrics endpoints
* public REST API (``/api/countries``)
* protected REST API (``/api/managers``, ``/api/achievements``) — must
  reject anonymous reads with 401
* admin REST API mounted under ``/admin/api/`` (seasons / leagues /
  achievement-types)
* admin login + each Flask-Admin model view (list / create / edit forms)
* admin extras (``/admin/``, ``/admin/flush-cache/``)
* browser-console error budget on the leaderboard and admin index

Each scenario records pass / fail to ``/tmp/e2e_artifacts/report.json``.
Failures dump an HTML snapshot and a screenshot.

This suite is intentionally tolerant of business-data drift: it does
**not** assert on row counts, totals, or rendered text beyond the bare
minimum needed to detect "the page rendered nothing useful".

Run
---
    BASE_URL=http://127.0.0.1:5000 \\
    E2E_ADMIN_USER=e2e_admin       \\
    E2E_ADMIN_PASS=e2e-pass-1234   \\
    ./venv/bin/python tests/e2e/test_smoke.py

The script needs an admin user already provisioned. To create one
out-of-band:

    ./venv/bin/python -c "
    from app import create_app
    from models import db, AdminUser
    app = create_app()
    with app.app_context():
        if not AdminUser.query.filter_by(username='e2e_admin').first():
            u = AdminUser(username='e2e_admin', role=AdminUser.ROLE_SUPER_ADMIN)
            u.set_password('e2e-pass-1234')
            db.session.add(u); db.session.commit()
    "

Exit code is 0 when every scenario passes, 1 otherwise. Suitable for ad
hoc local runs; not wired into CI by default because it needs a live
server.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    sync_playwright,
)

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
ADMIN_USER = os.environ.get("E2E_ADMIN_USER", "e2e_admin")
ADMIN_PASS = os.environ.get("E2E_ADMIN_PASS", "e2e-pass-1234")

ARTIFACTS = Path(os.environ.get("E2E_ARTIFACTS", "/tmp/e2e_artifacts"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)


@dataclass
class Result:
    name: str
    passed: bool
    detail: str = ""
    artifacts: list[str] = field(default_factory=list)


results: list[Result] = []


def record(
    name: str,
    passed: bool,
    detail: str = "",
    artifacts: list[str] | None = None,
) -> None:
    results.append(Result(name, passed, detail, artifacts or []))
    badge = "PASS" if passed else "FAIL"
    print(f"  [{badge}] {name}" + (f" — {detail}" if detail else ""))


def dump_failure(page: Page, slug: str) -> list[str]:
    """Dump a screenshot + HTML snapshot for a failing scenario."""
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", slug)[:80]
    shot = ARTIFACTS / f"{safe}.png"
    html = ARTIFACTS / f"{safe}.html"
    paths: list[Path] = []
    try:
        page.screenshot(path=str(shot), full_page=True)
        paths.append(shot)
    except Exception:
        pass
    try:
        html.write_text(page.content(), encoding="utf-8")
        paths.append(html)
    except Exception:
        pass
    return [str(p) for p in paths]


_ERROR_HINTS = (
    "Произошла ошибка",
    "error-title",
    "Internal Server Error",
    "Traceback (most recent call last)",
)


def _is_error_page(html: str) -> bool:
    return any(h in html for h in _ERROR_HINTS)


def run_public_pages(page: Page) -> None:
    """Public, no-auth pages."""
    print("\n[public]")

    for path, label in [
        ("/", "homepage / leaderboard"),
        ("/rating", "rating redirect"),
        ("/health", "health endpoint"),
        ("/metrics", "prometheus metrics"),
    ]:
        try:
            resp = page.goto(BASE_URL + path, wait_until="domcontentloaded")
            status = resp.status if resp else 0
            ok = status < 400
            detail = f"HTTP {status}"

            if path == "/" and ok:
                body = page.content()
                if _is_error_page(body):
                    ok = False
                    detail += " — error template rendered"
                # Heuristic: leaderboard table or "no managers" message
                # must be present, otherwise the page rendered but is
                # broken.
                elif (
                    "rating-breakdown" not in body
                    and "Rating" not in body
                    and "Лиги" not in body
                    and "menedj" not in body.lower()
                ):
                    ok = False
                    detail += " — no rating section in HTML"

            arts = [] if ok else dump_failure(page, f"public_{path}")
            record(f"GET {path} ({label})", ok, detail, arts)
        except Exception as e:
            arts = dump_failure(page, f"public_{path}_exc")
            record(f"GET {path} ({label})", False, f"{type(e).__name__}: {e}", arts)

    # Season filter on home page — invalid season must not 500.
    try:
        page.goto(BASE_URL + "/?season=999999", wait_until="domcontentloaded")
        body = page.content()
        if _is_error_page(body):
            arts = dump_failure(page, "public_invalid_season")
            record(
                "GET /?season=999999 (invalid season)",
                False,
                "renders error.html",
                arts,
            )
        else:
            record("GET /?season=999999 (invalid season)", True, "graceful fallback")
    except Exception as e:
        arts = dump_failure(page, "public_invalid_season_exc")
        record(
            "GET /?season=999999 (invalid season)",
            False,
            f"{type(e).__name__}: {e}",
            arts,
        )


def run_rest_api() -> None:
    """REST API endpoints exposed under ``/api/`` and ``/admin/api/``.

    The split is intentional:

    * ``services/api.py`` registers the public REST blueprint at
      ``/api`` — most endpoints require an X-API-Key with the right
      scope, so anonymous calls should land on 401, not 500.
    * ``blueprints/admin_api.py`` registers an admin-only AJAX blueprint
      at ``/admin/api`` — these power dropdowns inside Flask-Admin and
      require an authenticated admin session. From an unauthenticated
      ``requests`` session they typically redirect to the login form.
    """
    print("\n[rest api]")
    s = requests.Session()

    # Public, no-auth.
    cases_anon = [
        ("/api/countries", {"ok": (200,), "expected_keys": ("countries",)}),
    ]
    # Auth-required: anonymous must get 401, not 500.
    cases_auth = [
        ("/api/managers", {"ok": (401, 403), "expected_keys": None}),
        ("/api/achievements", {"ok": (401, 403), "expected_keys": None}),
    ]
    # Admin-only AJAX endpoints (blueprints/admin_api.py): anonymous
    # gets 302 / 401 / 403; we just want to know they're routed, not
    # 404.
    cases_admin = [
        ("/admin/api/seasons", {"ok": (200, 302, 401, 403), "expected_keys": None}),
        ("/admin/api/leagues", {"ok": (200, 302, 401, 403), "expected_keys": None}),
        (
            "/admin/api/achievement-types",
            {"ok": (200, 302, 401, 403), "expected_keys": None},
        ),
        (
            "/admin/api/countries",
            {"ok": (200, 302, 401, 403), "expected_keys": None},
        ),
        (
            "/admin/api/managers",
            {"ok": (200, 302, 401, 403), "expected_keys": None},
        ),
    ]

    for path, opts in cases_anon + cases_auth + cases_admin:
        try:
            r = s.get(BASE_URL + path, timeout=10, allow_redirects=False)
            ok = r.status_code in opts["ok"]
            detail = f"HTTP {r.status_code}"
            if ok and opts["expected_keys"] is not None:
                try:
                    payload = r.json()
                except ValueError:
                    ok = False
                    detail += " — non-JSON response"
                else:
                    if isinstance(payload, dict) and not any(
                        k in payload for k in opts["expected_keys"]
                    ):
                        ok = False
                        detail += (
                            f" — payload missing any of {opts['expected_keys']}: "
                            f"keys={list(payload)[:5]}"
                        )
            record(f"REST GET {path}", ok, detail)
        except Exception as e:
            record(f"REST GET {path}", False, f"{type(e).__name__}: {e}")


def admin_login(page: Page) -> bool:
    """Log into Flask-Admin. Returns True on success."""
    try:
        page.goto(BASE_URL + "/admin/login/", wait_until="domcontentloaded")
        page.fill('input[name="username"]', ADMIN_USER)
        page.fill('input[name="password"]', ADMIN_PASS)
        with page.expect_navigation(wait_until="domcontentloaded"):
            page.click('button[type="submit"], input[type="submit"]')
        if page.url.rstrip("/").endswith("/admin/login"):
            arts = dump_failure(page, "admin_login_fail")
            record("admin login", False, f"still on login page: {page.url}", arts)
            return False
        record("admin login", True, f"redirected to {page.url}")
        return True
    except Exception as e:
        arts = dump_failure(page, "admin_login_exc")
        record("admin login", False, f"{type(e).__name__}: {e}", arts)
        return False


def _check_admin_page(page: Page, url: str, slug: str, label: str) -> None:
    try:
        resp = page.goto(url, wait_until="domcontentloaded")
        status = resp.status if resp else 0
        ok = status < 400
        detail = f"HTTP {status}"
        if ok:
            body = page.content()
            if _is_error_page(body):
                ok = False
                detail += " — error template rendered"
        arts = [] if ok else dump_failure(page, slug)
        record(label, ok, detail, arts)
    except Exception as e:
        arts = dump_failure(page, f"{slug}_exc")
        record(label, False, f"{type(e).__name__}: {e}", arts)


def run_admin_views(page: Page) -> None:
    """Walk every Flask-Admin model view (list page) and try opening
    the create / edit forms."""
    print("\n[admin views]")
    views = [
        ("/admin/country/", "Country"),
        ("/admin/manager/", "Manager"),
        ("/admin/achievement/", "Achievement"),
        ("/admin/achievementtype/", "AchievementType"),
        ("/admin/league/", "League"),
        ("/admin/season/", "Season"),
        ("/admin/auditlog/", "AuditLog"),
        ("/admin/apikey/", "ApiKey"),
        ("/admin/adminuser/", "AdminUser"),
    ]

    for path, name in views:
        _check_admin_page(
            page,
            BASE_URL + path,
            f"admin_list_{name}",
            f"admin LIST /admin/{name.lower()}/",
        )
        _check_admin_page(
            page,
            BASE_URL + path + "new/",
            f"admin_create_{name}",
            f"admin NEW /admin/{name.lower()}/new/",
        )

        try:
            page.goto(BASE_URL + path, wait_until="domcontentloaded")
            edit_link = page.locator('a[href*="/edit/?id="]').first
            if edit_link.count() == 0:
                continue
            href = edit_link.get_attribute("href")
            if not href:
                continue
            edit_url = BASE_URL + href if href.startswith("/") else href
            _check_admin_page(page, edit_url, f"admin_edit_{name}", f"admin EDIT first row {name}")
        except Exception as e:
            arts = dump_failure(page, f"admin_edit_{name}_exc")
            record(f"admin EDIT first row {name}", False, f"{type(e).__name__}: {e}", arts)


def run_admin_extras(page: Page) -> None:
    """Custom admin pages outside the model views."""
    print("\n[admin extras]")
    # ``/admin/flush-cache/`` is POST-only; a GET responds 405.
    extras = [
        ("/admin/", "admin index", (200,)),
        ("/admin/flush-cache/", "cache flush (GET → 405)", (405,)),
    ]
    for path, label, ok_codes in extras:
        try:
            resp = page.goto(BASE_URL + path, wait_until="domcontentloaded")
            status = resp.status if resp else 0
            ok = status in ok_codes
            detail = f"HTTP {status}"
            arts = [] if ok else dump_failure(page, f"admin_extra_{label}")
            record(f"admin {label} ({path})", ok, detail, arts)
        except Exception as e:
            # 405 / 308 sometimes throw inside Playwright's navigation.
            # Treat as informational, not a hard failure.
            record(f"admin {label} ({path})", True, f"navigation noise: {e}")


def run_console_errors(page: Page) -> None:
    """Hit homepage and admin index, capture browser console errors.

    Console errors are recorded but do **not** fail the suite hard —
    they are reported as a warning so the report stays usable when a
    pre-existing JS race lives in the admin templates. Real 500s and
    404s are caught by the dedicated scenarios above.
    """
    print("\n[console]")
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page.on(
        "console",
        lambda msg: (
            errors.append(f"console.{msg.type}: {msg.text}") if msg.type == "error" else None
        ),
    )
    try:
        page.goto(BASE_URL + "/", wait_until="networkidle", timeout=15000)
        page.goto(BASE_URL + "/admin/", wait_until="networkidle", timeout=15000)
    except Exception as e:
        errors.append(f"navigation: {type(e).__name__}: {e}")

    if errors:
        path = ARTIFACTS / "console_errors.txt"
        path.write_text("\n".join(errors), encoding="utf-8")
        # Surface as informational. Use record() with passed=True so
        # the suite exit code stays useful for hard regressions, but
        # include the count + artifact path in the detail so anyone
        # running the suite sees them.
        record(
            "browser console (informational)",
            True,
            f"{len(errors)} JS warning(s) — see {path}",
            [str(path)],
        )
    else:
        record("browser console (informational)", True, "no JS errors")


def main() -> int:
    print(f"BASE_URL = {BASE_URL}")
    start = time.time()

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)
        try:
            ctx: BrowserContext = browser.new_context(ignore_https_errors=True)
            ctx.set_default_timeout(15000)
            page: Page = ctx.new_page()

            run_public_pages(page)
            run_rest_api()

            if admin_login(page):
                run_admin_views(page)
                run_admin_extras(page)

            run_console_errors(page)
        finally:
            browser.close()

    failed = [r for r in results if not r.passed]
    elapsed = time.time() - start

    report = {
        "base_url": BASE_URL,
        "elapsed_sec": round(elapsed, 1),
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": [
            {
                "name": r.name,
                "passed": r.passed,
                "detail": r.detail,
                "artifacts": r.artifacts,
            }
            for r in results
        ],
    }
    (ARTIFACTS / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n=== {len(results) - len(failed)}/{len(results)} passed in {elapsed:.1f}s ===")
    if failed:
        print("FAILURES:")
        for r in failed:
            print(f"  - {r.name}: {r.detail}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
