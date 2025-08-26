"""Core data models for the clean insight synthesizer."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    INTERVIEW_TRANSCRIPT = "interview_transcript"
    MEETING_NOTES = "meeting_notes"
    SURVEY_RESPONSES = "survey_responses"
    FIELD_NOTES = "field_notes"
    USER_FEEDBACK = "user_feedback"
    UNKNOWN = "unknown"


class AnalysisLens(Enum):
    PAIN_POINTS = "pain_points"
    USER_NEEDS = "user_needs"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    EMOTIONAL_DRIVERS = "emotional_drivers"
    DECISION_FACTORS = "decision_factors"
    BARRIERS = "barriers"
    MOTIVATIONS = "motivations"
    FRUSTRATIONS = "frustrations"
    SATISFACTION_DRIVERS = "satisfaction_drivers"
    WORKAROUNDS = "workarounds"


@dataclass
class ResearchPlan:
    questions: List[str]
    background: Optional[str] = None
    assumptions: List[str] = field(default_factory=list)
    methodology: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    target_lenses: List[AnalysisLens] = field(default_factory=list)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.questions:
            errors.append("At least one research question required")
        if not self.target_lenses:
            errors.append("At least one analysis lens required")
        return errors


@dataclass
class Document:
    path: Path
    content: str
    doc_type: DocumentType
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def word_count(self) -> int:
        return len(self.content.split())


@dataclass
class Chunk:
    text: str
    source: Document
    chunk_type: str
    speaker: Optional[str] = None
    embedding: Optional[List[float]] = None  # type: ignore[type-arg]
    cluster_id: Optional[int] = None
    metadata: Dict = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


@dataclass
class Theme:
    name: str
    summary: str
    supporting_chunks: List[Chunk]
    confidence: float
    addresses_questions: List[int]
    primary_lens: AnalysisLens
    secondary_lenses: List[AnalysisLens] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    @property
    def chunk_count(self) -> int:
        return len(self.supporting_chunks)


@dataclass
class Report:
    research_plan: ResearchPlan
    themes: List[Theme]
    coverage_analysis: Dict
    tensions: List[Dict]
    markdown: str
    generated_at: datetime = field(default_factory=datetime.now)

