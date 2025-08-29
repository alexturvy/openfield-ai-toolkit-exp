"""Document processing components for Insight Synthesizer."""

from .file_handlers import extract_text_from_file, find_supported_files, check_dependencies
from .structure_classifier import StructureClassifier, StructureClassification
from .adaptive_chunking import AdaptiveChunker, AdaptiveChunk

__all__ = [
    "extract_text_from_file",
    "find_supported_files",
    "check_dependencies",
    "StructureClassifier",
    "StructureClassification",
    "AdaptiveChunker",
    "AdaptiveChunk"
]