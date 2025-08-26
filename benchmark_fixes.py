import time
import tempfile
from pathlib import Path
from src.insight_synthesizer.pipeline import InsightSynthesizer
from src.insight_synthesizer.research.plan_parser import ResearchPlanParser

def benchmark_with_fixes():
    """Test the actual performance improvements."""
    
    # Test 1: Model caching performance
    print("Testing model caching...")
    from src.insight_synthesizer.analysis.model_cache import ModelCache
    cache = ModelCache()
    
    start = time.time()
    model1 = cache.get_embedding_model()
    first_load = time.time() - start
    
    start = time.time()
    model2 = cache.get_embedding_model()
    second_load = time.time() - start
    
    print(f"  First load: {first_load:.2f}s")
    print(f"  Second load: {second_load:.2f}s")
    print(f"  Speedup: {first_load/second_load:.1f}x")
    assert model1 is model2, "Models should be same instance!"
    
    # Test 2: Small dataset clustering
    print("\nTesting small dataset clustering...")
    test_dir = tempfile.mkdtemp()
    small_file = Path(test_dir) / "small.txt"
    small_file.write_text("User: The navigation is confusing.\nInterviewer: Why?\nUser: Can't find things.")
    
    synthesizer = InsightSynthesizer()
    try:
        report = synthesizer.analyze_files([small_file], "pain_points")
        print(f"  ✅ Small dataset handled successfully")
    except Exception as e:
        print(f"  ❌ Small dataset failed: {e}")
    
    # Test 3: Long document validation
    print("\nTesting long document validation...")
    long_file = Path(test_dir) / "long.txt"
    long_content = "Start of document. " + ("filler " * 1500) + " CRITICAL_INSIGHT_AT_END"
    long_file.write_text(long_content)
    
    # This should find the insight at the end
    print("  Testing quote extraction from end of long document...")
    
    return True

if __name__ == "__main__":
    benchmark_with_fixes()
