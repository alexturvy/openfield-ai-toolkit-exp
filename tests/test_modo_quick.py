#!/usr/bin/env python3
"""Quick test of research-aware analysis with sample data."""

from pathlib import Path
from src.insight_synthesizer.pipeline import InsightSynthesizer
from src.insight_synthesizer.research.goal_manager import ResearchGoal

def test_quick():
    """Quick test with sample data to verify research-aware functionality."""
    
    # Define simple research goals
    research_goals = ResearchGoal(
        primary_questions=[
            "What challenges do users face with the current system?",
            "What features would users find most valuable?",
            "How does the product fit into existing workflows?"
        ],
        methodology="User interviews",
        key_hypotheses=["Users struggle with complexity"]
    )
    
    # Initialize synthesizer
    synthesizer = InsightSynthesizer()
    
    # Use sample notes directory for quick test
    sample_dir = Path("sample_notes")
    
    print("\n=== Quick Research-Aware Analysis Test ===")
    print(f"Research questions: {len(research_goals.primary_questions)}")
    
    try:
        # Run analysis with research goals
        report_path = synthesizer.analyze_directory(
            str(sample_dir),
            lens="pain_points",
            file_selection="all",
            research_goals=research_goals
        )
        
        print(f"\n✅ Report generated: {report_path}")
        
        # Check if research sections are in report
        with open(report_path, 'r') as f:
            content = f.read()
            
        # Verify key sections exist
        sections_found = []
        for section in ["Research Context", "Research Coverage Analysis", "addressed_questions", "research_implications"]:
            if section in content:
                sections_found.append(section)
                
        print(f"\n✅ Research sections found: {', '.join(sections_found)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_quick()