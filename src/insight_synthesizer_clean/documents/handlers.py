"""Document handlers implementing a simple plugin system."""

from pathlib import Path
from typing import List, Protocol

from ..models import Document, Chunk, DocumentType
from .chunking import classify_document, chunk_by_paragraphs, chunk_speaker_turns


class DocumentHandler(Protocol):
    def can_handle(self, path: Path) -> bool:
        ...

    def load(self, path: Path) -> Document:
        ...

    def chunk(self, document: Document) -> List[Chunk]:
        ...


class InterviewTranscriptHandler:
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in [".txt", ".md"]

    def load(self, path: Path) -> Document:
        content = path.read_text(encoding="utf-8", errors="ignore")
        dtype = classify_document(content)
        if dtype is DocumentType.UNKNOWN:
            dtype = DocumentType.INTERVIEW_TRANSCRIPT
        return Document(path=path, content=content, doc_type=dtype)

    def chunk(self, document: Document) -> List[Chunk]:
        if document.doc_type is DocumentType.INTERVIEW_TRANSCRIPT:
            return chunk_speaker_turns(document)
        return chunk_by_paragraphs(document)


class NotesHandler:
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in [".txt", ".md"]

    def load(self, path: Path) -> Document:
        content = path.read_text(encoding="utf-8", errors="ignore")
        dtype = classify_document(content)
        if dtype is DocumentType.UNKNOWN:
            dtype = DocumentType.MEETING_NOTES
        return Document(path=path, content=content, doc_type=dtype)

    def chunk(self, document: Document) -> List[Chunk]:
        return chunk_by_paragraphs(document)


DOCUMENT_HANDLERS: List[DocumentHandler] = [
    InterviewTranscriptHandler(),
    NotesHandler(),
]


def get_handler_for_path(path: Path) -> DocumentHandler:
    for handler in DOCUMENT_HANDLERS:
        if handler.can_handle(path):
            return handler
    # Fallback: treat as notes
    return NotesHandler()

