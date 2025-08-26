"""Centralized prompt registry for all LLM interactions."""

from typing import Dict


class PromptRegistry:
    """Single source of truth for all LLM prompts."""

    CLASSIFY_DOCUMENT = (
        """
Analyze this document and identify its type and characteristics.

Document sample:
{document_sample}

Return JSON with:
{
  "type": "interview_transcript|meeting_notes|survey_responses|field_notes|user_feedback|unknown",
  "confidence": 0.0-1.0,
  "chunking_strategy": "speaker_turns|paragraphs|semantic|mixed",
  "key_characteristics": ["features", "that", "justify", "the", "classification"]
}
        """
    )

    EXTRACT_RESEARCH_PLAN = (
        """
Extract research questions and context from this document.

Content:
{content}

Return JSON with:
{
  "questions": ["research question 1", "research question 2"],
  "background": "context and background information",
  "assumptions": ["assumption 1", "assumption 2"],
  "methodology": "research methodology if mentioned"
}
        """
    )

    SYNTHESIZE_THEME = (
        """
Analyze these text chunks through the lens of {lens}.

Research Questions:
{questions}

Text Chunks:
{chunks}

Return JSON with:
{
  "theme_name": "concise theme name",
  "summary": "2-3 sentence summary",
  "key_insights": ["insight 1", "insight 2"],
  "confidence": 0.0-1.0,
  "question_indices": [0, 1],
  "secondary_lenses": ["lens1", "lens2"]
}
        """
    )

    EXTRACT_QUOTES = (
        """
Find the most compelling quotes supporting this theme: {theme_name}

Theme Summary: {theme_summary}

From content: {content}

Return JSON with:
{
  "quotes": [
    {"text": "exact quote", "speaker": "who said it", "relevance_score": 0.0-1.0}
  ],
  "confidence": 0.0-1.0
}
        """
    )

    LENS_GUIDANCE: Dict[str, str] = {
        "pain_points": "Focus on problems, frustrations, and obstacles users face.",
        "user_needs": "Identify underlying needs, desires, and requirements.",
        "behavioral_patterns": "Look for recurring behaviors, habits, and actions.",
        "emotional_drivers": "Identify emotional states, motivations, and feelings.",
        "decision_factors": "Focus on what influences choices and decisions.",
        "barriers": "Identify obstacles, challenges, and blocking factors.",
        "motivations": "Look for what drives and inspires people.",
        "frustrations": "Identify sources of annoyance and dissatisfaction.",
        "satisfaction_drivers": "Focus on what creates positive experiences.",
        "workarounds": "Look for creative solutions and adaptations.",
    }

    @classmethod
    def get(cls, prompt_name: str, **kwargs) -> str:
        prompt = getattr(cls, prompt_name)
        return prompt.format(**kwargs)

    @classmethod
    def with_lens_guidance(cls, base_prompt: str, lens: str) -> str:
        guidance = cls.LENS_GUIDANCE.get(lens, "Analyze the content for patterns and insights.")
        return f"{base_prompt}\n\nLens Guidance: {guidance}"

