# 🤖 Multi-Agent System для Shadow Hockey League

## 📋 Обзор

Модульная система агентов с **полной обратной совместимостью** со старым подходом через `.windsurfrules`.

### Ключевые возможности

✅ **3 режима работы:**
- `automatic` - агенты автоматически делегируют задачи друг другу
- `manual` - ручной режим через `@role` команды (старый подход)
- `hybrid` - можно переключаться на лету

✅ **Полная изоляция:**
- Старый подход через `.windsurfrules` **не затронут**
- Можно вернуться к ручному режиму в любой момент
- Оба подхода работают параллельно

✅ **6 ролей:**
- `ANALYST` - анализ требований
- `ARCHITECT` - проектирование архитектуры
- `PLANNER` - создание планов
- `DEVELOPER` - написание кода
- `QA_TESTER` - тестирование
- `DESIGNER` - UI/UX дизайн

## 🚀 Быстрый старт

### 1. Автоматический режим (новый подход)

```python
from agents import AgentRouter

# Создаём маршрутизатор
router = AgentRouter(mode="automatic")

# Выполняем задачу
result = router.execute_task(
    "ANALYST",
    "Проанализировать требования для системы управления турнирами"
)

# Проверяем результат
if result.success:
    print("✅ Задача выполнена:", result.data)
    
if result.needs_delegation:
    print("🔄 Делегировано на:", result.delegation_request.target_role)
    print("Причина:", result.delegation_request.reason)
```

### 2. Ручной режим (старый подход)

```python
from agents import AgentRouter

# Создаём маршрутизатор в ручном режиме
router = AgentRouter(mode="manual")

# Получаем инструкцию для ручной работы
result = router.execute_task(
    "ANALYST",
    "Проанализировать требования для системы управления турнирами"
)

# Выводим инструкцию
print(result.data["instruction"])
```

### 3. Гибридный режим (переключение на лету)

```python
from agents import AgentRouter

router = AgentRouter(mode="hybrid")

# Автоматическое выполнение
result1 = router.execute_task("ANALYST", "Анализ требований")

# Переключаемся на ручной режим
router.switch_mode("manual")
result2 = router.execute_task("DEVELOPER", "Написать код")

# Обратно на автоматический
router.switch_mode("automatic")
result3 = router.execute_task("QA_TESTER", "Тестирование")
```

## 📊 Воркфлоу

### Последовательное выполнение задач

```python
from agents import AgentRouter

router = AgentRouter(mode="automatic")

# Определяем воркфлоу
workflow = [
    {"role": "ANALYST", "task": "Анализ требований"},
    {"role": "ARCHITECT", "task": "Проектирование архитектуры"},
    {"role": "PLANNER", "task": "Создание плана реализации"},
    {"role": "DEVELOPER", "task": "Реализация"},
    {"role": "QA_TESTER", "task": "Тестирование"},
]

# Выполняем
results = router.execute_workflow(workflow)

for i, result in enumerate(results, 1):
    print(f"Шаг {i}: {'✅' if result.success else '❌'}")
```

### Автоматическое делегирование

```python
from agents import AgentRouter

router = AgentRouter(mode="automatic")

# DEVELOPER находит противоречие в требованиях и делегирует ANALYST
result = router.execute_task(
    "DEVELOPER",
    "Реализовать систему рейтинга, но требования противоречивы"
)

# Если требуется делегирование:
if result.needs_delegation:
    print(f"Делегировано: {result.delegation_request.target_role}")
    print(f"Причина: {result.delegation_request.reason}")
```

## 🎯 Сравнение подходов

| Аспект | Старый (.windsurfrules) | Новый (Agents) |
|--------|-------------------------|----------------|
| **Управление** | Ручное через @role | Автоматическое |
| **Контроль границ** | На совести AI | Программный |
| **Делегирование** | Текстовые команды | Автоматическое |
| **Контекст** | Ручное | Автоматическое |
| **Безопасность** | Ручная проверка | Автоматическая |
| **Fallback** | ❌ Нет | ✅ На ручной режим |

## 🔄 Миграция со старого подхода

### Шаг 1: Попробуйте новый подход

```python
from agents import AgentRouter

# Создаём маршрутизатор в hybrid режиме
router = AgentRouter(mode="hybrid")

# Пробуем автоматический режим
result = router.execute_task("ANALYST", "Ваша задача")
```

### Шаг 2: Если что-то не так - fallback

```python
# Переключаемся на ручной режим
router.switch_mode("manual")

# Получаем инструкцию для старого подхода
result = router.execute_task("ANALYST", "Ваша задача")
print(result.data["instruction"])
```

### Шаг 3: Можно вернуться в любой момент

```python
# Обратно на автоматический
router.switch_mode("automatic")

# Или на гибридный
router.switch_mode("hybrid")
```

## 📁 Структура модуля

```
agents/
├── __init__.py              # Точка входа
├── base.py                  # Базовый класс BaseAgent
├── context_manager.py       # Управление контекстом
├── concrete_agents.py       # Реализации 6 агентов
├── router.py                # Маршрутизатор задач
└── README.md                # Эта документация

prompts/                     # Старые промпты (не тронуты)
├── 01_ANALYST.md
├── 02_ARCHITECT.md
├── 03_PLANNER.md
├── 04_DEVELOPER.md
├── 05_QA_TESTER.md
└── 06_DESIGNER.md

context/                     # Контекст (не тронут)
├── state_summary.md
├── active_plan.md
├── architecture.md
└── ...

.windsurfrules               # Старый протокол (не тронут)
```

## 🔧 Конфигурация

### RouterConfig

```python
from agents import AgentRouter
from agents.router import RouterConfig

config = RouterConfig(
    mode="automatic",
    max_delegation_depth=5,      # Макс. глубина делегирования
    auto_save_context=True,      # Автосохранение контекста
    enable_boundary_check=True,  # Проверка границ ролей
    fallback_to_manual=True      # Fallback при ошибках
)

router = AgentRouter(config=config)
```

### ContextManager

```python
from agents import ContextManager

ctx = ContextManager(context_dir="path/to/context")

# Загрузить весь контекст
data = ctx.load_all()

# Проверить размер
size = ctx.get_context_size()
print(f"Токенов: {size['total']['tokens']}")

# Проверить нужна ли суммаризация
if ctx.needs_summarization(data):
    ctx.create_summary(data, "Краткая версия...")
```

## 🛡️ Безопасность

### Автоматическое редактирование секретов

ContextManager автоматически заменяет секреты на `[REDACTED]`:

- Пароли (`password`, `passwd`, `pwd`)
- API ключи (`api_key`, `api_token`)
- Токены (`token`, `access_token`)
- Секреты (`secret`, `secret_key`)
- AWS ключи (`aws_access_key`, `aws_secret_key`)
- Приватные ключи (`-----BEGIN PRIVATE KEY-----`)

### Проверка перед сохранением

```python
from agents import ContextManager

ctx = ContextManager()

# Секреты будут заменены на [REDACTED]
ctx.save_state_summary("Пароль: super_secret_123")
# В файле будет: "Пароль: [REDACTED]"
```

## 📈 Мониторинг

### Статус агентов

```python
from agents import AgentRouter

router = AgentRouter(mode="automatic")

# Выполняем задачи
router.execute_task("ANALYST", "Задача 1")
router.execute_task("DEVELOPER", "Задача 2")

# Получаем статус
status = router.get_agent_status()

print(f"Режим: {status['mode']}")
print(f"Делегирований: {status['delegation_count']}")
print(f"Размер контекста: {status['context_size']['total']['tokens']} токенов")

for role, data in status['agents'].items():
    print(f"{role}: {data['tasks_completed']} выполнено, {data['tasks_failed']} ошибок")
```

## 🎓 Примеры использования

### Пример 1: Анализ нового функционала

```python
from agents import AgentRouter

router = AgentRouter(mode="automatic")

# Аналитик анализирует требования
result = router.execute_task(
    "ANALYST",
    "Проанализировать требования для системы уведомлений"
)

# Если всё ок - продолжаем
if result.success and not result.needs_delegation:
    # Архитектор проектирует
    result2 = router.execute_task(
        "ARCHITECT",
        "Спроектировать архитектуру системы уведомлений"
    )
```

### Пример 2: Исправление бага с делегированием

```python
from agents import AgentRouter

router = AgentRouter(mode="automatic")

# QA находит баг и делегирует DEVELOPER
result = router.execute_task(
    "QA_TESTER",
    "Найден баг в системе рейтинга - нужно исправить код"
)

# QA не правит код, а делегирует
if result.needs_delegation:
    assert result.delegation_request.target_role == "DEVELOPER"
    print("✅ QA правильно делегировал задачу разработчику")
```

### Пример 3: Полный цикл разработки

```python
from agents import AgentRouter

router = AgentRouter(mode="automatic")

workflow = [
    {"role": "ANALYST", "task": "Анализ требований для нового функционала"},
    {"role": "ARCHITECT", "task": "Проектирование архитектуры"},
    {"role": "DESIGNER", "task": "Создание UI/UX дизайна"},
    {"role": "PLANNER", "task": "Создание плана реализации"},
    {"role": "DEVELOPER", "task": "Реализация функционала"},
    {"role": "QA_TESTER", "task": "Тестирование"},
]

results = router.execute_workflow(workflow)

# Проверяем результат
all_success = all(r.success for r in results)
print(f"{'✅' if all_success else '❌'} Воркфлоу завершён")
```

## 🔮 Планы развития

- [ ] Интеграция с Qwen Subagents API
- [ ] Автоматическая генерация промптов из кода
- [ ] Веб-интерфейс для мониторинга
- [ ] Интеграция с Flask приложением
- [ ] Поддержка параллельного выполнения задач
- [ ] История и откат изменений

## 📞 Поддержка

Если что-то не работает:

1. Проверьте логи: `logging.getLogger("agents")`
2. Попробуйте fallback: `router.switch_mode("manual")`
3. Сбросьте состояние: `router.reset()`
4. Проверьте контекст: `router.context_manager.get_context_size()`

## ⚠️ Важно

- ✅ **Старый подход не тронут** - `.windsurfrules` и `prompts/` работают как раньше
- ✅ **Можно вернуться** в любой момент через `router.switch_mode("manual")`
- ✅ **Полная изоляция** - новый код не модифицирует старые файлы
- ✅ **Fallback всегда доступен** - при ошибках автоматически переключается на ручной режим
