import pytest
from models import Achievement, AchievementType, Country, League, Season, Manager, AdminUser, db

@pytest.fixture
def auth_client(client, admin_user):
    """Client authenticated as admin."""
    client.post('/admin/login/', data={
        'username': 'testadmin',
        'password': 'testpass123'
    }, follow_redirects=True)
    return client

def test_achievement_auto_calculation(app, db_session):
    """Test that Achievement fields are auto-filled in on_model_change."""
    from services.admin import AchievementModelView
    
    # Create reference data
    country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
    db.session.add(country)
    db.session.flush()
    
    manager = Manager(name="Test Manager", country_id=country.id)
    db.session.add(manager)
    
    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800.0, base_points_l2=400.0)
    db.session.add(ach_type)
    
    league = League(code="1", name="League 1")
    db.session.add(league)
    
    season = Season(code="25/26", name="Season 25/26", multiplier=1.5, is_active=True)
    db.session.add(season)
    db.session.commit()
    
    # Create achievement
    achievement = Achievement(
        manager_id=manager.id,
        type_id=ach_type.id,
        league_id=league.id,
        season_id=season.id
    )
    db.session.add(achievement)
    
    # Simulate on_model_change
    # In Flask-Admin, by the time on_model_change is called, 
    # the model has its FKs and relationships assigned from the form.
    view = AchievementModelView(Achievement, db.session)
    
    # Manually populate relationships if they aren't loaded
    achievement.type = ach_type
    achievement.league = league
    achievement.season = season
    
    view.on_model_change(None, achievement, True)
    
    # Assertions
    assert achievement.title == "Top 1 League 1 Season 25/26"
    assert achievement.icon_path == "/static/img/cups/top1.svg"
    assert achievement.base_points == 800.0
    assert achievement.multiplier == 1.5
    assert achievement.final_points == 1200.0

def test_api_calculate_points(auth_client, seeded_db):
    """Test the calculation API endpoint."""
    ach_type = db.session.query(AchievementType).filter_by(code="TOP1").first()
    league = db.session.query(League).filter_by(code="1").first()
    season = db.session.query(Season).filter_by(code="23/24").first()
    
    resp = auth_client.get(f'/admin/api/calculate-points?type_id={ach_type.id}&league_id={league.id}&season_id={season.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['base_points'] == 10.0
    assert data['multiplier'] == 1.0
    assert data['final_points'] == 10.0

def test_api_bulk_add_achievement(auth_client, seeded_db):
    """Test bulk adding achievements to a manager."""
    manager = db.session.query(Manager).first()
    ach_type = db.session.query(AchievementType).filter_by(code="TOP1").first()
    league = db.session.query(League).filter_by(code="1").first()
    
    # Create a new season to avoid duplicate
    new_season = Season(code="25/26", name="S25", multiplier=2.0, is_active=True)
    db.session.add(new_season)
    db.session.commit()
    
    payload = {
        'achievements': [
            {
                'type_id': ach_type.id,
                'league_id': league.id,
                'season_id': new_season.id
            }
        ]
    }
    
    resp = auth_client.post(f'/admin/api/managers/{manager.id}/achievements/bulk-add', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['summary']['created'] == 1
    
    # Verify in DB
    ach = db.session.query(Achievement).filter_by(manager_id=manager.id, season_id=new_season.id).first()
    assert ach is not None
    assert ach.final_points == 20.0 # 10 * 2.0
    assert ach.icon_path == "/static/img/cups/top1.svg"

def test_api_delete_achievement(auth_client, seeded_db):
    """Test deleting an achievement."""
    manager = db.session.query(Manager).first()
    ach = db.session.query(Achievement).filter_by(manager_id=manager.id).first()
    ach_id = ach.id
    
    resp = auth_client.delete(f'/admin/api/managers/{manager.id}/achievements/{ach_id}')
    assert resp.status_code == 200
    
    # Verify in DB
    assert db.session.query(Achievement).get(ach_id) is None
