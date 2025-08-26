"""Document handlers implementing a simple plugin system."""

from pathlib import Path
from typing import List, Protocol

from ..models import Document, Chunk, DocumentType


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
        return Document(path=path, content=content, doc_type=DocumentType.INTERVIEW_TRANSCRIPT)

    def chunk(self, document: Document) -> List[Chunk]:
        # Naive speaker-turn chunking: split on blank lines; attach no speaker for now
        paragraphs = [p.strip() for p in document.content.split("\n\n") if p.strip()]
        chunks: List[Chunk] = []
        for i, para in enumerate(paragraphs):
            if len(para) < 80:
                continue
            chunks.append(
                Chunk(
                    text=para,
                    source=document,
                    chunk_type="speaker_turn",
                    metadata={"paragraph_index": i},
                )
            )
        return chunks


class NotesHandler:
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in [".txt", ".md"]

    def load(self, path: Path) -> Document:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return Document(path=path, content=content, doc_type=DocumentType.MEETING_NOTES)

    def chunk(self, document: Document) -> List[Chunk]:
        paragraphs = [p.strip() for p in document.content.split("\n\n") if p.strip()]
        chunks: List[Chunk] = []
        for i, para in enumerate(paragraphs):
            if len(para) < 100:
                continue
            chunks.append(
                Chunk(
                    text=para,
                    source=document,
                    chunk_type="paragraph",
                    metadata={"paragraph_index": i},
                )
            )
        return chunks


DOCUMENT_HANDLERS: List[DocumentHandler] = [
    InterviewTranscriptHandler(),
    NotesHandler(),
]


def get_handler_for_path(path: Path) -> DocumentHandler:
    for handler in DOCUMENT_HANDLERS:
        if handler.can_handle(path):
            return handler
    raise ValueError(f"No handler found for {path}")

