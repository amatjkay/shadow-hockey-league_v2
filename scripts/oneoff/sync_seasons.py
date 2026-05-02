from app import create_app
from models import Season, db


def sync_multipliers():
    app = create_app()
    with app.app_context():
        mapping = {
            "25/26": 1.05,
            "24/25": 1.00,
            "23/24": 0.95,
            "22/23": 0.90,
            "21/22": 0.85,
            "20/21": 0.80,
        }
        for code, mult in mapping.items():
            season = Season.query.filter_by(code=code).first()
            if season:
                season.multiplier = mult
                print(f"Set Season {code} multiplier to {mult}")

        db.session.commit()
        print("Synchronization complete!")


if __name__ == "__main__":
    sync_multipliers()
