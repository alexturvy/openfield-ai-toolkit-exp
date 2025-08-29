"""LLM-powered insight synthesis for research clusters."""

import json
import time
import os
from typing import Dict, List, Optional, TYPE_CHECKING
import subprocess
import shutil
import platform
from rich.console import Console
from ..config import LLM_CONFIG, ANALYSIS_LENSES

console = Console()


def ensure_ollama_ready() -> None:
    """Legacy function for backward compatibility."""
    # Now handled by UnifiedLLMClient
    pass


if TYPE_CHECKING:
    from ..research.goal_manager import ResearchGoalManager


def synthesize_insights(cluster, lens: str, goal_manager: Optional['ResearchGoalManager'] = None, research_question: Optional[str] = None) -> Dict:
    """
    Synthesize insights for a cluster using LLM with lens-specific focus.
    
    Args:
        cluster: Cluster object with chunks
        lens: Analysis lens name
        goal_manager: Optional research goal manager for focused analysis
        
    Returns:
        Dictionary with synthesized insights including speaker attribution
    """
    # Import LLM client
    from ..llm.client import get_llm_client
    # Collect quotes with speaker information
    quotes_with_speakers = []
    speaker_distribution = {}
    
    for chunk in cluster.chunks:
        speaker = None
        if hasattr(chunk, '_adaptive_metadata') and chunk._adaptive_metadata:
            speaker = chunk._adaptive_metadata.get('speaker')
            is_interviewer = chunk._adaptive_metadata.get('is_interviewer', False)
            
            # Track speaker distribution
            if speaker:
                speaker_key = f"{speaker} ({'Interviewer' if is_interviewer else 'Participant'})"
                speaker_distribution[speaker_key] = speaker_distribution.get(speaker_key, 0) + 1
        
        if speaker:
            quotes_with_speakers.append(f"[{speaker}]: {chunk.text}")
        else:
            quotes_with_speakers.append(f"[Unknown]: {chunk.text}")
    
    # Get lens configuration
    if lens not in ANALYSIS_LENSES:
        raise ValueError(f"Unknown lens: {lens}")
    
    lens_config = ANALYSIS_LENSES[lens]
    focus = lens_config['focus']
    extra_field, extra_desc = lens_config['extra_field']
    
    # Create speaker context for the prompt
    speaker_context = ""
    if speaker_distribution:
        speaker_context = f"""
SPEAKER DISTRIBUTION IN THIS CLUSTER:
{chr(10).join(f'- {speaker}: {count} contributions' for speaker, count in speaker_distribution.items())}

"""
    
    # Build question-driven extractive prompt if a specific research question is provided
    if research_question:
        prompt = f"""You are a research analyst. Your task is to answer the following research question using ONLY the provided quotes.

RESEARCH QUESTION: {research_question}

QUOTES:
{chr(10).join(quotes_with_speakers)}

Extract every distinct finding from the quotes that addresses the research question. For each finding, provide the speaker and the verbatim supporting quote.

Return ONLY valid JSON with this structure:
{{
  "findings": [
    {{
      "finding": "A specific point, observation, or opinion from a participant.",
      "speaker": "The name of the speaker who made this point.",
      "supporting_quote": "The exact quote from the 'QUOTES' section that contains this finding."
    }}
  ]
}}

Rules:
- Do not summarize or generalize. Extract the specific points.
- If a single quote contains multiple distinct findings, create a separate object for each.
- Ensure the 'supporting_quote' is an exact match from the provided text.
"""
    # Otherwise, build research-aware prompt if goal_manager is provided
    elif goal_manager:
        # Get the most relevant research question for this cluster
        cluster_text = " ".join([chunk.text for chunk in cluster.chunks])
        relevant_questions = goal_manager.identify_relevant_questions(cluster_text)
        
        if relevant_questions:
            primary_question = goal_manager._questions[relevant_questions[0][0]]
            prompt = f"""You are a UX researcher. Your task is to extract the key findings from the following user quotes that directly answer the research question provided.

RESEARCH QUESTION: {primary_question}

{speaker_context}QUOTES:
{chr(10).join(quotes_with_speakers)}

Return ONLY valid JSON with this exact structure:
{{
  "theme_name": "A concise, actionable theme name that answers the research question",
  "findings": [
    {{
      "finding": "A specific, granular finding that directly answers the research question.",
      "speaker": "The speaker who expressed this finding.",
      "supporting_quote": "The exact, verbatim quote from the 'QUOTES' section that supports this finding."
    }}
  ]
}}

Rules:
- Each 'finding' must directly address the research question.
- The 'speaker' must be one of the speakers listed in the quotes.
- The 'supporting_quote' must be an exact quote from the provided text.
- If there are multiple distinct findings, create a separate object for each in the 'findings' array.
"""
        else:
            # This cluster doesn't map to research questions - skip it
            return None
    else:
        # Original prompt for backward compatibility
        prompt = f"""You are a UX researcher. {focus} from these user quotes with speaker attribution:

{speaker_context}QUOTES:
{chr(10).join(f'- {quote}' for quote in quotes_with_speakers)}

Return valid JSON with this exact structure:
{{
    "theme_name": "Clear, concise theme name",
    "summary": "Brief summary of the key insight",
    "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
    "{extra_field}": "{extra_desc}",
    "speaker_distribution": {{"speaker_name": contribution_count}},
    "primary_contributors": ["Most active speakers for this theme"],
    "cross_speaker_patterns": "Any patterns that emerge across different speakers"
}}

Pay attention to:
1. Which speakers contributed most to this theme
2. Whether insights come from participants vs interviewers  
3. Any patterns that emerge across multiple speakers
4. How different speakers express similar or different perspectives

Be specific and evidence-based. Focus on patterns and insights from the data."""

    # Get LLM client and generate response
    client = get_llm_client()
    success, synthesis = client.generate_json(
        prompt=prompt,
        system="You are a UX researcher analyzing interview data",
        max_tokens=4096  # Allow comprehensive responses
    )
    
    if not success:
        raise ValueError(f"Synthesis failed: {synthesis.get('error', 'Unknown error')}")
    
    # Validation: accept new extractive schema or legacy schema
    if 'findings' in synthesis and isinstance(synthesis['findings'], list):
        return synthesis
    legacy_required = ['theme_name', 'summary', 'key_insights']
    if all(key in synthesis for key in legacy_required):
        if 'speaker_distribution' not in synthesis:
            synthesis['speaker_distribution'] = speaker_distribution
        if 'primary_contributors' not in synthesis:
            contributors = list(speaker_distribution.keys()) if speaker_distribution else []
            synthesis['primary_contributors'] = [str(c) for c in contributors[:3]]
        if 'cross_speaker_patterns' not in synthesis:
            synthesis['cross_speaker_patterns'] = "Multiple speakers contributed to this theme" if len(speaker_distribution) > 1 else "Single speaker theme"
        return synthesis
    raise ValueError("Missing required keys for synthesis output")


# Legacy function name for compatibility
call_llm_for_synthesis = synthesize_insights