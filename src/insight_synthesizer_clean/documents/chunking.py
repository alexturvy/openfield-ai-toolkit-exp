"""Chunking strategies and simple classifier."""

from typing import List
import re
from ..models import Document, Chunk, DocumentType


def classify_document(content: str) -> DocumentType:
    # Very simple heuristic classifier
    if re.search(r"^\s*interviewer\b.*:|^\s*user\b.*:", content, re.I | re.M):
        return DocumentType.INTERVIEW_TRANSCRIPT
    if len(content.splitlines()) > 5 and any(h in content.lower() for h in ["meeting", "notes", "action items"]):
        return DocumentType.MEETING_NOTES
    return DocumentType.UNKNOWN


def chunk_by_paragraphs(document: Document, min_chars: int = 100) -> List[Chunk]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", document.content) if p.strip()]
    chunks: List[Chunk] = []
    for i, p in enumerate(paras):
        if len(p) < min_chars:
            continue
        chunks.append(Chunk(text=p, source=document, chunk_type="paragraph", metadata={"paragraph_index": i}))
    return chunks


def chunk_speaker_turns(document: Document, min_chars: int = 80) -> List[Chunk]:
    turns = re.split(r"\n\s*\n", document.content)
    chunks: List[Chunk] = []
    for i, t in enumerate(turns):
        t = t.strip()
        if len(t) < min_chars:
            continue
        m = re.match(r"^(?P<speaker>[A-Za-z][A-Za-z0-9 _-]{0,40}):\s*(?P<text>.+)$", t, re.S)
        speaker = m.group("speaker") if m else None
        text = m.group("text") if m else t
        chunks.append(Chunk(text=text, source=document, chunk_type="speaker_turn", speaker=speaker, metadata={"turn_index": i}))
    return chunks

