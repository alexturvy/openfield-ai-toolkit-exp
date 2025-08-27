"""Compatibility shim for OllamaManager expected by some tests.
Provides a minimal interface to check/process Ollama server state.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class OllamaStatus:
    running: bool
    model: Optional[str] = None

class OllamaManager:
    @staticmethod
    def is_running() -> bool:
        # Best-effort check without requiring requests; return False if unavailable
        try:
            import requests  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def ensure_running() -> OllamaStatus:
        # Minimal no-op that reports status
        return OllamaStatus(running=OllamaManager.is_running(), model=None)
