"""
CLI Commands - Команды для управления системой агентов

Использование:
    python -m agents.cli status              # Статус системы
    python -m agents.cli execute ROLE TASK   # Выполнить задачу
    python -m agents.cli workflow FILE       # Выполнить воркфлоу из файла
    python -m agents.cli switch MODE         # Переключить режим
    python -m agents.cli context             # Показать размер контекста
    python -m agents.cli reset               # Сбросить состояние
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from agents import AgentRouter, ContextManager
from agents.router import RouterConfig

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("agents.cli")


def cmd_status(args):
    """Показать статус системы агентов."""
    router = AgentRouter(mode=args.mode)
    status = router.get_agent_status()
    
    print("\n" + "="*60)
    print("🤖 Multi-Agent System Status")
    print("="*60)
    
    print(f"\n📊 Режим: {status['mode']}")
    print(f"🔄 Делегирований: {status['delegation_count']}")
    
    print(f"\n📦 Размер контекста:")
    ctx_size = status['context_size']
    if 'total' in ctx_size:
        print(f"   Токенов: {ctx_size['total']['tokens']:,}")
        print(f"   Символов: {ctx_size['total']['chars']:,}")
    
    print(f"\n👥 Агенты:")
    for role, data in status['agents'].items():
        icon = "✅" if data['tasks_completed'] > 0 else "⭕"
        print(f"   {icon} {role}:")
        print(f"      Выполнено: {data['tasks_completed']}")
        print(f"      Ошибок: {data['tasks_failed']}")
        print(f"      Всего: {data['total_tasks']}")
    
    print("\n" + "="*60)


def cmd_execute(args):
    """Выполнить задачу через агента."""
    router = AgentRouter(mode=args.mode)
    
    print(f"\n🎯 Выполнение задачи:")
    print(f"   Роль: {args.role}")
    print(f"   Задача: {args.task}")
    print(f"   Режим: {args.mode}\n")
    
    result = router.execute_task(args.role, args.task)
    
    if result.success:
        print("✅ Задача выполнена успешно")
        if result.data:
            print(f"\n📄 Результат:")
            if isinstance(result.data, dict):
                print(json.dumps(result.data, indent=2, ensure_ascii=False))
            else:
                print(result.data)
    else:
        print("❌ Ошибка выполнения")
        if result.error:
            print(f"\n⚠️  Ошибка: {result.error}")
    
    if result.needs_delegation:
        delegation = result.delegation_request
        print(f"\n🔄 Требуется делегирование:")
        print(f"   Цель: {delegation.target_role}")
        print(f"   Причина: {delegation.reason}")
        print(f"   Запрос: {delegation.specific_request}")
    
    if result.artifacts:
        print(f"\n📦 Артефакты:")
        print(json.dumps(result.artifacts, indent=2, ensure_ascii=False))


def cmd_workflow(args):
    """Выполнить воркфлоу из файла."""
    workflow_file = Path(args.file)
    
    if not workflow_file.exists():
        print(f"❌ Файл не найден: {workflow_file}")
        sys.exit(1)
    
    try:
        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        sys.exit(1)
    
    router = AgentRouter(mode=args.mode)
    
    print(f"\n🚀 Выполнение воркфлоу:")
    print(f"   Файл: {workflow_file}")
    print(f"   Шагов: {len(workflow)}")
    print(f"   Режим: {args.mode}\n")
    
    results = router.execute_workflow(workflow)
    
    print("\n" + "="*60)
    print("📊 Результаты воркфлоу")
    print("="*60)
    
    for i, (step, result) in enumerate(zip(workflow, results), 1):
        icon = "✅" if result.success else "❌"
        print(f"\n{i}. {icon} {step['role']}")
        print(f"   Задача: {step['task'][:80]}...")
        
        if result.needs_delegation:
            print(f"   🔄 Делегировано на: {result.delegation_request.target_role}")
    
    success_count = sum(1 for r in results if r.success)
    print(f"\n{'='*60}")
    print(f"Итого: {success_count}/{len(results)} выполнено")
    print(f"{'='*60}\n")


def cmd_switch(args):
    """Переключить режим работы."""
    mode = args.mode.lower()
    
    if mode not in ["automatic", "manual", "hybrid"]:
        print(f"❌ Неверный режим: {mode}")
        print("   Доступные: automatic, manual, hybrid")
        sys.exit(1)
    
    router = AgentRouter(mode="manual")  # Начинаем с manual для демонстрации
    router.switch_mode(mode)
    
    print(f"\n✅ Режим переключён на: {mode}")
    print(f"   Текущий режим: {router.mode}")
    
    if mode == "manual":
        print(f"\n📋 Ручной режим активирован")
        print(f"   Используйте .windsurfrules и @role команды")
        print(f"   Промпты загружаются из prompts/")
    elif mode == "automatic":
        print(f"\n🤖 Автоматический режим активирован")
        print(f"   Агенты автоматически делегируют задачи")
    else:
        print(f"\n🔀 Гибридный режим активирован")
        print(f"   Можно переключаться между режимами на лету")


def cmd_context(args):
    """Показать информацию о контексте."""
    ctx = ContextManager()
    
    print("\n" + "="*60)
    print("📦 Context Manager Status")
    print("="*60)
    
    size = ctx.get_context_size()
    
    print(f"\n📊 Размер контекста:")
    for filename, data in size.items():
        if filename != "total":
            print(f"   {filename}:")
            print(f"      Символов: {data['chars']:,}")
            print(f"      Токенов: {data['tokens']:,}")
    
    if 'total' in size:
        print(f"\n   📈 Всего:")
        print(f"      Символов: {size['total']['chars']:,}")
        print(f"      Токенов: {size['total']['tokens']:,}")
        
        # Проверка лимита
        if size['total']['tokens'] > ctx.TOKEN_LIMIT:
            print(f"\n   ⚠️  Превышен лимит токенов!")
            print(f"   Лимит: {ctx.TOKEN_LIMIT:,}")
            print(f"   Рекомендуется суммаризация")
    
    print("\n" + "="*60)


def cmd_reset(args):
    """Сбросить состояние маршрутизатора."""
    if not args.force:
        response = input("⚠️  Вы уверены, что хотите сбросить состояние? (y/N): ")
        if response.lower() != 'y':
            print("❌ Отменено")
            return
    
    router = AgentRouter(mode="manual")
    router.reset()
    
    print("\n✅ Состояние сброшено")
    print("   - Кэш агентов очищен")
    print("   - История делегирований очищена")


def cmd_windsurfrules(args):
    """Показать содержимое .windsurfrules."""
    router = AgentRouter(mode="manual")
    rules = router.get_windsurfrules()
    
    print("\n" + "="*60)
    print("📜 .windsurfrules")
    print("="*60 + "\n")
    print(rules)
    print("\n" + "="*60)


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description="Shadow Hockey League - Multi-Agent System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s status                          # Статус системы
  %(prog)s execute ANALYST "Анализ"        # Выполнить задачу
  %(prog)s workflow workflow.json          # Выполнить воркфлоу
  %(prog)s switch automatic                # Переключить режим
  %(prog)s context                         # Размер контекста
  %(prog)s reset --force                   # Сбросить состояние
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["automatic", "manual", "hybrid"],
        default="automatic",
        help="Режим работы (по умолчанию: automatic)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Команда")
    
    # status
    subparsers.add_parser("status", help="Показать статус системы")
    
    # execute
    exec_parser = subparsers.add_parser("execute", help="Выполнить задачу")
    exec_parser.add_argument("role", help="Имя роли (ANALYST, ARCHITECT, etc.)")
    exec_parser.add_argument("task", help="Описание задачи")
    
    # workflow
    wf_parser = subparsers.add_parser("workflow", help="Выполнить воркфлоу")
    wf_parser.add_argument("file", help="Файл с воркфлоу (JSON)")
    
    # switch
    sw_parser = subparsers.add_parser("switch", help="Переключить режим")
    sw_parser.add_argument("mode", choices=["automatic", "manual", "hybrid"])
    
    # context
    subparsers.add_parser("context", help="Показать размер контекста")
    
    # reset
    reset_parser = subparsers.add_parser("reset", help="Сбросить состояние")
    reset_parser.add_argument("--force", action="store_true", help="Без подтверждения")
    
    # windsurfrules
    subparsers.add_parser("windsurfrules", help="Показать .windsurfrules")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Маппинг команд к функциям
    commands = {
        "status": cmd_status,
        "execute": cmd_execute,
        "workflow": cmd_workflow,
        "switch": cmd_switch,
        "context": cmd_context,
        "reset": cmd_reset,
        "windsurfrules": cmd_windsurfrules,
    }
    
    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
