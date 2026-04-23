"""Service for recalculating achievement points.

Handles point recalculation when:
- AchievementType base_points change
- Season multiplier changes
- Achievement league changes

All recalculations are atomic transactions that update base_points and final_points.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from flask_login import current_user

from models import Achievement, AchievementType, League, Season, db

logger = logging.getLogger(__name__)


def _recalc_single_achievement(achievement: Achievement) -> None:
    """Recalculate base_points and final_points for a single achievement.

    Uses parent_code logic:
    - league.parent_code == '1' OR league.code == '1' -> base_points_l1
    - else -> base_points_l2

    Updates achievement.base_points and achievement.final_points in place.
    """
    # Ensure relationships are loaded if we only have IDs
    if not achievement.type and achievement.type_id:
        achievement.type = db.session.get(AchievementType, achievement.type_id)
    if not achievement.league and achievement.league_id:
        achievement.league = db.session.get(League, achievement.league_id)
    if not achievement.season and achievement.season_id:
        achievement.season = db.session.get(Season, achievement.season_id)

    if not all([achievement.type, achievement.league, achievement.season]):
        logger.warning(
            f"Achievement {achievement.id} missing related entities "
            f"(type={achievement.type_id}, league={achievement.league_id}, season={achievement.season_id})"
        )
        return

    ach_type = achievement.type
    league = achievement.league
    season = achievement.season

    # Determine which base_points field to use based on league hierarchy
    root_code = league.parent_code or league.code
    if root_code == '1':
        achievement.base_points = float(ach_type.base_points_l1)
    else:
        achievement.base_points = float(ach_type.base_points_l2)

    achievement.final_points = round(achievement.base_points * season.multiplier, 2)


def _get_user_id() -> int | None:
    """Get current user ID safely."""
    try:
        if current_user and current_user.is_authenticated:
            return current_user.id
    except RuntimeError:
        pass
    return None


def recalc_by_achievement_type(type_id: int) -> dict[str, Any]:
    """Recalculate all achievements of a given type.

    Returns: {'affected': int, 'errors': list[str]}
    """
    ach_type = db.session.get(AchievementType, type_id)
    if not ach_type:
        return {'affected': 0, 'errors': ['Achievement type not found']}

    # Store old values for audit log
    old_l1 = ach_type.base_points_l1
    old_l2 = ach_type.base_points_l2

    # Get all achievements for this type
    achievements = Achievement.query.filter_by(type_id=type_id).all()
    
    if not achievements:
        return {'affected': 0, 'errors': []}

    affected = 0
    errors = []

    for achievement in achievements:
        try:
            _recalc_single_achievement(achievement)
            affected += 1
        except Exception as e:
            logger.error(f"Error recalculating achievement {achievement.id}: {e}")
            errors.append(f"Achievement {achievement.id}: {str(e)}")

    if affected > 0:
        try:
            db.session.commit()

            # Audit log (one entry for the whole batch)
            # Only log if we have a user_id (AuditLog requires it)
            user_id = _get_user_id()
            if user_id:
                from services.audit_service import log_action
                log_action(
                    user_id=user_id,
                    action='RECALCULATE_POINTS',
                    target_model='AchievementType',
                    target_id=type_id,
                    changes=json.dumps({
                        'affected_count': affected,
                        'old_base_points_l1': old_l1,
                        'new_base_points_l1': ach_type.base_points_l1,
                        'old_base_points_l2': old_l2,
                        'new_base_points_l2': ach_type.base_points_l2,
                    })
                )

            # Invalidate cache
            from services.cache_service import invalidate_leaderboard_cache
            invalidate_leaderboard_cache()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing recalculation for type {type_id}: {e}")
            errors.append(f"Commit failed: {str(e)}")
            return {'affected': 0, 'errors': errors}

    return {'affected': affected, 'errors': errors}


def recalc_by_season(season_id: int) -> dict[str, Any]:
    """Recalculate all achievements of a given season.

    Returns: {'affected': int, 'errors': list[str]}
    """
    season = db.session.get(Season, season_id)
    if not season:
        return {'affected': 0, 'errors': ['Season not found']}

    old_multiplier = season.multiplier

    achievements = Achievement.query.filter_by(season_id=season_id).all()
    
    if not achievements:
        return {'affected': 0, 'errors': []}

    affected = 0
    errors = []

    for achievement in achievements:
        try:
            _recalc_single_achievement(achievement)
            affected += 1
        except Exception as e:
            logger.error(f"Error recalculating achievement {achievement.id}: {e}")
            errors.append(f"Achievement {achievement.id}: {str(e)}")

    if affected > 0:
        try:
            db.session.commit()

            # Audit log
            user_id = _get_user_id()
            if user_id:
                from services.audit_service import log_action
                log_action(
                    user_id=user_id,
                    action='RECALCULATE_POINTS',
                    target_model='Season',
                    target_id=season_id,
                    changes=json.dumps({
                        'affected_count': affected,
                        'old_multiplier': old_multiplier,
                        'new_multiplier': season.multiplier,
                    })
                )

            # Invalidate cache
            from services.cache_service import invalidate_leaderboard_cache
            invalidate_leaderboard_cache()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing recalculation for season {season_id}: {e}")
            errors.append(f"Commit failed: {str(e)}")
            return {'affected': 0, 'errors': errors}

    return {'affected': affected, 'errors': errors}


def recalc_single_achievement_id(achievement_id: int) -> bool:
    """Recalculate a single achievement (e.g., after league change).

    Returns: True if successful, False otherwise.
    """
    achievement = db.session.get(Achievement, achievement_id)
    if not achievement:
        return False

    try:
        _recalc_single_achievement(achievement)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recalculating single achievement {achievement_id}: {e}")
        return False
