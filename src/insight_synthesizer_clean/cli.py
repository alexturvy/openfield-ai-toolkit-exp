"""CLI for the clean pipeline."""

from pathlib import Path
import click

from .pipeline import Pipeline


@click.command()
@click.option("--research-plan", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--documents", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--pattern", default="**/*.txt", help="Glob to match documents")
@click.option("--output", type=click.Path(path_type=Path), default=Path("report.md"))
def main(research_plan: Path, documents: Path, pattern: str, output: Path):
    pipeline = Pipeline()
    doc_paths = sorted(documents.glob(pattern))
    report = pipeline.run(research_plan, doc_paths)
    output.write_text(report.markdown, encoding="utf-8")
    click.echo(f"✓ Report saved to {output}")


if __name__ == "__main__":
    main()

