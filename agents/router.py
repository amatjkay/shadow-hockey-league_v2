"""
Agent Router - Маршрутизатор задач между агентами

Центральный оркестратор, который:
- Управляет переключением между режимами (automatic/manual/hybrid)
- Автоматически делегирует задачи между агентами
- Обеспечивает fallback на ручной режим (.windsurfrules)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agents.base import BaseAgent, AgentResult, DelegationRequest
from agents.context_manager import ContextManager
from agents.concrete_agents import create_agent, AGENT_FACTORY

logger = logging.getLogger(__name__)


@dataclass
class RouterConfig:
    """Конфигурация маршрутизатора."""
    mode: str = "automatic"  # automatic, manual, hybrid
    max_delegation_depth: int = 5  # Максимальная глубина делегирования
    auto_save_context: bool = True  # Автоматически сохранять контекст
    enable_boundary_check: bool = True  # Проверять границы ролей
    fallback_to_manual: bool = True  # Fallback на ручной режим при ошибках


class AgentRouter:
    """
    Маршрутизатор задач между агентами.
    
    Пример использования:
        router = AgentRouter(mode="automatic")
        result = router.execute_task("ANALYST", "Проанализировать требования")
        
        # Проверить было ли делегирование
        if result.needs_delegation:
            print(f"Делегировано на: {result.delegation_request.target_role}")
    """

    def __init__(
        self,
        mode: str = "automatic",
        context_dir: Optional[str] = None,
        config: Optional[RouterConfig] = None
    ):
        """
        Инициализация маршрутизатора.
        
        Args:
            mode: Режим работы (automatic/manual/hybrid)
            context_dir: Путь к директории context/
            config: Конфигурация маршрутизатора
        """
        self.mode = mode
        self.config = config or RouterConfig(mode=mode)
        
        # Инициализация менеджера контекста
        self.context_manager = ContextManager(context_dir=context_dir)
        
        # Кэш агентов
        self._agents: Dict[str, BaseAgent] = {}
        
        # История делегирований
        self.delegation_history: List[DelegationRequest] = []
        
        # Счётчик глубины делегирования
        self._delegation_depth = 0
        
        # Fallback: загрузка .windsurfrules
        self.windsurfrules = self._load_windsurfrules()
        
        logger.info(f"AgentRouter initialized in {mode} mode")

    def execute_task(
        self,
        role_name: str,
        task: str,
        **kwargs
    ) -> AgentResult:
        """
        Выполнить задачу через агента.
        
        Args:
            role_name: Имя роли (ANALYST, ARCHITECT, etc.)
            task: Описание задачи
            **kwargs: Дополнительные параметры
            
        Returns:
            AgentResult с результатом
        """
        logger.info(f"[Router] Executing task for {role_name}: {task[:100]}...")
        
        try:
            # В ручном режиме просто возвращаем инструкцию
            if self.mode == "manual":
                return self._execute_manual(role_name, task)
            
            # В автоматическом/гибридном режиме используем агентов
            agent = self._get_agent(role_name)
            result = agent.execute(task, **kwargs)
            
            # Если требуется делегирование и режим automatic
            if result.needs_delegation and self.mode == "automatic":
                return self._handle_delegation(result, **kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"[Router] Task execution failed: {e}", exc_info=True)
            
            # Fallback на ручной режим
            if self.config.fallback_to_manual:
                logger.warning("[Router] Falling back to manual mode")
                return self._execute_manual(role_name, task)
            
            return AgentResult(success=False, error=str(e))

    def execute_workflow(
        self,
        workflow: List[Dict[str, str]],
        **kwargs
    ) -> List[AgentResult]:
        """
        Выполнить воркфлоу - последовательность задач для разных ролей.
        
        Args:
            workflow: Список задач [{"role": "ANALYST", "task": "..."}, ...]
            **kwargs: Дополнительные параметры
            
        Returns:
            Список результатов
        """
        results = []
        
        for step in workflow:
            role = step["role"]
            task = step["task"]
            
            logger.info(f"[Router] Workflow step: {role} - {task[:50]}...")
            
            result = self.execute_task(role, task, **kwargs)
            results.append(result)
            
            # Если ошибка и не fallback - останавливаем
            if not result.success and not result.needs_delegation:
                logger.warning(f"[Router] Workflow stopped at {role}")
                break
            
            # Автоматическое делегирование в workflow
            if result.needs_delegation and self.mode == "automatic":
                delegation = result.delegation_request
                logger.info(f"[Router] Auto-delegating to {delegation.target_role}")
                
                # Добавляем делегированную задачу в workflow
                workflow.append({
                    "role": delegation.target_role,
                    "task": delegation.specific_request
                })
        
        return results

    def switch_mode(self, mode: str):
        """
        Переключить режим работы.
        
        Args:
            mode: Новый режим (automatic/manual/hybrid)
        """
        if mode not in ["automatic", "manual", "hybrid"]:
            raise ValueError(f"Invalid mode: {mode}. Must be automatic/manual/hybrid")
        
        old_mode = self.mode
        self.mode = mode
        self.config.mode = mode
        
        logger.info(f"[Router] Mode switched: {old_mode} -> {mode}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Получить статус всех агентов."""
        status = {
            "mode": self.mode,
            "agents": {},
            "delegation_count": len(self.delegation_history),
            "context_size": self.context_manager.get_context_size()
        }
        
        for role_name, agent in self._agents.items():
            status["agents"][role_name] = agent.get_status()
        
        return status

    def get_windsurfrules(self) -> str:
        """Получить содержимое .windsurfrules для ручного режима."""
        if self.windsurfrules:
            return self.windsurfrules
        return "# .windsurfrules not found"

    def _get_agent(self, role_name: str) -> BaseAgent:
        """
        Получить или создать агента для роли.
        
        Args:
            role_name: Имя роли
            
        Returns:
            Экземпляр агента
        """
        role_name = role_name.upper()
        
        if role_name not in self._agents:
            logger.info(f"[Router] Creating agent: {role_name}")
            self._agents[role_name] = create_agent(
                role_name=role_name,
                context_manager=self.context_manager,
                config=self.config.__dict__,
                mode=self.mode
            )
        
        return self._agents[role_name]

    def _handle_delegation(
        self,
        result: AgentResult,
        **kwargs
    ) -> AgentResult:
        """
        Обработать запрос на делегирование.
        
        Args:
            result: Результат с запросом на делегирование
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат от делегированного агента
        """
        delegation = result.delegation_request
        
        # Проверка глубины делегирования
        self._delegation_depth += 1
        if self._delegation_depth > self.config.max_delegation_depth:
            logger.error(f"[Router] Max delegation depth exceeded: {self._delegation_depth}")
            return AgentResult(
                success=False,
                error=f"Max delegation depth ({self.config.max_delegation_depth}) exceeded"
            )
        
        # Запись в историю
        self.delegation_history.append(delegation)
        
        logger.info(
            f"[Router] Delegating from {delegation.source_role or 'unknown'} "
            f"to {delegation.target_role}: {delegation.reason}"
        )
        
        # Получаем целевого агента
        target_agent = self._get_agent(delegation.target_role)
        
        # Выполняем делегированную задачу
        delegated_result = target_agent.execute(
            delegation.specific_request,
            **kwargs
        )
        
        # Уменьшаем счётчик глубины
        self._delegation_depth -= 1
        
        return delegated_result

    def _execute_manual(self, role_name: str, task: str) -> AgentResult:
        """
        Ручной режим - возвращаем инструкцию для пользователя.
        
        Это fallback на старый подход с .windsurfrules.
        
        Args:
            role_name: Имя роли
            task: Задача
            
        Returns:
            AgentResult с инструкцией
        """
        role_name = role_name.upper()
        
        instruction = f"""
📋 РУЧНОЙ РЕЖИМ - Роль: {role_name}

Задача: {task}

Инструкции:
1. Загрузите промпт роли: prompts/*_{role_name}.md
2. Следуйте правилам из .windsurfrules
3. Используйте команды:
   - @role {role_name} - активировать роль
   - @delegate [РОЛЬ] [ПРИЧИНА] - делегировать
   - @save - сохранить контекст
   - @next - следующий этап

Промпт роли:
{self._load_role_prompt(role_name)}

---
.windsurfrules загружен: {bool(self.windsurfrules)}
"""
        
        return AgentResult(
            success=True,
            data={"instruction": instruction, "mode": "manual"},
            metadata={"role": role_name, "task": task}
        )

    def _load_windsurfrules(self) -> Optional[str]:
        """Загрузить .windsurfrules для fallback."""
        rules_file = Path(__file__).parent.parent / ".windsurfrules"
        
        if not rules_file.exists():
            logger.warning(".windsurfrules not found")
            return None
        
        try:
            content = rules_file.read_text(encoding="utf-8")
            logger.info(f".windsurfrules loaded ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Failed to load .windsurfrules: {e}")
            return None

    def _load_role_prompt(self, role_name: str) -> str:
        """Загрузить промпт конкретной роли."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        
        for prompt_file in prompts_dir.glob(f"*_{role_name}.md"):
            try:
                return prompt_file.read_text(encoding="utf-8")
            except Exception:
                pass
        
        return f"[Prompt not found for {role_name}]"

    def reset(self):
        """Сбросить состояние маршрутизатора."""
        self._agents.clear()
        self.delegation_history.clear()
        self._delegation_depth = 0
        logger.info("[Router] State reset")
