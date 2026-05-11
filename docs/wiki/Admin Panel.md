# Admin Panel

Flask-Admin 2.0.2 wrapped in [`services/admin/`](../../services/admin/)
(post-TIK-42 package split). Mounted at `/admin/`.

## Modules

- [`__init__.py`](../../services/admin/__init__.py) — `init_admin(app)`,
  called from `app.py::register_extensions`.
- [`base.py`](../../services/admin/base.py) — `SHLModelView` parent
  class: hooks `on_model_change`, formatters, defaults.
- [`views.py`](../../services/admin/views.py) — one `ModelView` per
  resource (`Country`, `League`, `Season`, `Manager`,
  `AchievementType`, `Achievement`, `AuditLog`, `APIKey`, `User`).
- [`_rate_limit.py`](../../services/admin/_rate_limit.py) — login-form
  throttling via shared `Limiter` from `services/extensions.py`.

## Key behaviours

- **AJAX achievements UI** — managers/achievements support inline
  picker via [`blueprints/admin_api/`](../../blueprints/admin_api/).
- **Auto-calculated `Achievement.points`** — recomputed via
  `on_model_change`; never trust client-submitted values.
- **Audit capture** — see [[Audit Log]].

## Compatibility notes

Flask-Admin 2.0.2 ships with the `cls=self` fallback in
`BaseView._run_view`; WTForms 3.2.x no longer accepts `allow_blank` on
`Field`. The old `utils/patches.py` shim was removed in TIK-34. If a
future upgrade reintroduces the incompatibility, restore the patch and
call it from `create_app()` before `init_admin(app)`.

## See also

- [docs/ADMIN_RECALC.md](../ADMIN_RECALC.md) — recalc UI.
- [[REST API]] — public REST surface (separate from admin).
