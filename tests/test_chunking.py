from pathlib import Path
from src.insight_synthesizer.document_processing.adaptive_chunking import AdaptiveChunker
from src.insight_synthesizer.document_processing.structure_classifier import (
    StructureClassification,
    ChunkingStrategy,
    ContentType,
)


def _make_classification() -> StructureClassification:
    return StructureClassification(
        content_type=ContentType.NARRATIVE_NOTES,
        speaker_labels=False,
        structure_confidence=1.0,
        suggested_chunking=ChunkingStrategy.BASIC_SENTENCE,
        metadata={},
        reasoning="test",
    )


def test_chunk_by_sentences_creates_chunks():
    chunker = AdaptiveChunker(max_chunk_size=50, min_chunk_size=1)
    text = "Sentence one. Sentence two! Sentence three?"
    classification = _make_classification()
    chunks = chunker._chunk_by_sentences(text, Path("file.txt"), classification)
    assert len(chunks) == 1
    assert chunks[0].metadata["sentence_count"] == 3
