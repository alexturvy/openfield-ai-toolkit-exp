"""Clean pipeline coordinator tying existing services to the new models."""

from pathlib import Path
from typing import List

from .models import ResearchPlan, Document, Chunk, Theme, Report, AnalysisLens
from .documents.handlers import get_handler_for_path
from .analysis.synthesis import ThemeSynthesizer
from insight_synthesizer.validation.theme_validator import ThemeValidator
from .reports.generator import ReportGenerator
from .config import PipelineConfig
from insight_synthesizer.utils.progress_manager import get_progress_manager, ProgressStage

# Reuse existing embedding + clustering
from insight_synthesizer.analysis.embeddings import generate_embeddings
from insight_synthesizer.analysis.clustering import perform_clustering


class Pipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig.from_env()
        self.synthesizer = ThemeSynthesizer()
        self.validator = ThemeValidator()
        self.reporter = ReportGenerator()
        self.progress = get_progress_manager()

    def run(self, research_plan_path: Path, document_paths: List[Path]) -> Report:
        self.progress.start_pipeline(total_stages=7)
        plan = self._parse_research_plan(research_plan_path)
        with self.progress.stage_context(ProgressStage.DOCUMENT_PROCESSING, len(document_paths), "Chunking documents"):
            chunks = self._load_and_chunk_documents(document_paths)
        with self.progress.stage_context(ProgressStage.EMBEDDING_GENERATION, len(chunks), "Generating embeddings"):
            chunks = generate_embeddings(chunks, progress_manager=self.progress)
        with self.progress.stage_context(ProgressStage.CLUSTERING, 1, "Clustering chunks"):
            chunks, clusters = perform_clustering(chunks, progress_manager=self.progress)
        cluster_lists: List[List[Chunk]] = [c.chunks for c in clusters]
        with self.progress.stage_context(ProgressStage.INSIGHT_SYNTHESIS, len(cluster_lists), "Synthesizing themes"):
            themes = self.synthesizer.synthesize_for_lenses(cluster_lists, plan)
        with self.progress.stage_context(ProgressStage.VALIDATION, len(themes), "Validating with quotes"):
            validation = self._validate_themes(themes, document_paths)
        with self.progress.stage_context(ProgressStage.REPORT_GENERATION, 1, "Generating report"):
            report = self.reporter.generate(plan, themes, validation)
        self.progress.finish()
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

    def _validate_themes(self, themes: List[Theme], paths: List[Path]):
        # Adapt Theme objects to dict format expected by ThemeValidator
        theme_dicts = []
        for t in themes:
            theme_dicts.append({
                'theme_name': t.name,
                'summary': t.summary,
                'confidence': t.confidence,
                'question_indices': t.addresses_questions,
                'primary_lens': t.primary_lens.value,
            })
        return self.validator.validate_themes(theme_dicts, paths)

    # report generation handled by ReportGenerator

