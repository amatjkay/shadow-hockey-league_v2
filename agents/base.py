"""
Base Agent - Базовый класс для всех агентов

Определяет общий интерфейс, управление контекстом и границы ролей.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Результат работы агента."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    delegation_request: Optional[DelegationRequest] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def needs_delegation(self) -> bool:
        return self.delegation_request is not None


@dataclass
class DelegationRequest:
    """Запрос на делегирование другому агенту."""
    target_role: str
    reason: str
    context: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    specific_request: str = ""
    source_role: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseAgent(ABC):
    """
    Базовый класс для всех агентов системы.
    
    Каждый конкретный агент (ANALYST, ARCHITECT, etc.) наследуется от этого класса
    и реализует абстрактные методы.
    """

    ROLE_NAME: str = "BASE"
    ROLE_DESCRIPTION: str = "Base agent class"
    
    # Границы роли - что агент НЕ должен делать
    BOUNDARIES: List[str] = []
    
    # Что агент МОЖЕТ делать
    CAPABILITIES: List[str] = []

    def __init__(
        self,
        context_manager: Optional[ContextManager] = None,
        config: Optional[Dict[str, Any]] = None,
        mode: str = "automatic"
    ):
        """
        Инициализация агента.
        
        Args:
            context_manager: Менеджер контекста для чтения/записи
            config: Конфигурация агента
            mode: Режим работы (automatic/manual/hybrid)
        """
        self.context_manager = context_manager
        self.config = config or {}
        self.mode = mode
        self.task_history: List[Dict[str, Any]] = []
        
        # Загрузка промпта из prompts/ если существует
        self.prompt = self._load_prompt_from_file()
        
        logger.info(f"Agent {self.ROLE_NAME} initialized in {mode} mode")

    def _load_prompt_from_file(self) -> Optional[str]:
        """Загрузить промпт роли из файла prompts/XX_ROLE.md."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        
        # Ищем файл промпта (01_ANALYST.md, 02_ARCHITECT.md, etc.)
        for prompt_file in prompts_dir.glob(f"*_{self.ROLE_NAME}.md"):
            try:
                content = prompt_file.read_text(encoding="utf-8")
                logger.info(f"Loaded prompt from {prompt_file}")
                return content
            except Exception as e:
                logger.warning(f"Failed to load prompt from {prompt_file}: {e}")
        
        logger.warning(f"No prompt file found for {self.ROLE_NAME}")
        return None

    def execute(self, task: str, **kwargs) -> AgentResult:
        """
        Выполнить задачу.
        
        Args:
            task: Описание задачи
            **kwargs: Дополнительные параметры
            
        Returns:
            AgentResult с результатом или запросом на делегирование
        """
        logger.info(f"[{self.ROLE_NAME}] Executing task: {task[:100]}...")
        
        try:
            # Проверка границ перед выполнением
            boundary_check = self._check_boundaries(task)
            if not boundary_check.allowed:
                logger.warning(f"[{self.ROLE_NAME}] Boundary violation: {boundary_check.reason}")
                return AgentResult(
                    success=False,
                    error=f"Boundary violation: {boundary_check.reason}",
                    delegation_request=DelegationRequest(
                        target_role=boundary_check.suggested_role,
                        reason=boundary_check.reason,
                        context={"original_task": task},
                        specific_request=task
                    )
                )
            
            # Загрузка контекста если доступен
            if self.context_manager:
                self._load_context()
            
            # Выполнение задачи
            result = self._execute_task(task, **kwargs)
            
            # Сохранение результата
            if result.success and self.context_manager:
                self._save_context(result)
            
            # Запись в историю
            self.task_history.append({
                "task": task,
                "result": result.success,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.ROLE_NAME}] Task execution failed: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    @abstractmethod
    def _execute_task(self, task: str, **kwargs) -> AgentResult:
        """
        Реализация выполнения задачи конкретным агентом.
        
        Args:
            task: Описание задачи
            **kwargs: Дополнительные параметры
            
        Returns:
            AgentResult с результатом
        """
        pass

    def _check_boundaries(self, task: str) -> BoundaryCheck:
        """
        Проверка, не нарушает ли задача границы роли.
        
        Returns:
            BoundaryCheck с результатом проверки
        """
        # Базовая реализация всегда разрешает
        # Переопределить в конкретных агентах
        return BoundaryCheck(allowed=True)

    def _load_context(self):
        """Загрузить контекст из context/ перед выполнением."""
        if not self.context_manager:
            return
        
        try:
            # Загружаем основные файлы контекста
            self.context_manager.load_state_summary()
            self.context_manager.load_active_plan()
            self.context_manager.load_architecture()
            
            logger.info(f"[{self.ROLE_NAME}] Context loaded")
        except Exception as e:
            logger.warning(f"[{self.ROLE_NAME}] Failed to load context: {e}")

    def _save_context(self, result: AgentResult):
        """Сохранить результаты в context/ после выполнения."""
        if not self.context_manager:
            return
        
        try:
            # Сохраняем артефакты если есть
            if result.artifacts:
                self.context_manager.save_artifacts(self.ROLE_NAME, result.artifacts)
            
            logger.info(f"[{self.ROLE_NAME}] Context saved")
        except Exception as e:
            logger.warning(f"[{self.ROLE_NAME}] Failed to save context: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Получить статус агента."""
        return {
            "role": self.ROLE_NAME,
            "mode": self.mode,
            "tasks_completed": len([t for t in self.task_history if t["result"]]),
            "tasks_failed": len([t for t in self.task_history if not t["result"]]),
            "total_tasks": len(self.task_history),
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} role={self.ROLE_NAME} mode={self.mode}>"


@dataclass
class BoundaryCheck:
    """Результат проверки границ роли."""
    allowed: bool
    reason: str = ""
    suggested_role: str = ""


# Импортируем здесь чтобы избежать циклических зависимостей
from agents.context_manager import ContextManager
