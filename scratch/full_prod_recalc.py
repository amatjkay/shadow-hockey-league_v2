from app import create_app
from models import db, AchievementType, Achievement

def sync_all_constants_with_prod():
    app = create_app()
    with app.app_context():
        # 1. Update/Create Achievement Types with REAL Prod points
        types_config = {
            "TOP1": {"l1": 800, "l2": 300},
            "TOP2": {"l1": 550, "l2": 200},
            "TOP3": {"l1": 450, "l2": 100},
            "BEST_REG": {"l1": 50, "l2": 25},
            "HOCKEY_STICKS_AND_PUCK": {"l1": 10, "l2": 5}, # ROUND 1
        }
        
        for code, points in types_config.items():
            at = AchievementType.query.filter_by(code=code).first()
            if not at:
                at = AchievementType(code=code, name=code)
                db.session.add(at)
            at.base_points_l1 = points["l1"]
            at.base_points_l2 = points["l2"]
            print(f"Synced {code}: L1={points['l1']}, L2={points['l2']}")
        
        db.session.commit()
        
        # 2. Recalculate ALL achievements
        achievements = Achievement.query.all()
        print(f"Recalculating {len(achievements)} achievements...")
        for ach in achievements:
            # Re-map type if it's a legacy one
            if ach.type.code == 'BEST': # Example of legacy fix
                 ach.type = AchievementType.query.filter_by(code='TOP3').first()
            
            base = ach.type.base_points_l1 if ach.league.code == '1' else ach.type.base_points_l2
            mult = ach.season.multiplier
            ach.base_points = float(base)
            ach.multiplier = float(mult)
            ach.final_points = round(float(base * mult), 2)
            
        db.session.commit()
        print("Recalculation complete!")

if __name__ == "__main__":
    sync_all_constants_with_prod()
