"""Anthropic Claude adapter."""
import os
from anthropic import Anthropic
from typing import Dict, Any
from .base import LLMAdapter, LLMConfig

class AnthropicAdapter(LLMAdapter):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = Anthropic(api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY"))

    def query(self, prompt: str, context: Dict[str, Any] = None):
        response = self.client.messages.create(
            model=self.config.model_name,
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def chat(self, messages: list, context: Dict[str, Any] = None):
        formatted = []
        for m in messages:
            role = "user" if m["role"] == "human" else "assistant"
            formatted.append({"role": role, "content": m["content"]})
        response = self.client.messages.create(
            model=self.config.model_name,
            max_tokens=1024,
            temperature=0.0,
            messages=formatted,
        )
        return response.content[0].text.strip()