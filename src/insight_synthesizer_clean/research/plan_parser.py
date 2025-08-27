"""Research plan parser with LLM fallback."""

from pathlib import Path
from typing import List

from ..models import ResearchPlan, AnalysisLens
from ..prompts import PromptRegistry
from insight_synthesizer.llm.client import get_llm_client


class ResearchPlanParser:
    def __init__(self):
        self.llm = get_llm_client()

    def parse(self, path: Path) -> ResearchPlan:
        content = path.read_text(encoding="utf-8", errors="ignore")
        questions = self._extract_bullets(content)
        if len(questions) < 2:
            ok, data = self.llm.generate_json(PromptRegistry.get("EXTRACT_RESEARCH_PLAN", content=content))
            if ok:
                questions.extend(data.get("questions", []))
        # Default to all lenses if none specified
        lenses = [l for l in AnalysisLens]
        return ResearchPlan(questions=questions, target_lenses=lenses)

    def _extract_bullets(self, content: str) -> List[str]:
        lines = [ln.strip() for ln in content.splitlines()]
        qs = [ln[2:].strip() for ln in lines if ln.startswith("- ") and len(ln) > 2]
        return qs

