"""Multi-model adapter package for LLM providers."""
import json
import os
from pathlib import Path
from typing import Optional, Any, Dict

from .base import LLMAdapter, LLMConfig
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .qwen_adapter import QwenAdapter

__all__ = [
    'LLMAdapter',
    'LLMConfig',
    'OpenAIAdapter',
    'AnthropicAdapter',
    'QwenAdapter',
    'load_config',
]


def _default_config_path() -> Path:
    # `.qwen/adapters/__init__.py` -> parent is `.qwen/`
    return Path(__file__).resolve().parents[1] / "config.json"


def load_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """Load best-effort config for adapters.

    Priority:
    - Environment variables (always)
    - `.qwen/config.json` (optional, mostly for non-secret flags)
    """
    provider_from_env = os.getenv("LLM_PROVIDER")
    provider_effective = (provider or provider_from_env or "").strip() or None

    cfg: Dict[str, Any] = {
        "provider": provider_effective,
        "model_name": (os.getenv("LLM_MODEL_NAME") or "").strip() or None,
        "api_key": (os.getenv("LLM_API_KEY") or "").strip() or None,
        "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", "2")),
        "extra": {},
    }

    # Provider-specific overrides (model + key)
    if provider_effective == "openai":
        cfg["model_name"] = (os.getenv("OPENAI_MODEL") or cfg["model_name"] or "").strip() or None
        cfg["api_key"] = (os.getenv("OPENAI_API_KEY") or cfg["api_key"] or "").strip() or None
    elif provider_effective == "anthropic":
        cfg["model_name"] = (os.getenv("ANTHROPIC_MODEL") or cfg["model_name"] or "").strip() or None
        cfg["api_key"] = (os.getenv("ANTHROPIC_API_KEY") or cfg["api_key"] or "").strip() or None
    elif provider_effective == "qwen":
        cfg["model_name"] = (os.getenv("QWEN_MODEL") or cfg["model_name"] or "").strip() or None
        cfg["extra"]["endpoint"] = (os.getenv("QWEN_ENDPOINT") or "").strip() or None

    # Optional `.qwen/config.json` read (do not expect secrets there)
    try:
        path = _default_config_path()
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            # Keep the door open for future fields without breaking callers.
            cfg["extra"]["operation_mode"] = raw.get("operation_mode", {}).get("current")
            cfg["extra"]["llm_provider_current"] = raw.get("llm_provider", {}).get("current")
    except Exception:
        # Best-effort: ignore file parsing errors and rely on env vars.
        pass

    return cfg


def get_adapter(provider: str, config: Optional[LLMConfig] = None) -> LLMAdapter:
    """Factory to get the appropriate adapter for a provider."""
    if config is None:
        loaded = load_config(provider=provider)
        if not loaded.get("model_name"):
            raise ValueError(
                "LLM config is missing required field `model_name`. "
                "Provide `config=LLMConfig(...)` explicitly or set environment variable "
                "`LLM_MODEL_NAME` (or provider-specific `OPENAI_MODEL` / `ANTHROPIC_MODEL` / `QWEN_MODEL`)."
            )
        config = LLMConfig(**loaded, provider=provider)

    if provider == 'openai':
        return OpenAIAdapter(config)
    if provider == 'anthropic':
        return AnthropicAdapter(config)
    if provider == 'qwen':
        return QwenAdapter(config)
    raise ValueError(f"Unsupported provider: {provider}")