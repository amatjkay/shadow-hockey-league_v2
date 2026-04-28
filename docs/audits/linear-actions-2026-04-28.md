# Linear actions — execution plan after audit-2026-04-28

> **Why a separate file?** Linear MCP установлен в организации, но его tool'ы регистрируются только при старте сессии Devin. Текущая сессия стартовала ДО установки — поэтому tool'ы вида `mcp_linear_*` недоступны. Этот файл — точный сценарий, который пройдёт в одну прогонку из новой сессии Devin, либо вручную через Linear UI.
>
> **Формат:** для каждого действия указан желаемый результат, identifier тикета (TIK-NN), тулз-вызовы (если делать через MCP), и ссылка на источник в коде/доках.

---

## A. Изменения статусов в существующих тикетах

| ID | Action | Reason | Source |
|---|---|---|---|
| TIK-12 | **Cancel** | Premature optimization. `RatingService.build_leaderboard()` уже кешируется через `@cache.memoize` на 5 минут (`services/rating_service.py`); реальной деградации производительности нет. Если станет медленно — переоткроем. | `audit-2026-04-28.md` §3, `audit-2026-04-28-analysis.md` §6 T-L-1 |
| TIK-16 | **Mark Done** | Уже выполнено в TIK-33 / PR #24 (docs refresh). Таблицы баллов и множителей актуализированы в `PROJECT_KNOWLEDGE.md`. | `audit-2026-04-28.md` §3 |
| TIK-18 | **Cancel** | No clear scope. Tandem managers уже представлены через `Manager.partner_id` self-FK; что именно «формализовать» — не определено. Открывать заново при появлении конкретного требования. | `audit-2026-04-28.md` §3 |
| TIK-19 | **Cancel** | Покрывается тестами. `tests/test_rating_service.py` уже содержит 30 кейсов формулы; отдельный prod-cross-check скрипт overkill. | `audit-2026-04-28.md` §3 |

### MCP tool calls (для исполнения в новой сессии)

```
# Шаг 1: получить team UUID и states
mcp_linear_linear_get_teams

# Шаг 2: резолвить identifier → UUID
mcp_linear_linear_search_issues_by_identifier
  identifiers: ["TIK-12", "TIK-16", "TIK-18", "TIK-19"]

# Шаг 3: применить статусы (UUID состояний — из шага 1)
mcp_linear_linear_edit_issue
  issueId: <TIK-12-uuid>
  stateId: <Cancelled-uuid>

mcp_linear_linear_edit_issue
  issueId: <TIK-16-uuid>
  stateId: <Done-uuid>

mcp_linear_linear_edit_issue
  issueId: <TIK-18-uuid>
  stateId: <Cancelled-uuid>

mcp_linear_linear_edit_issue
  issueId: <TIK-19-uuid>
  stateId: <Cancelled-uuid>
```

При cancel — добавить комментарий со ссылкой на этот файл и причиной.

---

## B. Новые тикеты на подтверждённые баги

> Создавать через `mcp_linear_linear_create_issue` (точное имя инструмента — после первой инвокации MCP). Поле `teamId` берётся из `mcp_linear_linear_get_teams`.

### B.1. TIK-NN: B9 — Audit log not wired in production (P1)

**Title:** `[B9] Audit log not written in production — set_current_user_for_audit() never called from app code`

**Priority:** Urgent (P1)

**Labels:** `security`, `compliance`, `bug`

**Description:**

```markdown
## Problem

`AGENTS.md` §5 декларирует: «All admin CRUD actions logged via audit_service.log_action()».
В реальности:

1. Функция `audit_service.log_action()` в коде **отсутствует**. Есть только листенер
   `@event.listens_for(Session, "after_flush")` в `services/audit_service.py:209-216`.
2. Листенер early-return'ит, если `flask.g.current_user_id` пуст:
   ```python
   current_user_id = getattr(g, "current_user_id", None)
   if not current_user_id:
       return  # Skip if no authenticated user
   ```
3. Setter `set_current_user_for_audit(user_id)` определён в `services/audit_service.py:286-288`,
   но **никем не вызывается** в production-коде. `grep set_current_user_for_audit`:
   - 3 хита в `tests/test_audit_delete.py`
   - 8 хитов в `tests/integration/test_audit_logging.py`
   - 1 хит — определение
   - 3 хита — упоминания самой проблемы в `docs/decisionLog.md:114`, `docs/progress.md:126`,
     `PROJECT_KNOWLEDGE.md:42`

→ В production ни одно admin-действие не пишется в `audit_log`. Compliance-нарушение
с момента введения механизма.

## Acceptance criteria

- [ ] В `app.py::create_app()` зарегистрирован `before_request`, который читает
      `flask_login.current_user` и вызывает `set_current_user_for_audit(current_user.id)`
      для аутентифицированного пользователя.
- [ ] Зарегистрирован `teardown_request` (или эквивалент), сбрасывающий контекст.
- [ ] Интеграционный тест `tests/integration/test_audit_logging_e2e.py`: логин → admin
      mutation → проверка строки в `audit_log`.
- [ ] `AGENTS.md` §5 обновлён: либо переписан на корректный API (listener-based), либо
      добавлена реальная функция `log_action()`.
- [ ] `docs/activeContext.md` Active Blockers — B9 убран после фикса.

## References

- Code: `services/audit_service.py:209-216`, `services/audit_service.py:286-288`
- Audit: `audit-2026-04-28.md` §4 B9
- Analysis: `docs/audits/audit-2026-04-28-analysis.md` §1.1, §6 T-B9-1/2/3

## Effort

≤ 1 час фикс + 30 мин тест + 15 мин docs.
```

### B.2. TIK-NN: B10 — `/health` blocks without socket_timeout (P2)

**Title:** `[B10] /health endpoint blocks 5-7s when Redis unavailable — missing socket_timeout`

**Priority:** Medium (P2 dev / P3 prod)

**Labels:** `bug`, `performance`, `dev-experience`

**Description:**

```markdown
## Problem

`blueprints/health.py:75-82`:

```python
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    socket_connect_timeout=2,
)
redis_client.ping()
```

Установлен `socket_connect_timeout=2`, но `socket_timeout` не задан. Если Redis принимает
соединение, но не отвечает (или сетевые проблемы после connect), `ping()` зависает до
системного дефолта. На dev-окружениях без Redis наблюдается зависание `/health` на 5-7
секунд.

## Acceptance criteria

- [ ] Добавлен `socket_timeout=1.0` в `redis.Redis(...)`.
- [ ] Локальный smoke (без redis): `time curl localhost:5000/health` возвращает <1.5s.
- [ ] Регрессионный тест: mock Redis, имитирующий медленный read; `/health` не висит.

## References

- Code: `blueprints/health.py:75-82`
- Audit: `audit-2026-04-28.md` §4 B10
- Analysis: `docs/audits/audit-2026-04-28-analysis.md` §1.5, §6 T-B10-1

## Effort

≤ 15 минут фикс + 30 мин тест.
```

### B.3. TIK-NN: B11 — Metrics banner mismatches /metrics output (P3)

**Title:** `[B11] App startup banner advertises http_requests_total but /metrics doesn't expose it`

**Priority:** Low (P3 cosmetic)

**Labels:** `bug`, `observability`

**Description:**

```markdown
## Problem

`app.py:233-236`:

```python
app.logger.info("Prometheus metrics enabled at /metrics")
app.logger.info(
    "Default metrics: http_requests_total, http_request_duration_seconds"
)
```

Согласно аудиту, на `/metrics` фактически торчит только `http_request_duration_seconds`
(histogram). Counter `http_requests_total` не зарегистрирован в `prometheus_flask_exporter`.

**Гипотеза**, требующая верификации (T-V-3): запустить app локально, дёрнуть `/metrics`,
выписать реальный список metric families.

## Acceptance criteria

- [ ] Запустить `make run` локально, выписать `curl localhost:5000/metrics | grep -E '^# (HELP|TYPE)'`.
- [ ] Если `http_requests_total` отсутствует — либо убрать из лог-баннера, либо
      зарегистрировать counter через `PrometheusMetrics(app).request_counter` (если ещё не).
- [ ] Лог-баннер 1-в-1 совпадает с фактическим `/metrics` после фикса.

## References

- Code: `app.py:233-236`
- Audit: `audit-2026-04-28.md` §4 B11
- Analysis: `docs/audits/audit-2026-04-28-analysis.md` §1.6, §6 T-V-3, T-B11-1

## Effort

≤ 30 минут (с верификацией T-V-3).
```

### MCP tool calls (для исполнения)

```
mcp_linear_linear_create_issue
  teamId: <team-uuid>
  title: "[B9] Audit log not written in production..."
  description: <см. B.1>
  priority: 1   # Urgent
  labels: ["security", "compliance", "bug"]

mcp_linear_linear_create_issue
  teamId: <team-uuid>
  title: "[B10] /health endpoint blocks 5-7s..."
  description: <см. B.2>
  priority: 3   # Medium
  labels: ["bug", "performance"]

mcp_linear_linear_create_issue
  teamId: <team-uuid>
  title: "[B11] App startup banner mismatch..."
  description: <см. B.3>
  priority: 4   # Low
  labels: ["bug", "observability"]
```

---

## C. Тикеты, которые остаются открытыми (без изменений статуса)

| ID | Action | Comment |
|---|---|---|
| TIK-14 | Keep open, понизить приоритет до P3 | Player Search UI на главной — реальный feature gap, но 42 менеджера помещаются на одну страницу. Не срочно. |
| TIK-15 | Keep open, P3 | Admin Achievement Preview — небольшая UX-доработка. |
| TIK-17 | Keep open, P3 | OpenAPI spec — полезно при появлении внешних интеграторов. Сейчас интеграций нет. |

---

## D. Чек-лист для исполнителя в новой Devin-сессии

- [ ] Подтвердить, что Linear MCP tool'ы зарегистрированы (`mcp_linear_linear_get_teams` отвечает).
- [ ] Получить team UUID и states (особенно UUID состояний `Cancelled` и `Done`).
- [ ] Применить §A (4 status update'а).
- [ ] Создать 3 новых тикета по §B (B9 / B10 / B11) с описаниями выше.
- [ ] В каждом из новых тикетов добавить ссылку на PR #31 (analysis PR) и на конкретный
      коммит `docs/audits/audit-2026-04-28-analysis.md`.
- [ ] Обновить `docs/audits/audit-2026-04-28-analysis.md` §6 — заменить `TIK-NN` на
      реальные identifier'ы новых тикетов.
- [ ] Закоммитить обновление в ветку `devin/1777399212-audit-analysis`.
