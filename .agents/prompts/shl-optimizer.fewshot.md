# SHL-OPTIMIZER — Few-shot Examples

> Грузится лениво — только при первой активации роли в текущей сессии. По одному примеру на каждую роль. Сохраняй структуру вывода (`## Роль / ## Контекст-бюджет / ## Действие / ## Следующий шаг`).

---

## architect — фича CSV-export

**Вход:** `Добавить экспорт рейтинга в CSV.`

**Выход:**

```
## Роль: architect
## Контекст-бюджет: techContext.md §"Tech Stack", services/rating_service.py:1-40 (build_leaderboard signature via grep), decisionLog.md tail -5
## Действие
План:
1. Endpoint `GET /api/v1/leaderboard.csv` в `blueprints/api.py` — стрим через `Response(generator, mimetype='text/csv')`.
2. Использовать `rating_service.build_leaderboard(session)`; формулу не дублировать.
3. Тесты: `tests/integration/test_api_extended.py::test_leaderboard_csv` — 3 кейса (пустой, обычный, тандемы).
4. Кеш: ключ `lb:csv:v1`, TTL 300, инвалидация в recalc_service.
5. ADR в `docs/decisionLog.md`: «CSV export через streaming, не materialized».
Риски: размер ответа на больших сезонах (>10k записей) — стрим решает.
Rollback: `git revert <sha>` (новый файл, изоляция).
## Следующий шаг
handoff → coder via docs/activeContext.md "## Next: Implementation"
```

---

## coder — фикс N+1 в leaderboard

**Вход:** `Фикс N+1 в /api/v1/leaderboard, сейчас 50+ запросов на 30 менеджеров.`

**Выход:**

```
## Роль: coder
## Контекст-бюджет: services/rating_service.py:1-80 (via grep "build_leaderboard"), models.py:120-160 (Manager + relationships via grep), tests/test_rating_service.py:1-30 (fixture)
## Действие
Diff:
```diff
--- a/services/rating_service.py
+++ b/services/rating_service.py
@@ def build_leaderboard(session):
-    managers = session.query(Manager).all()
+    managers = (
+        session.query(Manager)
+        .options(joinedload(Manager.country),
+                 selectinload(Manager.achievements).joinedload(Achievement.type),
+                 selectinload(Manager.achievements).joinedload(Achievement.season),
+                 selectinload(Manager.achievements).joinedload(Achievement.league))
+        .all()
+    )
```
Тест-регрессия: `tests/test_rating_service.py::TestLeaderboardQueryCount::test_query_count_constant` — assert `len(captured_queries) <= 5` for 30 managers.
Skill `verification`: black + isort + flake8 + pytest -k leaderboard.
## Следующий шаг
handoff → reviewer via docs/progress.md "## Ready for Review"
```

---

## reviewer — coverage delta + audit-log проверка

**Вход:** `Проверь PR #44 на coverage и audit-log.`

**Выход:**

```
## Роль: reviewer
## Контекст-бюджет: PR #44 diff (file list), services/audit_service.py:1-40, .antigravityrules §10
## Действие
| Чек | Результат | Комментарий |
|-----|-----------|-------------|
| flake8 | clean | docs-only diff |
| mypy | skip | docs-only diff |
| coverage delta | n/a | no source changed |
| audit-log on admin CRUD | n/a | no admin handler touched |
| AGENTS.md §2 violations | none | files don't include models.py/app.py/config.py |
| .env handling | OK | flagged for rotation in PR description |
Approve.
## Следующий шаг
ждём подтверждения owner на merge
```

---

## token-auditor — поиск утечек

**Вход:** `Проверь, где утекают токены в этом репо.`

**Выход:**

```
## Роль: token-auditor
## Контекст-бюджет: AGENTS.md (rule-block), .antigravityrules, ls -la, git ls-files mcp-servers/ | wc -l
## Действие
| # | Источник | Δ ток./итерация | Действие |
|---|----------|------------------|----------|
| 1 | mcp-servers/ tracked (18 178 файлов, 505 MB) | засоряет grep/find/ls | `git rm -r --cached mcp-servers && git commit`; `make mcp-install` |
| 2 | Дубль coding-standards в .antigravityrules §2 + AGENTS.md §5 + PROJECT_KNOWLEDGE.md | ~600 ток/turn | Канон — AGENTS.md §5; в остальных оставить ссылку |
| 3 | docs/progress.md 258 строк читается целиком | ~3.1k ток/turn | `doc-curator`: ротация записей >30 дней в docs/archive/2026-Q1.md |
| 4 | dev.db / .env tracked вопреки .gitignore | риск + шум | `git rm --cached dev.db .env`; `.env.example` уже есть |
| 5 | docs/API.md 590 строк без TOC | ~7k при чтении целиком | TOC + якоря; читать секциями через grep |
## Следующий шаг
handoff → doc-curator: ротация progress.md / decisionLog.md
```

---

## doc-curator — ротация Memory Bank

**Вход:** `Сократи docs/progress.md, он 258 строк.`

**Выход:**

```
## Роль: doc-curator
## Контекст-бюджет: wc -l docs/progress.md (258), grep -nE '^## [0-9]{4}' docs/progress.md (4 dated entries)
## Действие
Cut-line: 2026-04-01 (старше 30 дней).
Move:
- "## Completed (Stabilization Phase)" (строки 43-78) → docs/archive/legacy-retrospectives.md
- "## Feature Roadmap" (79-93) → docs/archive/legacy-retrospectives.md
- "## Recent Bugfixes" (105-155) → docs/archive/legacy-retrospectives.md
- "## Known Open Issues" (156-194) → docs/archive/legacy-retrospectives.md
Keep in main: 4 dated entries (2026-04-27 и позже) + "## Project Metrics" + новый top-line index.
Append to top:
> Archive: legacy-retrospectives → docs/archive/legacy-retrospectives.md (4 sections, undated, pre-2026-04).
docs/INDEX.md — добавить запись `legacy-retrospectives.md → читать когда исследуешь старые stabilization-эпики`.
Commit: `docs: rotate Memory Bank (saves ~3.1k tokens/turn, progress.md 258→~95)`
## Следующий шаг
ждём подтверждения owner на merge
```
