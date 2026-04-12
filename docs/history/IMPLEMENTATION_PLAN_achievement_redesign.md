# Implementation Plan: Achievement Redesign

**Phase-by-phase guide for DEVELOPER to implement the Achievement system redesign.**

**Pre-requisites:**
- All existing tests pass
- Database schema is correct — NO migrations needed
- Existing API endpoints (API-001 through API-006) work correctly

---

## Phase 1: Achievement Types Page with Calculator

**Goal:** Add a live points calculator to the Achievement Type create/edit forms.

### Step 1.1 — Create Calculator Templates

**File: `templates/admin/achievement_type_create.html`**

Extend `admin/model/create.html`. Inject via `{% block tail %}`:
1. Two extra Select2 dropdowns (League, Season) — NOT form-bound, just for preview.
2. A display area for calculated points: `base_points x multiplier = final_points`.
3. JavaScript:
   - On page load: populate leagues via `GET /admin/api/leagues`.
   - On league select: populate seasons via `GET /admin/api/seasons?league_id=X`.
   - On league or season select: trigger calculation.
   - Calculation logic: read `base_points_l1` or `base_points_l2` from the form fields (they are already on the AchievementType form). Read `multiplier` from the fetched season data. Compute `final_points = base_points * multiplier`.

**Key difference from old achievement calculator:**
- Base points come from the FORM fields (`base_points_l1`, `base_points_l2`) — NOT from an API call, because the user is editing those values right now.
- The calculator shows what the points WOULD BE if an achievement of this type were created with the selected League and Season.

**File: `templates/admin/achievement_type_edit.html`**

Same as create template, but also fetches the current object's data for initial display.

### Step 1.2 — Wire Templates to AchievementTypeModelView

In `services/admin.py`, on `AchievementTypeModelView`:

```python
class AchievementTypeModelView(SecureModelView):
    name = 'Achievement Types'
    create_template = 'admin/achievement_type_create.html'
    edit_template = 'admin/achievement_type_edit.html'
    # ... rest unchanged
```

### Step 1.3 — Calculator Display

Add a styled display box below the form fields:

```html
<div id="points-calculator" style="margin-top: 20px; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 8px; color: white;">
  <h4>Points Calculator (Preview)</h4>
  <div>
    <span>League:</span> <span id="calc-league">—</span>
  </div>
  <div>
    <span>Base Points:</span> <span id="calc-base">—</span>
  </div>
  <div>
    <span>Season:</span> <span id="calc-season">—</span>
  </div>
  <div>
    <span>Multiplier:</span> <span id="calc-multiplier">—</span>
  </div>
  <hr>
  <div style="font-size: 24px; font-weight: bold;">
    <span>Final Points:</span> <span id="calc-final">—</span>
  </div>
</div>
```

### Acceptance Criteria

- [ ] Achievement Types create/edit pages show calculator section
- [ ] Selecting League shows correct base_points (from form's base_points_l1 or base_points_l2)
- [ ] Selecting Season shows multiplier
- [ ] Final points update in real-time: base_points * multiplier
- [ ] Calculator is display-only — does not affect form submission

---

## Phase 2: Manager Achievement Table + Add Form

**Goal:** Add achievement table and "Add Achievement" modal to the manager edit page.

### Step 2.1 — Extend Manager Edit Template

**File: `templates/admin/manager_edit.html`**

Add below the main form (in `{% block tail %}`, after existing content):

```html
<!-- Achievement Table Section -->
<div id="achievements-section" style="margin-top: 30px;">
  <h3>Achievements</h3>

  <!-- Existing Achievements Table -->
  <table id="achievements-table" class="table table-striped">
    <thead>
      <tr>
        <th>Type</th>
        <th>League</th>
        <th>Season</th>
        <th>Base</th>
        <th>Multi</th>
        <th>Points</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody id="achievements-tbody">
      <!-- Populated by JS from API -->
    </tbody>
    <tfoot>
      <tr>
        <td colspan="5"><strong>Total</strong></td>
        <td colspan="2"><strong id="achievements-total">0.00</strong></td>
      </tr>
    </tfoot>
  </table>

  <button type="button" id="add-achievement-btn" class="btn btn-primary">+ Add Achievement</button>
</div>

<!-- Add Achievement Modal -->
<div id="achievement-modal" class="modal" style="display:none;">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h4>Add Achievement</h4>
        <button type="button" class="close" data-dismiss="modal">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>Type</label>
          <select id="ach-type" class="form-control select2" style="width:100%"></select>
        </div>
        <div class="form-group">
          <label>League</label>
          <select id="ach-league" class="form-control select2" style="width:100%"></select>
        </div>
        <div class="form-group">
          <label>Season</label>
          <select id="ach-season" class="form-control select2" style="width:100%" disabled></select>
        </div>
        <div class="form-group">
          <label>Points (auto-calculated)</label>
          <input type="text" id="ach-points" class="form-control" readonly>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" id="ach-add-btn" class="btn btn-success">+ Add Another</button>
        <button type="button" id="ach-save-all-btn" class="btn btn-primary">Save All</button>
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
      </div>
    </div>
  </div>
</div>

<!-- Pending Achievements (client-side, not yet saved) -->
<table id="pending-achievements-table" class="table table-warning" style="margin-top: 10px; display:none;">
  <thead>
    <tr>
      <th>Type</th>
      <th>League</th>
      <th>Season</th>
      <th>Points</th>
      <th>Action</th>
    </tr>
  </thead>
  <tbody id="pending-achievements-tbody"></tbody>
</table>
```

### Step 2.2 — JavaScript for Achievement Table

In the same template's `{% block tail %}`:

```javascript
$(document).ready(function() {
  var managerId = {{ id }};  // Flask-Admin provides this
  var pendingAchievements = [];

  // Load existing achievements
  loadAchievements();

  function loadAchievements() {
    $.get('/admin/api/managers/' + managerId + '/achievements', function(data) {
      var tbody = $('#achievements-tbody').empty();
      data.achievements.forEach(function(ach) {
        tbody.append('<tr data-id="' + ach.id + '">' +
          '<td>' + ach.type.code + '</td>' +
          '<td>' + ach.league.code + '</td>' +
          '<td>' + ach.season.code + '</td>' +
          '<td>' + ach.base_points + '</td>' +
          '<td>x' + ach.multiplier + '</td>' +
          '<td>' + ach.final_points.toFixed(2) + '</td>' +
          '<td><button class="btn btn-sm btn-danger delete-ach-btn" data-id="' + ach.id + '">X</button></td>' +
        '</tr>');
      });
      $('#achievements-total').text(data.total_points.toFixed(2));
    });
  }

  // Initialize Select2 dropdowns in modal
  initSelect2Dropdowns();

  function initSelect2Dropdowns() {
    // Type
    $('#ach-type').select2({
      ajax: {
        url: '/admin/api/achievement-types',
        dataType: 'json',
        delay: 250,
        data: function(params) { return { q: params.term || '' }; },
        processResults: function(data) { return { results: data.items }; },
        cache: true
      },
      minimumInputLength: 1,
      placeholder: 'Select type...',
      width: '100%'
    });

    // League
    $('#ach-league').select2({
      ajax: {
        url: '/admin/api/leagues',
        dataType: 'json',
        processResults: function(data) {
          return { results: data.items.map(function(l) { return { id: l.id, text: l.name + ' (' + l.code + ')' }; }) };
        },
        cache: true
      },
      placeholder: 'Select league...',
      width: '100%'
    });

    // Season (cascaded)
    $('#ach-season').select2({
      ajax: {
        url: '/admin/api/seasons',
        dataType: 'json',
        data: function() { return { league_id: $('#ach-league').val(), active_only: true }; },
        processResults: function(data) {
          return { results: data.items.map(function(s) { return { id: s.id, text: s.name + ' (x' + s.multiplier + ')' }; }) };
        },
        cache: true
      },
      placeholder: 'Select league first...',
      disabled: true,
      width: '100%'
    });

    // Cascade: league -> season
    $('#ach-league').on('select2:select', function() {
      $('#ach-season').prop('disabled', false).empty().trigger('change');
      calculatePoints();
    });

    // Recalculate on any selection change
    $('#ach-type, #ach-season').on('select2:select change', function() { calculatePoints(); });
  }

  function calculatePoints() {
    var typeId = $('#ach-type').val();
    var leagueId = $('#ach-league').val();
    var seasonId = $('#ach-season').val();
    if (!typeId || !leagueId || !seasonId) return;

    $.get('/admin/api/achievement-types/' + typeId + '/points', { league_id: leagueId }, function(typeData) {
      // Get season multiplier
      $.get('/admin/api/seasons', { league_id: leagueId }, function(seasonData) {
        var season = seasonData.items.find(function(s) { return s.id == seasonId; });
        if (season) {
          var base = typeData.base_points;
          var mult = season.multiplier;
          var final = (base * mult).toFixed(2);
          $('#ach-points').val(final);
        }
      });
    });
  }

  // Open modal
  $('#add-achievement-btn').on('click', function() {
    $('#achievement-modal').modal('show');
  });

  // Add Another
  $('#ach-add-btn').on('click', function() {
    var typeId = $('#ach-type').val();
    var leagueId = $('#ach-league').val();
    var seasonId = $('#ach-season').val();
    var points = $('#ach-points').val();

    if (!typeId || !leagueId || !seasonId) {
      alert('Please fill all fields');
      return;
    }

    // Get display text from Select2 data
    var typeText = $('#ach-type').select2('data')[0].text;
    var leagueText = $('#ach-league').select2('data')[0].text;
    var seasonText = $('#ach-season').select2('data')[0].text;

    pendingAchievements.push({
      type_id: parseInt(typeId),
      league_id: parseInt(leagueId),
      season_id: parseInt(seasonId),
      type_text: typeText,
      league_text: leagueText,
      season_text: seasonText,
      points: parseFloat(points)
    });

    renderPendingAchievements();
    clearModalForm();
  });

  function renderPendingAchievements() {
    var tbody = $('#pending-achievements-tbody').empty();
    if (pendingAchievements.length === 0) {
      $('#pending-achievements-table').hide();
      return;
    }
    $('#pending-achievements-table').show();
    pendingAchievements.forEach(function(ach, idx) {
      tbody.append('<tr data-idx="' + idx + '">' +
        '<td>' + ach.type_text + '</td>' +
        '<td>' + ach.league_text + '</td>' +
        '<td>' + ach.season_text + '</td>' +
        '<td>' + ach.points.toFixed(2) + '</td>' +
        '<td><button class="btn btn-sm btn-danger remove-pending-btn" data-idx="' + idx + '">X</button></td>' +
      '</tr>');
    });
  }

  function clearModalForm() {
    $('#ach-type').val(null).trigger('change');
    $('#ach-league').val(null).trigger('change');
    $('#ach-season').val(null).trigger('change').prop('disabled', true);
    $('#ach-points').val('');
  }

  // Remove pending row
  $(document).on('click', '.remove-pending-btn', function() {
    var idx = parseInt($(this).data('idx'));
    pendingAchievements.splice(idx, 1);
    renderPendingAchievements();
  });

  // Save All
  $('#ach-save-all-btn').on('click', function() {
    if (pendingAchievements.length === 0) {
      alert('No achievements to save. Use "Add Another" first.');
      return;
    }

    var btn = $(this).prop('disabled', true).text('Saving...');

    $.ajax({
      url: '/admin/api/managers/' + managerId + '/achievements/bulk-add',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ achievements: pendingAchievements }),
      success: function(response) {
        var msg = 'Created: ' + response.summary.created;
        if (response.summary.skipped_duplicates > 0) {
          msg += ', Skipped (duplicates): ' + response.summary.skipped_duplicates;
        }
        if (response.summary.errors > 0) {
          msg += ', Errors: ' + response.summary.errors;
        }
        alert(msg);
        pendingAchievements = [];
        renderPendingAchievements();
        loadAchievements();  // Reload table
        $('#achievement-modal').modal('hide');
      },
      error: function(xhr) {
        var err = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Unknown error';
        alert('Failed to save: ' + err);
      },
      complete: function() {
        btn.prop('disabled', false).text('Save All');
      }
    });
  });

  // Delete existing achievement
  $(document).on('click', '.delete-ach-btn', function() {
    if (!confirm('Delete this achievement?')) return;
    var achId = $(this).data('id');
    var row = $(this).closest('tr');

    $.ajax({
      url: '/admin/api/managers/' + managerId + '/achievements/' + achId,
      method: 'DELETE',
      success: function(response) {
        row.remove();
        $('#achievements-total').text(response.manager_total_points.toFixed(2));
      },
      error: function(xhr) {
        alert('Failed to delete: ' + (xhr.responseJSON && xhr.responseJSON.error || 'Unknown error'));
      }
    });
  });
});
```

### Step 2.3 — Manager List View Update

**File: `services/admin.py` — ManagerModelView**

The `_manage_achievements` formatter already links to `achievement.create_view`. Change it to link to the manager edit page:

```python
def _manage_achievements(view, context, model, name):
    url = url_for('.edit_view', id=model.id)
    return Markup(f'<a href="{url}">Manage achievements ({len(model.achievements)})</a>')
```

### Acceptance Criteria

- [ ] Manager edit page shows achievement table with existing data
- [ ] "Add Achievement" button opens modal
- [ ] Modal has Type, League, Season Select2 dropdowns
- [ ] Season dropdown cascades from League selection
- [ ] Points auto-calculate in modal
- [ ] "Add Another" appends to pending table and clears form
- [ ] "Save All" POSTs to bulk-add API
- [ ] Delete button removes existing achievements
- [ ] Total points sum displays correctly
- [ ] Manager list shows "Manage achievements (N)" link to edit page

---

## Phase 3: Bulk-Add API Endpoint (API-005)

**Goal:** Implement `POST /admin/api/managers/{manager_id}/achievements/bulk-add`

### Step 3.1 — Add Endpoint

**File: `blueprints/admin_api.py`**

```python
@admin_api_bp.route('/managers/<int:manager_id>/achievements/bulk-add', methods=['POST'])
@login_required
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

        # Load existing achievements for this manager (for duplicate check)
        existing = set(
            db.session.query(Achievement.type_id, Achievement.league_id, Achievement.season_id)
            .filter(Achievement.manager_id == manager_id)
            .all()
        )
        existing_keys = {(e[0], e[1], e[2]) for e in existing}

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

            # VR-003: Duplicate check
            key = (type_id, league_id, season_id)
            if key in existing_keys:
                skipped.append({
                    'type_name': ach_type.name,
                    'league_name': league.name,
                    'season_name': season.name,
                    'reason': 'Achievement already exists for this manager'
                })
                continue

            # Calculate points
            base_points = float(ach_type.base_points_l1 if league.code == '1' else ach_type.base_points_l2)
            multiplier = float(season.multiplier)
            final_points = round(base_points * multiplier, 2)

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
            created.append(achievement.id)
            existing_keys.add(key)  # Prevent intra-batch duplicates

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
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in POST /admin/api/managers/{manager_id}/achievements/bulk-add: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### Step 3.2 — Add GET Endpoint for Manager Achievements

```python
@admin_api_bp.route('/managers/<int:manager_id>/achievements', methods=['GET'])
@login_required
def get_manager_achievements(manager_id):
    """Get all achievements for a manager."""
    try:
        manager = db.session.get(Manager, manager_id)
        if not manager:
            return jsonify({'error': 'Manager not found'}), 404

        achievements = db.session.query(Achievement).filter_by(manager_id=manager_id).all()

        total_points = sum(a.final_points for a in achievements)

        return jsonify({
            'manager_id': manager.id,
            'manager_name': manager.name,
            'total_points': total_points,
            'achievements': [
                {
                    'id': a.id,
                    'type': {'id': a.type_id, 'code': a.type.code if a.type else '', 'name': a.type.name if a.type else ''},
                    'league': {'id': a.league_id, 'code': a.league.code if a.league else '', 'name': a.league.name if a.league else ''},
                    'season': {'id': a.season_id, 'code': a.season.code if a.season else '', 'name': a.season.name if a.season else '', 'multiplier': a.season.multiplier if a.season else 1.0},
                    'base_points': a.base_points,
                    'multiplier': a.multiplier,
                    'final_points': a.final_points,
                    'title': a.title,
                    'icon_path': a.icon_path
                }
                for a in achievements
            ]
        })

    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/managers/{manager_id}/achievements: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### Step 3.3 — Add DELETE Endpoint

```python
@admin_api_bp.route('/managers/<int:manager_id>/achievements/<int:achievement_id>', methods=['DELETE'])
@login_required
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

        db.session.delete(achievement)
        db.session.commit()

        invalidate_leaderboard_cache()

        total_points = db.session.query(db.func.sum(Achievement.final_points)) \
            .filter(Achievement.manager_id == manager_id).scalar() or 0.0

        return jsonify({
            'success': True,
            'deleted_id': achievement_id,
            'manager_total_points': total_points,
            'recalculation_triggered': True
        })

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### Acceptance Criteria

- [ ] `POST /managers/{id}/achievements/bulk-add` creates achievements correctly
- [ ] Duplicate detection works (returns skipped array)
- [ ] League/Season compatibility validation (VR-004)
- [ ] Points calculated correctly on server
- [ ] `GET /managers/{id}/achievements` returns full data
- [ ] `DELETE /managers/{id}/achievements/{ach_id}` removes achievement and validates ownership
- [ ] Cache invalidation triggered on all mutations
- [ ] `manager_total_points` returned in all mutation responses

---

## Phase 4: Delete Achievement + Validation

**Goal:** Ensure all validation rules are enforced and edge cases handled.

### Step 4.1 — Inline Duplicate Detection in Modal

In the manager_achievements.js, when user selects Type + League + Season:
1. Check against loaded existing achievements (from the `loadAchievements` data).
2. If duplicate, show inline warning: "This achievement already exists for this manager."
3. Disable the "Add Another" button until user changes selection.

### Step 4.2 — Duplicate Detection in Pending Table

Before adding to pending array in `#ach-add-btn` click handler:
```javascript
var isDuplicate = pendingAchievements.some(function(p) {
    return p.type_id === typeId && p.league_id === leagueId && p.season_id === seasonId;
});
if (isDuplicate) {
    alert('This achievement is already in the pending list.');
    return;
}
```

### Step 4.3 — Server-Side Validation (Already Covered in Phase 3)

The bulk-add endpoint validates:
- Existence of all FK references
- League/Season compatibility (VR-004)
- Uniqueness constraint (VR-003)
- Max 50 achievements per request

### Step 4.4 — Error Display

When bulk-add returns errors, display them in the UI:
- Highlight specific rows in the pending table that had errors.
- Show error messages next to each problematic row.
- Keep successfully created rows in the table (they were already committed).

### Acceptance Criteria

- [ ] Client-side duplicate prevention (against existing + pending)
- [ ] Server-side duplicate handling (skips, not errors)
- [ ] Clear error messages for all validation failures
- [ ] No negative points possible (base_points and multiplier are always non-negative by model design)

---

## Phase 5: Cleanup Old Achievement CRUD

**Goal:** Remove the old standalone Achievement CRUD from the admin menu while preserving backend functionality.

### Step 5.1 — Hide AchievementModelView from Menu

In `services/admin.py`, in the `init_admin` function, remove this line:

```python
admin.add_view(AchievementModelView(Achievement, db.session, name='Achievements', category='Data', menu_icon_type='fa', menu_icon_value='fa-trophy'))
```

Keep the `AchievementModelView` class definition in case an admin needs direct access via URL for emergency edits.

### Step 5.2 — Update Manager Link

Already done in Phase 2, Step 2.3 — the `_manage_achievements` formatter now links to the manager edit page instead of the old achievement create page.

### Step 5.3 — Repurpose or Remove Old Templates

The files `templates/admin/achievement_create.html` and `templates/admin/achievement_edit.html` are no longer linked from the UI. Options:

- **Option A (Recommended):** Keep them as-is. If someone navigates to `/admin/achievement/new/` directly, the form still works. This provides a safety net.
- **Option B:** Rename to `achievement_create_legacy.html` and `achievement_edit_legacy.html` to signal they are deprecated.
- **Option C:** Delete entirely. Only do this after Phase 1-4 are fully tested.

Recommendation: Start with Option A. After 2 weeks of production use with no issues, move to Option B.

### Step 5.4 — Update Spec Document

In `docs/SPECIFICATION.md`, update the implementation status table:

| Requirement | Old Status | New Status |
|-------------|-----------|------------|
| FR-03: Achievements | Partial | Complete |
| FR-03.1: Manager achievements | Not started | Complete |
| FR-04: Bulk add to manager | Not started | Complete |
| API-005: Bulk add endpoint | Not started | Complete |
| Duplicate error with link | Not started | Complete |

### Acceptance Criteria

- [ ] "Achievements" no longer appears in admin menu
- [ ] Achievement Types page remains accessible and functional
- [ ] Manager edit page has full achievement management
- [ ] All existing tests pass
- [ ] No dead links in the admin interface

---

## File Inventory

### New Files
| File | Purpose |
|------|---------|
| `templates/admin/achievement_type_create.html` | AchievementType create with calculator |
| `templates/admin/achievement_type_edit.html` | AchievementType edit with calculator |

### Modified Files
| File | Changes |
|------|---------|
| `services/admin.py` | AchievementTypeModelView: add templates; ManagerModelView: fix link; AchievementModelView: hide from menu |
| `templates/admin/manager_edit.html` | Add achievement table, modal, JS |
| `blueprints/admin_api.py` | Add 3 new endpoints (bulk-add, get, delete) |

### Unchanged Files (No modifications needed)
| File | Reason |
|------|--------|
| `models.py` | Schema is correct |
| `templates/admin/achievement_create.html` | Kept as legacy fallback |
| `templates/admin/achievement_edit.html` | Kept as legacy fallback |
| `templates/admin/manager_create.html` | No achievements on new managers (they start with zero) |

---

## Test Checklist

### API Tests
- [ ] `GET /admin/api/managers/{id}/achievements` — returns correct data for manager with achievements
- [ ] `GET /admin/api/managers/{id}/achievements` — returns empty array for manager with no achievements
- [ ] `POST /admin/api/managers/{id}/achievements/bulk-add` — creates achievements, returns correct summary
- [ ] `POST /admin/api/managers/{id}/achievements/bulk-add` — skips duplicates
- [ ] `POST /admin/api/managers/{id}/achievements/bulk-add` — validates FK existence
- [ ] `POST /admin/api/managers/{id}/achievements/bulk-add` — validates league/season compatibility
- [ ] `POST /admin/api/managers/{id}/achievements/bulk-add` — rejects >50 achievements
- [ ] `DELETE /admin/api/managers/{id}/achievements/{ach_id}` — deletes and returns updated total
- [ ] `DELETE /admin/api/managers/{id}/achievements/{ach_id}` — rejects if achievement belongs to different manager
- [ ] All endpoints require authentication

### UI Tests
- [ ] Achievement Types calculator shows correct base_points for League 1 and League 2
- [ ] Achievement Types calculator shows correct multiplier for selected season
- [ ] Manager edit page loads achievement table
- [ ] Add Achievement modal opens and initializes Select2 dropdowns
- [ ] Season dropdown enables and populates when league is selected
- [ ] Points display updates when all three fields are selected
- [ ] "Add Another" appends to pending table and clears form
- [ ] "Save All" sends correct payload and handles response
- [ ] Delete button removes achievement from table
- [ ] Total points sum is correct

### Regression Tests
- [ ] All existing API endpoint tests pass
- [ ] Achievement Types CRUD still works (create, edit, delete)
- [ ] Manager CRUD still works (create, edit, delete)
- [ ] Existing bulk-create endpoint (multiple managers) still works
- [ ] Leaderboard cache invalidation triggers on all mutations
