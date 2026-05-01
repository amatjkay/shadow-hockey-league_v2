# docs/ Index — read-trigger map

> **Purpose:** агенты читают этот файл (≤ 60 строк) **вместо** обхода всего `docs/`. Колонка «триггер» подсказывает, когда грузить конкретный файл; колонка «лимит чтения» — что брать из файла, чтобы не читать его целиком.

## Memory Bank (per AGENTS.md §1)

| Файл | Триггер | Лимит чтения |
|------|---------|--------------|
| `activeContext.md` | старт любой задачи | `head -40` |
| `techContext.md` | стек / БД / схема / зависимости | секцию через `grep -nE '^##? '` |
| `decisionLog.md` | «почему так», поиск ADR | `tail -5` или конкретная дата через `grep` |
| `progress.md` | статус задачи / прогресс / blockers | `tail -50`, **никогда целиком** |
| `projectbrief.md` | вопросы про цели проекта | целиком (≤ 50 строк) |
| `../PROJECT_KNOWLEDGE.md` | формула рейтинга, инварианты | секция через `grep` |
| `../AGENTS.md` | правила субагентов, Memory Bank protocol | целиком — инжектится через rule-block |
| `../.antigravityrules` | стандарты кода, бизнес-правила | целиком — инжектится через rule-block |

## Reference

| Файл | Триггер | Лимит чтения |
|------|---------|--------------|
| `API.md` | новый эндпоинт / изменение API | `grep -n "<route>"` ± 30 строк |
| `ARCHITECTURE.md` | новый модуль / cross-cutting concern | секция через `grep` |
| `MIGRATIONS.md` | Alembic / новая таблица / индекс | целиком (≤ 100 строк) |
| `ADMIN_RECALC.md` | recalc rating / ручная пересборка | целиком (≤ 50 строк) |
| `TROUBLESHOOTING.md` | runtime-ошибки в проде / dev | секция через `grep` |
| `GITHUB_CLI.md` | работа с PR/issues через `gh` | целиком (≤ 30 строк) |
| `AI_WORKFLOW.md` | декомпозиция сложной задачи | целиком (≤ 80 строк) |

## Audits

| Файл | Триггер |
|------|---------|
| `audits/audit-2026-04-28-analysis.md` | контекст по 11 deep-probe багам B1–B11 |
| `audits/audit-2026-04-28-plan.md` | план фаз 2A–4 |
| `audits/test-inventory-2026-04-29.md` | инвентарь тестов (Phase C) |
| `audits/linear-actions-2026-04-28.md` | сценарий синка с Linear |

## Archive (rotated by doc-curator)

| Файл | Содержит |
|------|----------|
| `archive/2026-Q1.md` | (если создан) entries из `progress.md` / `decisionLog.md` старше 30 дней |
| `archive/legacy-retrospectives.md` | (если создан) недатированные секции "Stabilization", "Feature Roadmap", "Known Open Issues" |

## Forbidden full-read

`progress.md`, `decisionLog.md`, `API.md`, `mcp-servers/**` — никогда не читать целиком; используй `grep` + диапазон строк или skill `codebase-map` / `token-budget`.
