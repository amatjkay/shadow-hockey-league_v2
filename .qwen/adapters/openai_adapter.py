"""OpenAI GPT adapter."""
import os
import openai
from typing import Dict, Any
from .base import LLMAdapter, LLMConfig

class OpenAIAdapter(LLMAdapter):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        openai.api_key = config.api_key or os.getenv("OPENAI_API_KEY")

    def query(self, prompt: str, context: Dict[str, Any] = None):
        response = openai.ChatCompletion.create(
            model=self.config.model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=self.config.timeout,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def chat(self, messages: list, context: Dict[str, Any] = None):
        response = openai.ChatCompletion.create(
            model=self.config.model_name,
            messages=messages,
            timeout=self.config.timeout,
        )
        return response.choices[0].message.content.strip()