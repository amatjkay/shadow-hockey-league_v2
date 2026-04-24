"""Monkey-patches for library compatibility.

This module contains patches for Flask-Admin and WTForms to ensure compatibility
between specific versions (e.g., Flask-Admin 2.0.2 and WTForms 3.x).
"""

from typing import Any, Callable
import flask_admin.base
from wtforms.fields.core import Field

def apply_patches() -> None:
    """Apply all monkey-patches for the application."""
    patch_flask_admin_baseview()
    patch_wtforms_field_init()

def patch_flask_admin_baseview() -> None:
    """Monkey-patch Flask-Admin 2.0.2 BaseView._run_view.
    
    Flask-Admin 2.0.2 passes cls=self to view functions but they don't accept it.
    This patch removes the cls parameter for compatibility.
    """
    original_run_view = flask_admin.base.BaseView._run_view

    def patched_run_view(self: Any, f: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Remove cls parameter from _run_view for compatibility."""
        return f(self, *args, **kwargs)

    flask_admin.base.BaseView._run_view = patched_run_view

def patch_wtforms_field_init() -> None:
    """Monkey-patch WTForms Field.__init__ to remove allow_blank.
    
    Flask-Admin passes allow_blank to fields, but WTForms 3.x doesn't accept it in base Field.
    """
    original_field_init = Field.__init__

    def patched_field_init(self: Any, *args: Any, **kwargs: Any) -> None:
        """Remove allow_blank from field options for WTForms 3.x compatibility."""
        if 'allow_blank' in kwargs:
            del kwargs['allow_blank']
        return original_field_init(self, *args, **kwargs)

    Field.__init__ = patched_field_init
