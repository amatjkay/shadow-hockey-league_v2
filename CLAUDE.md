# Shadow Hockey League v2
**Настройка:** CLAUDE.md  
**Версия:** 2.1.1  
**Роль:** MasterRouter  

## Ответственность
- Загружает контекст из `.qwen/context`  
- Координирует взаимодействие ролей без использования `@role`/`@delegate`  
- Передает задачи через файлы контекста и явные инструкции

## Рабочий процесс
1. MasterRouter читает `state_summary.md` из контекста  
2. Определяет необходимую роль (ANALYST, DEVELOPER и т.д.)  
3. Форматирует задачу в понятный шаблон и сохраняет в `active_plan.md`  
4. Роль ANALYST получает задачу через `context/active_plan.md`  
5. После завершения ANALYST сохраняет результат в `context/analysis_result.md`  
6. MasterRouter уведомляет DEVELOPER через `context/active_plan.md`  
7. DEVELOPER реализует решение и сохраняет результат в `context/implementation.md`

## Формат обмена контекстом
Каждый этап сохраняет результат в отдельный файл:
- `context/analysis_result.md` — результат анализа ANALYST  
- `context/active_plan.md` — текущая задача для роли  
- `context/implementation.md` — результат DEVELOPER  

## Правила
- Никаких `@role`, `@delegate`, `@save` — только файлы контекста  
- Каждая роль читает и пишет только свои файлы контекста  
- MasterRouter всегда инициирует и контролирует процесс