from app import create_app
from models import db, Manager, Achievement, Country, League, Season, AchievementType

def run_audit():
    app = create_app()
    with app.app_context():
        print("Starting Data Integrity Audit...")
        
        # 1. Orphaned Achievements
        orphans = Achievement.query.filter(Achievement.manager_id == None).all()
        print(f"- Orphaned Achievements: {len(orphans)}")
        
        # 2. Managers without countries
        no_country = Manager.query.filter(Manager.country_id == None).all()
        print(f"- Managers without country: {len(no_country)}")
        
        # 3. Invalid Reference Links
        print("- Checking Foreign Keys integrity...")
        ach_invalid_type = Achievement.query.filter(~Achievement.type_id.in_(db.session.query(AchievementType.id))).count()
        ach_invalid_league = Achievement.query.filter(~Achievement.league_id.in_(db.session.query(League.id))).count()
        ach_invalid_season = Achievement.query.filter(~Achievement.season_id.in_(db.session.query(Season.id))).count()
        
        print(f"  * Achievements with invalid Type: {ach_invalid_type}")
        print(f"  * Achievements with invalid League: {ach_invalid_league}")
        print(f"  * Achievements with invalid Season: {ach_invalid_season}")
        
        # 4. Point calculation consistency
        from services.rating_service import calculate_achievement_points
        print("- Verifying Point Calculation consistency...")
        mismatch_count = 0
        for ach in Achievement.query.limit(100).all():
            expected = calculate_achievement_points(ach)['points']
            if round(ach.final_points) != expected:
                mismatch_count += 1
                if mismatch_count <= 5:
                    print(f"  ! Mismatch in ACH {ach.id}: DB={ach.final_points}, Expected={expected}")
        
        print(f"- Total calculation mismatches (sample of 100): {mismatch_count}")
        print("\nAudit Complete.")

if __name__ == "__main__":
    run_audit()
