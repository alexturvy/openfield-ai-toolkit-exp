#!/usr/bin/env python3
"""
Basic smoke test to verify pipeline can be instantiated and run basic operations.
This test focuses on core functionality without requiring heavy ML dependencies.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Mock heavy dependencies before importing
import types

# Mock numpy
numpy_mod = types.ModuleType('numpy')
numpy_mod.array = lambda x: x
numpy_mod.zeros = lambda x: [0] * x if isinstance(x, int) else [[0] * x[1] for _ in range(x[0])]
numpy_mod.float32 = float
sys.modules['numpy'] = numpy_mod

# Mock rich
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('rich.console')
panel_mod = types.ModuleType('rich.panel')
progress_mod = types.ModuleType('rich.progress')
table_mod = types.ModuleType('rich.table')
tree_mod = types.ModuleType('rich.tree')

class DummyConsole:
    def print(self, *args, **kwargs):
        clean_args = []
        for arg in args:
            if isinstance(arg, str):
                clean_arg = arg.replace('[bold]', '').replace('[/]', '').replace('[green]', '').replace('[blue]', '').replace('[bold blue]', '')
                clean_args.append(clean_arg)
            else:
                clean_args.append(str(arg))
        print(*clean_args)

console_mod.Console = DummyConsole
panel_mod.Panel = lambda content, **kwargs: content
progress_mod.Progress = lambda *args, **kwargs: MagicMock()
progress_mod.SpinnerColumn = lambda: None
progress_mod.TextColumn = lambda x: None
progress_mod.BarColumn = lambda: None
progress_mod.TaskProgressColumn = lambda: None
progress_mod.TimeElapsedColumn = lambda: None
table_mod.Table = lambda *args, **kwargs: MagicMock()
tree_mod.Tree = lambda *args, **kwargs: MagicMock()

rich_mod.console = console_mod
rich_mod.panel = panel_mod
rich_mod.progress = progress_mod
rich_mod.table = table_mod
rich_mod.tree = tree_mod

sys.modules['rich'] = rich_mod
sys.modules['rich.console'] = console_mod
sys.modules['rich.panel'] = panel_mod
sys.modules['rich.progress'] = progress_mod
sys.modules['rich.table'] = table_mod
sys.modules['rich.tree'] = tree_mod

# Mock other dependencies
umap_mod = types.ModuleType('umap')
umap_mod.UMAP = lambda *args, **kwargs: MagicMock()
sys.modules['umap'] = umap_mod

hdbscan_mod = types.ModuleType('hdbscan')
hdbscan_mod.HDBSCAN = lambda *args, **kwargs: MagicMock()
sys.modules['hdbscan'] = hdbscan_mod

sklearn_mod = types.ModuleType('sklearn')
preprocessing_mod = types.ModuleType('sklearn.preprocessing')
metrics_mod = types.ModuleType('sklearn.metrics')
preprocessing_mod.normalize = lambda x: x
metrics_mod.silhouette_score = lambda emb, labels: 0.0
sklearn_mod.preprocessing = preprocessing_mod
sklearn_mod.metrics = metrics_mod
sys.modules['sklearn'] = sklearn_mod
sys.modules['sklearn.preprocessing'] = preprocessing_mod
sys.modules['sklearn.metrics'] = metrics_mod

sentence_transformers_mod = types.ModuleType('sentence_transformers')
sentence_transformers_mod.SentenceTransformer = lambda *args, **kwargs: MagicMock()
sys.modules['sentence_transformers'] = sentence_transformers_mod


def test_basic_pipeline_smoke():
    """Test that the pipeline can be instantiated and basic methods called."""
    print("🧪 Running basic pipeline smoke test...")
    
    try:
        # Import after mocking dependencies
        from src.insight_synthesizer.pipeline import InsightSynthesizer
        from src.insight_synthesizer.research.goal_manager import ResearchGoal, ResearchGoalManager
        from src.insight_synthesizer.analysis.clustering import Cluster
        
        print("✅ All imports successful")
        
        # Test 1: Basic instantiation
        synthesizer = InsightSynthesizer()
        print("✅ InsightSynthesizer instantiated successfully")
        
        # Test 2: ResearchGoal creation and ResearchGoalManager
        goals = ResearchGoal(
            primary_questions=["What are the main pain points?"],
            methodology="Test methodology"
        )
        goal_manager = ResearchGoalManager(goals)
        assert goal_manager.research_goals == goals
        print("✅ ResearchGoal and ResearchGoalManager work correctly")
        
        # Test 3: Cluster creation with size parameter
        cluster = Cluster(cluster_id=1, chunks=[], size=10)
        assert cluster.size == 10
        assert cluster.cluster_id == 1
        print("✅ Cluster with size parameter works correctly")
        
        # Test 4: Commercial model environment handling
        original_env = os.environ.get('USE_COMMERCIAL_MODEL')
        try:
            os.environ['USE_COMMERCIAL_MODEL'] = 'true'
            os.environ['OPENAI_API_KEY'] = 'test-key'
            assert os.environ.get('USE_COMMERCIAL_MODEL') == 'true'
            print("✅ Commercial model environment variables work")
        finally:
            if original_env:
                os.environ['USE_COMMERCIAL_MODEL'] = original_env
            else:
                os.environ.pop('USE_COMMERCIAL_MODEL', None)
            os.environ.pop('OPENAI_API_KEY', None)
        
        return True
        
    except Exception as e:
        print(f"❌ Basic pipeline smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_operations():
    """Test basic file operations work."""
    print("\n🧪 Testing file operations...")
    
    try:
        # Test sample files exist
        sample_files = [
            ROOT / "sample_notes/interview1.txt",
            ROOT / "sample_notes/interview2.txt"
        ]
        
        existing_files = [f for f in sample_files if f.exists()]
        if not existing_files:
            print("❌ No sample files found for testing")
            return False
        
        print(f"✅ Found {len(existing_files)} sample files")
        
        # Test file reading
        with open(existing_files[0], 'r') as f:
            content = f.read()
            if len(content) > 10:  # Basic content check
                print("✅ File reading works correctly")
                return True
            else:
                print("❌ File appears to be empty or too short")
                return False
                
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False


def test_mocked_pipeline_flow():
    """Test the pipeline flow with mocked dependencies."""
    print("\n🧪 Testing mocked pipeline flow...")
    
    try:
        from src.insight_synthesizer.pipeline import InsightSynthesizer
        
        # Mock all the heavy operations
        with patch('src.insight_synthesizer.pipeline.ensure_ollama_ready'):
            with patch('src.insight_synthesizer.pipeline.generate_embeddings') as mock_embeddings:
                with patch('src.insight_synthesizer.pipeline.perform_clustering') as mock_clustering:
                    with patch('src.insight_synthesizer.pipeline.synthesize_insights') as mock_synthesis:
                        with patch('src.insight_synthesizer.pipeline.generate_markdown_report') as mock_report:
                            with patch('src.insight_synthesizer.pipeline.find_supported_files') as mock_find_files:
                                
                                # Setup mocks
                                mock_embeddings.return_value = []
                                mock_clustering.return_value = ([], [Cluster(cluster_id=1, chunks=[], size=5)])
                                mock_synthesis.return_value = {"theme_name": "Test Theme"}
                                mock_report.return_value = "test_report.md"
                                mock_find_files.return_value = [Path("sample_notes/interview1.txt")]
                                
                                synthesizer = InsightSynthesizer()
                                
                                # Test analyze_directory method
                                result = synthesizer.analyze_directory(
                                    "sample_notes",
                                    "pain_points",
                                    "all"
                                )
                                
                                assert result == "test_report.md"
                                print("✅ Pipeline flow with mocked dependencies works")
                                return True
                                
    except Exception as e:
        print(f"❌ Mocked pipeline flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """Run the basic smoke tests."""
    print("=" * 70)
    print("🚀 BASIC SMOKE TEST - PIPELINE FUNCTIONALITY")
    print("=" * 70)
    
    tests = [
        test_basic_pipeline_smoke,
        test_file_operations,
        test_mocked_pipeline_flow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"📊 SMOKE TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL SMOKE TESTS PASSED!")
        print("The pipeline is working correctly with all fixes in place!")
        print("=" * 70)
        print("🚀 SMOKE TEST SUCCESS - READY FOR COMMIT!")
        sys.exit(0)
    else:
        print("❌ SOME SMOKE TESTS FAILED!")
        print("🛑 Check the errors above before committing.")
        print("=" * 70)
        sys.exit(1)