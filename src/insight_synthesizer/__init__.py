"""
Insight Synthesizer - AI-powered research data analysis tool.

This module provides functionality to analyze qualitative research data
through a hybrid approach combining semantic embeddings, statistical clustering,
and focused LLM synthesis.
"""

from .pipeline import InsightSynthesizer
from .config import get_config, get_lens_config, ANALYSIS_LENSES

__version__ = "1.0.0"
__all__ = [
    "InsightSynthesizer",
    "get_config", 
    "get_lens_config",
    "ANALYSIS_LENSES"
]