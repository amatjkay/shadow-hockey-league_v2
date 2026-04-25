from app import create_app
from models import db, Season, AchievementType

def final_sync_with_prod():
    app = create_app()
    with app.app_context():
        # 1. Sync Achievement Types
        # TOP1 L2 -> 300
        top1 = AchievementType.query.filter_by(code='TOP1').first()
        if top1:
            top1.base_points_l2 = 300
            print("Set TOP1 L2 base points to 300")
            
        # 2. Sync Seasons
        season_mapping = {
            "25/26": 1.00,
            "24/25": 0.95,
            "23/24": 0.90,
            "22/23": 0.85,
            "21/22": 0.80,
            "20/21": 0.75
        }
        for code, mult in season_mapping.items():
            season = Season.query.filter_by(code=code).first()
            if season:
                season.multiplier = mult
                print(f"Set Season {code} multiplier to {mult}")
        
        db.session.commit()
        print("Constants updated. Now recalculating achievements...")
        
        # 3. Recalculate all achievements
        from models import Achievement
        achievements = Achievement.query.all()
        for ach in achievements:
            base = ach.type.base_points_l1 if ach.league.code == '1' else ach.type.base_points_l2
            mult = ach.season.multiplier
            ach.base_points = float(base)
            ach.multiplier = float(mult)
            ach.final_points = round(float(base * mult), 2)
            
        db.session.commit()
        print("Recalculation complete! All data matches production.")

if __name__ == "__main__":
    final_sync_with_prod()
