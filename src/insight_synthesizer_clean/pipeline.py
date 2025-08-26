"""Clean pipeline coordinator tying existing services to the new models."""

from pathlib import Path
from typing import List

from .models import ResearchPlan, Document, Chunk, Theme, Report, AnalysisLens
from .documents.handlers import get_handler_for_path
from .analysis.synthesis import ThemeSynthesizer

# Reuse existing embedding + clustering
from ..insight_synthesizer.analysis.embeddings import generate_embeddings
from ..insight_synthesizer.analysis.clustering import perform_clustering


class Pipeline:
    def __init__(self):
        self.synthesizer = ThemeSynthesizer()

    def run(self, research_plan_path: Path, document_paths: List[Path]) -> Report:
        plan = self._parse_research_plan(research_plan_path)
        chunks = self._load_and_chunk_documents(document_paths)
        chunks = generate_embeddings(chunks)
        chunks, clusters = perform_clustering(chunks)
        cluster_lists: List[List[Chunk]] = [c.chunks for c in clusters]
        themes = self.synthesizer.synthesize_for_lenses(cluster_lists, plan)
        report = self._generate_report(plan, themes)
        return report

    def _parse_research_plan(self, path: Path) -> ResearchPlan:
        content = path.read_text(encoding="utf-8", errors="ignore")
        # naive parse: lines starting with "- " are questions
        questions: List[str] = [ln[2:].strip() for ln in content.splitlines() if ln.strip().startswith("- ")]
        if not questions:
            questions = [ln.strip() for ln in content.splitlines() if ln.strip()]
            questions = questions[:3]

        # default: analyze across all lenses
        lenses = [l for l in AnalysisLens]
        return ResearchPlan(questions=questions, target_lenses=lenses)

    def _load_and_chunk_documents(self, paths: List[Path]) -> List[Chunk]:
        chunks: List[Chunk] = []
        for p in paths:
            handler = get_handler_for_path(p)
            doc: Document = handler.load(p)
            chunks.extend(handler.chunk(doc))
        return chunks

    def _generate_report(self, plan: ResearchPlan, themes: List[Theme]) -> Report:
        # very simple markdown for now
        md_lines: List[str] = []
        md_lines.append("# Insight Report")
        md_lines.append("")
        md_lines.append("## Research Questions")
        for i, q in enumerate(plan.questions):
            md_lines.append(f"- ({i}) {q}")
        md_lines.append("")
        md_lines.append("## Themes")
        for t in themes:
            md_lines.append(f"### {t.name} [{t.primary_lens.value}] ({t.confidence:.2f})")
            md_lines.append(t.summary)
            md_lines.append("")

        markdown = "\n".join(md_lines)
        coverage = {"num_themes": len(themes)}
        return Report(
            research_plan=plan,
            themes=themes,
            coverage_analysis=coverage,
            tensions=[],
            markdown=markdown,
        )

