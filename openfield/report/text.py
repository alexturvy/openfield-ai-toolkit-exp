from __future__ import annotations

from typing import Dict

from openfield.models import ResearchPlan


def generate_report(findings: Dict, research: ResearchPlan) -> str:
    lines = []
    lines.append('=' * 60)
    lines.append('RESEARCH FINDINGS REPORT')
    lines.append('=' * 60)
    lines.append('')

    lines.append('RESEARCH QUESTIONS & ANSWERS')
    lines.append('-' * 40)

    for item in findings.get('answered_questions', []):
        lines.append(f"\nQ: {item['question']}")
        lines.append(f"A: {item['summary']}")
        lines.append('\nSupporting Evidence:')
        for q in item['quotes'][:3]:
            lines.append(f'  "{q["text"]}"')
            lines.append(f'  - {q["speaker"]}, {q["source"]}:{q["start_line"]}-{q["end_line"]}')
            lines.append('')

    return '\n'.join(lines)


