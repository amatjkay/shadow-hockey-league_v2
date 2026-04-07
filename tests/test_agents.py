"""
Tests for Multi-Agent System

Тесты для проверки работы системы агентов:
- Базовый класс агентов
- Менеджер контекста
- Маршрутизатор
- Конкретные агенты
- Fallback на ручной режим
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from agents.base import BaseAgent, AgentResult, DelegationRequest, BoundaryCheck
from agents.context_manager import ContextManager
from agents.router import AgentRouter, RouterConfig
from agents.concrete_agents import (
    AnalystAgent, ArchitectAgent, PlannerAgent,
    DeveloperAgent, QATesterAgent, DesignerAgent,
    create_agent, AGENT_FACTORY
)


class TestAgentResult:
    """Тесты для AgentResult."""

    def test_success_result(self):
        result = AgentResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.needs_delegation is False
        assert result.data == {"key": "value"}

    def test_error_result(self):
        result = AgentResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_delegation_result(self):
        delegation = DelegationRequest(
            target_role="DEVELOPER",
            reason="Need to write code",
            specific_request="Implement feature"
        )
        result = AgentResult(success=True, delegation_request=delegation)
        assert result.needs_delegation is True
        assert result.delegation_request.target_role == "DEVELOPER"


class TestDelegationRequest:
    """Тесты для DelegationRequest."""

    def test_delegation_request_creation(self):
        req = DelegationRequest(
            target_role="ANALYST",
            reason="Unclear requirements",
            context={"task": "test"},
            specific_request="Analyze requirements"
        )
        assert req.target_role == "ANALYST"
        assert req.reason == "Unclear requirements"
        assert req.timestamp is not None


class TestBoundaryCheck:
    """Тесты для BoundaryCheck."""

    def test_allowed_boundary(self):
        check = BoundaryCheck(allowed=True)
        assert check.allowed is True
        assert check.reason == ""
        assert check.suggested_role == ""

    def test_violated_boundary(self):
        check = BoundaryCheck(
            allowed=False,
            reason="Out of scope",
            suggested_role="ARCHITECT"
        )
        assert check.allowed is False
        assert check.suggested_role == "ARCHITECT"


class TestContextManager:
    """Тесты для ContextManager."""

    @pytest.fixture
    def temp_context_dir(self):
        """Создать временную директорию для контекста."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_context_manager_creation(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        assert ctx.context_dir.exists()
        assert ctx.context_dir.is_dir()

    def test_read_nonexistent_file(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        content = ctx.load_state_summary()
        assert content == ""

    def test_write_and_read_file(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        test_content = "# Test Content\n\nThis is a test."
        
        ctx.save_state_summary(test_content)
        content = ctx.load_state_summary()
        
        assert content == test_content

    def test_redact_secrets_string(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        
        test_data = "password=secret123 and api_key=abc456"
        result = ctx._redact_secrets(test_data)
        
        assert "secret123" not in result
        assert "abc456" not in result
        assert "[REDACTED]" in result

    def test_redact_secrets_dict(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        
        test_data = {
            "username": "admin",
            "password": "secret123",
            "api_key": "abc456"
        }
        result = ctx._redact_secrets(test_data)
        
        assert result["username"] == "admin"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"

    def test_estimate_token_count(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        
        text = "A" * 4000  # ~1000 tokens
        count = ctx.estimate_token_count(text)
        
        assert count == 1000

    def test_get_context_size(self, temp_context_dir):
        ctx = ContextManager(context_dir=str(temp_context_dir))
        
        # Создаём файлы контекста
        ctx.save_state_summary("Test content")
        
        size = ctx.get_context_size()
        assert "total" in size
        assert size["total"]["chars"] > 0


class TestAgentRouter:
    """Тесты для AgentRouter."""

    @pytest.fixture
    def temp_context_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def router(self, temp_context_dir):
        return AgentRouter(
            mode="automatic",
            context_dir=str(temp_context_dir)
        )

    def test_router_creation(self, router):
        assert router.mode == "automatic"
        assert router.context_manager is not None
        assert router.windsurfrules is not None

    def test_router_manual_mode(self, temp_context_dir):
        router = AgentRouter(mode="manual", context_dir=str(temp_context_dir))
        result = router.execute_task("ANALYST", "Test task")
        
        assert result.success is True
        assert result.data["mode"] == "manual"
        assert "instruction" in result.data

    def test_router_automatic_mode(self, router):
        result = router.execute_task("ANALYST", "Test task")
        
        assert result.success is True
        assert isinstance(result, AgentResult)

    def test_router_switch_mode(self, router):
        assert router.mode == "automatic"
        
        router.switch_mode("manual")
        assert router.mode == "manual"
        
        router.switch_mode("hybrid")
        assert router.mode == "hybrid"

    def test_router_invalid_mode(self, router):
        with pytest.raises(ValueError):
            router.switch_mode("invalid")

    def test_router_get_status(self, router):
        status = router.get_agent_status()
        
        assert "mode" in status
        assert "agents" in status
        assert "delegation_count" in status
        assert "context_size" in status

    def test_router_reset(self, router):
        router.execute_task("ANALYST", "Test task")
        assert len(router._agents) > 0
        
        router.reset()
        assert len(router._agents) == 0
        assert len(router.delegation_history) == 0


class TestConcreteAgents:
    """Тесты для конкретных агентов."""

    @pytest.fixture
    def temp_context_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def context_manager(self, temp_context_dir):
        return ContextManager(context_dir=str(temp_context_dir))

    def test_analyst_agent_creation(self, context_manager):
        agent = AnalystAgent(context_manager=context_manager)
        assert agent.ROLE_NAME == "ANALYST"
        assert len(agent.CAPABILITIES) > 0
        assert len(agent.BOUNDARIES) > 0

    def test_architect_agent_creation(self, context_manager):
        agent = ArchitectAgent(context_manager=context_manager)
        assert agent.ROLE_NAME == "ARCHITECT"

    def test_planner_agent_creation(self, context_manager):
        agent = PlannerAgent(context_manager=context_manager)
        assert agent.ROLE_NAME == "PLANNER"

    def test_developer_agent_creation(self, context_manager):
        agent = DeveloperAgent(context_manager=context_manager)
        assert agent.ROLE_NAME == "DEVELOPER"

    def test_qa_tester_agent_creation(self, context_manager):
        agent = QATesterAgent(context_manager=context_manager)
        assert agent.ROLE_NAME == "QA_TESTER"

    def test_designer_agent_creation(self, context_manager):
        agent = DesignerAgent(context_manager=context_manager)
        assert agent.ROLE_NAME == "DESIGNER"

    def test_create_agent_factory(self, context_manager):
        for role_name in AGENT_FACTORY.keys():
            agent = create_agent(role_name, context_manager=context_manager)
            assert agent is not None
            assert agent.ROLE_NAME == role_name

    def test_create_agent_invalid_role(self, context_manager):
        with pytest.raises(ValueError):
            create_agent("INVALID_ROLE", context_manager=context_manager)

    def test_agent_execute_task(self, context_manager):
        agent = AnalystAgent(context_manager=context_manager)
        result = agent.execute("Test analysis task")
        
        assert result.success is True

    def test_agent_boundary_check(self, context_manager):
        agent = AnalystAgent(context_manager=context_manager)
        
        # Задача в границах
        result = agent._check_boundaries("Analyze requirements")
        assert result.allowed is True
        
        # Задача вне границ (архитектура)
        result = agent._check_boundaries("Design architecture")
        assert result.allowed is False
        assert result.suggested_role == "ARCHITECT"


class TestFallbackMechanism:
    """Тесты для fallback механизма."""

    @pytest.fixture
    def temp_context_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_fallback_to_manual_on_error(self, temp_context_dir):
        config = RouterConfig(fallback_to_manual=True)
        router = AgentRouter(
            mode="automatic",
            context_dir=str(temp_context_dir),
            config=config
        )
        
        # Даже при ошибке должен сработать fallback
        result = router.execute_task("ANALYST", "Test task")
        assert result.success is True

    def test_windsurfrules_loaded(self, temp_context_dir):
        router = AgentRouter(
            mode="manual",
            context_dir=str(temp_context_dir)
        )
        
        rules = router.get_windsurfrules()
        assert rules is not None
        assert len(rules) > 0

    def test_manual_mode_returns_instruction(self, temp_context_dir):
        router = AgentRouter(mode="manual", context_dir=str(temp_context_dir))
        result = router.execute_task("ANALYST", "Test task")
        
        assert result.success is True
        assert "instruction" in result.data
        assert "ANALYST" in result.data["instruction"]


class TestWorkflowExecution:
    """Тесты для выполнения воркфлоу."""

    @pytest.fixture
    def temp_context_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def router(self, temp_context_dir):
        return AgentRouter(mode="automatic", context_dir=str(temp_context_dir))

    def test_simple_workflow(self, router):
        workflow = [
            {"role": "ANALYST", "task": "Task 1"},
            {"role": "ARCHITECT", "task": "Task 2"},
        ]
        
        results = router.execute_workflow(workflow)
        
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_workflow_with_delegation(self, router):
        workflow = [
            {"role": "ANALYST", "task": "Analyze requirements"},
        ]
        
        results = router.execute_workflow(workflow)
        
        assert len(results) >= 1
        assert results[0].success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
