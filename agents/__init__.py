"""
Shadow Hockey League - Multi-Agent System

Модульная система агентов с поддержкой:
- Автоматического делегирования задач между ролями
- Управления контекстом через context/
- Fallback на ручной режим через .windsurfrules
- Интеграции с Flask приложением
- Подготовки для Qwen Subagents API

Режимы работы:
1. AUTOMATIC - агенты управляют делегированием автоматически
2. MANUAL - ручной режим через @role команды (старый подход)
3. HYBRID - можно переключаться между режимами на лету

Пример использования:
    from agents import AgentRouter
    
    # Автоматический режим
    router = AgentRouter(mode="automatic")
    result = router.execute_task("ANALYST", "Проанализировать требования")
    
    # Ручной режим (fallback)
    router = AgentRouter(mode="manual")
    # Использует старые промпты из prompts/
"""

from agents.router import AgentRouter, RouterConfig
from agents.context_manager import ContextManager
from agents.base import BaseAgent, AgentResult, DelegationRequest
from agents.concrete_agents import create_agent, AGENT_FACTORY
from agents.qwen_subagent_wrapper import QwenSubagentWrapper, QwenSubagentConfig

__all__ = [
    "AgentRouter",
    "RouterConfig",
    "ContextManager",
    "BaseAgent",
    "AgentResult",
    "DelegationRequest",
    "create_agent",
    "AGENT_FACTORY",
    "QwenSubagentWrapper",
    "QwenSubagentConfig",
]
__version__ = "1.0.0"
