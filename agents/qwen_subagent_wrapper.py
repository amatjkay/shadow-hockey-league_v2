"""
Qwen Subagents Integration - Обёртка для использования Qwen Subagents API

Этот модуль предоставляет интеграцию с нативными субагентами Qwen,
сохраняя совместимость с текущей системой агентов.

Когда использовать:
- Для сложных задач, требующих изолированного контекста
- Для параллельного выполнения задач
- Для использования специализированных субагентов Qwen

Когда НЕ использовать:
- Для простых задач - используйте локальных агентов
- Когда нужен полный контроль над контекстом
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agents.base import BaseAgent, AgentResult
from agents.context_manager import ContextManager

logger = logging.getLogger(__name__)


@dataclass
class QwenSubagentConfig:
    """Конфигурация для Qwen Subagent."""
    subagent_type: str = "general-purpose"
    description: str = ""
    timeout: int = 300  # Таймаут в секундах
    max_retries: int = 3


class QwenSubagentWrapper:
    """
    Обёртка для использования Qwen Subagents через локальный интерфейс агентов.
    
    Позволяет прозрачно использовать Qwen Subagents там, где это выгодно,
    и fallback на локальных агентов в остальных случаях.
    
    Пример использования:
        wrapper = QwenSubagentWrapper()
        
        # Используем Qwen Subagent для сложной задачи
        result = wrapper.execute_with_subagent(
            "ANALYST",
            "Сложный анализ требований",
            use_qwen_subagent=True
        )
    """

    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        config: Optional[QwenSubagentConfig] = None
    ):
        """
        Инициализация обёртки.
        
        Args:
            context_manager: Менеджер контекста
            config: Конфигурация субагента
        """
        self.context_manager = context_manager or ContextManager()
        self.config = config or QwenSubagentConfig()
        
        # Флаг доступности Qwen Subagents
        self.qwen_available = self._check_qwen_availability()
        
        logger.info(
            f"QwenSubagentWrapper initialized "
            f"(Qwen available: {self.qwen_available})"
        )

    def execute_with_subagent(
        self,
        role_name: str,
        task: str,
        use_qwen_subagent: bool = True,
        **kwargs
    ) -> AgentResult:
        """
        Выполнить задачу с использованием Qwen Subagent или локального агента.
        
        Args:
            role_name: Имя роли
            task: Задача
            use_qwen_subagent: Использовать ли Qwen Subagent
            **kwargs: Дополнительные параметры
            
        Returns:
            AgentResult с результатом
        """
        if use_qwen_subagent and self.qwen_available:
            return self._execute_via_qwen(role_name, task, **kwargs)
        else:
            # Fallback на локального агента
            return self._execute_via_local(role_name, task, **kwargs)

    def execute_parallel(
        self,
        tasks: List[Dict[str, str]],
        use_qwen_subagents: bool = True
    ) -> List[AgentResult]:
        """
        Выполнить несколько задач параллельно.
        
        Args:
            tasks: Список задач [{"role": "...", "task": "..."}]
            use_qwen_subagents: Использовать ли Qwen Subagents
            
        Returns:
            Список результатов
        """
        results = []
        
        for task_info in tasks:
            role = task_info["role"]
            task = task_info["task"]
            
            result = self.execute_with_subagent(
                role, task, use_qwen_subagent=use_qwen_subagents
            )
            results.append(result)
        
        return results

    def _execute_via_qwen(
        self,
        role_name: str,
        task: str,
        **kwargs
    ) -> AgentResult:
        """
        Выполнить задачу через Qwen Subagent.
        
        NOTE: Это заглушка для будущей интеграции с Qwen Subagents API.
        Когда Qwen предоставит API для программного вызова субагентов,
        этот метод будет использовать его.
        """
        logger.info(f"[Qwen Subagent] Would execute: {role_name} - {task[:50]}...")
        
        # TODO: Интеграция с Qwen Subagents API
        # Когда API станет доступен:
        # 1. Вызов task tool с нужным subagent_type
        # 2. Передать промпт роли и контекст
        # 3. Вернуть результат
        
        # Пока возвращаем заглушку
        return AgentResult(
            success=True,
            data={
                "message": "Qwen Subagent integration pending",
                "role": role_name,
                "task": task,
                "fallback": "local"
            },
            metadata={"used_qwen_subagent": False}
        )

    def _execute_via_local(
        self,
        role_name: str,
        task: str,
        **kwargs
    ) -> AgentResult:
        """
        Выполнить задачу через локального агента (fallback).
        
        Args:
            role_name: Имя роли
            task: Задача
            **kwargs: Дополнительные параметры
            
        Returns:
            AgentResult с результатом
        """
        from agents.concrete_agents import create_agent
        
        logger.info(f"[Local Agent] Executing: {role_name} - {task[:50]}...")
        
        agent = create_agent(
            role_name=role_name,
            context_manager=self.context_manager,
            mode="automatic"
        )
        
        return agent.execute(task, **kwargs)

    def _check_qwen_availability(self) -> bool:
        """
        Проверить доступность Qwen Subagents API.
        
        Returns:
            True если API доступен
        """
        try:
            # TODO: Проверить доступность Qwen Subagents API
            # Пока возвращаем False - API ещё не доступен
            return False
        except Exception as e:
            logger.warning(f"Qwen Subagents not available: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Получить статус обёртки."""
        return {
            "qwen_available": self.qwen_available,
            "subagent_type": self.config.subagent_type,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries
        }
