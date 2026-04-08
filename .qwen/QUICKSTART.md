# 🚀 Quick Start Guide - MasterRouter v2.1 Universal

**Версия:** 2.1.1
**Дата:** 7 апреля 2026 г.

---

## ⚡ Быстрый старт (30 секунд)

### 1. Проверь структуру

```bash
# Должны существовать:
.qwen/
├── config.json              ✅ Конфигурация
├── context/
│   ├── state_summary.md     ✅ Состояние проекта
│   ├── active_plan.md       ✅ Активный план
│   └── memory.md            ✅ Память проекта
└── agents/
    ├── analyst.md           ✅ Определение ANALYST
    ├── architect.md         ✅ Определение ARCHITECT
    ├── planner.md           ✅ Определение PLANNER
    ├── developer.md         ✅ Определение DEVELOPER
    ├── qa_tester.md         ✅ Определение QA_TESTER
    └── designer.md          ✅ Определение DESIGNER

.windsurfrules               ✅ Универсальные правила
```

### 2. Проверь конфигурацию

Открой `.qwen/config.json`:
```json
{
  "llm_provider": { "current": "qwen_code_companion" },
  "operation_mode": { "current": "hybrid" }
}
```

### 3. Начни работу

Просто напиши задачу:
```
Проанализируй требования для системы уведомлений
```

Или активируй роль:
```
@role ANALYST
```

---

## 🎯 Использование в Qwen Code Companion

### Режим full_subagents

```
@role ANALYST
Проанализируй требования для системы уведомлений

@delegate ARCHITECT Спроектировать архитектуру на основе анализа
```

### Режим hybrid (по умолчанию)

```
# AI автоматически определит возможности
Просто опи задачу - AI решит, использовать субагентов или нет
```

### Режим direct_only

```
# Работа как Senior Generalist
Просто опи задачу - AI выполнит напрямую
```

---

## 🌐 Использование в других LLM

### GPT-4, Gemini, Claude, Local LLM

```
# Просто опи задачу
Проанализируй требования для системы уведомлений

# AI проигнорирует @ команды и выполнит напрямую
@role ANALYST  # Будет проигнорировано
Проанализируй требования  # Выполнится напрямую
```

---

## 📂 Управление контекстом

### Сохранить состояние

```
@save
```

Обновит:
- `.qwen/context/state_summary.md`
- `.qwen/context/active_plan.md`

### Перейти к следующему шагу

```
@next
```

Прочитает `.qwen/context/active_plan.md` и перейдёт к следующему шагу.

### Восстановить состояние

```
@restore
```

Загрузит последнее состояние из `.qwen/context/archive/`.

### Диагностика

```
@debug_rules
```

Покажет:
- Текущую конфигурацию
- Активный режим
- Доступные роли
- Пути к контекстным файлам

---

## 🔧 Переключение режимов

### Через config.json

Открой `.qwen/config.json` и измени:
```json
{
  "operation_mode": {
    "current": "full_subagents"  // или "hybrid" или "direct_only"
  }
}
```

### Через команду (в Qwen)

```
Переключи режим на direct_only
```

---

## 🧪 Проверка работы

### Тест 1: Проверка структуры

```bash
ls -la .qwen/config.json
ls -la .qwen/context/
ls -la .qwen/agents/
```

### Тест 2: Проверка конфигурации

```bash
cat .qwen/config.json | python -m json.tool
```

### Тест 3: Проверка контекста

```bash
cat .qwen/context/state_summary.md
cat .qwen/context/active_plan.md
cat .qwen/context/memory.md
```

---

## 📚 Документация

| Тема | Файл |
|------|------|
| Конфигурация | `.qwen/config.json` |
| Состояние проекта | `.qwen/context/state_summary.md` |
| План | `.qwen/context/active_plan.md` |
| Память | `.qwen/context/memory.md` |
| Роли | `.qwen/agents/*.md` |
| Правила | `.windsurfrules` |

---

## 🆘 Troubleshooting

### Проблема: AI не читает контекст

**Решение:** Убедись что `.qwen/context/` файлы существуют:
```bash
ls -la .qwen/context/
```

### Проблема: Команды @role/@delegate не работают

**Решение:** Проверь `llm_provider` в `.qwen/config.json`:
```json
{
  "llm_provider": { "current": "qwen_code_companion" }
}
```

### Проблема: Секреты не редактируются

**Решение:** Проверь `universal_core.security.secrets_policy`:
```json
{
  "universal_core": {
    "security": {
      "secrets_policy": "REDACT"
    }
  }
}
```

---

**Готово!** Система работает. 🎉
