# Анализ аудита 2026-04-28 + план декомпозиции

**Источник:** `audit-2026-04-28.md` (внешний файл, передан пользователем).
**Целевой репозиторий:** `amatjkay/shadow-hockey-league_v2` @ `main` (HEAD `ff6bca0`).
**Рабочая ветка анализа:** `devin/<ts>-audit-analysis` (этот PR — только аналитический артефакт, кода не меняет).

> Документ построен по правилам: каждый тезис — с привязкой к файлу/строке; всё неподтверждённое маркируется как «гипотеза».

---

## 0. Состояние интеграций / MCP

| Что нужно | Статус | Действие |
|---|---|---|
| GitHub | установлено | OK |
| **Linear MCP** | **НЕ установлено** (по `list_integrations` оба варианта — native `linear` и MCP `linear` — `is_installed: false`) | **Блокер для шага «подключи Linear»** — нужен установочный шаг от владельца аккаунта: `https://app.devin.ai/settings/mcp-marketplace/setup/linear` (MCP) или `https://app.devin.ai/settings/integrations/linear` (нативная интеграция). Без этого создание/обновление тикетов в Linear из этой сессии невозможно. |
| Skill `linear-sync` (внутри репо) | присутствует, описывает workflow | используется как контракт после подключения MCP |

Пока Linear MCP не подключён — в этом отчёте идёт **подготовка**: список тикетов для bulk-операций оформлен в виде задач T-L-* (см. §6), готовых к выполнению одним проходом, как только MCP появится.

---

## 1. Валидация тезисов аудита (по коду)

Каждый тезис проверен прямой инспекцией файлов в `main` HEAD `ff6bca0`. Расхождений с аудитом не обнаружено.

### 1.1. B9 — audit log не пишется в проде ✅ ПОДТВЕРЖДЕНО (P1)

- `services/audit_service.py:209` — `@event.listens_for(Session, "after_flush")` вешает листенер.
- `services/audit_service.py:214-216` — early-return, если в `flask.g.current_user_id` пусто.
- `services/audit_service.py:286-288` — `set_current_user_for_audit(user_id)` определена.
- `grep set_current_user_for_audit` по всему репозиторию: **15 хитов, ВСЕ — в тестах или документации.** Производственного вызова нет.
  - `tests/test_audit_delete.py` — 3 вызова.
  - `tests/integration/test_audit_logging.py` — 8 вызовов.
  - `services/audit_service.py:286` — определение.
  - `docs/decisionLog.md:114`, `docs/progress.md:126`, `PROJECT_KNOWLEDGE.md:42` — упоминания самой проблемы.
- `app.py` — нет `before_request`/Flask-Login-моста к `set_current_user_for_audit`.

**Противоречие документации:** `AGENTS.md` §5 декларирует «All admin CRUD actions logged via `audit_service.log_action()`». В коде `audit_service.log_action` отсутствует (есть только листенер `after_flush` и helper `_log_model_change`). Это вторая проблема — расхождение API между AGENTS.md и реальностью.

### 1.2. PR #16 — `api_limiter` инертен + memory storage ✅ ПОДТВЕРЖДЕНО

- `services/api.py:36-39` — создаётся локальный `Limiter(...)` без `init_app(app)`.
- `services/api.py` — **15 декораторов** `@api_limiter.limit("100 per minute")` на эндпоинтах (строки 92, 117, 171, 199, 256, 290, 332, 393, 439, 504, 533, 592, 702, 742, 849). Все — silent no-op без `init_app`.
- `app.py:160-165` — глобальный `Limiter` с `storage_uri="memory://"`. На gunicorn с 4 воркерами (`make prod` → `--workers 4`) счётчики не разделяются.

### 1.3. PR #17 — сравнение `league.code == "1"` в продакшен-коде ✅ ПОДТВЕРЖДЕНО

В производственном коде (без `scratch/`) — **9 мест**:

| Файл | Строки |
|---|---|
| `services/api.py` | 647, 817 |
| `services/rating_service.py` | 84, 319 |
| `services/admin.py` | 339 |
| `blueprints/admin_api.py` | 282, 362, 493, 802 |

Корректное место (через `parent_code`): `services/recalc_service.py:28` (комментарий описывает правильный алгоритм).

Также в `scratch/`: `verify_points.py:13`, `final_prod_sync.py:38`, `sync_ids.py:50`, `recalc_points.py:12`, `full_prod_recalc.py:36` — но это одноразовые скрипты; рефакторить не обязательно, можно оставить как есть с пометкой «archive only».

**Гипотеза (не подтверждено по миграции):** при появлении подлиги вида `2.1.1` или `3.x` все 9 мест посчитают очки по `base_points_l2` независимо от родителя. Подтверждение требует рассмотрения миграции `8a3279741758` и поля `League.base_points_field` (упомянуто в описании PR #17, но не открывал в этой сессии). Помечено как T-V-2 (verification task).

### 1.4. PR #28 — ProxyFix default ✅ ПОДТВЕРЖДЕНО

- `app.py:59` — `proxy_count = int(app.config.get("PROXY_FIX_X_FOR", os.environ.get("PROXY_FIX_X_FOR", "1")))`. **Дефолт = "1"**.
- `services/admin.py:585` — комментарий ссылается на ARCHITECTURE.md и предупреждает «set `PROXY_FIX_X_FOR=0`» для не-прокси-окружений.
- `services/admin.py:575` — упоминание ProxyFix в `app.create_app`.

PR #28 предлагает дефолт `"0"`. Аудит корректно описывает риск: если на проде сейчас просто смержить — клиенты будут бакетиться под IP nginx (127.0.0.1), один клиент сможет залочить login для всех. Прод-конфиг прода (env-переменные на сервере) недоступен из этой сессии — выводы по «текущему состоянию прода» **гипотеза**, требующая шага T-V-1.

### 1.5. B10 — `/health` без `socket_timeout` ✅ ПОДТВЕРЖДЕНО (P2)

- `blueprints/health.py:75-82` — `redis.Redis(host=..., port=..., socket_connect_timeout=2)`. **`socket_timeout` не задан.** Аудит верен: connect timeout без read timeout — `redis_client.ping()` может зависнуть на read до системного дефолта.

### 1.6. B11 — баннер метрик ⚠️ ЧАСТИЧНО ПОДТВЕРЖДЕНО (P3 косметика)

- `app.py:235` — лог-сообщение: `"Default metrics: http_requests_total, http_request_duration_seconds"`. Утверждение про counter `_total` в коде не валидировал (требует посмотреть, какие default-метрики регистрирует `prometheus_flask_exporter`). Помечено T-V-3.

---

## 2. Состояние документации vs реальность

| Файл | Расхождение | Источник |
|---|---|---|
| `AGENTS.md` §5 | **Было:** «All admin CRUD actions logged via `audit_service.log_action()`» → **Стало (факт):** функции `log_action()` в `services/audit_service.py` не существует, листенер `after_flush` не получает `current_user_id` в продакшене (см. §1.1). | `services/audit_service.py:209-216`, `:286` |
| `docs/activeContext.md` (раздел Status) | **Было:** «Branch: `feature/admin-enhancement` (HEAD `1da8d6d`, post PR #23 merge)» → **Стало (факт):** `feature/admin-enhancement` смержена в `main` через PR #25; текущий HEAD `main` = `ff6bca0` (PR #29, #30 — TIK-35). Активный branch для команды теперь `main`. | `git log --oneline -5` |
| `docs/activeContext.md` Active Blockers | Заявлено «None». **Стало (факт):** есть открытый блокер B9 (P1) — это явное противоречие самому же файлу `progress.md:126` и `PROJECT_KNOWLEDGE.md:42`. | сравнение трёх файлов |
| `Makefile` `check` target | Сейчас mypy закомментирован, flake8 — с `extend-ignore`. Аудит прав в §«Tech debt»: 84 mypy ошибок и 131 flake8 нарушений в ignore — это техдолг, а не «зелёный CI». Документировать как «degraded check». | `Makefile:38-50` |

---

## 3. Список проблем (источник → проблема)

| # | Источник | Проблема | Серьёзность |
|---|---|---|---|
| P1 | `services/audit_service.py:214-216` + отсутствие в `app.py` `before_request` | B9: ни одно admin-действие в проде не пишется в audit-log. Compliance-нарушение vs `AGENTS.md` §5. | **P1** |
| P2 | `services/api.py:36-39`, 15 декораторов | T-002: `api_limiter` без `init_app` — все per-endpoint лимиты выключены. Любой клиент может бесконечно стучать в `/api/*`. | **P1** |
| P3 | `app.py:160-165` | T-011: `storage_uri="memory://"` на 4 gunicorn-воркерах → лимиты считаются per-worker, в 4 раза больше реального лимита. | **P2** |
| P4 | `services/api.py:647,817`, `services/rating_service.py:84,319`, `services/admin.py:339`, `blueprints/admin_api.py:282,362,493,802` | T-003/004/007/020: `league.code == "1"` вместо `League.base_points_field` в 9 местах → hidden-bug при появлении вложенных подлиг. | **P2** |
| P5 | `app.py:59` | PR #28: дефолт `PROXY_FIX_X_FOR="1"` — IP-spoof уязвимость в не-прокси deployment'ах. На текущем проде смягчается nginx, но мердж #28 без согласования env-переменной сломает per-IP лимит. | **P2** |
| P6 | `blueprints/health.py:80` | B10: отсутствует `socket_timeout` в `redis.Redis(...)`. В дев-окружениях `/health` может висеть 5+ сек. | **P2** (dev), **P3** (prod) |
| P7 | `app.py:235` | B11: баннер `Default metrics: http_requests_total, ...` ссылается на counter, который, судя по аудиту, не зарегистрирован. | P3 |
| P8 | `Makefile:38-50` + `pyproject.toml:[tool.mypy]` | Tech debt: 84 mypy errors, 131 flake8 в `extend-ignore`. CI «зелёный» — потому что check относительно мягкий. | P3 |
| P9 | `docs/activeContext.md` Status/Blockers | Внутренняя неконсистентность доков: `Active Blockers: None` соседствует с задокументированным P1-багом. | P3 (docs hygiene) |
| P10 | `AGENTS.md` §5 | Доки описывают несуществующий API (`audit_service.log_action()`). | P3 (docs hygiene) |

---

## 4. Улучшения (что менять и зачем)

Каждое улучшение проверяемо: указан файл и тест.

### I-1. Audit log — production wiring (для P1)
- **Что:** добавить `before_request` в `app.py::create_app()`, читающий `flask_login.current_user` и вызывающий `set_current_user_for_audit(current_user.id)`. Плюс `teardown_request` сбрасывает контекст.
- **Эффект:** все admin-CRUD из проды пишут audit-row.
- **Тест:** интеграционный — выполнить admin-mutation залогиненным юзером, проверить запись в `audit_log`.

### I-2. Rate limiter — единый источник (для P2/P3)
- Уже реализовано в **PR #16**. Решение — перенаправить base на `main` и смержить (см. §5 действий).

### I-3. base_points unification (для P4)
- Уже реализовано в **PR #17**. Зависимость от #16. Перенаправить и смержить после #16.

### I-4. ProxyFix — безопасный default (для P5)
- Уже реализовано в **PR #28**, но требует pre-merge step: установить `PROXY_FIX_X_FOR=1` в проде (env/systemd/.env). Без этого после мерджа per-IP лимит на проде сломается.

### I-5. /health — read timeout (для P6)
- **Что:** `blueprints/health.py:75-82` — добавить `socket_timeout=1.0` в `redis.Redis(...)`.
- **Эффект:** /health отвечает за <1.5s даже без redis в dev.

### I-6. Metrics banner consistency (для P7)
- **Что:** в `app.py:233-236` либо убрать `http_requests_total` из лога, либо зарегистрировать counter в `prometheus_flask_exporter`. Перед фиксом — проверить, что реально торчит на `/metrics`.

### I-7. Tech-debt PR (для P8)
- Два отдельных трека: mypy clean-up (по файлам), flake8 ignore reduction. Не критично, отдельный roadmap.

### I-8. Docs sync (для P9/P10)
- `docs/activeContext.md` — обновить раздел Status (HEAD/branch) и Blockers (внести B9 явно).
- `AGENTS.md` §5 — заменить «logged via `audit_service.log_action()`» на актуальное описание (`after_flush` listener + `set_current_user_for_audit` setter).

---

## 5. Открытые вопросы для пользователя (нужны ответы прежде, чем что-то менять)

1. **Linear MCP:** установить нативную интеграцию `linear` или MCP-сервер `linear`? Без этого задачи T-L-* останутся на бумаге. (см. §0)
2. **PR #11:** подтверждаете ли «закрыть без мерджа» (контент уже в `main` через #25)?
3. **Стек `devin/integration-analyst-fixes` (#15/#16/#17):**
   - PR #16 и #17 содержат реальные баги — выбрать один из вариантов: (a) перенаправить base #16 на main → смержить → перебазировать #17 на main → смержить; (b) смержить весь стек integration-analyst-fixes в main одним вливанием; (c) закрыть стек и перенести фиксы новыми PR.
   - PR #15 (cleanup mcp-servers/) — закрыть, перенаправить на main, или оставить?
4. **PR #28:** готов ли прод-конфиг сегодня же получить `PROXY_FIX_X_FOR=1` (env/systemd)? Если да — выполнить шаг и затем мерджить #28. Если нет — закрыть #28 и оставить текущий «небезопасный» default (на проде за nginx это OK).
5. **TIK-12, TIK-18, TIK-19:** подтверждаете «cancel»? TIK-16 — «mark Done»?
6. **Cleanup веток (§5 аудита):** разрешаете удаление 13 уже-смерженных веток списком?

---

## 6. Декомпозиция задач (≤1 час каждая, для исполнения другим ИИ)

Формат: `ID | Что сделать | Зависимости | Критерий готовности`.

### Группа V — верификация (предусловия для остальных задач)

- **T-V-1** | Считать прод-конфиг (`/etc/systemd/system/shadow-hockey-league.service`, `.env` на сервере) и подтвердить наличие/отсутствие `PROXY_FIX_X_FOR`. **Зависимости:** SSH-доступ к проду или ответ пользователя. **Готовность:** в комментарии к этому PR указано фактическое значение env на проде.
- **T-V-2** | Подтвердить гипотезу из §1.3 — открыть миграцию `migrations/versions/8a3279741758_*.py` и `models.py::League.base_points_field`, документировать поведение для подлиг `2.1`, `2.2` и гипотетических `2.1.1`, `3.x`. **Зависимости:** нет. **Готовность:** в `docs/audits/audit-2026-04-28-analysis.md` добавлен раздел «§1.3 verification» с цитатой из кода.
- **T-V-3** | Подтвердить B11 — запустить app локально, обратиться к `/metrics`, выписать реальный список метрик, сравнить с лог-баннером `app.py:235`. **Зависимости:** dev-server. **Готовность:** в этот же документ добавлен список фактических метрик.

### Группа A — PR triage

- **T-A-1** | Закрыть PR #11 без мерджа. **Зависимости:** ответ на вопрос §5.2. **Готовность:** PR в статусе `closed`, без коммита в `main`.
- **T-A-2** | По решению пользователя: `git rebase --onto main devin/integration-analyst-fixes devin/1777322380-rate-limiter-fix` (или равносильный workflow), переориентировать base PR #16 на `main`. **Зависимости:** §5.3 = вариант (a). **Готовность:** PR #16 base = `main`, CI зелёный или unchanged.
- **T-A-3** | После A-2: ребейз `devin/1777323700-points-unification` поверх обновлённого `devin/1777322380-rate-limiter-fix` или поверх `main` (после мерджа #16). PR #17 base = `main`. **Зависимости:** T-A-2 + мердж #16. **Готовность:** PR #17 base = `main`, CI без новых regressions.
- **T-A-4** | Решение по PR #15: либо закрыть, либо переориентировать на `main`. **Зависимости:** §5.3. **Готовность:** PR в финальном статусе.
- **T-A-5** | Установить `PROXY_FIX_X_FOR=1` в `/etc/systemd/system/shadow-hockey-league.service` или прод-`.env`, перезапустить сервис, проверить `/health`. **Зависимости:** §5.4 = «да». **Готовность:** `systemctl show … | grep PROXY_FIX_X_FOR` возвращает `=1`.
- **T-A-6** | После T-A-5: переориентировать PR #28 на `main` и смержить. **Зависимости:** T-A-5. **Готовность:** #28 merged, на проде после деплоя `request.remote_addr` = реальный IP клиента (smoke-тест: rate-limit 11 fail-логинов с одного IP даёт 429).

### Группа B — баги, требующие code change

- **T-B9-1** | В `app.py::create_app()` добавить:
  ```python
  @app.before_request
  def _audit_user_context():
      from flask_login import current_user
      if current_user.is_authenticated:
          from services.audit_service import set_current_user_for_audit
          set_current_user_for_audit(current_user.id)
  ```
  **Зависимости:** нет. **Готовность:** локально admin создаёт Achievement → `SELECT COUNT(*) FROM audit_log WHERE action='CREATE'` увеличивается на 1.
- **T-B9-2** | Добавить интеграционный тест `tests/integration/test_audit_logging_e2e.py`: логин под admin → POST на admin-endpoint → проверить наличие `AuditLog`-row. **Зависимости:** T-B9-1. **Готовность:** тест зелёный, в `make test` count `+1`.
- **T-B9-3** | Обновить `AGENTS.md` §5 (заменить ссылку на `log_action()` на корректное описание listener'а), `docs/activeContext.md` (Status/Blockers), `docs/decisionLog.md` (decision: «B9 fixed in PR …»). **Зависимости:** T-B9-1. **Готовность:** docs-PR с тремя файлами.
- **T-B10-1** | `blueprints/health.py:75-82` — добавить `socket_timeout=1.0` в `redis.Redis(...)`. **Зависимости:** нет. **Готовность:** локально без redis `/health` отвечает <1500ms (`time curl localhost:5000/health`).
- **T-B11-1** | Запустить app локально, выписать фактический набор метрик с `/metrics`, синхронизировать строку `app.py:235` ИЛИ зарегистрировать недостающие counter'ы. **Зависимости:** T-V-3. **Готовность:** баннер в логе совпадает 1-в-1 с `/metrics`.

### Группа L — Linear backlog (только после установки Linear MCP)

- **T-L-1** | Cancel TIK-12 (premature optimization). **Зависимости:** Linear MCP. **Готовность:** статус Cancelled, комментарий со ссылкой на `services/cache_service.py::@cache.memoize`.
- **T-L-2** | Cancel TIK-18 (no scope), TIK-19 (covered by tests). **Зависимости:** Linear MCP. **Готовность:** оба Cancelled.
- **T-L-3** | Mark TIK-16 as Done (выполнено в TIK-33 / PR #24). **Зависимости:** Linear MCP. **Готовность:** статус Done, ссылка на PR #24.
- **T-L-4** | Создать новый тикет TIK-NN: B9 — Audit log not wired in production. Priority: P1. Включить ссылки на `services/audit_service.py:209-216`, `:286`, и план T-B9-1/2/3. **Зависимости:** Linear MCP. **Готовность:** тикет открыт, P1, in `Todo`.
- **T-L-5** | Создать тикет TIK-NN: B10 — `/health` Redis blocking без timeout. Priority: P2 (dev), P3 (prod). Ссылка на `blueprints/health.py:80`. **Зависимости:** Linear MCP. **Готовность:** тикет открыт.
- **T-L-6** | Создать тикет TIK-NN: B11 — Metrics banner mismatch. Priority: P3. Ссылка на `app.py:235`. **Зависимости:** Linear MCP, T-V-3. **Готовность:** тикет открыт.
- **T-L-7** | TIK-14 (player search) — оставить открытым, понизить приоритет до P3 с пояснением. **Зависимости:** Linear MCP. **Готовность:** комментарий + label.
- **T-L-8** | TIK-15 (achievement preview) — оставить открытым P3. **Зависимости:** Linear MCP. **Готовность:** комментарий.
- **T-L-9** | TIK-17 (OpenAPI) — оставить открытым P3 «when needed». **Зависимости:** Linear MCP. **Готовность:** комментарий.

### Группа C — cleanup веток (после §5 решений)

- **T-C-1** | `git push origin --delete <ветка>` для 13 смерженных веток из §5 аудита (`origin/devin/tik-35-test-fixes-followup`, …, `origin/tik-5/audit-deletion-logging`). **Зависимости:** §5.6 ответ. **Готовность:** `git branch -r` не содержит указанных.
- **T-C-2** | По `origin/feature/tech-debt-and-rating-refactor` — diff vs `main`, решение «keep / archive / delete». **Зависимости:** §5.6 ответ. **Готовность:** ветка либо удалена, либо помечена комментарием в `docs/decisionLog.md`.

### Группа D — tech debt (отдельный roadmap, низкий приоритет)

- **T-D-1** | Зафиксировать список 84 mypy ошибок в `docs/audits/mypy-debt-2026-04-28.md` (вывод `mypy .` с включённым в `Makefile::check`). **Зависимости:** нет. **Готовность:** файл создан с полным списком, по 1 строке на ошибку.
- **T-D-2** | Зафиксировать 131 flake8 нарушение из `extend-ignore` (отдельно по каждому коду: E402, E711, …). **Зависимости:** нет. **Готовность:** файл `docs/audits/flake8-debt-2026-04-28.md` с разбивкой по error-code.
- **T-D-3** | Создать в Linear эпик «mypy zero», подзадачи по файлам (18 файлов). **Зависимости:** Linear MCP, T-D-1. **Готовность:** эпик + 18 подзадач.
- **T-D-4** | Создать в Linear эпик «flake8 zero», подзадачи по error-code. **Зависимости:** Linear MCP, T-D-2. **Готовность:** эпик + N подзадач.

---

## 7. Что НЕ делается в этом PR

Этот PR — только аналитический документ. Он **не меняет** код приложения, миграции, тесты, конфиги. Любые задачи из §6 берутся в отдельные PR'ы, по одной группе за раз.
