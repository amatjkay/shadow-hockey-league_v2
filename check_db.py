#!/usr/bin/env python
"""Check database contents."""

from models import db, Manager, Achievement, Country
from app import create_app

app = create_app('config.DevelopmentConfig')

with app.app_context():
    print("=" * 50)
    print("DATABASE CONTENTS")
    print("=" * 50)
    
    countries = db.session.query(Country).all()
    managers = db.session.query(Manager).all()
    achievements = db.session.query(Achievement).all()
    
    print(f"\n📊 Summary:")
    print(f"   Countries:    {len(countries)}")
    print(f"   Managers:     {len(managers)}")
    print(f"   Achievements: {len(achievements)}")
    
    print(f"\n🌍 Countries:")
    for c in countries[:10]:
        print(f"   - {c.name} ({c.code})")
    
    print(f"\n👥 Managers (first 20):")
    for m in managers[:20]:
        mgr_achievements = db.session.query(Achievement).filter_by(manager_id=m.id).count()
        print(f"   - {m.name} (country_id={m.country_id}, achievements={mgr_achievements})")
    
    print(f"\n🏆 Achievements by type:")
    from sqlalchemy import func
    result = db.session.query(
        Achievement.achievement_type,
        func.count(Achievement.id)
    ).group_by(Achievement.achievement_type).all()
    
    for achievement_type, count in result:
        print(f"   - {achievement_type}: {count}")
    
    print("=" * 50)
