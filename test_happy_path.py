#!/usr/bin/env python3
"""
Happy Path Test - If this works, we ship.
Run: python test_happy_path.py
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_happy_path():
    """Test the most common use case."""
    
    print("=" * 60)
    print("HAPPY PATH TEST")
    print("=" * 60)
    
    # Step 1: Check LLM connection
    print("\n1. Testing LLM connection...")
    from src.insight_synthesizer.llm.client import test_llm
    
    if not test_llm():
        print("❌ LLM not working. Fix this first:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export USE_COMMERCIAL_MODEL=true")
        return False
    print("✅ LLM connection working")
    
    # Step 2: Parse research plan
    print("\n2. Testing research plan parsing...")
    from src.insight_synthesizer.research.plan_parser import ResearchPlanParser
    
    parser = ResearchPlanParser()
    plan_file = Path("test_data/research_plans/formal_plan.txt")
    
    if not plan_file.exists():
        print(f"❌ Test file not found: {plan_file}")
        return False
        
    plan = parser.parse_document(plan_file)
    
    if not plan.research_questions:
        print("❌ No research questions extracted")
        return False
    
    print(f"✅ Extracted {len(plan.research_questions)} questions")
    
    # Step 3: Process sample documents
    print("\n3. Testing document processing...")
    from src.insight_synthesizer.pipeline import InsightSynthesizer
    
    sample_files = list(Path("sample_notes").glob("*.txt"))[:3]
    
    if len(sample_files) < 3:
        print("❌ Need at least 3 sample files")
        return False
    
    print(f"   Processing {len(sample_files)} files...")
    
    start_time = time.time()
    synthesizer = InsightSynthesizer()
    
    try:
        report_path = synthesizer.analyze_files(
            sample_files,
            lens="pain_points",
            research_goals=plan
        )
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return False
    
    elapsed = time.time() - start_time
    
    # Step 4: Verify output
    print("\n4. Verifying output...")
    
    if not Path(report_path).exists():
        print("❌ No report generated")
        return False
    
    report_size = Path(report_path).stat().st_size
    if report_size < 1000:
        print("❌ Report too small, probably failed")
        return False
    
    print(f"✅ Report generated: {report_path}")
    print(f"   Size: {report_size:,} bytes")
    print(f"   Time: {elapsed:.1f} seconds")
    
    # Check content
    content = Path(report_path).read_text()
    required_sections = ["Research Questions", "Key Themes", "Supporting Evidence"]
    missing = [s for s in required_sections if s not in content]
    
    if missing:
        print(f"❌ Missing sections: {missing}")
        return False
    
    print("✅ All required sections present")
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 HAPPY PATH TEST PASSED!")
    print(f"   Processed {len(sample_files)} files in {elapsed:.1f}s")
    print(f"   Using: {os.environ.get('USE_COMMERCIAL_MODEL', 'false')}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_happy_path()
    sys.exit(0 if success else 1)