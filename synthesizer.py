#!/usr/bin/env python3
"""
Insight Synthesizer - AI-powered research data analysis tool.

This is the main entry point for the Insight Synthesizer, which provides
qualitative research data analysis through a hybrid approach combining
semantic embeddings, statistical clustering, and focused LLM synthesis.

Features:
- Adaptive document processing and chunking strategies
- Structure-aware content classification  
- Source-anchored insight generation
- Multiple analysis lenses (pain_points, opportunities, jobs_to_be_done, etc.)
- Clean modular architecture for maintainability

Usage:
    python3 synthesizer.py

The tool will guide you through selecting analysis lens and input directory.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from insight_synthesizer.cli import main
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running with the virtual environment activated:")
    print("  source .venv/bin/activate && python3 synthesizer.py")
    sys.exit(1)

if __name__ == "__main__":
    main()