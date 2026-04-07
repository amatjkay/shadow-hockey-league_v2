"""
Concrete Agents - Реализация конкретных агентов

ANALYST, ARCHITECT, PLANNER, DEVELOPER, QA_TESTER, DESIGNER
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult, BoundaryCheck

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Агент-аналитик: анализ требований, выявление противоречий."""

    ROLE_NAME = "ANALYST"
    ROLE_DESCRIPTION = "Анализ требований и бизнес-логики"
    CAPABILITIES = [
        "Анализ пользовательских требований",
        "Выявление противоречий в требованиях",
        "Создание пользовательских сценариев",
        "Анализ бизнес-логики",
        "Документирование требований",
    ]
    BOUNDARIES = [
        "Не проектирует архитектуру системы",
        "Не пишет код",
        "Не создаёт планы реализации",
        "Не тестирует код",
        "Не создаёт дизайн UI/UX",
    ]

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """Проверка границ для ANALYST."""
        # Если задача явно про архитектуру или код - делегируем
        if any(keyword in task.lower() for keyword in [
            "архитектур", "architecture", "спроектировать", "design architecture"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к архитектуре системы",
                suggested_role="ARCHITECT"
            )
        
        if any(keyword in task.lower() for keyword in [
            "напиши код", "write code", "реализовать функцию", "implement"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к написанию кода",
                suggested_role="DEVELOPER"
            )
        
        return BoundaryCheck(allowed=True)

    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """Выполнить задачу анализа."""
        # Здесь будет логика анализа с использованием LLM
        # Пока возвращаем заглушку
        logger.info(f"[ANALYST] Analyzing: {task[:50]}...")
        
        return AgentResult(
            success=True,
            data={"analysis": "Analysis completed", "task": task},
            artifacts={"task": task, "status": "analyzed"}
        )


class ArchitectAgent(BaseAgent):
    """Агент-архитектор: проектирование архитектуры системы."""

    ROLE_NAME = "ARCHITECT"
    ROLE_DESCRIPTION = "Проектирование архитектуры системы"
    CAPABILITIES = [
        "Проектирование архитектуры",
        "Выбор технологий",
        "Определение компонентов системы",
        "Создание диаграмм архитектуры",
        "Анализ технических ограничений",
    ]
    BOUNDARIES = [
        "Не анализирует бизнес-требования (это делает ANALYST)",
        "Не пишет код",
        "Не создаёт детальные планы реализации",
        "Не тестирует код",
        "Не создаёт дизайн UI/UX",
    ]

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """Проверка границ для ARCHITECT."""
        if any(keyword in task.lower() for keyword in [
            "требовани", "requirement", "бизнес-логик", "business logic"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к анализу требований",
                suggested_role="ANALYST"
            )
        
        if any(keyword in task.lower() for keyword in [
            "напиши код", "write code", "реализовать функцию", "implement"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к написанию кода",
                suggested_role="DEVELOPER"
            )
        
        return BoundaryCheck(allowed=True)

    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """Выполнить задачу проектирования."""
        logger.info(f"[ARCHITECT] Designing: {task[:50]}...")
        
        return AgentResult(
            success=True,
            data={"architecture": "Architecture designed", "task": task},
            artifacts={"task": task, "status": "architected"}
        )


class PlannerAgent(BaseAgent):
    """Агент-планировщик: создание планов реализации."""

    ROLE_NAME = "PLANNER"
    ROLE_DESCRIPTION = "Создание планов и дорожных карт"
    CAPABILITIES = [
        "Создание планов реализации",
        "Разбиение задач на этапы",
        "Определение зависимостей",
        "Создание дорожных карт",
        "Управление приоритетами",
    ]
    BOUNDARIES = [
        "Не анализирует требования (это делает ANALYST)",
        "Не проектирует архитектуру (это делает ARCHITECT)",
        "Не пишет код",
        "Не тестирует код",
        "Не создаёт дизайн UI/UX",
    ]

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """Проверка границ для PLANNER."""
        if any(keyword in task.lower() for keyword in [
            "архитектур", "architecture", "спроектировать"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к архитектуре системы",
                suggested_role="ARCHITECT"
            )
        
        return BoundaryCheck(allowed=True)

    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """Выполнить задачу планирования."""
        logger.info(f"[PLANNER] Planning: {task[:50]}...")
        
        return AgentResult(
            success=True,
            data={"plan": "Plan created", "task": task},
            artifacts={"task": task, "status": "planned"}
        )


class DeveloperAgent(BaseAgent):
    """Агент-разработчик: написание и рефакторинг кода."""

    ROLE_NAME = "DEVELOPER"
    ROLE_DESCRIPTION = "Разработка и рефакторинг кода"
    CAPABILITIES = [
        "Написание кода",
        "Рефакторинг",
        "Исправление багов",
        "Создание тестов",
        "Оптимизация производительности",
    ]
    BOUNDARIES = [
        "Не анализирует бизнес-требования (это делает ANALYST)",
        "Не проектирует архитектуру (это делает ARCHITECT)",
        "Не создаёт планы (это делает PLANNER)",
        "Не проводит финальное тестирование (это делает QA_TESTER)",
        "Не создаёт дизайн UI/UX (это делает DESIGNER)",
    ]

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """Проверка границ для DEVELOPER."""
        if any(keyword in task.lower() for keyword in [
            "протестируй", "test", "qa", "найди баг", "find bug"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к тестированию",
                suggested_role="QA_TESTER"
            )
        
        return BoundaryCheck(allowed=True)

    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """Выполнить задачу разработки."""
        logger.info(f"[DEVELOPER] Developing: {task[:50]}...")
        
        return AgentResult(
            success=True,
            data={"code": "Code implemented", "task": task},
            artifacts={"task": task, "status": "developed"}
        )


class QATesterAgent(BaseAgent):
    """Агент-QA: тестирование и контроль качества."""

    ROLE_NAME = "QA_TESTER"
    ROLE_DESCRIPTION = "Тестирование и контроль качества"
    CAPABILITIES = [
        "Создание тест-планов",
        "Ручное тестирование",
        "Автоматическое тестирование",
        "Создание баг-репортов",
        "Регрессионное тестирование",
    ]
    BOUNDARIES = [
        "Не анализирует требования (это делает ANALYST)",
        "Не проектирует архитектуру (это делает ARCHITECT)",
        "Не пишет продакшен-код (только тесты)",
        "Не создаёт планы (это делает PLANNER)",
        "Не создаёт дизайн UI/UX (это делает DESIGNER)",
    ]

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """Проверка границ для QA_TESTER."""
        if any(keyword in task.lower() for keyword in [
            "исправь баг", "fix bug", "напиши код", "write code", "реализовать"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача требует исправления кода",
                suggested_role="DEVELOPER"
            )
        
        return BoundaryCheck(allowed=True)

    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """Выполнить задачу тестирования."""
        logger.info(f"[QA_TESTER] Testing: {task[:50]}...")
        
        return AgentResult(
            success=True,
            data={"test_result": "Tests completed", "task": task},
            artifacts={"task": task, "status": "tested"}
        )


class DesignerAgent(BaseAgent):
    """Агент-дизайнер: создание UI/UX дизайна."""

    ROLE_NAME = "DESIGNER"
    ROLE_DESCRIPTION = "UI/UX дизайн и прототипирование"
    CAPABILITIES = [
        "Создание мокапов",
        "Прототипирование",
        "Дизайн пользовательского интерфейса",
        "Создание дизайн-систем",
        "Анализ UX",
    ]
    BOUNDARIES = [
        "Не анализирует требования (это делает ANALYST)",
        "Не проектирует архитектуру (это делает ARCHITECT)",
        "Не пишет код (это делает DEVELOPER)",
        "Не создаёт планы (это делает PLANNER)",
        "Не тестирует код (это делает QA_TESTER)",
    ]

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """Проверка границ для DESIGNER."""
        if any(keyword in task.lower() for keyword in [
            "напиши код", "write code", "реализовать", "implement"
        ]):
            return BoundaryCheck(
                allowed=False,
                reason="Задача относится к написанию кода",
                suggested_role="DEVELOPER"
            )
        
        return BoundaryCheck(allowed=True)

    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """Выполнить задачу дизайна."""
        logger.info(f"[DESIGNER] Designing: {task[:50]}...")
        
        return AgentResult(
            success=True,
            data={"design": "Design created", "task": task},
            artifacts={"task": task, "status": "designed"}
        )


# Фабрика для создания агентов по имени роли
AGENT_FACTORY: Dict[str, type] = {
    "ANALYST": AnalystAgent,
    "ARCHITECT": ArchitectAgent,
    "PLANNER": PlannerAgent,
    "DEVELOPER": DeveloperAgent,
    "QA_TESTER": QATesterAgent,
    "DESIGNER": DesignerAgent,
}


def create_agent(
    role_name: str,
    context_manager=None,
    config: Optional[Dict[str, Any]] = None,
    mode: str = "automatic"
) -> BaseAgent:
    """
    Создать агент по имени роли.
    
    Args:
        role_name: Имя роли (ANALYST, ARCHITECT, etc.)
        context_manager: Менеджер контекста
        config: Конфигурация
        mode: Режим работы
        
    Returns:
        Экземпляр агента
        
    Raises:
        ValueError: Если роль не найдена
    """
    role_name = role_name.upper()
    
    if role_name not in AGENT_FACTORY:
        raise ValueError(
            f"Unknown role: {role_name}. "
            f"Available roles: {', '.join(AGENT_FACTORY.keys())}"
        )
    
    agent_class = AGENT_FACTORY[role_name]
    return agent_class(
        context_manager=context_manager,
        config=config,
        mode=mode
    )
