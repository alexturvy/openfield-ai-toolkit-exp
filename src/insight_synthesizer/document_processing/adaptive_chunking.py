"""Adaptive Chunking Strategies for Research Data"""

import re
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from .structure_classifier import StructureClassification, ContentType, ChunkingStrategy
from ..config import PROCESSING_CONFIG
from ..utils import ProgressReporter
from ..utils.progress_reporter import ProcessType


@dataclass 
class AdaptiveChunk:
    """Enhanced chunk with adaptive metadata."""
    text: str
    source_file: Path
    chunk_type: str  # e.g., "speaker_turn", "paragraph", "response"
    metadata: Dict  # Speaker, timestamp, context, etc.
    embedding: Optional[object] = None
    cluster_id: Optional[int] = None


class AdaptiveChunker:
    """Routes to appropriate chunking strategy based on document classification."""
    
    def __init__(self, max_chunk_size: Optional[int] = None, min_chunk_size: Optional[int] = None, progress_reporter: Optional[ProgressReporter] = None):
        self.max_chunk_size = max_chunk_size or PROCESSING_CONFIG['max_chunk_size']
        self.min_chunk_size = min_chunk_size or PROCESSING_CONFIG['min_chunk_size']
        self.progress_reporter = progress_reporter
    
    def chunk_document(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """
        Chunk document using strategy recommended by structure classification.
        
        Args:
            text: Document content
            file_path: Source file path
            classification: Structure classification result
            
        Returns:
            List of AdaptiveChunk objects
        """
        strategy = classification.suggested_chunking
        
        if self.progress_reporter:
            self.progress_reporter.start_process(
                ProcessType.ADAPTIVE_CHUNKING,
                details={
                    "strategy": strategy.value,
                    "file": file_path.name,
                    "content_type": classification.content_type.value,
                    "document_length": f"{len(text):,} characters"
                },
                rationale=f"Using {strategy.value} to preserve semantic context and maintain speaker attribution based on document structure",
                confidence=classification.structure_confidence
            )
        
        # Route to appropriate chunking method
        if strategy == ChunkingStrategy.SPEAKER_TURNS:
            chunks = self._chunk_by_speaker_turns(text, file_path, classification)
        elif strategy == ChunkingStrategy.CONTENT_TYPE_SEPARATION:
            chunks = self._chunk_by_content_separation(text, file_path, classification)
        elif strategy == ChunkingStrategy.SEMANTIC_PARAGRAPHS:
            chunks = self._chunk_by_semantic_paragraphs(text, file_path, classification)
        elif strategy == ChunkingStrategy.RESPONSE_BASED:
            chunks = self._chunk_by_responses(text, file_path, classification)
        elif strategy == ChunkingStrategy.FACILITATED_DISCUSSION:
            chunks = self._chunk_by_facilitated_discussion(text, file_path, classification)
        else:
            # Fallback to basic sentence chunking
            chunks = self._chunk_by_sentences(text, file_path, classification)
        
        # Report final metrics
        if self.progress_reporter:
            speaker_chunks = sum(1 for chunk in chunks if chunk.metadata.get('speaker'))
            research_chunks = sum(1 for chunk in chunks if chunk.metadata.get('is_research_data', True))
            
            self.progress_reporter.complete_process({
                "chunks_generated": len(chunks),
                "speaker_attributed": speaker_chunks,
                "research_content": research_chunks,
                "avg_chunk_size": f"{sum(len(chunk.text) for chunk in chunks) // len(chunks) if chunks else 0} chars"
            })
        
        return chunks
    
    def _chunk_by_speaker_turns(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """Chunk by speaker turns for interview transcripts."""
        chunks = []
        
        # Clean up text - strip leading/trailing whitespace
        text = text.strip()
        
        # Pre-process to remove common artifacts that could interfere
        # Remove timestamp markers but keep the content
        text = re.sub(r'###\s*\d{2}:\d{2}:\d{2}\s*\n?', '\n', text)
        text = re.sub(r'###\s*Meeting ended.*', '', text, flags=re.MULTILINE)
        
        # Remove standalone ellipsis lines that are just pauses
        text = re.sub(r'^\s*\.\.\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Enhanced speaker patterns - ordered by specificity
        speaker_patterns = [
            # Pattern 1: Names with special characters (hyphens, periods, apostrophes)
            r"([A-Za-z][A-Za-z\s\-.']+?):\s*([^:]+?)(?=\n[A-Za-z][^:]*?:|$)",
            # Pattern 2: Full names "First Last: content"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*:\s*([^:]+?)(?=\n[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*:|$)',
            # Pattern 3: Standard "Name: content" format (fallback)
            r'([^\n:]+?):\s*([^:]+?)(?=\n[^\n:]+?:|$)',
            # Pattern 4: ALL CAPS "INTERVIEWER: content"  
            r'([A-Z]{2,})\s*:\s*([^:]+?)(?=\n[A-Z]{2,}\s*:|$)',
            # Pattern 5: Markdown bold "**Name**: content"
            r'(\*\*[^*]+\*\*)\s*:\s*([^:]+?)(?=\n\*\*[^*]+\*\*\s*:|$)',
        ]
        
        # Try each pattern until we find one that works
        best_pattern = None
        best_matches = []
        
        for pattern in speaker_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            if matches and len(matches) > len(best_matches):
                best_pattern = pattern
                best_matches = matches
        
        if best_matches:
            # Process speaker turns
            for i, (speaker, content) in enumerate(best_matches):
                content = content.strip()
                
                # Skip empty content but keep short responses
                if len(content) == 0:
                    continue
                
                # Handle continuation markers within content
                content = re.sub(r'\s*\.\.\.\s*', ' ', content)
                
                # Split long speaker turns into smaller chunks while preserving speaker context
                if len(content) > self.max_chunk_size:
                    sub_chunks = self._split_long_content(content, speaker)
                    for j, sub_content in enumerate(sub_chunks):
                        chunks.append(AdaptiveChunk(
                            text=sub_content,
                            source_file=file_path,
                            chunk_type="speaker_turn",
                            metadata={
                                "speaker": self._clean_speaker_name(speaker),
                                "turn_number": i,
                                "sub_chunk": j if len(sub_chunks) > 1 else None,
                                "is_interviewer": self._is_interviewer(speaker),
                                "content_type": "dialogue"
                            }
                        ))
                else:
                    chunks.append(AdaptiveChunk(
                        text=content,
                        source_file=file_path,
                        chunk_type="speaker_turn",
                        metadata={
                            "speaker": self._clean_speaker_name(speaker),
                            "turn_number": i,
                            "is_interviewer": self._is_interviewer(speaker),
                            "content_type": "dialogue"
                        }
                    ))
        else:
            # Fallback if no speaker patterns found
            return self._chunk_by_sentences(text, file_path, classification)
        
        return chunks
    
    def _chunk_by_content_separation(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """Separate meta-content from research data."""
        chunks = []
        
        # Identify sections that are likely meta-content vs actual research data
        lines = text.split('\n')
        current_section = []
        current_type = "unknown"
        
        meta_indicators = [
            r'creating|developing|crafting|establishing|outlining',
            r'persona|framework|structure|methodology',
            r'next step|moving on|focus on',
            r'I\'m|I\'ve|I will|My next'
        ]
        
        research_indicators = [
            r'interviewer:|interviewee:|alex:|dr\.|professor',
            r'thank you|appreciate|experience|frustrated',
            r'what|how|why|when|where',
            r'student|research|paper|assignment'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Classify line as meta-content or research data
            meta_score = sum(1 for pattern in meta_indicators if re.search(pattern, line, re.IGNORECASE))
            research_score = sum(1 for pattern in research_indicators if re.search(pattern, line, re.IGNORECASE))
            
            line_type = "meta" if meta_score > research_score else "research"
            
            # Start new section if type changes
            if line_type != current_type and current_section:
                section_text = '\n'.join(current_section)
                if len(section_text) >= self.min_chunk_size:
                    chunks.append(AdaptiveChunk(
                        text=section_text,
                        source_file=file_path,
                        chunk_type="content_section",
                        metadata={
                            "content_type": current_type,
                            "is_research_data": current_type == "research"
                        }
                    ))
                current_section = []
            
            current_section.append(line)
            current_type = line_type
        
        # Add final section
        if current_section:
            section_text = '\n'.join(current_section)
            if len(section_text) >= self.min_chunk_size:
                chunks.append(AdaptiveChunk(
                    text=section_text,
                    source_file=file_path,
                    chunk_type="content_section",
                    metadata={
                        "content_type": current_type,
                        "is_research_data": current_type == "research"
                    }
                ))
        
        return chunks
    
    def _chunk_by_semantic_paragraphs(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """Chunk by semantic paragraphs for narrative content."""
        chunks = []
        
        # Split by paragraphs (double newline or clear breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph would exceed max size, finish current chunk
            if current_length + len(para) > self.max_chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(AdaptiveChunk(
                        text=chunk_text,
                        source_file=file_path,
                        chunk_type="semantic_paragraph",
                        metadata={
                            "paragraph_count": len(current_chunk),
                            "content_type": "narrative"
                        }
                    ))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(para)
            current_length += len(para)
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(AdaptiveChunk(
                    text=chunk_text,
                    source_file=file_path,
                    chunk_type="semantic_paragraph",
                    metadata={
                        "paragraph_count": len(current_chunk),
                        "content_type": "narrative"
                    }
                ))
        
        return chunks
    
    def _chunk_by_responses(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """Chunk by individual responses for survey data."""
        # This would handle structured Q&A formats
        # Implementation depends on specific survey formats
        return self._chunk_by_semantic_paragraphs(text, file_path, classification)
    
    def _chunk_by_facilitated_discussion(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """Chunk facilitated discussions with multiple speakers."""
        # Similar to speaker turns but handles multiple participants
        return self._chunk_by_speaker_turns(text, file_path, classification)
    
    def _chunk_by_sentences(self, text: str, file_path: Path, classification: StructureClassification) -> List[AdaptiveChunk]:
        """Fallback sentence-based chunking."""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_length + len(sentence) > self.max_chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(AdaptiveChunk(
                        text=chunk_text,
                        source_file=file_path,
                        chunk_type="sentence_group",
                        metadata={
                            "sentence_count": len(current_chunk),
                            "content_type": "basic"
                        }
                    ))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += len(sentence)
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(AdaptiveChunk(
                    text=chunk_text,
                    source_file=file_path,
                    chunk_type="sentence_group",
                    metadata={
                        "sentence_count": len(current_chunk),
                        "content_type": "basic"
                    }
                ))
        
        return chunks
    
    def _split_long_content(self, content: str, speaker: str) -> List[str]:
        """Split long speaker content while preserving meaning."""
        # Try to split at sentence boundaries first
        sentences = re.split(r'(?<=[.!?])\s+', content)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > self.max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += len(sentence)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _clean_speaker_name(self, speaker: str) -> str:
        """Clean up speaker name for consistent identification."""
        # Remove markdown, parentheses content, etc.
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', speaker)  # Remove **bold**
        cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()   # Remove (role)
        return cleaned
    
    def _is_interviewer(self, speaker: str) -> bool:
        """Determine if speaker is likely the interviewer."""
        interviewer_indicators = [
            'interviewer', 'alex', 'researcher', 'moderator',
            'juli', 'lanzillotta'  # Add common interviewer names from your transcripts
        ]
        speaker_lower = speaker.lower()
        return any(indicator in speaker_lower for indicator in interviewer_indicators)