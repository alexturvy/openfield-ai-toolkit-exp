#!/usr/bin/env python3
"""Test research-aware analysis with real Modo interview data."""

from pathlib import Path
from src.insight_synthesizer.pipeline import InsightSynthesizer
from src.insight_synthesizer.research.goal_manager import ResearchGoal

def test_modo_research():
    """Test with actual Modo research goals and interview data."""
    
    # Define research goals based on likely Modo research objectives
    research_goals = ResearchGoal(
        primary_questions=[
            "What are instructors' initial reactions to Modo as an AI teaching assistant?",
            "What barriers prevent instructors from adopting Modo in their teaching?",
            "Which Modo features do instructors find most valuable and why?",
            "How would Modo fit into instructors' existing course workflows?",
            "What concerns do instructors have about using AI in education?"
        ],
        methodology="Semi-structured interviews with university instructors",
        participant_criteria="University instructors across various disciplines with classroom teaching experience",
        key_hypotheses=[
            "Instructors will value time-saving features like automated grading",
            "Integration with existing LMS platforms will be critical for adoption",
            "Concerns about AI accuracy and student privacy will be primary barriers",
            "Instructors in technical fields will be more receptive to AI assistance"
        ]
    )
    
    # Initialize synthesizer
    synthesizer = InsightSynthesizer()
    
    # Use modo transcripts directory
    modo_dir = Path("modo_transcripts")
    
    if not modo_dir.exists():
        print(f"Error: {modo_dir} directory not found")
        return
    
    try:
        print("\n=== Starting Research-Aware Analysis of Modo Interviews ===")
        print(f"Research questions: {len(research_goals.primary_questions)}")
        print(f"Hypotheses: {len(research_goals.key_hypotheses or [])}")
        print(f"Analysis lens: pain_points (barriers to adoption)\n")
        
        # List available files
        from src.insight_synthesizer.document_processing import find_supported_files
        files = find_supported_files(modo_dir)
        print(f"Found {len(files)} interview transcripts")
        
        # Run analysis with research goals - analyze first 3 files for speed
        report_path = synthesizer.analyze_directory(
            str(modo_dir),
            lens="pain_points",
            file_selection="1-3",  # First 3 files for testing
            research_goals=research_goals
        )
        
        print(f"\n✅ Success! Report generated: {report_path}")
        
        # Display key sections of the report
        with open(report_path, 'r') as f:
            content = f.read()
            
        # Find and display research coverage section
        if "## Research Coverage Analysis" in content:
            coverage_start = content.find("## Research Coverage Analysis")
            coverage_end = content.find("\n##", coverage_start + 1)
            if coverage_end == -1:
                coverage_end = len(content)
            
            print("\n--- Research Coverage Summary ---")
            print(content[coverage_start:coverage_end])
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_modo_research()