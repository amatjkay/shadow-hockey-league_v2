from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Country(db.Model):
    __tablename__ = 'countries'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)
    flag_path = db.Column(db.String(100), nullable=False)
    managers = db.relationship('Manager', backref='country', lazy=True)

    def __repr__(self):
        return f'<Country {self.code}>'

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    league = db.Column(db.String(20), nullable=False)
    season = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    icon_path = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=False)

    def __repr__(self):
        return f'<Achievement {self.type} {self.season}>'

    def to_html(self):
        return f'<img src="{self.icon_path}" title="Shadow {self.league} league {self.title} s{self.season}">'

class Manager(db.Model):
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    achievements = db.relationship('Achievement', backref='manager', lazy=True)

    def __repr__(self):
        return f'<Manager {self.name}>'

    @property
    def achievements_html(self):
        return [achievement.to_html() for achievement in self.achievements] 