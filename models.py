"""SQLAlchemy models for Shadow Hockey League.

Database schema for storing managers, countries, achievements, and reference data.
"""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


class AdminUser(db.Model, UserMixin):
    """Admin user table for authentication."""

    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password: str) -> None:
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<AdminUser {self.username}>"


class ApiKey(db.Model):
    """API key table for authentication and rate limiting.

    Supports three scopes:
    - read: GET endpoints only
    - write: GET + POST/PUT/DELETE
    - admin: Full access (including key management in future)
    """

    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(256), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # Human-readable name
    scope = db.Column(db.String(20), nullable=False, default="read")  # read/write/admin
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    expires_at = db.Column(db.DateTime, nullable=True)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Valid scopes
    VALID_SCOPES = {"read", "write", "admin"}

    def __repr__(self) -> str:
        return f"<ApiKey {self.name} ({self.scope})>"

    @property
    def is_expired(self) -> bool:
        """Check if key has expired."""
        if self.expires_at is None:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if key is active (not revoked and not expired)."""
        return not self.revoked and not self.is_expired

    def has_scope(self, required_scope: str) -> bool:
        """Check if key has required scope.

        Scope hierarchy: admin > write > read
        """
        scope_levels = {"read": 1, "write": 2, "admin": 3}
        key_level = scope_levels.get(self.scope, 0)
        required_level = scope_levels.get(required_scope, 0)
        return key_level >= required_level


# ==================== Reference (dictionary) tables ====================


class AchievementType(db.Model):
    """Reference table for achievement types (TOP1, TOP2, BEST, R3, R1)."""

    __tablename__ = "achievement_types"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # TOP1, TOP2, BEST, R3, R1
    name = db.Column(db.String(50), nullable=False)  # Human-readable label
    base_points_l1 = db.Column(db.Integer, nullable=False, default=0)  # Base points for League 1
    base_points_l2 = db.Column(db.Integer, nullable=False, default=0)  # Base points for League 2

    def __repr__(self) -> str:
        return f"<AchievementType {self.code}>"


class League(db.Model):
    """Reference table for leagues (1, 2, 3...)."""

    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)  # "1", "2", "3"
    name = db.Column(db.String(50), nullable=False)  # Human-readable label

    def __repr__(self) -> str:
        return f"<League {self.code}>"


class Season(db.Model):
    """Reference table for seasons with multipliers."""

    __tablename__ = "seasons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)  # "22/23", "23/24"
    name = db.Column(db.String(50), nullable=False)  # Human-readable label
    multiplier = db.Column(db.Float, nullable=False, default=1.0)  # Season multiplier for rating
    is_active = db.Column(db.Boolean, nullable=False, default=False)  # Current season flag

    def __repr__(self) -> str:
        return f"<Season {self.code}>"


# ==================== Core tables ====================


class Country(db.Model):
    """Country table with flag information."""

    __tablename__ = "countries"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, default="Unknown")  # Название страны (например, "Russia")
    flag_path = db.Column(db.String(100), nullable=False)
    managers = db.relationship("Manager", backref="country", lazy="select")

    def __repr__(self) -> str:
        return f"<Country {self.name} ({self.code})>"

    @staticmethod
    def resolve_name(code: str) -> str:
        """Resolve country name from code using reference data.

        Falls back to "Unknown" if code is not found.

        Args:
            code: 3-letter country code

        Returns:
            Human-readable country name
        """
        from data.countries_reference import get_country_name

        return get_country_name(code) or "Unknown"


class Manager(db.Model):
    """Manager table with name and country reference."""

    __tablename__ = "managers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    country_id = db.Column(
        db.Integer, db.ForeignKey("countries.id", ondelete="RESTRICT"), nullable=False
    )
    achievements = db.relationship(
        "Achievement", backref="manager", lazy="select", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Manager {self.name}>"

    @property
    def is_tandem(self) -> bool:
        """Check if manager is a tandem (name starts with 'Tandem:' or contains comma)."""
        return self.name.startswith("Tandem:") or "," in self.name

    @property
    def display_name(self) -> str:
        """Get display name without 'Tandem:' prefix."""
        if self.name.startswith("Tandem:"):
            return self.name[7:].strip()
        return self.name


class Achievement(db.Model):
    """Achievement table storing manager awards."""

    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint(
            "manager_id", "league", "season", "achievement_type",
            name="uq_achievement_manager_league_season_type"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    achievement_type = db.Column(db.String(20), nullable=False, index=True)
    league = db.Column(db.String(10), nullable=False, index=True)
    season = db.Column(db.String(10), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    icon_path = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(
        db.Integer, db.ForeignKey("managers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Achievement {self.achievement_type} {self.league} {self.season}>"

    def to_html(self) -> str:
        """Generate HTML img tag for this achievement."""
        return (
            f'<img src="{self.icon_path}" '
            f'title="Shadow {self.league} league {self.title} s{self.season}">'
        )


class AuditLog(db.Model):
    """Audit log table for tracking admin actions.
    
    Records all CRUD operations, logins, and cache flushes performed by admin users.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    action = db.Column(db.String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, FLUSH_CACHE
    target_model = db.Column(db.String(50), nullable=True, index=True)  # Model name (e.g., 'Manager')
    target_id = db.Column(db.Integer, nullable=True, index=True)  # Primary key of target
    changes = db.Column(db.Text, nullable=True)  # JSON string of changes (for UPDATE)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), nullable=False, index=True)

    # Composite index for user+timestamp queries
    __table_args__ = (
        db.Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id} at {self.timestamp}>"

    def to_dict(self) -> dict:
        """Convert audit log entry to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'target_model': self.target_model,
            'target_id': self.target_id,
            'changes': self.changes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
