"""Base ModelView shared by every admin model view."""

from __future__ import annotations

import logging
from typing import Any

from flask import redirect, request, url_for
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

admin_logger = logging.getLogger("shleague.admin")


class SHLModelView(ModelView):
    """Base model view with common security and logging."""

    # UI Customization
    list_template = "admin/model/list.html"
    create_template = "admin/model/create.html"
    edit_template = "admin/model/edit.html"

    can_export = True
    page_size = 50

    def is_accessible(self) -> bool:
        """Check if user is authenticated and has admin role."""
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        """Redirect to login if access is denied."""
        return redirect(url_for("admin.login", next=request.url))

    def on_model_change(self, form: Any, model: Any, is_created: bool) -> None:
        """Log changes to audit log."""
        action = "CREATE" if is_created else "UPDATE"

        # We don't log the actual changes here (done via SQLAlchemy events for better coverage),
        # but we can log the action intent.
        username = getattr(current_user, "username", "system")
        admin_logger.debug(f"{action} {model.__class__.__name__} by {username}")

    def on_model_delete(self, model: Any) -> None:
        """Log deletion to audit log."""

        username = getattr(current_user, "username", "system")
        admin_logger.info(
            f"DELETE {model.__class__.__name__} {getattr(model, 'id', 'unknown')} by {username}"
        )


# Resolve alias
SecureModelView = SHLModelView
