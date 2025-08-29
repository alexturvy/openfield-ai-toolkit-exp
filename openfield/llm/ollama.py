from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx


class OllamaClient:
    def __init__(self, base_url: str = 'http://localhost:11434', model: str = 'llama3.1') -> None:
        self.base_url = base_url.rstrip('/')
        self.model = model

    def chat_json(self, system: str, user: str, temperature: float = 0.1) -> Dict[str, Any]:
        prompt = f"System:\n{system}\n\nUser:\n{user}"
        data = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': temperature},
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(f'{self.base_url}/api/generate', json=data)
            resp.raise_for_status()
            out = resp.json()
        # Ollama returns plain text; attempt to parse JSON body from response
        text = out.get('response', '').strip()
        try:
            return json.loads(text)
        except Exception:
            # Try to extract JSON object from text
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
            raise ValueError('Ollama response was not valid JSON')


