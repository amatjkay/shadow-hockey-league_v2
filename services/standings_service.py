"""Service for standings/league table calculations."""
from typing import Dict, Any, List
from models import db, Manager, Match, Season

class StandingsService:
    @staticmethod
    def record_match_result(match) -> None:
        """Update manager stats based on a match result."""
        # Simple points: win=3, draw=1, loss=0
        if match.home_score > match.away_score:
            home_points, away_points = 3, 0
        elif match.home_score == match.away_score:
            home_points, away_points = 1, 1
        else:
            home_points, away_points = 0, 3

        home_manager = db.session.get(Manager, match.home_team_id)
        away_manager = db.session.get(Manager, match.away_team_id)
        if home_manager:
            home_manager.total_points += home_points
            home_manager.matches_played += 1
            db.session.add(home_manager)
        if away_manager:
            away_manager.total_points += away_points
            away_manager.matches_played += 1
            db.session.add(away_manager)
        db.session.commit()

    @staticmethod
    def list_for_season(season_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        managers = db.session.query(Manager)\
            .filter_by(season_id=season_id, is_active=True)\
            .order_by(Manager.total_points.desc(), Manager.matches_played.asc())\
            .offset(offset).limit(page_size).all()
        total = db.session.query(Manager).filter_by(season_id=season_id, is_active=True).count()
        return {
            "items": [{"id": m.id, "name": m.name, "points": m.total_points, "played": m.matches_played} for m in managers],
            "pagination": {"page": page, "page_size": page_size, "total": total}
        }