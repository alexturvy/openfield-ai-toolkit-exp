"""Detection of tensions and contradictions between themes."""

from typing import List, Dict
import json
import time
import requests
from rich.console import Console

from ..config import LLM_CONFIG
from ..utils import ProgressReporter
from ..utils.progress_reporter import ProcessType

console = Console()


def detect_tensions(themes: List[Dict], progress_reporter: ProgressReporter | None = None) -> List[Dict]:
    """Identify tensions or contradictions between synthesized themes."""
    from ..llm.client import get_llm_client
    
    if not themes:
        return []

    if progress_reporter:
        progress_reporter.start_process(
            ProcessType.TENSION_ANALYSIS,
            details={"themes": len(themes)},
            rationale="Highlight opposing sentiments or contradictory findings across themes",
        )

    # Create simplified theme descriptions to avoid JSON issues
    theme_descriptions = []
    for idx, t in enumerate(themes):
        # Sanitize theme data to avoid JSON parsing issues
        theme_name = str(t.get('theme_name', f'Theme {idx+1}')).replace('"', "'")
        summary = str(t.get('summary', '')).replace('"', "'").replace('\n', ' ')
        theme_descriptions.append(f"{idx + 1}. {theme_name}: {summary}")
    
    theme_text = "\n".join(theme_descriptions)

    # Simplified prompt to reduce JSON complexity
    prompt = f"""Analyze these themes for contradictions. Keep responses simple and short.

THEMES:
{theme_text}

Return ONLY valid JSON with opposing theme pairs:
{{
  "tensions": [
    {{
      "theme_a": 1,
      "theme_b": 2,
      "summary": "Brief tension description (max 50 chars)"
    }}
  ]
}}

Rules:
- Use theme numbers only (1, 2, 3, etc.)
- Keep summaries under 50 characters
- Maximum 5 tensions
- No special characters in summaries"""

    client = get_llm_client()
    success, parsed = client.generate_json(
        prompt=prompt,
        system="You are analyzing themes for contradictions",
        max_tokens=300
    )
    
    if not success:
        console.print(f"[yellow]Tension detection skipped: {parsed.get('error')}[/]")
        if progress_reporter:
            progress_reporter.complete_process({"tensions_found": 0})
        return []
    
    tensions = parsed.get("tensions", [])
    
    # Validate tension structure
    valid_tensions = []
    for t in tensions:
        if isinstance(t, dict) and all(k in t for k in ["theme_a", "theme_b", "summary"]):
            # Ensure theme indices are valid
            if 1 <= t["theme_a"] <= len(themes) and 1 <= t["theme_b"] <= len(themes):
                valid_tensions.append(t)
    
    if progress_reporter:
        progress_reporter.complete_process({"tensions_found": len(valid_tensions)})
    return valid_tensions
