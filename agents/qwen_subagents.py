"""
Qwen Subagents Integration - Использование нативных субагентов Qwen

Этот модуль использует встроенный task tool Qwen Code для создания
специализированных субагентов без внешних API.

Как это работает:
1. Создаём субагент через task tool с нужной ролью
2. Передаём промпт роли и контекст
3. Получаем результат обратно
4. Сохраняем в context/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QwenAgentResult:
    """Результат от Qwen субагента."""
    success: bool
    content: str = ""
    error: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class QwenSubagentOrchestrator:
    """
    Оркестратор для использования Qwen Subagents.
    
    Вместо создания отдельных агентов, мы используем
    нативный task tool Qwen Code для запуска субагентов.
    
    Пример использования:
        orchestrator = QwenSubagentOrchestrator()
        
        # Запустить субагент-аналитика
        result = orchestrator.run_agent(
            role="ANALYST",
            task="Проанализировать требования",
            context=load_context()
        )
    """

    # Промпты для каждой роли - загружаются из prompts/
    ROLE_PROMPTS: Dict[str, str] = {}

    def __init__(self, context_dir: Optional[str] = None):
        """
        Инициализация оркестратора.
        
        Args:
            context_dir: Путь к директории context/
        """
        from agents.context_manager import ContextManager
        
        # Загружаем промпты если ещё не загружены
        if not QwenSubagentOrchestrator.ROLE_PROMPTS:
            self._load_role_prompts()
        
        self.context_manager = ContextManager(context_dir=context_dir)
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"QwenSubagentOrchestrator initialized with {len(QwenSubagentOrchestrator.ROLE_PROMPTS)} roles")

    def _load_role_prompts(self):
        """Загрузить все промпты из директории prompts/."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        
        role_files = {
            "ANALYST": "01_ANALYST.md",
            "ARCHITECT": "02_ARCHITECT.md",
            "PLANNER": "03_PLANNER.md",
            "DEVELOPER": "04_DEVELOPER.md",
            "QA_TESTER": "05_QA_TESTER.md",
            "DESIGNER": "06_DESIGNER.md",
        }
        
        for role, filename in role_files.items():
            filepath = prompts_dir / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding="utf-8")
                    QwenSubagentOrchestrator.ROLE_PROMPTS[role] = content
                    logger.info(f"Loaded prompt for {role} from {filepath}")
                except Exception as e:
                    logger.error(f"Failed to load prompt for {role}: {e}")
            else:
                logger.warning(f"Prompt file not found: {filepath}")

    def run_agent(
        self,
        role: str,
        task: str,
        additional_context: Optional[str] = None
    ) -> QwenAgentResult:
        """
        Запустить субагент для выполнения задачи.
        
        Args:
            role: Роль (ANALYST, ARCHITECT, etc.)
            task: Задача
            additional_context: Дополнительный контекст
            
        Returns:
            QwenAgentResult с результатом
        """
        role = role.upper()
        
        if role not in QwenSubagentOrchestrator.ROLE_PROMPTS:
            return QwenAgentResult(
                success=False,
                error=f"Unknown role: {role}. Available: {', '.join(QwenSubagentOrchestrator.ROLE_PROMPTS.keys())}"
            )
        
        # Формируем промпт для субагента
        system_prompt = QwenSubagentOrchestrator.ROLE_PROMPTS[role]
        
        if additional_context:
            system_prompt += f"\n\nДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:\n{additional_context}"
        
        system_prompt += f"\n\nЗАДАЧА: {task}"
        
        logger.info(f"Running {role} agent with task: {task[:50]}...")
        
        # Здесь мы возвращаем промпт для выполнения через task tool
        # Фактическое выполнение будет через Qwen Code task tool
        return QwenAgentResult(
            success=True,
            content=system_prompt,
            artifacts={
                "role": role,
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
        )

    def get_agent_prompt(self, role: str) -> str:
        """Получить промпт для роли."""
        return QwenSubagentOrchestrator.ROLE_PROMPTS.get(role.upper(), "")

    def get_available_roles(self) -> List[str]:
        """Получить список доступных ролей."""
        return list(QwenSubagentOrchestrator.ROLE_PROMPTS.keys())
