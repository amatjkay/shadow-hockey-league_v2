"""Local Qwen agent adapter."""
import os
from typing import Dict, Any
from .base import LLMAdapter, LLMConfig

class QwenAdapter(LLMAdapter):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Local Qwen agent may use a socket or local server; placeholder.
        self.endpoint = config.extra.get("endpoint") or os.getenv("QWEN_ENDPOINT")

    def query(self, prompt: str, context: Dict[str, Any] = None):
        # In a real implementation, call local Qwen agent over HTTP/socket.
        # For now, return a placeholder.
        return f"[Qwen local endpoint: {self.endpoint}] Response to: {prompt}"

    def chat(self, messages: list, context: Dict[str, Any] = None):
        text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        return f"[Qwen local] {text}"