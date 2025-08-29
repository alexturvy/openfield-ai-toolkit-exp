"""
Research Plan Parser - Intelligent ingestion of research documents
Location: src/insight_synthesizer/research/plan_parser.py
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
from rich.console import Console

console = Console()


@dataclass
class ParsedResearchPlan:
    """Structured research plan extracted from document."""
    background: Optional[str] = None
    research_goal: Optional[str] = None
    research_questions: List[str] = None
    assumptions: List[str] = None
    hypotheses: List[str] = None
    methodology: Optional[str] = None
    success_metrics: List[str] = None
    participant_criteria: Optional[str] = None
    timeline: Optional[str] = None
    raw_text: str = ""
    confidence_scores: Dict[str, float] = None
    
    def __post_init__(self):
        if self.research_questions is None:
            self.research_questions = []
        if self.assumptions is None:
            self.assumptions = []
        if self.hypotheses is None:
            self.hypotheses = []
        if self.success_metrics is None:
            self.success_metrics = []
        if self.confidence_scores is None:
            self.confidence_scores = {}


class ResearchPlanParser:
    """Intelligent parser for research plan documents."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """Initialize parser with optional LLM configuration."""
        self.llm_config = llm_config or {
            'base_url': 'http://localhost:11434',
            'model_name': 'mistral',
            'timeout': 60
        }
        
        # Pattern library for common research document structures
        self.patterns = {
            'questions': [
                r'(?:research\s+)?questions?:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
                r'RQ\d+:?\s*(.+)',
                r'(?:key\s+)?questions?\s+to\s+answer:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
                r'what\s+we\s+want\s+to\s+learn:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
            ],
            'background': [
                r'background:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
                r'context:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
                r'introduction:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
            ],
            'goals': [
                r'(?:research\s+)?goals?:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
                r'objectives?:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
                r'purpose:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
            ],
            'assumptions': [
                r'assumptions?:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
                r'we\s+(?:assume|believe)\s+that:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
            ],
            'hypotheses': [
                r'hypothes[ei]s:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
                r'H\d+:?\s*(.+)',
                r'we\s+(?:expect|predict)\s+that:?\s*\n((?:[-•*\d]+\.?\s*.+\n?)+)',
            ],
            'methodology': [
                r'method(?:ology)?:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
                r'approach:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
                r'how\s+we\s+will\s+conduct:?\s*\n((?:.+\n?)+?)(?=\n[A-Z]|\n\n|\Z)',
            ]
        }
    
    def parse_document(self, file_path: Path) -> ParsedResearchPlan:
        """
        Parse a research plan document using hybrid approach.
        
        Args:
            file_path: Path to research plan document
            
        Returns:
            Parsed research plan with confidence scores
        """
        # Read document
        from ..document_processing.file_handlers import extract_text_from_file
        try:
            content = extract_text_from_file(file_path)
        except Exception as e:
            raise ValueError(f"Could not read research plan: {e}")
        
        console.print(f"[cyan]Parsing research plan: {file_path.name}[/]")
        
        # Step 1: Pattern-based extraction for structured content
        pattern_results = self._extract_with_patterns(content)
        
        # Step 2: LLM-based extraction for nuanced understanding
        llm_results = self._extract_with_llm(content)
        
        # Step 3: Merge results with confidence scoring
        merged_plan = self._merge_results(pattern_results, llm_results, content)
        
        # Step 4: Validate and clean
        final_plan = self._validate_and_clean(merged_plan)
        
        return final_plan
    
    def _extract_with_patterns(self, content: str) -> ParsedResearchPlan:
        """Extract information using regex patterns."""
        plan = ParsedResearchPlan()
        
        # Normalize content for better pattern matching
        content = re.sub(r'\r\n', '\n', content)  # Normalize line endings
        
        # Extract research questions
        questions = []
        for pattern in self.patterns['questions']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                text = match.group(1) if match.groups() else match.group(0)
                # Split into individual questions
                lines = text.strip().split('\n')
                for line in lines:
                    clean = re.sub(r'^[-•*\d]+\.?\s*', '', line.strip())
                    if clean and len(clean) > 10:  # Min length for valid question
                        questions.append(clean)
        
        plan.research_questions = self._deduplicate_list(questions)
        
        # Extract background
        for pattern in self.patterns['background']:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                plan.background = match.group(1).strip()
                break
        
        # Extract goals
        for pattern in self.patterns['goals']:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                plan.research_goal = match.group(1).strip()
                break
        
        # Extract assumptions
        assumptions = []
        for pattern in self.patterns['assumptions']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                text = match.group(1)
                lines = text.strip().split('\n')
                for line in lines:
                    clean = re.sub(r'^[-•*\d]+\.?\s*', '', line.strip())
                    if clean and len(clean) > 10:
                        assumptions.append(clean)
        
        plan.assumptions = self._deduplicate_list(assumptions)
        
        # Extract hypotheses
        hypotheses = []
        for pattern in self.patterns['hypotheses']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                text = match.group(1) if match.groups() else match.group(0)
                lines = text.strip().split('\n')
                for line in lines:
                    clean = re.sub(r'^[-•*\d]+\.?\s*', '', line.strip())
                    if clean and len(clean) > 10:
                        hypotheses.append(clean)
        
        plan.hypotheses = self._deduplicate_list(hypotheses)
        
        # Extract methodology
        for pattern in self.patterns['methodology']:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                plan.methodology = match.group(1).strip()
                break
        
        return plan
    
    def _extract_with_llm(self, content: str) -> ParsedResearchPlan:
        """Use LLM for intelligent extraction."""
        from ..llm.client import get_llm_client
        
        # Truncate if too long
        content_sample = content[:6000] if len(content) > 6000 else content
        
        prompt = f"""You are analyzing a research plan document. Extract the key components and return them as structured JSON.

DOCUMENT:
{content_sample}

Extract and organize the following elements if present:
1. Background/Context - The situation or problem being researched
2. Research Goal/Objective - The main purpose of the research
3. Research Questions - Specific questions to be answered (list them all)
4. Assumptions - Things assumed to be true
5. Hypotheses - Predictions or expected outcomes
6. Methodology - How the research will be conducted
7. Success Metrics - How success will be measured
8. Participant Criteria - Who will be researched

Return ONLY valid JSON with this structure:
{{
    "background": "extracted background or null",
    "research_goal": "extracted main goal or null",
    "research_questions": ["Q1", "Q2", ...] or [],
    "assumptions": ["A1", "A2", ...] or [],
    "hypotheses": ["H1", "H2", ...] or [],
    "methodology": "extracted methodology or null",
    "success_metrics": ["M1", "M2", ...] or [],
    "participant_criteria": "extracted criteria or null"
}}

Be thorough - extract ALL research questions you find, even if they're phrased differently."""
        
        client = get_llm_client()
        success, result = client.generate_json(
            prompt=prompt,
            system="You are analyzing research plan documents",
            max_tokens=2000
        )
        
        if not success:
            console.print(f"[yellow]LLM extraction failed: {result.get('error')}, using pattern-based only[/]")
            return ParsedResearchPlan()
        
        # Convert to ParsedResearchPlan
        return ParsedResearchPlan(
            background=result.get('background'),
            research_goal=result.get('research_goal'),
            research_questions=result.get('research_questions', []),
            assumptions=result.get('assumptions', []),
            hypotheses=result.get('hypotheses', []),
            methodology=result.get('methodology'),
            success_metrics=result.get('success_metrics', []),
            participant_criteria=result.get('participant_criteria')
        )
    
    def _merge_results(self, pattern_plan: ParsedResearchPlan, 
                      llm_plan: ParsedResearchPlan,
                      raw_content: str) -> ParsedResearchPlan:
        """Merge pattern and LLM results with confidence scoring."""
        merged = ParsedResearchPlan(raw_text=raw_content)
        confidence = {}
        
        # Research questions - combine both sources
        all_questions = []
        if pattern_plan.research_questions:
            all_questions.extend(pattern_plan.research_questions)
            confidence['questions_pattern'] = 0.9
        if llm_plan.research_questions:
            all_questions.extend(llm_plan.research_questions)
            confidence['questions_llm'] = 0.8
        
        merged.research_questions = self._deduplicate_list(all_questions)
        confidence['research_questions'] = max(
            confidence.get('questions_pattern', 0),
            confidence.get('questions_llm', 0)
        )
        
        # Background - prefer pattern if found, else LLM
        if pattern_plan.background:
            merged.background = pattern_plan.background
            confidence['background'] = 0.9
        elif llm_plan.background:
            merged.background = llm_plan.background
            confidence['background'] = 0.7
        
        # Research goal
        if pattern_plan.research_goal:
            merged.research_goal = pattern_plan.research_goal
            confidence['research_goal'] = 0.9
        elif llm_plan.research_goal:
            merged.research_goal = llm_plan.research_goal
            confidence['research_goal'] = 0.7
        
        # Assumptions - combine
        all_assumptions = []
        if pattern_plan.assumptions:
            all_assumptions.extend(pattern_plan.assumptions)
        if llm_plan.assumptions:
            all_assumptions.extend(llm_plan.assumptions)
        merged.assumptions = self._deduplicate_list(all_assumptions)
        
        # Hypotheses - combine
        all_hypotheses = []
        if pattern_plan.hypotheses:
            all_hypotheses.extend(pattern_plan.hypotheses)
        if llm_plan.hypotheses:
            all_hypotheses.extend(llm_plan.hypotheses)
        merged.hypotheses = self._deduplicate_list(all_hypotheses)
        
        # Methodology
        merged.methodology = pattern_plan.methodology or llm_plan.methodology
        
        # LLM-only fields
        merged.success_metrics = llm_plan.success_metrics
        merged.participant_criteria = llm_plan.participant_criteria
        
        merged.confidence_scores = confidence
        
        return merged
    
    def _deduplicate_list(self, items: List[str]) -> List[str]:
        """Remove duplicates while preserving order."""
        seen = set()
        result = []
        for item in items:
            # Normalize for comparison
            normalized = re.sub(r'\s+', ' ', item.lower().strip())
            if normalized not in seen and len(item.strip()) > 10:
                seen.add(normalized)
                result.append(item.strip())
        return result
    
    def _validate_and_clean(self, plan: ParsedResearchPlan) -> ParsedResearchPlan:
        """Validate and clean the extracted plan."""
        
        # Ensure we have at least some research questions
        if not plan.research_questions:
            console.print("[yellow]Warning: No research questions found[/]")
            
            # Try to extract from goal if available
            if plan.research_goal:
                # Convert goal to question format
                goal_as_question = self._goal_to_question(plan.research_goal)
                if goal_as_question:
                    plan.research_questions = [goal_as_question]
        
        # Clean up whitespace
        if plan.background:
            plan.background = ' '.join(plan.background.split())
        if plan.research_goal:
            plan.research_goal = ' '.join(plan.research_goal.split())
        if plan.methodology:
            plan.methodology = ' '.join(plan.methodology.split())
        
        # Ensure lists are not None
        plan.research_questions = plan.research_questions or []
        plan.assumptions = plan.assumptions or []
        plan.hypotheses = plan.hypotheses or []
        plan.success_metrics = plan.success_metrics or []
        
        return plan
    
    def _goal_to_question(self, goal: str) -> Optional[str]:
        """Convert a goal statement to a question format."""
        goal = goal.strip()
        
        # If already a question
        if '?' in goal:
            return goal
        
        # Convert statements to questions
        if goal.lower().startswith('to understand'):
            return goal.replace('To understand', 'What').replace('to understand', 'what') + '?'
        elif goal.lower().startswith('to identify'):
            return goal.replace('To identify', 'What are').replace('to identify', 'what are') + '?'
        elif goal.lower().startswith('to determine'):
            return goal.replace('To determine', 'How').replace('to determine', 'how') + '?'
        else:
            return f"How can we {goal.lower()}?"
    
    def display_parsed_plan(self, plan: ParsedResearchPlan) -> None:
        """Display the parsed plan for user confirmation."""
        from rich.panel import Panel
        from rich.table import Table
        
        # Create summary panel
        summary_lines = []
        
        if plan.background:
            summary_lines.append(f"[bold]Background:[/] {plan.background[:100]}...")
        
        if plan.research_goal:
            summary_lines.append(f"[bold]Goal:[/] {plan.research_goal[:100]}...")
        
        if plan.research_questions:
            summary_lines.append(f"[bold]Questions:[/] {len(plan.research_questions)} found")
            for i, q in enumerate(plan.research_questions[:3], 1):
                summary_lines.append(f"  {i}. {q[:60]}...")
            if len(plan.research_questions) > 3:
                summary_lines.append(f"  ... and {len(plan.research_questions) - 3} more")
        
        if plan.assumptions:
            summary_lines.append(f"[bold]Assumptions:[/] {len(plan.assumptions)} found")
        
        if plan.confidence_scores:
            avg_confidence = sum(plan.confidence_scores.values()) / len(plan.confidence_scores)
            color = "green" if avg_confidence > 0.8 else "yellow" if avg_confidence > 0.6 else "red"
            summary_lines.append(f"[bold]Confidence:[/] [{color}]{avg_confidence:.0%}[/]")
        
        console.print(Panel('\n'.join(summary_lines), title="Parsed Research Plan"))


def parse_research_plan_from_file(file_path: Path) -> ParsedResearchPlan:
    """Convenience function to parse a research plan file."""
    parser = ResearchPlanParser()
    return parser.parse_document(file_path)