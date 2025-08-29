"""Post-analysis validation system for theme coverage and source verification."""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import requests
from rich.console import Console
from ..config import LLM_CONFIG
from ..utils import ProgressReporter
from ..utils.progress_reporter import ProcessType
from ..llm.client import get_llm_client

console = Console()


@dataclass
class QuoteEvidence:
    """Individual quote with source attribution."""
    text: str
    source_file: str
    speaker: Optional[str] = None
    confidence: float = 0.0
    context: Optional[str] = None


@dataclass
class ThemeCoverage:
    """Coverage analysis for a single theme."""
    theme_name: str
    quotes: List[QuoteEvidence]
    speakers_covered: List[str]
    files_covered: List[str]
    coverage_score: float
    distribution_quality: str  # "excellent", "good", "limited", "poor"


@dataclass
class ValidationResult:
    """Complete validation results for all themes."""
    theme_coverages: List[ThemeCoverage]
    overall_quality: str
    total_quotes_extracted: int
    avg_coverage_score: float
    validation_summary: str


class ThemeValidator:
    """Validates theme coverage by extracting supporting quotes from original transcripts."""
    
    def __init__(self, progress_reporter: Optional[ProgressReporter] = None):
        self.progress_reporter = progress_reporter
        self.original_files: Dict[str, str] = {}  # filename -> full text content
    
    def validate_themes(self, synthesized_themes: List[Dict], original_file_paths: List[Path], progress_manager=None) -> ValidationResult:
        """
        Validate theme coverage by extracting quotes from original transcripts.
        
        Args:
            synthesized_themes: List of theme dictionaries from LLM synthesis
            original_file_paths: List of paths to original transcript files
            
        Returns:
            ValidationResult with coverage analysis
        """
        if self.progress_reporter:
            self.progress_reporter.start_process(
                ProcessType.VALIDATION,
                details={
                    "themes_to_validate": len(synthesized_themes),
                    "source_files": len(original_file_paths),
                    "validation_strategy": "LLM-powered quote extraction"
                },
                rationale="Ensuring themes are well-supported across original source material with traceable evidence"
            )
        
        # Load original files
        self._load_original_files(original_file_paths)
        
        if self.progress_reporter:
            self.progress_reporter.update_metrics({
                "source_files_loaded": len(self.original_files),
                "total_source_chars": sum(len(content) for content in self.original_files.values())
            })
        
        # Validate each theme
        theme_coverages = []
        for i, theme in enumerate(synthesized_themes):
            if progress_manager:
                from ..utils.progress_manager import ProgressStage
                progress_manager.set_stage_status(ProgressStage.VALIDATION, f"Validating theme {i+1}/{len(synthesized_themes)}: {theme.get('theme_name', 'Unnamed')}")
            coverage = self._validate_single_theme(theme, i + 1, progress_manager)
            theme_coverages.append(coverage)
            if progress_manager:
                progress_manager.update_stage(ProgressStage.VALIDATION, 1)
        
        # Calculate overall metrics
        validation_result = self._calculate_overall_metrics(theme_coverages)
        
        if self.progress_reporter:
            self.progress_reporter.complete_process({
                "themes_validated": len(theme_coverages),
                "total_quotes_found": validation_result.total_quotes_extracted,
                "avg_coverage_score": f"{validation_result.avg_coverage_score:.2f}",
                "overall_quality": validation_result.overall_quality
            })
        
        return validation_result
    
    def _load_original_files(self, file_paths: List[Path]) -> None:
        """Load original transcript files for quote extraction."""
        from ..document_processing.file_handlers import extract_text_from_file
        
        for file_path in file_paths:
            try:
                content = extract_text_from_file(file_path)
                self.original_files[file_path.name] = content
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load {file_path.name}: {e}[/]")
    
    def _validate_single_theme(self, theme: Dict, theme_number: int, progress_manager=None) -> ThemeCoverage:
        """Validate a single theme by extracting supporting quotes."""
        theme_name = theme.get('theme_name', f'Theme {theme_number}')
        theme_summary = theme.get('summary', '')
        
        if not progress_manager:
            console.print(f"[cyan]Validating theme: {theme_name}[/]")
        
        # Extract quotes using LLM
        all_quotes = []
        for i, (filename, content) in enumerate(self.original_files.items()):
            if progress_manager:
                progress_manager.log_info(f"Extracting quotes for '{theme_name}' from {filename}")
            quotes = self._extract_quotes_for_theme(theme_name, theme_summary, content, filename)
            all_quotes.extend(quotes)
            if progress_manager:
                progress_manager.log_info(f"Found {len(quotes)} quotes in {filename}")
        
        # Analyze coverage
        speakers_covered = list(set(q.speaker for q in all_quotes if q.speaker))
        files_covered = list(set(q.source_file for q in all_quotes))
        
        # Calculate coverage score based on distribution and quality
        coverage_score = self._calculate_coverage_score(all_quotes, speakers_covered, files_covered)
        distribution_quality = self._assess_distribution_quality(coverage_score, len(speakers_covered), len(files_covered))
        
        return ThemeCoverage(
            theme_name=theme_name,
            quotes=all_quotes,
            speakers_covered=speakers_covered,
            files_covered=files_covered,
            coverage_score=coverage_score,
            distribution_quality=distribution_quality
        )
    
    def _extract_quotes_for_theme(self, theme_name: str, theme_summary: str, content: str, filename: str) -> List[QuoteEvidence]:
        """Extract relevant quotes for a theme from a single file using LLM."""
        
        quotes = []
        
        # Process in chunks if content is long
        CHUNK_SIZE = 6000
        OVERLAP = 1000
        
        if len(content) <= CHUNK_SIZE:
            # Process normally for short content
            quotes.extend(self._extract_quotes_chunk(
                theme_name, theme_summary, content, filename, 0
            ))
        else:
            # Process in overlapping chunks for long content
            for i in range(0, len(content), CHUNK_SIZE - OVERLAP):
                chunk = content[i:i + CHUNK_SIZE]
                chunk_quotes = self._extract_quotes_chunk(
                    theme_name, theme_summary, chunk, filename, i
                )
                quotes.extend(chunk_quotes)
                
                # Stop after finding 4 good quotes to save API calls
                if len(quotes) >= 4:
                    break
        
        return quotes[:4]  # Return max 4 quotes
    
    def _extract_quotes_chunk(self, theme_name: str, theme_summary: str, 
                             content_chunk: str, filename: str, 
                             offset: int) -> List[QuoteEvidence]:
        """Extract quotes from a single chunk."""
        
        prompt = f"""You are analyzing interview transcripts to find quotes that support a specific research theme.

THEME: {theme_name}
SUMMARY: {theme_summary}

TRANSCRIPT CONTENT:
{content_chunk}

Find and extract 2-4 of the most relevant quotes that support this theme. For each quote:
1. It must be verbatim from the transcript
2. It should clearly relate to the theme
3. Include enough context to be meaningful
4. Identify the speaker if possible

Return valid JSON with this structure:
{{
    "quotes": [
        {{
            "text": "Exact quote from transcript",
            "speaker": "Speaker name or null",
            "confidence": 0.0-1.0,
            "context": "Brief context explanation"
        }}
    ]
}}

Only include quotes that genuinely support the theme. If no relevant quotes exist, return empty quotes array."""

        client = get_llm_client()
        success, parsed_result = client.generate_json(
            prompt=prompt,
            system="You are extracting quotes from research transcripts",
            max_tokens=800
        )
        
        if not success:
            console.print(f"[yellow]Warning: Quote extraction failed for {filename}: {parsed_result.get('error')}[/]")
            return []
        
        quotes = []
        for quote_data in parsed_result.get('quotes', []):
            quote = QuoteEvidence(
                text=quote_data.get('text', ''),
                source_file=filename,
                speaker=quote_data.get('speaker'),
                confidence=quote_data.get('confidence', 0.5),
                context=quote_data.get('context')
            )
            quotes.append(quote)
        
        return quotes
    
    def _calculate_coverage_score(self, quotes: List[QuoteEvidence], speakers: List[str], files: List[str]) -> float:
        """Calculate coverage score based on quote quality, speaker distribution, and file coverage."""
        if not quotes:
            return 0.0
        
        # Base score from number and quality of quotes
        quote_score = min(len(quotes) / 5.0, 1.0)  # Normalize to max 5 quotes
        confidence_score = sum(q.confidence for q in quotes) / len(quotes)
        
        # Speaker distribution bonus (multiple speakers is better)
        speaker_bonus = min(len(speakers) / 3.0, 1.0) if speakers else 0.0
        
        # File coverage bonus (multiple files is better)  
        file_bonus = min(len(files) / len(self.original_files), 1.0)
        
        # Weighted combination
        coverage_score = (
            quote_score * 0.4 +
            confidence_score * 0.3 +
            speaker_bonus * 0.2 +
            file_bonus * 0.1
        )
        
        return min(coverage_score, 1.0)
    
    def _assess_distribution_quality(self, coverage_score: float, num_speakers: int, num_files: int) -> str:
        """Assess the quality of theme distribution across sources."""
        if coverage_score >= 0.8 and num_speakers >= 2 and num_files >= 2:
            return "excellent"
        elif coverage_score >= 0.6 and num_speakers >= 1 and num_files >= 2:
            return "good"
        elif coverage_score >= 0.4 and num_files >= 1:
            return "limited"
        else:
            return "poor"
    
    def _calculate_overall_metrics(self, theme_coverages: List[ThemeCoverage]) -> ValidationResult:
        """Calculate overall validation metrics."""
        if not theme_coverages:
            return ValidationResult(
                theme_coverages=[],
                overall_quality="poor",
                total_quotes_extracted=0,
                avg_coverage_score=0.0,
                validation_summary="No themes to validate"
            )
        
        total_quotes = sum(len(tc.quotes) for tc in theme_coverages)
        avg_coverage = sum(tc.coverage_score for tc in theme_coverages) / len(theme_coverages)
        
        # Assess overall quality
        excellent_themes = sum(1 for tc in theme_coverages if tc.distribution_quality == "excellent")
        good_themes = sum(1 for tc in theme_coverages if tc.distribution_quality in ["excellent", "good"])
        
        if excellent_themes >= len(theme_coverages) * 0.7:
            overall_quality = "excellent"
        elif good_themes >= len(theme_coverages) * 0.6:
            overall_quality = "good"
        elif avg_coverage >= 0.5:
            overall_quality = "adequate"
        else:
            overall_quality = "needs_improvement"
        
        # Generate summary
        validation_summary = self._generate_validation_summary(theme_coverages, avg_coverage, overall_quality)
        
        return ValidationResult(
            theme_coverages=theme_coverages,
            overall_quality=overall_quality,
            total_quotes_extracted=total_quotes,
            avg_coverage_score=avg_coverage,
            validation_summary=validation_summary
        )
    
    def _generate_validation_summary(self, theme_coverages: List[ThemeCoverage], avg_coverage: float, overall_quality: str) -> str:
        """Generate a human-readable validation summary."""
        total_themes = len(theme_coverages)
        well_supported = sum(1 for tc in theme_coverages if tc.coverage_score >= 0.7)
        
        summary = f"Validation Results: {well_supported}/{total_themes} themes are well-supported "
        summary += f"(avg coverage: {avg_coverage:.1%}). "
        
        if overall_quality == "excellent":
            summary += "Themes show excellent distribution across multiple speakers and sources."
        elif overall_quality == "good":
            summary += "Themes have good coverage with adequate source diversity."
        elif overall_quality == "adequate":
            summary += "Themes have reasonable support but could benefit from broader coverage."
        else:
            summary += "Several themes need stronger evidence or broader source coverage."
        
        return summary