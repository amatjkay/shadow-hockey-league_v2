from app import create_app
from models import db, Achievement

def verify_points():
    app = create_app()
    with app.app_context():
        achievements = Achievement.query.all()
        errors = 0
        print(f"Checking {len(achievements)} achievements...")
        for ach in achievements:
            # Re-calculate
            base = ach.type.base_points_l1 if ach.league.code == '1' else ach.type.base_points_l2
            mult = ach.season.multiplier
            expected = round(float(base * mult), 2)
            
            if abs(ach.final_points - expected) > 0.01:
                print(f"ERR: {ach.manager.name} | {ach.title} | DB: {ach.final_points} | Expected: {expected}")
                errors += 1
        
        if errors == 0:
            print("SUCCESS: All points are calculated correctly!")
        else:
            print(f"FOUND {errors} errors.")

if __name__ == "__main__":
    verify_points()
