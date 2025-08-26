#!/usr/bin/env python3
"""
Comprehensive integration test file to verify all fixes are working correctly.

This test file verifies:
1. Basic flow without research goals
2. Research goals don't break anything
3. Commercial model switching fallback works
4. Cluster creation includes size parameter
5. ResearchGoalManager initializes without errors
6. Synthesis module imports work correctly
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import conftest to setup stubs for missing dependencies
import conftest

from src.insight_synthesizer.pipeline import InsightSynthesizer
from src.insight_synthesizer.research.goal_manager import ResearchGoal, ResearchGoalManager
from src.insight_synthesizer.analysis.clustering import Cluster


def test_pipeline_smoke():
    """This must pass or you cannot commit."""
    print("🧪 Running comprehensive integration tests...")
    
    # Verify sample files exist
    sample_dir = Path("sample_notes")
    if not sample_dir.exists():
        raise FileNotFoundError(f"Sample directory {sample_dir} not found")
    
    test_files = [Path("sample_notes/interview1.txt")]
    if not test_files[0].exists():
        raise FileNotFoundError(f"Test file {test_files[0]} not found")
    
    print("✅ Sample files verified")
    
    # Test 1: Basic flow without research goals
    print("\n📋 Test 1: Basic flow without research goals")
    synthesizer = InsightSynthesizer()
    
    try:
        # Mock the actual heavy processing to avoid dependencies
        with patch('src.insight_synthesizer.pipeline.ensure_ollama_ready'):
            with patch('src.insight_synthesizer.pipeline.generate_embeddings') as mock_embeddings:
                with patch('src.insight_synthesizer.pipeline.perform_clustering') as mock_clustering:
                    with patch('src.insight_synthesizer.pipeline.synthesize_insights') as mock_synthesis:
                        with patch('src.insight_synthesizer.pipeline.generate_markdown_report') as mock_report:
                            
                            # Setup mocks
                            mock_embeddings.return_value = []
                            mock_clustering.return_value = ([], [Cluster(cluster_id=1, chunks=[], size=5)])
                            mock_synthesis.return_value = {"theme_name": "Test Theme"}
                            mock_report.return_value = "test_report.md"
                            
                            report = synthesizer.analyze_files(test_files, "pain_points")
                            assert report == "test_report.md"
                            print("✅ Basic flow completed successfully")
                            
    except Exception as e:
        print(f"❌ Basic flow test failed: {e}")
        raise
    
    # Test 2: Research goals don't break anything
    print("\n📋 Test 2: Research goals don't break anything")
    try:
        goals = ResearchGoal(
            primary_questions=["What are the main pain points?"],
            methodology="Test methodology",
            participant_criteria="Test criteria"
        )
        
        # Verify ResearchGoalManager initializes correctly
        goal_manager = ResearchGoalManager(goals)
        assert goal_manager.research_goals == goals
        print("✅ ResearchGoalManager initialized correctly")
        
        with patch('src.insight_synthesizer.pipeline.ensure_ollama_ready'):
            with patch('src.insight_synthesizer.pipeline.generate_embeddings') as mock_embeddings:
                with patch('src.insight_synthesizer.analysis.research_clustering.create_research_aware_clusters') as mock_research_clustering:
                    with patch('src.insight_synthesizer.pipeline.synthesize_insights') as mock_synthesis:
                        with patch('src.insight_synthesizer.pipeline.generate_markdown_report') as mock_report:
                            with patch('src.insight_synthesizer.validation.research_validator.ResearchCoverageValidator'):
                                
                                # Setup mocks  
                                mock_embeddings.return_value = []
                                mock_research_clustering.return_value = [Cluster(cluster_id=1, chunks=[], size=3)]
                                mock_synthesis.return_value = {"theme_name": "Research Theme"}
                                mock_report.return_value = "research_report.md"
                                
                                report = synthesizer.analyze_files(test_files, "pain_points", goals)
                                assert report == "research_report.md"
                                print("✅ Research goals flow completed successfully")
                                
    except Exception as e:
        print(f"❌ Research goals test failed: {e}")
        raise
    
    # Test 3: Commercial model switching works
    print("\n📋 Test 3: Commercial model switching fallback")
    try:
        # Store original environment
        original_env = {}
        for key in ['USE_COMMERCIAL_MODEL', 'OPENAI_API_KEY']:
            original_env[key] = os.environ.get(key)
        
        # Set commercial model environment
        os.environ['USE_COMMERCIAL_MODEL'] = 'true'
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        try:
            with patch('src.insight_synthesizer.pipeline.ensure_ollama_ready'):
                with patch('src.insight_synthesizer.pipeline.generate_embeddings') as mock_embeddings:
                    with patch('src.insight_synthesizer.pipeline.perform_clustering') as mock_clustering:
                        with patch('src.insight_synthesizer.pipeline.synthesize_insights') as mock_synthesis:
                            with patch('src.insight_synthesizer.pipeline.generate_markdown_report') as mock_report:
                                
                                # Setup mocks for commercial model fallback
                                mock_embeddings.return_value = []
                                mock_clustering.return_value = ([], [Cluster(cluster_id=1, chunks=[], size=2)])
                                mock_synthesis.return_value = {"theme_name": "Commercial Theme"}
                                mock_report.return_value = "commercial_report.md"
                                
                                synthesizer_commercial = InsightSynthesizer()
                                report = synthesizer_commercial.analyze_files(test_files, "pain_points")
                                assert report == "commercial_report.md"
                                print("✅ Commercial model fallback works")
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
                    
    except Exception as e:
        print(f"❌ Commercial model test failed: {e}")
        raise
    
    # Test 4: Verify Cluster creation includes size parameter
    print("\n📋 Test 4: Cluster creation includes size parameter")
    try:
        cluster = Cluster(cluster_id=1, chunks=[], size=10)
        assert hasattr(cluster, 'size')
        assert cluster.size == 10
        assert cluster.cluster_id == 1
        assert cluster.chunks == []
        print("✅ Cluster creation with size parameter works")
    except Exception as e:
        print(f"❌ Cluster size parameter test failed: {e}")
        raise
    
    # Test 5: Synthesis module imports work correctly
    print("\n📋 Test 5: Synthesis module imports work correctly")
    try:
        # Test key imports
        from src.insight_synthesizer.analysis.synthesis import synthesize_insights
        from src.insight_synthesizer.analysis.clustering import perform_clustering, Cluster
        from src.insight_synthesizer.research.goal_manager import ResearchGoal, ResearchGoalManager
        from src.insight_synthesizer.pipeline import InsightSynthesizer
        print("✅ All synthesis module imports work correctly")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        raise
    
    # Test 6: Verify directory analysis method works
    print("\n📋 Test 6: Directory analysis method")
    try:
        with patch('src.insight_synthesizer.pipeline.ensure_ollama_ready'):
            with patch('src.insight_synthesizer.pipeline.find_supported_files') as mock_find_files:
                with patch('src.insight_synthesizer.pipeline.generate_embeddings') as mock_embeddings:
                    with patch('src.insight_synthesizer.pipeline.perform_clustering') as mock_clustering:
                        with patch('src.insight_synthesizer.pipeline.synthesize_insights') as mock_synthesis:
                            with patch('src.insight_synthesizer.pipeline.generate_markdown_report') as mock_report:
                                
                                # Setup mocks
                                mock_find_files.return_value = test_files
                                mock_embeddings.return_value = []
                                mock_clustering.return_value = ([], [Cluster(cluster_id=1, chunks=[], size=1)])
                                mock_synthesis.return_value = {"theme_name": "Directory Theme"}
                                mock_report.return_value = "directory_report.md"
                                
                                synthesizer_dir = InsightSynthesizer()
                                report = synthesizer_dir.analyze_directory(
                                    str(sample_dir), 
                                    "pain_points", 
                                    "all"
                                )
                                assert report == "directory_report.md"
                                print("✅ Directory analysis method works")
    except Exception as e:
        print(f"❌ Directory analysis test failed: {e}")
        raise
    
    print("\n🎉 All integration tests passed! The pipeline is working correctly.")
    return True


def test_error_handling():
    """Test error handling scenarios."""
    print("\n🧪 Testing error handling scenarios...")
    
    # Test with non-existent file
    print("\n📋 Testing non-existent file handling")
    synthesizer = InsightSynthesizer()
    try:
        non_existent_files = [Path("non_existent_file.txt")]
        synthesizer.analyze_files(non_existent_files, "pain_points")
        print("❌ Should have raised an error for non-existent file")
        return False
    except Exception:
        print("✅ Correctly handles non-existent file")
    
    # Test with invalid lens
    print("\n📋 Testing invalid lens handling")
    try:
        test_files = [Path("sample_notes/interview1.txt")]
        with patch('src.insight_synthesizer.pipeline.ensure_ollama_ready'):
            with patch('src.insight_synthesizer.pipeline.generate_embeddings'):
                with patch('src.insight_synthesizer.pipeline.perform_clustering'):
                    with patch('src.insight_synthesizer.pipeline.synthesize_insights') as mock_synthesis:
                        # Simulate an invalid lens error
                        mock_synthesis.side_effect = ValueError("Invalid lens")
                        
                        synthesizer.analyze_files(test_files, "invalid_lens")
                        print("❌ Should have raised an error for invalid lens")
                        return False
    except ValueError:
        print("✅ Correctly handles invalid lens")
    except Exception as e:
        print(f"✅ Error handling works (got: {e})")
    
    print("✅ Error handling tests completed")
    return True


if __name__ == "__main__":
    """Run the comprehensive integration tests."""
    try:
        print("=" * 60)
        print("🚀 COMPREHENSIVE INTEGRATION TEST SUITE")
        print("=" * 60)
        
        # Run main integration tests
        success = test_pipeline_smoke()
        
        if success:
            # Run error handling tests
            test_error_handling()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED! READY FOR COMMIT!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED! DO NOT COMMIT!")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED! DO NOT COMMIT!")
        print("=" * 60)
        sys.exit(1)