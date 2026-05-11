---
name: "Well-formed task"
about: "Чеклист корректно поставленной задачи (для людей и AI-агентов)."
title: "[TASK] <короткое описание>"
labels: ["task"]
---

> Source: `.agents/skills/task-formulation/SKILL.md`.
> Fill every section before assigning to a coder / AI agent.
> If a section can't be filled — stop, ask the requester, and decompose.

## 1. Контекст (Why?)

- **Проблема / ценность:** какую боль лечим или какую ценность даём?
  (Не *«сделать кнопку»*, а *«пользователь не может найти выход»*.)
- **Компоненты системы:** какие пакеты / сервисы / шаблоны затронуты?
  Дайте ссылку в `docs/wiki/Home.md` или `docs/ARCHITECTURE.md`, чтобы
  LLM без проектного контекста ориентировался за 30 секунд.

## 2. Образ результата (What?)

- **Happy path:** 3–7 шагов от лица пользователя — что произойдёт в
  идеальном сценарии?
- **Corner cases:** минимум 2 — пустые данные, неверная роль, гонка с
  кэшем, разорванная сеть, частично проинициализированная БД.

## 3. Definition of Done

- [ ] Acceptance criterion 1 — …
- [ ] Acceptance criterion 2 — …
- [ ] Acceptance criterion 3 — … *(опционально)*
- **Verification:** какие тесты / `make`-таргеты / Playwright-сценарии
  должны позеленеть? Если нужен новый тест — где он живёт?

Минимальный обязательный набор для этого репо:

- [ ] `make check` (black + isort + flake8 + mypy) — зелёный.
- [ ] `make test` — зелёный, coverage ≥ 87 % (TIK-54).
- [ ] Если затронут scoring/recalc — `make audit` зелёный.
- [ ] Если затронут UI/routes/admin — `make e2e` зелёный (Playwright).

## 4. Границы (Scope & Anti-Goals)

- **НЕ делаем:** список соседних рефакторингов и улучшений, которые
  в эту задачу **не** входят. (Пример: *«Не трогаем мобильную
  вёрстку, не меняем формулу рейтинга, не апгрейдим Flask-Admin.»*)
- **Sanity-check размера:** результат всё ещё умещается в ≤ ~300 LOC
  и одну рабочую сессию?
  - [ ] Да → продолжаем.
  - [ ] Нет → декомпозируем на под-задачи (`linear-sync` skill) и
        переносим этот чеклист в каждую из них.

## Связанные ссылки

- Linear: `TIK-…` *(если есть)*
- Прошлые ADR / PR-ы: …
- Skill-и для исполнителя: `karpathy-guidelines`, `feature-research`,
  `verification`, `linear-sync`.
