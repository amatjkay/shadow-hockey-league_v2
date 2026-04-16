"""Service for match lifecycle and result calculation."""
from typing import Optional, Dict, Any
from models import db, Match, Team, Season, Manager

class MatchService:
    @staticmethod
    def record_result(
        home_team_id: int,
        away_team_id: int,
        season_id: int,
        home_score: int,
        away_score: int,
        performed_by: int,
    ) -> Dict[str, Any]:
        """Record a match result atomically and update standings."""
        try:
            # Validate teams and season exist
            home = db.session.get(Team, home_team_id)
            away = db.session.get(Team, away_team_id)
            season = db.session.get(Season, season_id)
            if not all([home, away, season]):
                return {"ok": False, "error": "Invalid teams or season"}

            # Create match record
            match = Match(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                season_id=season_id,
                home_score=home_score,
                away_score=away_score,
                performed_by=performed_by,
            )
            db.session.add(match)
            db.session.flush()  # assign match.id

            # Update team stats via standings service
            from .standings_service import StandingsService
            StandingsService.record_match_result(match)

            db.session.commit()
            return {"ok": True, "match_id": match.id}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "error": str(e)}

    @staticmethod
    def list_for_season(season_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        from services.standings_service import StandingsService
        return StandingsService.list_for_season(season_id, page, page_size)