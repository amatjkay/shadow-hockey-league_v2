"""Base adapter class and configuration model."""
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 2
    extra: Dict[str, Any] = Field(default_factory=dict)

class LLMAdapter:
    """Base adapter for LLM providers."""
    def __init__(self, config: LLMConfig):
        self.config = config

    def query(self, prompt: str, context: Dict[str, Any] = None):
        """Send a prompt to the LLM and return the response."""
        raise NotImplementedError("Subclasses must implement query()")

    def chat(self, messages: list, context: Dict[str, Any] = None):
        """Send a multi-turn conversation to the LLM."""
        raise NotImplementedError("Subclasses must implement chat()")