# AI POLICY

## PRIORITY

1. sequential_thinking — ВСЕГДА первым
2. context MCP — для понимания проекта
3. filesystem — для работы с файлами

---

## RULES

- Любая задача >1 шага → sequential_thinking
- Перед чтением файлов → context.search_code или list_files
- Не читать вслепую большие файлы
- Не использовать bash без необходимости

---

## FLOW

1. sequential_thinking
2. context.search_code
3. context.read_file
4. действие (код/правка)

---

## FORBIDDEN

- Прямой bash без reasoning
- Чтение файлов без поиска
- Пропуск sequential_thinking

## FALLBACK

Если MCP недоступен:

- reasoning делать inline
- использовать filesystem напрямую
- упрощать план