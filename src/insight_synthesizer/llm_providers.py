# Compatibility shim expected by older tests
# Provides get_llm_provider(config) that returns an object with a generate(prompt, system) method.

from typing import Optional
from .llm.client import get_llm_client

class _ProviderWrapper:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.client = get_llm_client()
    def generate(self, prompt: str, system: Optional[str] = None):
        resp = self.client.generate(prompt, system=system, json_mode=False)
        if not resp.success:
            raise RuntimeError(resp.error or "Generation failed")
        return resp.content

def get_llm_provider(config: dict) -> _ProviderWrapper:
    # We ignore config details and return the unified client wrapper for compatibility
    return _ProviderWrapper(config.get('provider', 'unified'))
