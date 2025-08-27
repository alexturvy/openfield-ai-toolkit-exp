"""Markdown report generator for the clean pipeline."""

from typing import List
from ..models import ResearchPlan, Theme, Report


class ReportGenerator:
    def generate(self, plan: ResearchPlan, themes: List[Theme], validation, tensions: List[dict] | None = None) -> Report:
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
        md_lines.append("## Validation")
        md_lines.append(getattr(validation, 'validation_summary', ''))
        md_lines.append("")
        if tensions:
            md_lines.append("## Tensions")
            for t in tensions:
                md_lines.append(f"- {t.get('summary','')} (themes {t.get('theme_a','?')} vs {t.get('theme_b','?')})")
            md_lines.append("")
        markdown = "\n".join(md_lines)
        coverage = {
            "num_themes": len(themes),
            "overall_quality": getattr(validation, 'overall_quality', 'unknown')
        }
        return Report(
            research_plan=plan,
            themes=themes,
            coverage_analysis=coverage,
            tensions=tensions or [],
            markdown=markdown,
        )

