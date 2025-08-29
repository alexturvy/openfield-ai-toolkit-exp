"""
Insight Synthesizer - AI-powered research data analysis tool.

This module provides functionality to analyze qualitative research data
through a hybrid approach combining semantic embeddings, statistical clustering,
and focused LLM synthesis.
"""

from .pipeline import InsightSynthesizer
# Backward compatibility shim for tests expecting llm_providers
try:
    from .llm import client as llm_providers  # type: ignore
except Exception:
    llm_providers = None
from .config import get_config, get_lens_config, ANALYSIS_LENSES

__version__ = "1.0.0"
__all__ = [
    "InsightSynthesizer",
    "get_config", 
    "get_lens_config",
    "ANALYSIS_LENSES"
]