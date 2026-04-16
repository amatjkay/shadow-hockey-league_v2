"""Admin API endpoints for Select2 dropdowns and bulk operations.

Implements API-001 through API-006 from requirements.json.
All endpoints require admin authentication.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from models import (
    db, Country, Manager, Achievement, AchievementType,
    League, Season, AdminUser
)
from services.admin import invalidate_leaderboard_cache

def admin_required(func):
    """Ensure the current user has admin privileges."""
    from functools import wraps
    from flask import jsonify
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'error': 'Access denied'}), 403
        return func(*args, **kwargs)
    return wrapper

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin/api')

api_logger = logging.getLogger('shleague.admin_api')


# ==================== Helper ====================

def _paginate_query(query, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Helper to paginate query results for Select2."""
    page_size = min(max(page_size, 1), 100)  # Clamp 1-100
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        'items': items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size,
            'has_more': page * page_size < total
        }
    }


# ==================== API-001: Countries ====================

@admin_api_bp.route('/countries', methods=['GET'])
@admin_required
def get_countries():
    """API-001: Search and list countries for Select2 dropdown.

    Query params:
        q: Search query (country name or code)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
    """
    try:
        q = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        query = db.session.query(Country).filter_by(is_active=True)

        if q:
            query = query.filter(
                db.or_(
                    Country.name.ilike(f'%{q}%'),
                    Country.code.ilike(f'%{q}%')
                )
            )

        query = query.order_by(Country.name)
        result = _paginate_query(query, page, page_size)

        return jsonify({
            'items': [
                {
                    'id': c.id,
                    'code': c.code,
                    'name': c.name,
                    'flag_url': c.flag_display_url,
                    'is_active': c.is_active
                }
                for c in result['items']
            ],
            'pagination': result['pagination']
        })
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/countries: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-002: Managers ====================

@admin_api_bp.route('/managers', methods=['GET'])
@admin_required
def get_managers():
    """API-002: Search managers for Select2 dropdown.

    Query params:
        q: Search query (manager name)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        ids: Comma-separated list of manager IDs for bulk fetch (optional)
    """
    try:
        q = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        ids_param = request.args.get('ids', '').strip()

        # Handle bulk fetch by IDs (P0-1: bulk preview with real data)
        if ids_param:
            try:
                ids = [int(x.strip()) for x in ids_param.split(',') if x.strip()]
                if not ids:
                    return jsonify({'items': [], 'pagination': {'total': 0}})

                managers = db.session.query(Manager).filter(
                    Manager.id.in_(ids),
                    Manager.is_active == True
                ).all()

                # Sort by original order of IDs
                manager_map = {m.id: m for m in managers}
                sorted_managers = [manager_map[mid] for mid in ids if mid in manager_map]

                return jsonify({
                    'items': [
                        {
                            'id': m.id,
                            'name': m.name,
                            'country_id': m.country_id,
                            'country_name': m.country.name if m.country else 'Unknown',
                            'country_code': m.country.code if m.country else '',
                            'country_flag': m.country.flag_path if m.country else '',
                            'country_flag_url': m.country.flag_display_url if m.country else '',
                            'is_tandem': m.is_tandem
                        }
                        for m in sorted_managers
                    ],
                    'pagination': {'total': len(sorted_managers)}
                })
            except ValueError:
                return jsonify({'error': 'Invalid IDs format'}), 400

        # Standard paginated search
        query = db.session.query(Manager).filter_by(is_active=True)

        if q:
            query = query.filter(Manager.name.ilike(f'%{q}%'))

        query = query.order_by(Manager.name)
        result = _paginate_query(query, page, page_size)

        return jsonify({
            'items': [
                {
                    'id': m.id,
                    'name': m.name,
                    'country_id': m.country_id,
                    'country_name': m.country.name if m.country else 'Unknown',
                    'country_code': m.country.code if m.country else '',
                    'country_flag': m.country.flag_path if m.country else '',
                    'is_tandem': m.is_tandem
                }
                for m in result['items']
            ],
            'pagination': result['pagination']
        })
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/managers: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-003: Seasons ====================

@admin_api_bp.route('/seasons', methods=['GET'])
@admin_required
def get_seasons():
    """API-003: List seasons filtered by league.

    Query params:
        league_id: League ID to filter seasons (required)
        active_only: Only return active seasons (default: true)
    """
    try:
        league_id = request.args.get('league_id', type=int)
        if not league_id:
            return jsonify({'error': 'league_id is required'}), 400

        active_only = request.args.get('active_only', 'true').lower() == 'true'

        # Get league to check code
        league = db.session.get(League, league_id)
        if not league:
            return jsonify({'error': 'League not found'}), 404

        query = db.session.query(Season)
        if active_only:
            query = query.filter_by(is_active=True)

        # VR-004: League 2.1/2.2 only available from 2025
        if league.code in ('2.1', '2.2'):
            query = query.filter(Season.start_year >= 2025)

        seasons = query.order_by(Season.code.desc()).all()

        return jsonify({
            'items': [
                {
                    'id': s.id,
                    'code': s.code,
                    'name': s.name,
                    'multiplier': s.multiplier,
                    'start_year': s.start_year,
                    'end_year': s.end_year,
                    'is_active': s.is_active,
                    'is_available': True
                }
                for s in seasons
            ]
        })
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/seasons: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-004: Achievement Type Points ====================

@admin_api_bp.route('/achievement-types/<int:type_id>/points', methods=['GET'])
@admin_required
def get_achievement_points(type_id: int):
    """API-004: Get base points for achievement type based on league.

    Query params:
        league_id: League ID (required)
    """
    try:
        league_id = request.args.get('league_id', type=int)
        if not league_id:
            return jsonify({'error': 'league_id is required'}), 400

        ach_type = db.session.get(AchievementType, type_id)
        if not ach_type:
            return jsonify({'error': 'Achievement type not found'}), 404

        league = db.session.get(League, league_id)
        if not league:
            return jsonify({'error': 'League not found'}), 404

        # Determine base points based on league code
        if league.code == '1':
            base_points = ach_type.base_points_l1
            points_source = 'base_points_l1'
        else:
            base_points = ach_type.base_points_l2
            points_source = 'base_points_l2'

        return jsonify({
            'type_id': ach_type.id,
            'type_code': ach_type.code,
            'type_name': ach_type.name,
            'league_id': league.id,
            'league_code': league.code,
            'base_points': base_points,
            'points_source': points_source
        })
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/achievement-types/{type_id}/points: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-005: Leagues ====================

@admin_api_bp.route('/leagues', methods=['GET'])
@admin_required
def get_leagues():
    """API-005: List all active leagues."""
    try:
        leagues = db.session.query(League).filter_by(is_active=True).order_by(League.code).all()

        return jsonify({
            'items': [
                {
                    'id': l.id,
                    'code': l.code,
                    'name': l.name,
                    'is_active': l.is_active
                }
                for l in leagues
            ]
        })
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/leagues: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-Extra: Achievement Calculator ====================

@admin_api_bp.route('/calculate-points', methods=['GET'])
@admin_required
def calculate_points():
    """Calculate final points for achievement type based on league and season.
    
    Query params:
        type_id: Achievement Type ID (required)
        league_id: League ID (required)
        season_id: Season ID (required)
    """
    try:
        type_id = request.args.get('type_id', type=int)
        league_id = request.args.get('league_id', type=int)
        season_id = request.args.get('season_id', type=int)
        
        if not all([type_id, league_id, season_id]):
            return jsonify({'error': 'type_id, league_id, and season_id are required'}), 400
        
        # Get entities
        ach_type = db.session.get(AchievementType, type_id)
        league = db.session.get(League, league_id)
        season = db.session.get(Season, season_id)
        
        if not ach_type:
            return jsonify({'error': 'Achievement type not found'}), 404
        if not league:
            return jsonify({'error': 'League not found'}), 404
        if not season:
            return jsonify({'error': 'Season not found'}), 404
        
        # Calculate base points based on league code
        if league.code == '1':
            base_points = ach_type.base_points_l1
            points_source = 'base_points_l1'
        else:
            base_points = ach_type.base_points_l2
            points_source = 'base_points_l2'
        
        # Calculate final points
        final_points = base_points * season.multiplier
        
        return jsonify({
            'type_id': ach_type.id,
            'type_code': ach_type.code,
            'type_name': ach_type.name,
            'league_id': league.id,
            'league_code': league.code,
            'league_name': league.name,
            'season_id': season.id,
            'season_code': season.code,
            'season_name': season.name,
            'base_points': base_points,
            'points_source': points_source,
            'multiplier': season.multiplier,
            'final_points': round(final_points, 2)
        })
        
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/calculate-points: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-Extra: Achievement Types ====================

@admin_api_bp.route('/achievement-types', methods=['GET'])
@admin_required
def get_achievement_types():
    """List all active achievement types for Select2 dropdown."""
    try:
        q = request.args.get('q', '').strip()
        types = db.session.query(AchievementType).filter_by(is_active=True)

        if q:
            types = types.filter(
                db.or_(
                    AchievementType.name.ilike(f'%{q}%'),
                    AchievementType.code.ilike(f'%{q}%')
                )
            )

        types = types.order_by(AchievementType.name).all()

        return jsonify({
            'items': [
                {
                    'id': t.id,
                    'text': t.name + ' (L1: ' + str(t.base_points_l1) + ', L2: ' + str(t.base_points_l2) + ')'
                }
                for t in types
            ]
        })
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/achievement-types: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-006: Bulk Create ====================

@admin_api_bp.route('/achievements/bulk-create', methods=['POST'])
@admin_required
def bulk_create_achievements():
    """API-006: Create achievements for multiple managers.

    Request body:
        manager_ids: array of integers
        type_id: integer
        league_id: integer
        season_id: integer
    """
    try:
        # Permission check (Critical: prevent privilege escalation)
        if not current_user.has_permission('create'):
            return jsonify({'error': 'Insufficient permissions'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        manager_ids = data.get('manager_ids')
        type_id = data.get('type_id')
        league_id = data.get('league_id')
        season_id = data.get('season_id')

        # Validate required fields
        if not manager_ids or not isinstance(manager_ids, list):
            return jsonify({'error': 'manager_ids array is required'}), 400
        if len(manager_ids) > 100:
            return jsonify({'error': 'Maximum 100 managers per bulk operation'}), 400
        if not type_id or not league_id or not season_id:
            return jsonify({'error': 'type_id, league_id, season_id are required'}), 400

        # Validate existence
        ach_type = db.session.get(AchievementType, type_id)
        league = db.session.get(League, league_id)
        season = db.session.get(Season, season_id)

        if not ach_type:
            return jsonify({'error': 'Achievement type not found'}), 400
        if not league:
            return jsonify({'error': 'League not found'}), 400
        if not season:
            return jsonify({'error': 'Season not found'}), 400

        # VR-004: League/Season compatibility
        if league.code in ('2.1', '2.2') and season.start_year and season.start_year < 2025:
            return jsonify({
                'error': f'League {league.code} is only available from season 25/26 onwards'
            }), 400

        # Calculate points
        if league.code == '1':
            base_points = ach_type.base_points_l1
        else:
            base_points = ach_type.base_points_l2
        multiplier = season.multiplier
        final_points = round(base_points * multiplier, 2)

        # VR-005: Range validation for points (non-negative)
        if base_points < 0:
            return jsonify({'error': 'Base points cannot be negative'}), 400
        if multiplier < 0:
            return jsonify({'error': 'Season multiplier cannot be negative'}), 400
        if final_points < 0:
            return jsonify({'error': 'Final points cannot be negative'}), 400

        # Fix N+1: Batch-load managers and existing achievements (Critical: performance)
        managers = {
            m.id: m for m in db.session.query(Manager)
            .filter(Manager.id.in_(manager_ids))
            .all()
        }
        # VR-003: Get existing achievement IDs for duplicate handling
        existing_achievements = db.session.query(
            Achievement.id, Achievement.manager_id
        ).filter(
            Achievement.manager_id.in_(manager_ids),
            Achievement.type_id == type_id,
            Achievement.league_id == league_id,
            Achievement.season_id == season_id
        ).all()
        existing_manager_map = {ea[1]: ea[0] for ea in existing_achievements}  # manager_id -> achievement_id

        # Fix: Use correct icon_path based on achievement type (Critical: correctness)
        icon_path = f'/static/img/cups/{ach_type.code.lower()}.svg'

        # Process each manager
        created = []
        skipped = []
        errors = []

        for mid in manager_ids:
            # Fix N+1: Use batch-loaded dict instead of db.session.get
            manager = managers.get(mid)
            if not manager:
                errors.append({
                    'manager_id': mid,
                    'manager_name': 'Unknown',
                    'error_code': 'MANAGER_NOT_FOUND',
                    'error_message': f'Manager ID {mid} not found'
                })
                continue

            if not manager.is_active:
                skipped.append({
                    'manager_id': mid,
                    'manager_name': manager.name,
                    'reason': 'Manager is not active'
                })
                continue

            # VR-003: Use pre-loaded map for duplicate check with existing_id
            existing_achievement_id = existing_manager_map.get(mid)
            if existing_achievement_id:
                skipped.append({
                    'manager_id': mid,
                    'manager_name': manager.name,
                    'reason': 'Achievement already exists for this manager',
                    'existing_id': existing_achievement_id,
                    'existing_url': f'/admin/achievement/edit/?id={existing_achievement_id}'
                })
                continue

            # Create achievement
            achievement = Achievement(
                manager_id=mid,
                type_id=type_id,
                league_id=league_id,
                season_id=season_id,
                title=f'{ach_type.name} {league.name} {season.name}',
                icon_path=icon_path,
                base_points=base_points,
                multiplier=multiplier,
                final_points=final_points
            )
            db.session.add(achievement)
            created.append(achievement.id)

        db.session.commit()

        # Trigger rating recalculation
        invalidate_leaderboard_cache()

        return jsonify({
            'success': True,
            'summary': {
                'total_requested': len(manager_ids),
                'created': len(created),
                'skipped_duplicates': len(skipped),
                'errors': len(errors)
            },
            'details': {
                'created_ids': created,
                'skipped': skipped,
                'errors': errors
            },
            'recalculation_triggered': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in POST /admin/api/achievements/bulk-create: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== API-005 (NEW): Manager Achievements ====================


@admin_api_bp.route('/managers/<int:manager_id>/achievements', methods=['GET'])
@admin_required
def get_manager_achievements(manager_id):
    """Get all achievements for a manager.

    Uses joinedload to avoid N+1 queries on type/league/season relationships.
    """
    try:
        manager = db.session.get(Manager, manager_id)
        if not manager:
            return jsonify({'error': 'Manager not found'}), 404

        achievements = (
            db.session.query(Achievement)
            .options(
                joinedload(Achievement.type),
                joinedload(Achievement.league),
                joinedload(Achievement.season),
            )
            .filter_by(manager_id=manager_id)
            .all()
        )

        result_achievements = []
        total_points = 0.0

        for a in achievements:
            points = a.final_points or 0.0
            total_points += points

            result_achievements.append({
                'id': a.id,
                'type': {
                    'id': a.type_id,
                    'code': a.type.code if a.type else '',
                    'name': a.type.name if a.type else ''
                },
                'league': {
                    'id': a.league_id,
                    'code': a.league.code if a.league else '',
                    'name': a.league.name if a.league else ''
                },
                'season': {
                    'id': a.season_id,
                    'code': a.season.code if a.season else '',
                    'name': a.season.name if a.season else '',
                    'multiplier': a.season.multiplier if a.season else 1.0
                },
                'base_points': a.base_points,
                'multiplier': a.multiplier,
                'final_points': a.final_points,
                'title': a.title,
            })

        return jsonify({
            'manager_id': manager.id,
            'manager_name': manager.name,
            'total_points': total_points,
            'achievements': result_achievements
        })

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        api_logger.error(f"Error in GET /admin/api/managers/{manager_id}/achievements: {e}\n{error_detail}")
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


@admin_api_bp.route('/managers/<int:manager_id>/achievements/bulk-add', methods=['POST'])
@admin_required
def bulk_add_achievements(manager_id):
    """API-005: Add multiple achievements to a single manager."""
    try:
        if not current_user.has_permission('create'):
            return jsonify({'error': 'Insufficient permissions'}), 403

        data = request.get_json()
        if not data or 'achievements' not in data:
            return jsonify({'error': 'Request body with achievements array is required'}), 400

        achievements = data['achievements']
        if not isinstance(achievements, list):
            return jsonify({'error': 'achievements must be an array'}), 400
        if len(achievements) > 50:
            return jsonify({'error': 'Maximum 50 achievements per request'}), 400

        # Validate manager exists
        manager = db.session.get(Manager, manager_id)
        if not manager:
            return jsonify({'error': 'Manager not found'}), 404

        # Load reference data in batch
        type_ids = set(a.get('type_id') for a in achievements if a.get('type_id'))
        league_ids = set(a.get('league_id') for a in achievements if a.get('league_id'))
        season_ids = set(a.get('season_id') for a in achievements if a.get('season_id'))

        types = {t.id: t for t in db.session.query(AchievementType).filter(AchievementType.id.in_(type_ids)).all()}
        leagues = {l.id: l for l in db.session.query(League).filter(League.id.in_(league_ids)).all()}
        seasons = {s.id: s for s in db.session.query(Season).filter(Season.id.in_(season_ids)).all()}

        # VR-003: Load existing achievements for duplicate check with IDs
        existing = db.session.query(
            Achievement.id, Achievement.type_id, Achievement.league_id, Achievement.season_id
        ).filter(Achievement.manager_id == manager_id).all()
        existing_key_map = {(e[1], e[2], e[3]): e[0] for e in existing}  # (type, league, season) -> achievement_id

        created = []
        skipped = []
        errors = []

        for idx, ach_data in enumerate(achievements):
            type_id = ach_data.get('type_id')
            league_id = ach_data.get('league_id')
            season_id = ach_data.get('season_id')

            if not type_id or not league_id or not season_id:
                errors.append({'index': idx, 'error': 'type_id, league_id, season_id are required'})
                continue

            ach_type = types.get(type_id)
            league = leagues.get(league_id)
            season = seasons.get(season_id)

            if not ach_type:
                errors.append({'index': idx, 'error': f'Type {type_id} not found'})
                continue
            if not league:
                errors.append({'index': idx, 'error': f'League {league_id} not found'})
                continue
            if not season:
                errors.append({'index': idx, 'error': f'Season {season_id} not found'})
                continue

            # VR-004: League/Season compatibility
            if league.code in ('2.1', '2.2') and season.start_year and season.start_year < 2025:
                errors.append({'index': idx, 'error': f'League {league.code} only available from season 25/26'})
                continue

            # VR-003: Duplicate check with existing_id
            key = (type_id, league_id, season_id)
            existing_achievement_id = existing_key_map.get(key)
            if existing_achievement_id:
                skipped.append({
                    'type_id': type_id,
                    'type_name': ach_type.name,
                    'league_name': league.name,
                    'season_name': season.name,
                    'reason': 'Achievement already exists for this manager',
                    'existing_id': existing_achievement_id,
                    'existing_url': f'/admin/achievement/edit/?id={existing_achievement_id}'
                })
                continue

            # Calculate points
            base_points = float(ach_type.base_points_l1 if league.code == '1' else ach_type.base_points_l2)
            multiplier = float(season.multiplier)
            final_points = round(base_points * multiplier, 2)

            # VR-005: Range validation for points (non-negative)
            if base_points < 0 or multiplier < 0 or final_points < 0:
                errors.append({
                    'index': idx,
                    'error': f'Points calculation error: negative values (base={base_points}, multiplier={multiplier})'
                })
                continue

            # Icon path
            icon_path = f'/static/img/cups/{ach_type.code.lower()}.svg'

            # Create achievement
            achievement = Achievement(
                manager_id=manager_id,
                type_id=type_id,
                league_id=league_id,
                season_id=season_id,
                title=f'{ach_type.name} {league.name} {season.name}',
                icon_path=icon_path,
                base_points=base_points,
                multiplier=multiplier,
                final_points=final_points
            )
            db.session.add(achievement)
            db.session.flush()  # Get ID before commit
            created.append(achievement.id)
            existing_key_map[key] = achievement.id  # Prevent intra-batch duplicates

        db.session.commit()

        # Invalidate cache
        invalidate_leaderboard_cache()

        # Calculate manager total points
        total_points = db.session.query(db.func.sum(Achievement.final_points)) \
            .filter(Achievement.manager_id == manager_id).scalar() or 0.0

        return jsonify({
            'success': True,
            'summary': {
                'total_requested': len(achievements),
                'created': len(created),
                'skipped_duplicates': len(skipped),
                'errors': len(errors)
            },
            'details': {
                'created_ids': created,
                'skipped': skipped,
                'errors': errors
            },
            'manager_total_points': total_points,
            'recalculation_triggered': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in POST /admin/api/managers/{manager_id}/achievements/bulk-add: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_api_bp.route('/managers/<int:manager_id>/achievements', methods=['POST'])
@admin_required
def create_manager_achievement(manager_id):
    """Create a single achievement for a manager.

    Request body:
        type_id: integer
        league_id: integer
        season_id: integer
    """
    try:
        if not current_user.has_permission('create'):
            return jsonify({'error': 'Insufficient permissions'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        type_id = data.get('type_id')
        league_id = data.get('league_id')
        season_id = data.get('season_id')

        if not all([type_id, league_id, season_id]):
            return jsonify({'error': 'type_id, league_id, season_id are required'}), 400

        # Validate manager
        manager = db.session.get(Manager, manager_id)
        if not manager:
            return jsonify({'error': 'Manager not found'}), 404
        
        # V-010: Check manager is active
        if not manager.is_active:
            return jsonify({'error': 'Manager is not active'}), 400

        # Validate entities existence and activity (V-003, V-004, V-005)
        ach_type = db.session.get(AchievementType, type_id)
        league = db.session.get(League, league_id)
        season = db.session.get(Season, season_id)

        if not ach_type or not ach_type.is_active:
            return jsonify({'error': 'Achievement type not found or inactive'}), 400
        if not league or not league.is_active:
            return jsonify({'error': 'League not found or inactive'}), 400
        if not season or not season.is_active:
            return jsonify({'error': 'Season not found or inactive'}), 400

        # V-002: League/Season compatibility
        if league.code in ('2.1', '2.2') and season.start_year and season.start_year < 2025:
            return jsonify({'error': f'League {league.code} is only available from season 25/26'}), 400

        # V-001: Duplicate check
        existing = Achievement.query.filter_by(
            manager_id=manager_id,
            type_id=type_id,
            league_id=league_id,
            season_id=season_id
        ).first()
        if existing:
            return jsonify({'error': 'Achievement already exists', 'existing_id': existing.id}), 409

        # Calculate points
        root_code = league.parent_code or league.code
        base_points = ach_type.base_points_l1 if root_code == '1' else ach_type.base_points_l2
        final_points = round(base_points * season.multiplier, 2)

        # Auto icon path
        icon_path = f'/static/img/cups/{ach_type.code.lower()}.svg'

        achievement = Achievement(
            manager_id=manager_id,
            type_id=type_id,
            league_id=league_id,
            season_id=season_id,
            title=f'{ach_type.name} {league.name} {season.name}',
            icon_path=icon_path,
            base_points=base_points,
            multiplier=season.multiplier,
            final_points=final_points
        )
        db.session.add(achievement)
        db.session.commit()

        invalidate_leaderboard_cache()

        return jsonify({
            'success': True,
            'id': achievement.id,
            'type': {'id': ach_type.id, 'code': ach_type.code},
            'league': {'id': league.id, 'code': league.code},
            'season': {'id': season.id, 'code': season.code},
            'base_points': base_points,
            'multiplier': season.multiplier,
            'final_points': final_points
        }), 201

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in POST /admin/api/managers/{manager_id}/achievements: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_api_bp.route('/managers/<int:manager_id>/achievements/<int:achievement_id>', methods=['PUT'])
@admin_required
def update_manager_achievement(manager_id, achievement_id):
    """Update a single achievement (inline editing).

    Request body:
        type_id: integer (optional)
        league_id: integer (optional)
        season_id: integer (optional)
    """
    try:
        if not current_user.has_permission('edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        achievement = db.session.query(Achievement).filter_by(
            id=achievement_id, manager_id=manager_id
        ).first()

        if not achievement:
            return jsonify({'error': 'Achievement not found'}), 404

        # Update fields if provided
        new_type_id = data.get('type_id', achievement.type_id)
        new_league_id = data.get('league_id', achievement.league_id)
        new_season_id = data.get('season_id', achievement.season_id)

        # Validate new entities
        ach_type = db.session.get(AchievementType, new_type_id)
        league = db.session.get(League, new_league_id)
        season = db.session.get(Season, new_season_id)

        if not all([ach_type, league, season]):
            return jsonify({'error': 'One or more related entities not found'}), 400

        # V-001: Duplicate check (exclude current)
        duplicate = Achievement.query.filter(
            Achievement.manager_id == manager_id,
            Achievement.type_id == new_type_id,
            Achievement.league_id == new_league_id,
            Achievement.season_id == new_season_id,
            Achievement.id != achievement_id
        ).first()
        if duplicate:
            return jsonify({'error': 'Duplicate achievement exists', 'existing_id': duplicate.id}), 409

        # Update fields
        achievement.type_id = new_type_id
        achievement.league_id = new_league_id
        achievement.season_id = new_season_id

        # Update calculated fields
        root_code = league.parent_code or league.code
        achievement.base_points = ach_type.base_points_l1 if root_code == '1' else ach_type.base_points_l2
        achievement.final_points = round(achievement.base_points * season.multiplier, 2)
        achievement.icon_path = f'/static/img/cups/{ach_type.code.lower()}.svg'
        achievement.title = f'{ach_type.name} {league.name} {season.name}'

        db.session.commit()
        invalidate_leaderboard_cache()

        return jsonify({
            'success': True,
            'id': achievement.id,
            'base_points': achievement.base_points,
            'multiplier': achievement.multiplier,
            'final_points': achievement.final_points
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in PUT /admin/api/managers/{manager_id}/achievements/{achievement_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_api_bp.route('/managers/<int:manager_id>/achievements/<int:achievement_id>', methods=['DELETE'])
@admin_required
def delete_manager_achievement(manager_id, achievement_id):
    """Delete a single achievement from a manager."""
    try:
        if not current_user.has_permission('delete'):
            return jsonify({'error': 'Insufficient permissions'}), 403

        achievement = db.session.query(Achievement).filter_by(
            id=achievement_id, manager_id=manager_id
        ).first()

        if not achievement:
            return jsonify({'error': 'Achievement not found'}), 404

        lost_points = achievement.final_points or 0.0

        db.session.delete(achievement)
        db.session.commit()

        invalidate_leaderboard_cache()

        total_points = db.session.query(db.func.sum(Achievement.final_points)) \
            .filter(Achievement.manager_id == manager_id).scalar() or 0.0

        return jsonify({
            'success': True,
            'deleted_id': achievement_id,
            'lost_points': lost_points,
            'manager_total_points': total_points,
            'recalculation_triggered': True
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
