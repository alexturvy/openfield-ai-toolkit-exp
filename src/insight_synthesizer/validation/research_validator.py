"""Research coverage validation to ensure research questions are answered."""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..research.goal_manager import ResearchGoalManager

console = Console()


@dataclass
class QuestionCoverage:
    """Coverage analysis for a single research question."""
    question_idx: int
    question_text: str
    addressing_themes: List[int]  # Theme indices that address this question
    coverage_score: float  # 0-1 score indicating how well the question is covered
    key_insights: List[str]
    gaps: List[str]
    confidence_distribution: Dict[str, int]  # high/medium/low counts


@dataclass
class ResearchCoverageReport:
    """Complete coverage analysis report."""
    question_coverage: List[QuestionCoverage]
    overall_coverage: float
    well_addressed: List[str]
    partially_addressed: List[str]
    not_addressed: List[str]
    recommendations: List[str]
    coverage_matrix: Dict[int, List[int]]  # question_idx -> theme_indices


class ResearchCoverageValidator:
    """Validates that synthesis adequately addresses research questions."""
    
    def __init__(self, goal_manager: ResearchGoalManager):
        """
        Initialize with research goal manager.
        
        Args:
            goal_manager: Manager containing research questions and embeddings
        """
        self.goal_manager = goal_manager
        
    def analyze_coverage(self, synthesis_results: List[Dict]) -> ResearchCoverageReport:
        """
        Analyze how well synthesis addresses research questions.
        
        Args:
            synthesis_results: List of synthesized themes
            
        Returns:
            Comprehensive coverage report
        """
        coverage_by_question = []
        coverage_matrix = {}
        
        # Analyze coverage for each research question
        for q_idx, question in enumerate(self.goal_manager.goal.primary_questions):
            coverage = self._analyze_question_coverage(
                q_idx, question, synthesis_results
            )
            coverage_by_question.append(coverage)
            coverage_matrix[q_idx] = coverage.addressing_themes
            
        # Categorize coverage levels
        well_addressed = []
        partially_addressed = []
        not_addressed = []
        
        for coverage in coverage_by_question:
            if coverage.coverage_score >= 0.7:
                well_addressed.append(coverage.question_text)
            elif coverage.coverage_score >= 0.3:
                partially_addressed.append(coverage.question_text)
            else:
                not_addressed.append(coverage.question_text)
                
        # Generate recommendations
        recommendations = self._generate_recommendations(
            coverage_by_question, synthesis_results
        )
        
        # Calculate overall coverage
        overall_coverage = np.mean([c.coverage_score for c in coverage_by_question])
        
        return ResearchCoverageReport(
            question_coverage=coverage_by_question,
            overall_coverage=overall_coverage,
            well_addressed=well_addressed,
            partially_addressed=partially_addressed,
            not_addressed=not_addressed,
            recommendations=recommendations,
            coverage_matrix=coverage_matrix
        )
    
    def _analyze_question_coverage(self, q_idx: int, question: str, 
                                  synthesis_results: List[Dict]) -> QuestionCoverage:
        """
        Analyze coverage for a single research question.
        
        Args:
            q_idx: Question index
            question: Question text
            synthesis_results: All synthesis results
            
        Returns:
            Coverage analysis for this question
        """
        addressing_themes = []
        key_insights = []
        confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        # Check each theme for relevance to this question
        for t_idx, theme in enumerate(synthesis_results):
            # Check if theme explicitly addresses this question
            addressed_questions = theme.get('addressed_questions', [])
            if q_idx in addressed_questions:
                addressing_themes.append(t_idx)
                
                # Extract key insights
                if 'research_implications' in theme:
                    key_insights.append(theme['research_implications'])
                    
                # Track confidence
                confidence = theme.get('confidence', 'medium').lower()
                if confidence in confidence_distribution:
                    confidence_distribution[confidence] += 1
                    
            else:
                # Check semantic relevance as fallback
                theme_text = self._extract_theme_text(theme)
                relevance = self.goal_manager.calculate_relevance_score(theme_text)
                
                if relevance > 0.5:
                    addressing_themes.append(t_idx)
                    confidence_distribution['low'] += 1  # Lower confidence for indirect match
        
        # Calculate coverage score
        coverage_score = self._calculate_coverage_score(
            addressing_themes, synthesis_results, confidence_distribution
        )
        
        # Identify gaps
        gaps = self._identify_question_gaps(
            question, addressing_themes, synthesis_results
        )
        
        return QuestionCoverage(
            question_idx=q_idx,
            question_text=question,
            addressing_themes=addressing_themes,
            coverage_score=coverage_score,
            key_insights=key_insights[:5],  # Top 5 insights
            gaps=gaps,
            confidence_distribution=confidence_distribution
        )
    
    def _extract_theme_text(self, theme: Dict) -> str:
        """Extract searchable text from a theme."""
        parts = []
        
        for field in ['theme_name', 'summary', 'key_insights', 'research_implications']:
            if field in theme:
                if isinstance(theme[field], list):
                    parts.extend(theme[field])
                else:
                    parts.append(str(theme[field]))
                    
        return " ".join(parts)
    
    def _calculate_coverage_score(self, addressing_themes: List[int],
                                 synthesis_results: List[Dict],
                                 confidence_dist: Dict[str, int]) -> float:
        """
        Calculate a coverage score based on multiple factors.
        
        Args:
            addressing_themes: Indices of themes addressing this question
            synthesis_results: All synthesis results
            confidence_dist: Distribution of confidence levels
            
        Returns:
            Coverage score between 0 and 1
        """
        if not addressing_themes:
            return 0.0
            
        # Factor 1: Number of addressing themes (up to 0.4)
        theme_count_score = min(1.0, len(addressing_themes) / 3) * 0.4
        
        # Factor 2: Confidence distribution (up to 0.3)
        total_themes = sum(confidence_dist.values())
        if total_themes > 0:
            confidence_score = (
                confidence_dist['high'] * 1.0 +
                confidence_dist['medium'] * 0.5 +
                confidence_dist['low'] * 0.2
            ) / total_themes * 0.3
        else:
            confidence_score = 0.0
            
        # Factor 3: Quality of insights (up to 0.3)
        quality_score = 0.0
        for t_idx in addressing_themes:
            theme = synthesis_results[t_idx]
            
            # Check for actionable findings
            if theme.get('actionable_findings'):
                quality_score += 0.1
                
            # Check for specific implications
            if theme.get('research_implications') and len(theme['research_implications']) > 20:
                quality_score += 0.1
                
            # Check for evidence strength
            if theme.get('supporting_quotes') and len(theme.get('supporting_quotes', [])) >= 3:
                quality_score += 0.1
                
        quality_score = min(0.3, quality_score)
        
        return theme_count_score + confidence_score + quality_score
    
    def _identify_question_gaps(self, question: str, addressing_themes: List[int],
                               synthesis_results: List[Dict]) -> List[str]:
        """
        Identify what's missing in coverage of a question.
        
        Args:
            question: Research question text
            addressing_themes: Themes that address this question
            synthesis_results: All synthesis results
            
        Returns:
            List of identified gaps
        """
        gaps = []
        question_lower = question.lower()
        
        # No themes address the question
        if not addressing_themes:
            gaps.append("No themes directly address this research question")
            return gaps
            
        # Analyze the quality of coverage
        all_have_low_confidence = all(
            synthesis_results[t_idx].get('confidence', 'low') == 'low'
            for t_idx in addressing_themes
        )
        
        if all_have_low_confidence:
            gaps.append("All related themes have low confidence - need stronger evidence")
            
        # Check for missing actionable insights
        has_actionable = any(
            bool(synthesis_results[t_idx].get('actionable_findings'))
            for t_idx in addressing_themes
        )
        
        if not has_actionable:
            gaps.append("No actionable findings or recommendations provided")
            
        # Question-type specific gap analysis
        if 'why' in question_lower:
            has_reasons = any(
                any(word in str(synthesis_results[t_idx]).lower() 
                    for word in ['reason', 'because', 'due to', 'cause'])
                for t_idx in addressing_themes
            )
            if not has_reasons:
                gaps.append("Question asks 'why' but themes don't explain root causes")
                
        elif 'how' in question_lower:
            has_process = any(
                any(word in str(synthesis_results[t_idx]).lower() 
                    for word in ['process', 'method', 'approach', 'way', 'step'])
                for t_idx in addressing_themes
            )
            if not has_process:
                gaps.append("Question asks 'how' but themes don't describe processes or methods")
                
        elif 'what' in question_lower and 'barrier' in question_lower:
            has_barriers = any(
                any(word in str(synthesis_results[t_idx]).lower() 
                    for word in ['barrier', 'challenge', 'difficult', 'prevent', 'obstacle'])
                for t_idx in addressing_themes
            )
            if not has_barriers:
                gaps.append("Question asks about barriers but themes don't identify specific obstacles")
                
        return gaps
    
    def _generate_recommendations(self, coverage_by_question: List[QuestionCoverage],
                                 synthesis_results: List[Dict]) -> List[str]:
        """
        Generate actionable recommendations for improving coverage.
        
        Args:
            coverage_by_question: Coverage analysis for each question
            synthesis_results: All synthesis results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for questions with poor coverage
        poor_coverage = [c for c in coverage_by_question if c.coverage_score < 0.3]
        
        if poor_coverage:
            questions_text = [c.question_text for c in poor_coverage[:2]]
            recommendations.append(
                f"Critical gap: {len(poor_coverage)} research question(s) have poor coverage. "
                f"Priority: {'; '.join(questions_text)}"
            )
            
            # Suggest data collection
            recommendations.append(
                "Consider additional data collection focused on under-addressed questions, "
                "or refine interview guides to better target these areas."
            )
            
        # Check for imbalanced coverage
        coverage_scores = [c.coverage_score for c in coverage_by_question]
        if np.std(coverage_scores) > 0.3:
            recommendations.append(
                "Coverage is imbalanced across research questions. Some questions "
                "receive much more attention than others. Consider rebalancing the analysis."
            )
            
        # Check for lack of high-confidence themes
        total_high_confidence = sum(
            c.confidence_distribution['high'] for c in coverage_by_question
        )
        
        if total_high_confidence < len(coverage_by_question):
            recommendations.append(
                "Many questions lack high-confidence themes. Consider gathering "
                "more evidence or conducting follow-up interviews to strengthen findings."
            )
            
        # Check for missing actionable insights
        themes_with_actions = sum(
            1 for theme in synthesis_results 
            if theme.get('actionable_findings')
        )
        
        if themes_with_actions < len(synthesis_results) / 3:
            recommendations.append(
                "Few themes provide actionable findings. Consider asking participants "
                "for specific suggestions or solutions in future research."
            )
            
        # Suggest follow-up questions
        for coverage in coverage_by_question:
            if coverage.gaps and coverage.coverage_score < 0.5:
                recommendations.append(
                    f"Follow-up needed for '{coverage.question_text[:50]}...': "
                    f"{coverage.gaps[0]}"
                )
                
        return recommendations[:7]  # Limit to top 7 recommendations
    
    def display_coverage_report(self, report: ResearchCoverageReport) -> None:
        """
        Display coverage report in a formatted way.
        
        Args:
            report: Coverage report to display
        """
        # Overall summary panel
        summary_content = f"""[bold]Research Coverage Analysis[/]

Overall Coverage: [{'green' if report.overall_coverage >= 0.7 else 'yellow' if report.overall_coverage >= 0.4 else 'red'}]{report.overall_coverage:.0%}[/]

[green]✓ Well Addressed ({len(report.well_addressed)})[/]
[yellow]◐ Partially Addressed ({len(report.partially_addressed)})[/]
[red]✗ Not Addressed ({len(report.not_addressed)})[/]"""
        
        console.print(Panel(summary_content, title="Coverage Summary"))
        
        # Detailed question coverage
        if report.question_coverage:
            table = Table(title="Research Question Coverage", show_header=True)
            table.add_column("Question", style="cyan", width=40)
            table.add_column("Coverage", justify="center", width=10)
            table.add_column("Themes", justify="center", width=8)
            table.add_column("Confidence", width=20)
            table.add_column("Gaps", style="yellow", width=30)
            
            for coverage in report.question_coverage:
                # Format coverage score with color
                if coverage.coverage_score >= 0.7:
                    coverage_str = f"[green]{coverage.coverage_score:.0%}[/]"
                elif coverage.coverage_score >= 0.3:
                    coverage_str = f"[yellow]{coverage.coverage_score:.0%}[/]"
                else:
                    coverage_str = f"[red]{coverage.coverage_score:.0%}[/]"
                
                # Format confidence distribution
                conf_dist = coverage.confidence_distribution
                conf_str = f"H:{conf_dist['high']} M:{conf_dist['medium']} L:{conf_dist['low']}"
                
                # Format gaps
                gaps_str = coverage.gaps[0] if coverage.gaps else "None identified"
                
                table.add_row(
                    coverage.question_text[:40] + "...",
                    coverage_str,
                    str(len(coverage.addressing_themes)),
                    conf_str,
                    gaps_str[:30] + "..."
                )
            
            console.print(table)
        
        # Recommendations
        if report.recommendations:
            console.print("\n[bold]Recommendations:[/]")
            for i, rec in enumerate(report.recommendations, 1):
                console.print(f"{i}. {rec}")
    
    def generate_coverage_section(self, report: ResearchCoverageReport) -> str:
        """
        Generate markdown section for coverage report.
        
        Args:
            report: Coverage report
            
        Returns:
            Markdown formatted coverage section
        """
        section = "\n## Research Coverage Analysis\n\n"
        
        # Summary
        section += f"**Overall Coverage**: {report.overall_coverage:.0%}\n\n"
        
        # Coverage breakdown
        section += "### Coverage by Question\n\n"
        section += "| Research Question | Coverage | Themes | Confidence | Primary Gap |\n"
        section += "|------------------|----------|--------|------------|-------------|\n"
        
        for coverage in report.question_coverage:
            conf_dist = coverage.confidence_distribution
            conf_str = f"H:{conf_dist['high']} M:{conf_dist['medium']} L:{conf_dist['low']}"
            gap_str = coverage.gaps[0] if coverage.gaps else "Well covered"
            
            section += f"| {coverage.question_text[:50]}... | "
            section += f"{coverage.coverage_score:.0%} | "
            section += f"{len(coverage.addressing_themes)} | "
            section += f"{conf_str} | "
            section += f"{gap_str[:40]}... |\n"
        
        # Key insights by question
        section += "\n### Key Insights by Research Question\n\n"
        for coverage in report.question_coverage:
            if coverage.key_insights:
                section += f"**Q{coverage.question_idx + 1}**: {coverage.question_text}\n"
                for insight in coverage.key_insights[:3]:
                    section += f"- {insight}\n"
                section += "\n"
        
        # Recommendations
        if report.recommendations:
            section += "### Recommendations\n\n"
            for rec in report.recommendations[:5]:
                section += f"- {rec}\n"
            
        return section