#!/usr/bin/env python3
"""Test script for research-goal-aware analysis."""

from pathlib import Path
from src.insight_synthesizer.pipeline import InsightSynthesizer
from src.insight_synthesizer.research.goal_manager import ResearchGoal

def test_research_aware_analysis():
    """Test the research-aware analysis with sample data."""
    
    # Define research goals based on the Modo research
    research_goals = ResearchGoal(
        primary_questions=[
            "What are instructors' initial reactions to Modo as an AI teaching assistant?",
            "What barriers exist to adopting Modo in their teaching workflows?",
            "Which Modo features are most valuable to instructors?",
            "How does Modo fit into existing course management systems?"
        ],
        methodology="Semi-structured interviews with university instructors across multiple disciplines",
        participant_criteria="University instructors with at least 2 years teaching experience",
        key_hypotheses=[
            "Instructors will value time-saving features most highly",
            "Integration with existing LMS will be a key adoption factor",
            "Concerns about AI accuracy will be a primary barrier"
        ]
    )
    
    # Initialize synthesizer
    synthesizer = InsightSynthesizer()
    
    # Use sample notes directory
    sample_dir = Path("sample_notes")
    
    if not sample_dir.exists():
        print(f"Error: {sample_dir} directory not found")
        return
    
    try:
        # Run analysis with research goals
        print("Starting research-aware analysis...")
        print(f"Research questions: {len(research_goals.primary_questions)}")
        print(f"Key hypotheses: {len(research_goals.key_hypotheses or [])}")
        
        report_path = synthesizer.analyze_directory(
            str(sample_dir),
            lens="pain_points",
            file_selection="all",
            research_goals=research_goals
        )
        
        print(f"\nSuccess! Report generated: {report_path}")
        
        # Display a preview of the report
        with open(report_path, 'r') as f:
            lines = f.readlines()[:50]  # First 50 lines
            print("\n--- Report Preview ---")
            print(''.join(lines))
            print("...")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_research_aware_analysis()