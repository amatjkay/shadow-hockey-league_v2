"""Admin API endpoints for Select2 dropdowns and bulk operations.

Implements API-001 through API-006 from requirements.json.
All endpoints require admin authentication.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from models import (
    db, Country, Manager, Achievement, AchievementType,
    League, Season, AdminUser
)
from services.admin import invalidate_leaderboard_cache

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
@login_required
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
@login_required
def get_managers():
    """API-002: Search managers for Select2 dropdown.

    Query params:
        q: Search query (manager name)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
    """
    try:
        q = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

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
@login_required
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
@login_required
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
@login_required
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


# ==================== API-Extra: Achievement Types ====================

@admin_api_bp.route('/achievement-types', methods=['GET'])
@login_required
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
@login_required
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

        # Fix N+1: Batch-load managers and existing achievements (Critical: performance)
        managers = {
            m.id: m for m in db.session.query(Manager)
            .filter(Manager.id.in_(manager_ids))
            .all()
        }
        existing_achievements = set(
            db.session.query(Achievement.manager_id).filter(
                Achievement.manager_id.in_(manager_ids),
                Achievement.type_id == type_id,
                Achievement.league_id == league_id,
                Achievement.season_id == season_id
            ).all()
        )
        existing_manager_ids = {ea[0] for ea in existing_achievements}

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

            # Fix N+1: Use pre-loaded set instead of per-manager query
            if mid in existing_manager_ids:
                skipped.append({
                    'manager_id': mid,
                    'manager_name': manager.name,
                    'reason': 'Achievement already exists'
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
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in POST /admin/api/achievements/bulk-create: {e}")
        return jsonify({'error': 'Internal server error'}), 500
