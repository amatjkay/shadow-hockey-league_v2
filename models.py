"""SQLAlchemy models for Shadow Hockey League.

Database schema for storing managers, countries, and achievements.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Country(db.Model):
    """Country table with flag information."""

    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False, index=True)
    flag_path = db.Column(db.String(100), nullable=False)
    managers = db.relationship('Manager', backref='country', lazy='select')

    def __repr__(self) -> str:
        return f'<Country {self.code}>'


class Manager(db.Model):
    """Manager table with name and country reference."""

    __tablename__ = 'managers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    country_id = db.Column(
        db.Integer,
        db.ForeignKey('countries.id', ondelete='RESTRICT'),
        nullable=False
    )
    achievements = db.relationship(
        'Achievement',
        backref='manager',
        lazy='select',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Manager {self.name}>'

    @property
    def is_tandem(self) -> bool:
        """Check if manager is a tandem (name starts with 'Tandem:' or contains comma)."""
        return self.name.startswith('Tandem:') or ',' in self.name

    @property
    def display_name(self) -> str:
        """Get display name without 'Tandem:' prefix."""
        if self.name.startswith('Tandem:'):
            return self.name[7:].strip()
        return self.name


class Achievement(db.Model):
    """Achievement table storing manager awards."""

    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    achievement_type = db.Column(db.String(20), nullable=False, index=True)
    league = db.Column(db.String(10), nullable=False, index=True)
    season = db.Column(db.String(10), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    icon_path = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(
        db.Integer,
        db.ForeignKey('managers.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f'<Achievement {self.achievement_type} {self.league} {self.season}>'

    def to_html(self) -> str:
        """Generate HTML img tag for this achievement."""
        return (
            f'<img src="{self.icon_path}" '
            f'title="Shadow {self.league} league {self.title} s{self.season}">'
        )