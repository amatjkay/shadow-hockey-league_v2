from app import create_app
from models import Achievement, db


def recalculate_all_achievements():
    app = create_app()
    with app.app_context():
        achievements = Achievement.query.all()
        print(f"Recalculating {len(achievements)} achievements...")
        for ach in achievements:
            # Formula: Base * Multiplier
            base = ach.type.base_points_l1 if ach.league.code == "1" else ach.type.base_points_l2
            mult = ach.season.multiplier
            ach.base_points = float(base)
            ach.multiplier = float(mult)
            ach.final_points = round(float(base * mult), 2)

        db.session.commit()
        print("Recalculation complete!")


if __name__ == "__main__":
    recalculate_all_achievements()
