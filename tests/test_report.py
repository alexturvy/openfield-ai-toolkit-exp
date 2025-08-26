from pathlib import Path
from src.insight_synthesizer.output.report_generator import generate_markdown_report


def test_generate_markdown_report(tmp_path):
    data = [
        {
            'theme_name': 'Theme A',
            'summary': 'Summary',
            'key_insights': ['one', 'two'],
            'severity': 'low',
        }
    ]
    output = tmp_path / 'report.md'
    generate_markdown_report(data, 'pain_points', output_path=str(output))
    assert output.exists()
    content = output.read_text()
    assert '# Research Synthesis Report' in content
    assert 'Theme A' in content
