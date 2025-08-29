from __future__ import annotations

import json
from typing import List

from openfield.models import ResearchPlan
from openfield.llm.ollama import OllamaClient


SYSTEM = (
    "You extract research questions from arbitrary documents.\n"
    "Return strict JSON with: {\"questions\": [\"...\"]}.\n"
    "Only include well-formed, answerable questions; deduplicate and preserve order of appearance."
)


def llm_parse_research_plan(doc_text: str, base_url: str = 'http://localhost:11434', model: str = 'llama3.1') -> ResearchPlan:
    client = OllamaClient(base_url=base_url, model=model)
    user = (
        "Extract research questions and return JSON.\n"
        "Document:\n" + doc_text[:20000]
    )
    try:
        data = client.chat_json(SYSTEM, user)
        qs: List[str] = [q.strip() for q in data.get('questions', []) if q and isinstance(q, str)]
        return ResearchPlan(questions=qs)
    except Exception:
        # Fallback: return empty; upstream code will combine with heuristics
        return ResearchPlan(questions=[])


