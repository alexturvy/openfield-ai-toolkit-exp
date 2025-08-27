"""CLI for the clean pipeline."""

from pathlib import Path
import click

from .pipeline import Pipeline
from .models import AnalysisLens
from .config import PipelineConfig


@click.command()
@click.option("--research-plan", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--documents", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--pattern", default="**/*.txt", help="Glob to match documents")
@click.option("--output", type=click.Path(path_type=Path), default=Path("report.md"))
@click.option("--lenses", default="all", help="Comma-separated lenses or 'all'")
@click.option("--config", type=click.Path(exists=False, path_type=Path), required=False)
@click.option("--no-progress", is_flag=True, default=False, help="Disable progress display")
def main(research_plan: Path, documents: Path, pattern: str, output: Path, lenses: str, config: Path | None, no_progress: bool):
	if config:
		cfg = PipelineConfig.from_env()
	else:
		cfg = PipelineConfig.from_env()
	pipe = Pipeline(cfg)
	# Lenses override (optional)
	# For now, we keep default (all) to preserve multi-lens behavior
	doc_paths = sorted(documents.glob(pattern))
	report = pipe.run(research_plan, doc_paths)
	output.write_text(report.markdown, encoding="utf-8")
	click.echo(f"✓ Report saved to {output}")


if __name__ == "__main__":
	main()

