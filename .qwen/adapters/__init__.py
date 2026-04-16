"""Multi-model adapter package for LLM providers."""

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

def get_adapter(provider: str, config: LLMConfig = None) -> LLMAdapter:
    """Factory to get the appropriate adapter for a provider."""
    if provider == 'openai':
        return OpenAIAdapter(config or LLMConfig())
    if provider == 'anthropic':
        return AnthropicAdapter(config or LLMConfig())
    if provider == 'qwen':
        return QwenAdapter(config or LLMConfig())
    raise ValueError(f"Unsupported provider: {provider}")