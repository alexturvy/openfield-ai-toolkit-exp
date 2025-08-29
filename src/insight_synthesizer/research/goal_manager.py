"""Research goal management for guiding analysis."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
try:
    from rich.console import Console
except Exception:
    class Console:
        def print(self, *args, **kwargs):
            pass
from .plan_parser import ParsedResearchPlan

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ResearchGoal:
    """Structured research goal representation."""
    background: Optional[str] = None
    assumptions: Optional[List[str]] = None
    research_goal: Optional[str] = None
    research_questions: List[str] = None  # Primary field for questions
    
    # Legacy fields for backward compatibility
    primary_questions: Optional[List[str]] = None
    methodology: Optional[str] = None
    participant_criteria: Optional[str] = None  
    success_metrics: Optional[List[str]] = None
    key_hypotheses: Optional[List[str]] = None
    
    @classmethod
    def from_parsed_plan(cls, plan: ParsedResearchPlan) -> 'ResearchGoal':
        """Create ResearchGoal from parsed plan."""
        return cls(
            background=plan.background,
            assumptions=plan.assumptions,
            research_goal=plan.research_goal,
            research_questions=plan.research_questions,
            methodology=plan.methodology,
            key_hypotheses=getattr(plan, 'hypotheses', None),
            success_metrics=plan.success_metrics,
            participant_criteria=plan.participant_criteria
        )
    
    def __post_init__(self):
        """Enhanced synchronization and field harmonization."""
        # Handle both field names for backward compatibility
        if self.research_questions and not self.primary_questions:
            self.primary_questions = self.research_questions
        elif self.primary_questions and not self.research_questions:
            self.research_questions = self.primary_questions
        elif not self.research_questions and not self.primary_questions:
            self.research_questions = []
            self.primary_questions = []
        
        # Ensure both fields stay synchronized
        if self.research_questions != self.primary_questions:
            # If somehow they diverge, prefer research_questions
            self.primary_questions = self.research_questions
        
        # Ensure non-None lists
        self.assumptions = self.assumptions or []
        self.key_hypotheses = self.key_hypotheses or []
        self.success_metrics = self.success_metrics or []
    
    def to_context_string(self) -> str:
        """Convert to formatted context for LLM prompts."""
        context = []
        
        if self.background:
            context.append(f"BACKGROUND:\n{self.background}")
            context.append("")
            
        if self.assumptions:
            context.append("ASSUMPTIONS:")
            for assumption in self.assumptions:
                context.append(f"- {assumption}")
            context.append("")
            
        if self.research_goal:
            context.append(f"RESEARCH GOAL:\n{self.research_goal}")
            context.append("")
            
        questions = self.research_questions or self.primary_questions or []
        if questions:
            context.append("RESEARCH QUESTIONS:")
            for i, q in enumerate(questions, 1):
                context.append(f"{i}. {q}")
            context.append("")
            
        # Include other fields if present
        if self.key_hypotheses:
            context.append("KEY HYPOTHESES:")
            for h in self.key_hypotheses:
                context.append(f"- {h}")
            context.append("")
                
        if self.methodology:
            context.append(f"METHODOLOGY: {self.methodology}")
            
        if self.participant_criteria:
            context.append(f"PARTICIPANTS: {self.participant_criteria}")
            
        return "\n".join(context).strip()


class ResearchGoalManager:
    """Manages research goals throughout the analysis pipeline."""
    
    MAX_CACHE_SIZE = 1000  # Prevent unbounded cache growth
    
    def __init__(self, research_goal: ResearchGoal):
        """Initialize with research goals and create embeddings."""
        self.goal = research_goal
        
        # Use research_questions for all operations (set this BEFORE using it)
        self._questions = self.goal.research_questions or self.goal.primary_questions or []
        
        # Initialize embedder using cache
        from ..analysis.model_cache import get_embedding_model
        console.print("[dim]Loading embedding model for research goal analysis...[/]")
        self.embedder = get_embedding_model('all-MiniLM-L6-v2')
        
        # Pre-compute embeddings for research questions
        self.question_embeddings = self._generate_question_embeddings()
        
        # Create relevance scoring cache
        self.relevance_cache = {}
        
        console.print(f"[green]Research goal manager initialized with {len(self._questions)} questions[/]")
        
    def _generate_question_embeddings(self) -> "np.ndarray":
        """Generate embeddings for all research questions."""
        all_questions = self._questions.copy()
        
        # Include hypotheses if provided
        if self.goal.key_hypotheses:
            all_questions.extend(self.goal.key_hypotheses)
            
        return self.embedder.encode(all_questions)
    
    def calculate_relevance_score(self, text: str) -> float:
        """
        Calculate how relevant a text chunk is to research goals.
        
        Args:
            text: Text chunk to evaluate
            
        Returns:
            Relevance score between 0 and 1
        """
        # Check cache size and prune if needed
        if len(self.relevance_cache) > self.MAX_CACHE_SIZE:
            # Keep only the most recent half
            items = list(self.relevance_cache.items())
            self.relevance_cache = dict(items[-self.MAX_CACHE_SIZE//2:])
            logger.info(f"Pruned relevance cache to {len(self.relevance_cache)} entries")
        
        if text in self.relevance_cache:
            return self.relevance_cache[text]
            
        # Generate embedding for the text
        text_embedding = self.embedder.encode([text])[0]
        
        # Calculate cosine similarity with all research questions
        similarities = []
        for q_embedding in self.question_embeddings:
            # Cosine similarity
            similarity = np.dot(text_embedding, q_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(q_embedding)
            )
            similarities.append(similarity)
            
        # Handle case with no questions
        if not similarities:
            return 0.5  # Neutral relevance
            
        # Use max similarity (most relevant question) with decay
        max_similarity = max(similarities)
        avg_similarity = np.mean(similarities)
        
        # Weighted combination favoring strong matches
        # This ensures highly relevant content gets high scores
        # while maintaining some signal for moderately relevant content
        score = 0.7 * max_similarity + 0.3 * avg_similarity
        
        # Cache the result
        self.relevance_cache[text] = score
        
        return score
    
    def identify_relevant_questions(self, text: str, threshold: float = 0.5) -> List[Tuple[int, float]]:
        """
        Identify which research questions are most relevant to a text chunk.
        
        Args:
            text: Text chunk to analyze
            threshold: Minimum similarity threshold
            
        Returns:
            List of (question_index, similarity_score) tuples, sorted by relevance
        """
        text_embedding = self.embedder.encode([text])[0]
        
        relevant_questions = []
        
        # Only check primary questions (not hypotheses)
        num_primary_questions = len(self._questions)
        
        for i in range(num_primary_questions):
            question = self._questions[i]
            q_embedding = self.question_embeddings[i]
            
            # Calculate cosine similarity
            similarity = np.dot(text_embedding, q_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(q_embedding)
            )
            
            if similarity >= threshold:
                relevant_questions.append((i, similarity))
                
        # Sort by similarity score (descending)
        return sorted(relevant_questions, key=lambda x: x[1], reverse=True)
    
    def generate_focused_synthesis_prompt(self, cluster_content: List[str], lens: str) -> str:
        """
        Generate a synthesis prompt focused on research questions.
        
        Args:
            cluster_content: List of text chunks in the cluster
            lens: Analysis lens being used
            
        Returns:
            Research-focused prompt introduction
        """
        # Identify which questions this cluster might address
        all_text = " ".join(cluster_content)
        relevant_questions = self.identify_relevant_questions(all_text, threshold=0.4)
        
        prompt_parts = [
            "You are analyzing user research data for a specific study.",
            "",
            self.goal.to_context_string(),
            ""
        ]
        
        if relevant_questions:
            prompt_parts.append("This cluster appears most relevant to these research questions:")
            for q_idx, score in relevant_questions[:3]:  # Top 3
                prompt_parts.append(
                    f"- Q{q_idx+1}: {self._questions[q_idx]} "
                    f"(relevance: {score:.2f})"
                )
            prompt_parts.append("")
            
            prompt_parts.append(
                "IMPORTANT: Focus your analysis on insights that directly address "
                "these research questions. Be specific about which question each "
                "insight addresses and how."
            )
        else:
            prompt_parts.append(
                "NOTE: This cluster has low direct relevance to the primary research "
                "questions. Look for any indirect connections or contextual insights "
                "that might still be valuable."
            )
            
        prompt_parts.append("")
        prompt_parts.append(
            f"Analyze these quotes through the lens of '{lens}', keeping the "
            f"research questions in mind:"
        )
        
        return "\n".join(prompt_parts)
    
    def evaluate_synthesis_quality(self, synthesis_result: Dict) -> Dict[str, float]:
        """
        Evaluate how well a synthesis addresses research goals.
        
        Args:
            synthesis_result: Synthesis output dictionary
            
        Returns:
            Dictionary with quality metrics
        """
        metrics = {}
        
        # Check if synthesis addresses any research questions
        addressed_questions = synthesis_result.get('addressed_questions', [])
        # Handle case with no questions
        if len(self._questions) > 0:
            metrics['question_coverage'] = len(addressed_questions) / len(self._questions)
        else:
            metrics['question_coverage'] = 1.0  # If no questions, consider it covered
        
        # Check research implications
        has_implications = bool(synthesis_result.get('research_implications'))
        metrics['has_implications'] = 1.0 if has_implications else 0.0
        
        # Check actionability
        actionable_findings = synthesis_result.get('actionable_findings', [])
        metrics['actionability'] = min(1.0, len(actionable_findings) / 2)  # Expect at least 2
        
        # Check confidence
        confidence_map = {'high': 1.0, 'medium': 0.5, 'low': 0.2}
        confidence = synthesis_result.get('confidence', 'low')
        metrics['confidence'] = confidence_map.get(confidence, 0.2)
        
        # Overall quality score
        metrics['overall_quality'] = (
            0.4 * metrics['question_coverage'] +
            0.3 * metrics['has_implications'] +
            0.2 * metrics['actionability'] +
            0.1 * metrics['confidence']
        )
        
        return metrics