"""Export current database data to seed JSON files."""
import json
from app import create_app
from models import db, Country, Manager, Achievement

app = create_app()
with app.app_context():
    # Export countries
    countries = []
    for c in db.session.query(Country).all():
        countries.append({
            "code": c.code,
            "name": c.name,
            "flag_filename": c.flag_path.split('/')[-1]
        })
    
    # Export managers
    managers = []
    for m in db.session.query(Manager).all():
        country = db.session.get(Country, m.country_id)
        managers.append({
            "name": m.name,
            "country_code": country.code if country else "???"
        })
    
    # Export achievements
    achievements = []
    for a in db.session.query(Achievement).all():
        manager = db.session.get(Manager, a.manager_id)
        achievements.append({
            "manager_name": manager.name if manager else "???",
            "type": a.achievement_type,
            "league": a.league,
            "season": a.season,
            "title": a.title,
            "icon_filename": a.icon_path.split('/')[-1]
        })
    
    with open('data/seed/countries.json', 'w', encoding='utf-8') as f:
        json.dump(countries, f, indent=2, ensure_ascii=False)
    
    with open('data/seed/managers.json', 'w', encoding='utf-8') as f:
        json.dump(managers, f, indent=2, ensure_ascii=False)
    
    with open('data/seed/achievements.json', 'w', encoding='utf-8') as f:
        json.dump(achievements, f, indent=2, ensure_ascii=False)
    
    print(f"Exported: {len(countries)} countries, {len(managers)} managers, {len(achievements)} achievements")
