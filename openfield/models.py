from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class Utterance:
    utterance_index: int
    speaker_original: str
    speaker_canonical: str
    text: str
    start_line: int
    end_line: int
    start_char: int
    end_char: int
    approx_timestamp: Optional[str] = None


@dataclass
class Interview:
    filepath: Path
    title: Optional[str]
    date: Optional[str]
    participants: List[str]
    utterances: List[Utterance]


@dataclass
class ResearchPlan:
    questions: List[str]
    background: Optional[str] = None


@dataclass
class PotentialQuote:
    quote_fragment: str
    speaker: Optional[str]
    source: Optional[str]
    relevance: Optional[str] = None


@dataclass
class VerifiedQuote:
    text: str
    speaker_original: str
    speaker_canonical: str
    source_file: str
    utterance_index: int
    start_line: int
    end_line: int
    start_char: int
    end_char: int
    relevance: Optional[str] = None
    confidence: Optional[float] = None
    match_method: str = 'exact'


