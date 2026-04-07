"""
Agents Blueprint - Интеграция системы агентов с Flask

Предоставляет API endpoints для управления агентами через веб-интерфейс.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from agents import AgentRouter, ContextManager
from agents.router import RouterConfig

logger = logging.getLogger(__name__)

# Создаём blueprint
agents_bp = Blueprint(
    "agents",
    __name__,
    url_prefix="/api/agents"
)


@lru_cache(maxsize=1)
def get_router() -> AgentRouter:
    """
    Получить или создать маршрутизатор (singleton).
    
    Используем lru_cache для создания одного экземпляра на всё приложение.
    """
    config = RouterConfig(
        mode="automatic",
        max_delegation_depth=5,
        auto_save_context=True,
        enable_boundary_check=True,
        fallback_to_manual=True
    )
    
    return AgentRouter(config=config)


@agents_bp.route("/status", methods=["GET"])
def agent_status():
    """
    GET /api/agents/status
    
    Получить статус системы агентов.
    """
    try:
        router = get_router()
        status = router.get_agent_status()
        
        return jsonify({
            "success": True,
            "data": status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/execute", methods=["POST"])
def execute_task():
    """
    POST /api/agents/execute
    
    Выполнить задачу через агента.
    
    Body:
    {
        "role": "ANALYST",
        "task": "Описание задачи",
        "mode": "automatic"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        role = data.get("role")
        task = data.get("task")
        mode = data.get("mode", "automatic")
        
        if not role or not task:
            return jsonify({
                "success": False,
                "error": "role and task are required"
            }), 400
        
        # Получаем маршрутизатор и выполняем задачу
        router = get_router()
        
        # Если указан режим - переключаем
        if mode:
            router.switch_mode(mode)
        
        result = router.execute_task(role, task)
        
        response_data = {
            "success": result.success,
            "data": result.data,
            "metadata": result.metadata,
            "artifacts": result.artifacts
        }
        
        # Если требуется делегирование
        if result.needs_delegation:
            delegation = result.delegation_request
            response_data["delegation"] = {
                "target_role": delegation.target_role,
                "reason": delegation.reason,
                "specific_request": delegation.specific_request
            }
        
        # Если ошибка
        if result.error:
            response_data["error"] = result.error
        
        status_code = 200 if result.success else 400
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Error executing task: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/workflow", methods=["POST"])
def execute_workflow():
    """
    POST /api/agents/workflow
    
    Выполнить воркфлоу.
    
    Body:
    {
        "workflow": [
            {"role": "ANALYST", "task": "Задача 1"},
            {"role": "ARCHITECT", "task": "Задача 2"}
        ],
        "mode": "automatic"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        workflow = data.get("workflow")
        mode = data.get("mode", "automatic")
        
        if not workflow or not isinstance(workflow, list):
            return jsonify({
                "success": False,
                "error": "workflow array is required"
            }), 400
        
        router = get_router()
        
        if mode:
            router.switch_mode(mode)
        
        results = router.execute_workflow(workflow)
        
        response_data = {
            "success": True,
            "results": [
                {
                    "success": r.success,
                    "data": r.data,
                    "error": r.error,
                    "needs_delegation": r.needs_delegation,
                    "delegation": {
                        "target_role": r.delegation_request.target_role,
                        "reason": r.delegation_request.reason
                    } if r.needs_delegation else None
                }
                for r in results
            ],
            "total": len(results),
            "successful": sum(1 for r in results if r.success)
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/mode", methods=["POST"])
def switch_mode():
    """
    POST /api/agents/mode
    
    Переключить режим работы.
    
    Body:
    {
        "mode": "automatic"  // automatic, manual, hybrid
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        mode = data.get("mode")
        
        if mode not in ["automatic", "manual", "hybrid"]:
            return jsonify({
                "success": False,
                "error": f"Invalid mode: {mode}. Must be automatic, manual, or hybrid"
            }), 400
        
        router = get_router()
        router.switch_mode(mode)
        
        return jsonify({
            "success": True,
            "data": {
                "mode": mode
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error switching mode: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/mode", methods=["GET"])
def get_mode():
    """
    GET /api/agents/mode
    
    Получить текущий режим работы.
    """
    try:
        router = get_router()
        
        return jsonify({
            "success": True,
            "data": {
                "mode": router.mode
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting mode: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/context", methods=["GET"])
def context_status():
    """
    GET /api/agents/context
    
    Получить статус контекста.
    """
    try:
        ctx = ContextManager()
        size = ctx.get_context_size()
        
        return jsonify({
            "success": True,
            "data": {
                "size": size,
                "needs_summarization": False  # Можно добавить проверку
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting context status: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/context/summarize", methods=["POST"])
def summarize_context():
    """
    POST /api/agents/context/summarize
    
    Суммаризировать контекст.
    
    Body:
    {
        "summary": "Краткая версия контекста"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        summary = data.get("summary")
        
        if not summary:
            return jsonify({
                "success": False,
                "error": "summary is required"
            }), 400
        
        ctx = ContextManager()
        context_data = ctx.load_all()
        
        if ctx.needs_summarization(context_data):
            ctx.create_summary(context_data, summary)
            
            return jsonify({
                "success": True,
                "data": {
                    "message": "Context summarized successfully"
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Context size is within limits, summarization not needed"
            }), 400
        
    except Exception as e:
        logger.error(f"Error summarizing context: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/reset", methods=["POST"])
def reset():
    """
    POST /api/agents/reset
    
    Сбросить состояние маршрутизатора.
    """
    try:
        router = get_router()
        router.reset()
        
        # Сбрасываем кэш singleton
        get_router.cache_clear()
        
        return jsonify({
            "success": True,
            "data": {
                "message": "Agent router state reset"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route("/windsurfrules", methods=["GET"])
def get_windsurfrules():
    """
    GET /api/agents/windsurfrules
    
    Получить содержимое .windsurfrules.
    """
    try:
        router = get_router()
        rules = router.get_windsurfrules()
        
        return jsonify({
            "success": True,
            "data": {
                "rules": rules,
                "available": bool(rules)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting windsurfrules: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
