"""Adapter to reuse existing tension detection from legacy pipeline."""

from typing import List, Dict
from insight_synthesizer.analysis.tensions import detect_tensions


def detect_tensions_from_clean(themes: List[Dict]) -> List[Dict]:
    return detect_tensions(themes, progress_reporter=None)

