#!/usr/bin/env python
"""Check which database is being used."""

from models import db, Manager
from app import create_app
import os

print("=" * 50)
print("DATABASE CHECK")
print("=" * 50)

# Check config
app = create_app('config.DevelopmentConfig')
print(f"\n📁 Database URL from config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

# Check dev.db
print(f"\n📊 dev.db contents:")
os.environ['DATABASE_URL'] = 'sqlite:///dev.db'
app_dev = create_app('config.DevelopmentConfig')
with app_dev.app_context():
    managers = db.session.query(Manager).count()
    print(f"   Managers: {managers}")

# Check instance/shadow_league.db
print(f"\n📊 instance/shadow_league.db contents:")
app_instance = create_app()
app_instance.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/shadow_league.db'
db2 = db
db2.init_app(app_instance)
with app_instance.app_context():
    managers = db2.session.query(Manager).count()
    mgr = db2.session.query(Manager).first()
    print(f"   Managers: {managers}")
    if mgr:
        print(f"   First manager: {mgr.name}")

print("=" * 50)
