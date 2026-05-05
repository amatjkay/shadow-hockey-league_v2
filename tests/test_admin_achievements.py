import pytest

from models import Achievement, AchievementType, Country, League, Manager, Season, db


@pytest.fixture
def auth_client(client, admin_user):
    """Client authenticated as admin."""
    client.post(
        "/admin/login/",
        data={"username": "testadmin", "password": "testpass123"},
        follow_redirects=True,
    )
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

    ach_type = AchievementType(
        code="TOP1",
        name="Top 1",
        base_points_l1=800.0,
        base_points_l2=400.0,
        icon_path="/static/img/cups/top1.svg",
    )
    db.session.add(ach_type)

    league = League(code="1", name="League 1")
    db.session.add(league)

    season = Season(code="25/26", name="Season 25/26", multiplier=1.5, is_active=True)
    db.session.add(season)
    db.session.commit()

    # Create achievement
    achievement = Achievement(
        manager_id=manager.id, type_id=ach_type.id, league_id=league.id, season_id=season.id
    )
    db.session.add(achievement)

    # Simulate on_model_change
    # In Flask-Admin, by the time on_model_change is called,
    # the model has its FKs and relationships assigned from the form.
    view = AchievementModelView(Achievement, db)

    # Manually populate relationships if they aren't loaded
    achievement.type = ach_type
    achievement.league = league
    achievement.season = season

    view.on_model_change(None, achievement, True)

    # Assertions
    # Title = AchievementType.name only (TIK-78). League + season are added
    # by ``Achievement.to_html`` for the hover tooltip, so duplicating them
    # in ``title`` produced redundant strings.
    assert achievement.title == "Top 1"
    assert achievement.icon_path == "/static/img/cups/top1.svg"
    assert achievement.base_points == 800.0
    assert achievement.multiplier == 1.5
    assert achievement.final_points == 1200.0


def test_get_icon_url_falls_back_to_default(app, db_session):
    """``AchievementType.get_icon_url`` must return an existing SVG.

    Regression for TIK-77: the previous implementation built
    ``/static/img/cups/{code.lower()}.svg`` when ``icon_path`` was NULL,
    leaking 404-prone paths like ``r3.svg`` / ``r1.svg`` / ``best.svg``
    into the public leaderboard. The fallback now points at
    ``default.svg`` (which exists on disk).
    """

    t_no_icon = AchievementType(
        code="R3", name="Round 3", base_points_l1=100.0, base_points_l2=50.0
    )
    assert t_no_icon.get_icon_url() == "/static/img/cups/default.svg"

    t_with_icon = AchievementType(
        code="R3",
        name="Round 3",
        base_points_l1=100.0,
        base_points_l2=50.0,
        icon_path="/static/img/cups/hockey-sticks-and-puck.svg",
    )
    assert t_with_icon.get_icon_url() == "/static/img/cups/hockey-sticks-and-puck.svg"


def test_seed_service_populates_canonical_icon_paths(db_session):
    """``SeedService`` must populate canonical ``icon_path`` for default types.

    Regression for TIK-77: ``data/seed_service.py`` used to leave
    ``icon_path`` NULL, so every fresh DB started with broken icons
    until an admin manually edited each AchievementType row.
    """

    from data.seed_service import SeedService

    # Run only the AchievementType branch by calling _seed_reference_data
    # via the public ``seed_all`` against an already-migrated empty DB.
    service = SeedService(db.session, seed_dir="data/seeds")
    service._seed_reference_data()  # type: ignore[attr-defined]
    db.session.commit()

    expected = {
        "TOP1": "/static/img/cups/top1.svg",
        "TOP2": "/static/img/cups/top2.svg",
        "TOP3": "/static/img/cups/top3.svg",
        "BEST": "/static/img/cups/best-reg.svg",
        "R3": "/static/img/cups/hockey-sticks-and-puck.svg",
        "R1": "/static/img/cups/hockey-sticks-and-puck.svg",
    }
    for code, path in expected.items():
        row = db.session.query(AchievementType).filter_by(code=code).first()
        assert row is not None, f"Seed missing AchievementType {code}"
        assert row.icon_path == path, (
            f"AchievementType {code} icon_path={row.icon_path!r} " f"expected {path!r}"
        )


def test_api_calculate_points(auth_client, seeded_db):
    """Test the calculation API endpoint."""
    ach_type = db.session.query(AchievementType).filter_by(code="TOP1").first()
    league = db.session.query(League).filter_by(code="1").first()
    season = db.session.query(Season).filter_by(code="23/24").first()

    resp = auth_client.get(
        f"/admin/api/calculate-points?type_id={ach_type.id}&league_id={league.id}&season_id={season.id}"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["base_points"] == 800.0
    assert data["multiplier"] == 0.5
    assert data["final_points"] == 400.0


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
        "achievements": [
            {"type_id": ach_type.id, "league_id": league.id, "season_id": new_season.id}
        ]
    }

    resp = auth_client.post(f"/admin/api/managers/{manager.id}/achievements/bulk-add", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["summary"]["created"] == 1

    # Verify in DB
    ach = (
        db.session.query(Achievement)
        .filter_by(manager_id=manager.id, season_id=new_season.id)
        .first()
    )
    assert ach is not None
    assert ach.final_points == 1600.0  # 800 * 2.0
    assert ach.icon_path == "/static/img/cups/top1.svg"


def test_api_delete_achievement(auth_client, seeded_db):
    """Test deleting an achievement."""
    manager = db.session.query(Manager).first()
    ach = db.session.query(Achievement).filter_by(manager_id=manager.id).first()
    ach_id = ach.id

    resp = auth_client.delete(f"/admin/api/managers/{manager.id}/achievements/{ach_id}")
    assert resp.status_code == 200

    # Verify in DB
    assert db.session.get(Achievement, ach_id) is None
