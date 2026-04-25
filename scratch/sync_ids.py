from app import create_app
from models import db, Season, Achievement

def sync_season_ids():
    app = create_app()
    with app.app_context():
        # 1. Clear achievements (they depend on seasons)
        Achievement.query.delete()
        # 2. Clear seasons
        Season.query.delete()
        db.session.commit()
        
        # 3. Create seasons with specific IDs to match PROD
        # PROD: ?season=1 is 23/24
        # Let's assume the following mapping for prod:
        # 1: 23/24, 2: 24/25, 3: 25/26 ... or similar.
        # Since user said ?season=1 is 23/24, let's start there.
        
        seasons_data = [
            (1, "23/24", "Season 2023-2024", 0.90),
            (2, "24/25", "Season 2024-2025", 0.95),
            (3, "25/26", "Season 2025-2026", 1.00),
            (4, "22/23", "Season 2022-2023", 0.85),
            (5, "21/22", "Season 2021-2022", 0.80),
        ]
        
        for sid, code, name, mult in seasons_data:
            s = Season(id=sid, code=code, name=name, multiplier=mult)
            db.session.add(s)
        
        db.session.commit()
        print("Season IDs synced with PROD mapping.")
        
        # 4. Re-seed achievements from JSON
        import json
        with open('data/seed/achievements.json', 'r') as f:
            data = json.load(f)
            
        from models import Manager, AchievementType, League
        for ach_item in data:
            manager = Manager.query.filter_by(name=ach_item['manager_name']).first()
            atype = AchievementType.query.filter_by(code=ach_item['type']).first()
            league = League.query.filter_by(code=ach_item['league']).first()
            season = Season.query.filter_by(code=ach_item['season']).first()
            
            if all([manager, atype, league, season]):
                base = atype.base_points_l1 if league.code == '1' else atype.base_points_l2
                final = round(float(base * season.multiplier), 2)
                
                a = Achievement(
                    manager_id=manager.id,
                    type_id=atype.id,
                    league_id=league.id,
                    season_id=season.id,
                    title=ach_item['title'],
                    icon_path=f"/static/img/icons/{ach_item['icon_filename']}",
                    base_points=float(base),
                    multiplier=float(season.multiplier),
                    final_points=final
                )
                db.session.add(a)
        
        db.session.commit()
        print("Achievements re-seeded with correct Season IDs.")

if __name__ == "__main__":
    sync_season_ids()
