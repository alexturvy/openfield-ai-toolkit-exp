from __future__ import annotations

import re
from pathlib import Path
from typing import List

from openfield.models import ResearchPlan


QUESTION_PATTERNS = [
    re.compile(r'^\d+\.\s+(.+)$'),
    re.compile(r'^-\s+(.+\?)$'),
    re.compile(r'^RQ\d+:\s*(.+)$'),
]


def _read_docx(path: Path) -> str:
    try:
        from docx import Document  # type: ignore
    except Exception:
        raise RuntimeError('python-docx not installed. Install to read .docx files.')
    doc = Document(str(path))
    return '\n'.join(p.text for p in doc.paragraphs)


def load_research_plan(path_str: str) -> ResearchPlan:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == '.docx':
        content = _read_docx(path)
    else:
        content = path.read_text(errors='replace')
    lines = content.split('\n')
    questions: List[str] = []
    for line in lines:
        s = line.strip()
        for p in QUESTION_PATTERNS:
            m = p.match(s)
            if m:
                questions.append(m.group(1).strip())
                break
    if not questions:
        questions = [s.strip() for s in lines if '?' in s]
    return ResearchPlan(questions=questions)


