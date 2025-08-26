"""Theme synthesis and analysis across lenses."""

from typing import List, Optional

from ..models import Chunk, Theme, ResearchPlan, AnalysisLens
from ..prompts import PromptRegistry
from ...insight_synthesizer.llm.client import get_llm_client


class ThemeSynthesizer:
    def __init__(self):
        self.llm = get_llm_client()

    def synthesize_for_lenses(self, clusters: List[List[Chunk]], research_plan: ResearchPlan) -> List[Theme]:
        themes: List[Theme] = []
        for cluster in clusters:
            for lens in research_plan.target_lenses:
                theme = self._synthesize_single_theme(cluster, research_plan, lens)
                if theme and theme.confidence >= 0.6:
                    themes.append(theme)
        return themes

    def _synthesize_single_theme(self, cluster: List[Chunk], research_plan: ResearchPlan, lens: AnalysisLens) -> Optional[Theme]:
        chunks_text = self._format_chunks(cluster)
        questions_text = "\n".join(f"- {q}" for q in research_plan.questions)

        base_prompt = PromptRegistry.get(
            "SYNTHESIZE_THEME",
            chunks=chunks_text,
            questions=questions_text,
            lens=lens.value,
        )
        prompt = PromptRegistry.with_lens_guidance(base_prompt, lens.value)

        ok, data = self.llm.generate_json(prompt)
        if not ok:
            return None

        secondary_lenses: List[AnalysisLens] = []
        for l in data.get("secondary_lenses", []) or []:
            try:
                secondary_lenses.append(AnalysisLens(l))
            except Exception:
                continue

        return Theme(
            name=data.get("theme_name", ""),
            summary=data.get("summary", ""),
            supporting_chunks=cluster,
            confidence=float(data.get("confidence", 0.7)),
            addresses_questions=[int(i) for i in data.get("question_indices", [])],
            primary_lens=lens,
            secondary_lenses=secondary_lenses,
        )

    def _format_chunks(self, chunks: List[Chunk]) -> str:
        lines: List[str] = []
        for i, c in enumerate(chunks):
            speaker = f"[{c.speaker}] " if c.speaker else ""
            lines.append(f"Chunk {i+1}: {speaker}{c.text}")
        return "\n\n".join(lines)

