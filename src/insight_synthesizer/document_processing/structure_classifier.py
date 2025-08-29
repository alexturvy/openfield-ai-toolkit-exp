"""Structure Classifier for Research Data"""

import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
import requests
from enum import Enum
from ..utils import ProgressReporter, ProcessStep
from ..utils.progress_reporter import ProcessType


class ContentType(Enum):
    """Supported content types for research data."""
    INTERVIEW_TRANSCRIPT = "interview_transcript"
    CONVERSATIONAL_FLOW = "conversational_flow" 
    NARRATIVE_NOTES = "narrative_notes"
    MIXED_CONTENT = "mixed_content"
    SURVEY_RESPONSES = "survey_responses"
    WORKSHOP_FOCUS_GROUP = "workshop_focus_group"
    UNKNOWN = "unknown"


class ChunkingStrategy(Enum):
    """Available chunking strategies."""
    SPEAKER_TURNS = "speaker_turns"
    SEMANTIC_PARAGRAPHS = "semantic_paragraphs"
    CONTENT_TYPE_SEPARATION = "content_type_separation"
    RESPONSE_BASED = "response_based"
    FACILITATED_DISCUSSION = "facilitated_discussion"
    BASIC_SENTENCE = "basic_sentence"


@dataclass
class StructureClassification:
    """Result of structure classification."""
    content_type: ContentType
    speaker_labels: bool
    structure_confidence: float
    suggested_chunking: ChunkingStrategy
    metadata: Dict
    reasoning: str


class StructureClassifier:
    """Classifies document structure to inform chunking strategy."""
    
    def __init__(self, progress_reporter: Optional[ProgressReporter] = None):
        self.progress_reporter = progress_reporter
        # No need to store model info - UnifiedLLMClient handles it
        
    def classify_document(self, text: str, filename: Optional[str] = None) -> StructureClassification:
        """
        Classify the structure of a document and recommend chunking strategy.
        
        Args:
            text: The document content to classify
            filename: Optional filename for additional context
            
        Returns:
            StructureClassification with recommendations
        """
        # Start progress reporting
        if self.progress_reporter:
            self.progress_reporter.start_process(
                ProcessType.DOCUMENT_CLASSIFICATION,
                details={
                    "filename": filename or "unknown",
                    "document_length": f"{len(text):,} characters",
                    "lines": len(text.split('\n'))
                },
                rationale="Analyzing document structure to select optimal chunking strategy for semantic coherence"
            )
        
        # First do quick pattern-based analysis
        quick_analysis = self._quick_pattern_analysis(text)
        
        if self.progress_reporter:
            self.progress_reporter.update_metrics({
                "speaker_labels_detected": quick_analysis['has_speaker_labels'],
                "dialogue_ratio": f"{quick_analysis['dialogue_ratio']:.2f}",
                "pattern_indicators": len(quick_analysis['formatting_indicators'])
            })
        
        # Then use LLM for nuanced classification
        llm_classification = self._llm_classify(text, quick_analysis, filename)
        
        # Combine results
        final_classification = self._merge_classifications(quick_analysis, llm_classification)
        
        if self.progress_reporter:
            self.progress_reporter.complete_process({
                "content_type": final_classification.content_type.value,
                "chunking_strategy": final_classification.suggested_chunking.value,
                "final_confidence": f"{final_classification.structure_confidence:.2f}"
            })
        
        return final_classification
    
    def _quick_pattern_analysis(self, text: str) -> Dict:
        """Fast pattern-based analysis to inform LLM classification."""
        analysis = {
            'length': len(text),
            'line_count': len(text.split('\n')),
            'has_speaker_labels': False,
            'speaker_patterns': [],
            'formatting_indicators': [],
            'dialogue_ratio': 0.0
        }
        
        # Check for common speaker label patterns
        speaker_patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',  # "John Smith:" or "John:"
            r'^[A-Z][a-z]+\s*:',  # "John:"
            r'^[A-Z]{2,}\s*:',    # "INTERVIEWER:"
            r'^\w+\s*\([^)]+\)\s*:', # "Alex (UX Researcher):"
            r'^\*\*[^*]+\*\*\s*:', # "**Dr. Smith**:"
            r'^[A-Z]\.(?:[A-Z]\.)*\s*:',  # "B.H.:" or "S.F.:" or "J.D.L.:"
        ]
        
        lines = text.split('\n')
        speaker_line_count = 0
        
        for pattern in speaker_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                analysis['speaker_patterns'].append({
                    'pattern': pattern,
                    'count': len(matches),
                    'examples': matches[:3]
                })
                speaker_line_count += len(matches)
        
        analysis['has_speaker_labels'] = speaker_line_count > 0
        analysis['dialogue_ratio'] = speaker_line_count / len(lines) if lines else 0
        
        # Check for formatting indicators
        formatting_checks = [
            ('questions', r'\?'),
            ('bold_text', r'\*\*[^*]+\*\*'),
            ('timestamps', r'\d{1,2}:\d{2}'),
            ('meta_comments', r'\([^)]*\)'),
            ('structured_sections', r'^#{1,3}\s+'),
        ]
        
        for name, pattern in formatting_checks:
            count = len(re.findall(pattern, text))
            if count > 0:
                analysis['formatting_indicators'].append({
                    'type': name,
                    'count': count
                })
        
        return analysis
    
    def _llm_classify(self, text: str, quick_analysis: Dict, filename: Optional[str]) -> Dict:
        """Use LLM to classify document structure."""
        from ..llm.client import get_llm_client
        
        # Prepare context for the LLM
        context = f"Document length: {quick_analysis['length']} characters\n"
        context += f"Lines: {quick_analysis['line_count']}\n"
        context += f"Speaker labels detected: {quick_analysis['has_speaker_labels']}\n"
        context += f"Dialogue ratio: {quick_analysis['dialogue_ratio']:.2f}\n"
        
        if filename:
            context += f"Filename: {filename}\n"
        
        # Take a representative sample for classification (first 2000 chars)
        sample_text = text[:2000]
        if len(text) > 2000:
            sample_text += "\n\n[... document continues for " + str(len(text) - 2000) + " more characters]"
        
        prompt = f"""You are analyzing research data to understand its structure. Based on the document sample and metadata below, classify the content type and recommend a chunking strategy.

DOCUMENT METADATA:
{context}

DOCUMENT SAMPLE:
{sample_text}

Classify this document and return ONLY valid JSON with this exact structure:
{{
    "content_type": "interview_transcript|conversational_flow|narrative_notes|mixed_content|survey_responses|workshop_focus_group|unknown",
    "speaker_labels": true|false,
    "structure_confidence": 0.0-1.0,
    "suggested_chunking": "speaker_turns|semantic_paragraphs|content_type_separation|response_based|facilitated_discussion|basic_sentence",
    "metadata": {{
        "primary_speakers": ["list", "of", "speaker", "names"],
        "has_interviewer": true|false,
        "conversation_style": "formal|informal|mixed",
        "contains_meta_content": true|false,
        "estimated_participants": 0-10
    }},
    "reasoning": "Brief explanation of classification decision"
}}

CLASSIFICATION GUIDELINES:
- interview_transcript: Any research interview or Q&A format
- conversational_flow: General discussion or conversation
- narrative_notes: Written observations, summaries, or notes
- mixed_content: Documents with multiple types of content
- survey_responses: Structured survey data
- workshop_focus_group: Group discussions with many participants
- unknown: Cannot determine structure

Be flexible - real documents are often messy. Focus on the dominant pattern."""
        
        client = get_llm_client()
        success, result = client.generate_json(
            prompt=prompt,
            system="You are analyzing research document structure",
            max_tokens=1500
        )
        
        if not success:
            print(f"LLM classification failed: {result.get('error')}")
            return self._fallback_classification(quick_analysis)
        
        return result
    
    def _fallback_classification(self, quick_analysis: Dict) -> Dict:
        """Fallback classification based on patterns only."""
        if quick_analysis['has_speaker_labels'] and quick_analysis['dialogue_ratio'] > 0.1:
            content_type = "interview_transcript"
            chunking = "speaker_turns"
            confidence = 0.6
        elif quick_analysis['dialogue_ratio'] > 0.05:
            content_type = "conversational_flow"  
            chunking = "semantic_paragraphs"
            confidence = 0.5
        else:
            content_type = "narrative_notes"
            chunking = "semantic_paragraphs" 
            confidence = 0.4
        
        return {
            "content_type": content_type,
            "speaker_labels": quick_analysis['has_speaker_labels'],
            "structure_confidence": confidence,
            "suggested_chunking": chunking,
            "metadata": {
                "primary_speakers": [],
                "has_interviewer": False,
                "conversation_style": "unknown",
                "contains_meta_content": False,
                "estimated_participants": 0
            },
            "reasoning": "Fallback pattern-based classification"
        }
    
    def _merge_classifications(self, quick_analysis: Dict, llm_result: Dict) -> StructureClassification:
        """Merge quick analysis with LLM classification."""
        
        # Convert string enums to enum objects
        try:
            content_type = ContentType(llm_result['content_type'])
        except ValueError:
            content_type = ContentType.UNKNOWN
            
        try:
            chunking_strategy = ChunkingStrategy(llm_result['suggested_chunking'])
        except ValueError:
            chunking_strategy = ChunkingStrategy.BASIC_SENTENCE
        
        # Adjust confidence based on pattern analysis agreement
        confidence = llm_result['structure_confidence']
        
        # Lower confidence if pattern analysis disagrees with LLM
        if llm_result['speaker_labels'] != quick_analysis['has_speaker_labels']:
            confidence *= 0.8
        
        return StructureClassification(
            content_type=content_type,
            speaker_labels=llm_result['speaker_labels'],
            structure_confidence=confidence,
            suggested_chunking=chunking_strategy,
            metadata=llm_result['metadata'],
            reasoning=llm_result['reasoning']
        )