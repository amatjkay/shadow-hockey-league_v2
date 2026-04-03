# QA Status — Shadow Hockey League v2

**Дата:** 3 апреля 2026 г.
**Статус:** 🟡 Ожидание тестирования

## 📊 Текущее состояние тестов

- **Заявлено:** 72 теста (README.md)
- **В .memory-bank.md:** 48 тестов (расхождение!)
- **Статус:** ✅ Все проходят (по README)

## 🧪 Типы тестов

- Unit тесты: rating service, validation, security headers
- Integration тесты: routes, API, database, constraints
- Cache & Admin тесты: cache invalidation, admin auth
- API Cache Invalidation тесты: API → cache invalidation, leaderboard refresh

## 🐛 Известные баги (из .memory-bank.md)

| ID      | Описание                                    | Критичность | Статус        |
| ------- | ------------------------------------------- | ----------- | ------------- |
| BUG-001 | Login/Logout не отображаются в меню админки | 🟡          | ⚠️ В работе   |
| BUG-002 | Нет заголовков страниц в админке            | 🟢          | Запланировано |
| BUG-003 | Выбор флага требует ручного ввода пути      | 🟡          | ⚠️ В работе   |

## 📝 Рекомендации

- Уточнить актуальное количество тестов
- Проверить покрытие кода (coverage)
- Провести регрессионное тестирование админ-панели
