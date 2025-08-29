#!/usr/bin/env python3
"""
Research Insight Extractor - CLI entrypoint.
Implements a minimal end-to-end pipeline:
 - Load transcripts
 - Preprocess and parse into utterances with traceable spans
 - Parse research plan
 - Extract potential quotes (heuristic for now)
 - Verify quotes against source with exact spans
 - Generate a simple text report

Local-first: no network calls are required for the MVP.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from openfield.io.files import discover_files, read_text_file
from openfield.parse.transcripts import parse_transcript_file
from openfield.research.plan import load_research_plan
from openfield.research.plan_llm import llm_parse_research_plan
from openfield.analysis.extract_quotes import extract_relevant_quotes_heuristic
from openfield.analysis.verify import verify_quotes
from openfield.report.text import generate_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--interviews', nargs='+', required=True,
                        help='Glob(s) for transcript files (txt preferred).')
    parser.add_argument('--research', required=True,
                        help='Path to research questions markdown file.')
    parser.add_argument('--output', default='output/report.txt',
                        help='Path to write the generated report.')
    parser.add_argument('--model', default='ollama', choices=['ollama', 'openai', 'none'],
                        help='LLM backend for research plan parsing (ollama preferred).')
    parser.add_argument('--ollama-url', default='http://localhost:11434',
                        help='Ollama base URL.')
    parser.add_argument('--ollama-model', default='llama3.1',
                        help='Ollama model name.')
    args = parser.parse_args()

    interview_paths: List[Path] = discover_files(args.interviews)
    if not interview_paths:
        raise SystemExit('No interview files found for provided patterns.')

    interviews = []
    for path in interview_paths:
        raw_text = read_text_file(path)
        interviews.append(parse_transcript_file(path, raw_text))

    # Load research plan (LLM-first for DOCX, fallback to heuristics)
    base_plan = load_research_plan(args.research)
    if args.model == 'ollama':
        try:
            doc_text = Path(args.research).read_text(errors='replace') if not args.research.endswith('.docx') else None
            if doc_text is None:
                # If DOCX, re-use loader to convert to text
                from openfield.research.plan import _read_docx  # type: ignore
                doc_text = _read_docx(Path(args.research))
            llm_plan = llm_parse_research_plan(doc_text, base_url=args.ollama_url, model=args.ollama_model)
            questions = llm_plan.questions or base_plan.questions
        except Exception:
            questions = base_plan.questions
    else:
        questions = base_plan.questions
    research = base_plan.__class__(questions=questions, background=None)

    answered = []
    for q in research.questions:
        potentials = extract_relevant_quotes_heuristic(interviews, q)
        verified = verify_quotes(potentials, interviews)
        if verified:
            answered.append({
                'question': q,
                'quotes': verified,
                'summary': f"Found {len(verified)} verified quotes"
            })

    report_text = generate_report({
        'answered_questions': answered,
        'unexpected_insights': [],
        'tensions': []
    }, research)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text)
    print(f'Report written to {out_path}')


if __name__ == '__main__':
    main()


