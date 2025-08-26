"""Tests for progress indicator functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO
from rich.console import Console

from src.insight_synthesizer.utils.progress_manager import (
    UnifiedProgressManager, 
    ProgressStage,
    get_progress_manager,
    set_progress_manager,
    reset_progress_manager
)
from src.insight_synthesizer.analysis.embeddings import generate_embeddings, TextChunk
from src.insight_synthesizer.pipeline import InsightSynthesizer


class TestUnifiedProgressManager:
    """Test the unified progress management system."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_progress_manager()
        self.console = Console(file=StringIO(), width=80)
        self.manager = UnifiedProgressManager(console=self.console)
    
    def test_manager_initialization(self):
        """Test that the progress manager initializes correctly."""
        assert self.manager.console == self.console
        assert not self.manager.is_active
        assert len(self.manager.stage_tasks) == 0
        
    def test_pipeline_start_stop(self):
        """Test starting and stopping the pipeline progress."""
        self.manager.start_pipeline()
        assert self.manager.is_active
        assert self.manager.overall_task is not None
        
        self.manager.finish()
        assert not self.manager.is_active
        
    def test_stage_management(self):
        """Test stage creation and management."""
        self.manager.start_pipeline()
        
        # Start a stage
        task_id = self.manager.start_stage(
            ProgressStage.DOCUMENT_PROCESSING, 
            5, 
            "Processing test files"
        )
        
        assert ProgressStage.DOCUMENT_PROCESSING in self.manager.stage_tasks
        assert self.manager.current_stage == ProgressStage.DOCUMENT_PROCESSING
        
        # Update the stage
        self.manager.update_stage(ProgressStage.DOCUMENT_PROCESSING, 1)
        
        # Complete the stage
        self.manager.complete_stage(ProgressStage.DOCUMENT_PROCESSING)
        
        self.manager.finish()
        
    def test_substage_management(self):
        """Test substage creation and management."""
        self.manager.start_pipeline()
        
        # Start main stage
        main_task = self.manager.start_stage(ProgressStage.EMBEDDING_GENERATION, 100)
        
        # Add substage
        sub_task = self.manager.add_substage(
            ProgressStage.EMBEDDING_GENERATION,
            "Loading model",
            10
        )
        
        # Update substage
        self.manager.update_substage(sub_task, 5)
        self.manager.complete_substage(sub_task)
        
        self.manager.finish()
        
    def test_logging_functions(self):
        """Test logging functions don't crash."""
        self.manager.log_info("Test info message")
        self.manager.log_warning("Test warning message")
        self.manager.log_error("Test error message")
        self.manager.log_success("Test success message")
        
    def test_context_managers(self):
        """Test context manager functionality."""
        self.manager.start_pipeline()
        
        # Test stage context
        with self.manager.stage_context(ProgressStage.CLUSTERING, 10, "Test clustering") as task_id:
            assert task_id is not None
            self.manager.update_stage(ProgressStage.CLUSTERING, 5)
        
        # Test substage context
        with self.manager.stage_context(ProgressStage.VALIDATION, 20, "Test validation") as main_task:
            with self.manager.substage_context(ProgressStage.VALIDATION, "Quote extraction", 5) as sub_task:
                self.manager.update_substage(sub_task, 3)
        
        self.manager.finish()
        
    def test_global_manager_functions(self):
        """Test global manager instance functions."""
        # Reset to ensure clean state
        reset_progress_manager()
        
        # Get default manager
        manager1 = get_progress_manager()
        manager2 = get_progress_manager()
        assert manager1 is manager2  # Should be same instance
        
        # Set custom manager
        custom_manager = UnifiedProgressManager()
        set_progress_manager(custom_manager)
        
        manager3 = get_progress_manager()
        assert manager3 is custom_manager
        
        # Reset again
        reset_progress_manager()
        manager4 = get_progress_manager()
        assert manager4 is not custom_manager


class TestProgressIntegration:
    """Test progress indicators integration with existing components."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_progress_manager()
        
    @patch('src.insight_synthesizer.analysis.embeddings.SentenceTransformer')
    def test_embedding_progress_with_manager(self, mock_transformer):
        """Test embedding generation with progress manager."""
        # Mock the transformer
        mock_model = Mock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_model
        
        # Create test chunks
        chunks = [
            TextChunk("Test chunk 1", "file1.txt"),
            TextChunk("Test chunk 2", "file1.txt"),
            TextChunk("Test chunk 3", "file2.txt")
        ]
        
        # Create progress manager
        console = Console(file=StringIO(), width=80)
        manager = UnifiedProgressManager(console=console)
        manager.start_pipeline()
        manager.start_stage(ProgressStage.EMBEDDING_GENERATION, len(chunks))
        
        # Test embedding generation with progress manager
        result = generate_embeddings(chunks, progress_manager=manager)
        
        assert len(result) == 3
        assert all(chunk.embedding is not None for chunk in result)
        
        manager.finish()
        
    @patch('src.insight_synthesizer.analysis.embeddings.SentenceTransformer')
    def test_embedding_progress_without_manager(self, mock_transformer):
        """Test embedding generation without progress manager (fallback)."""
        # Mock the transformer
        mock_model = Mock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_model
        
        # Create test chunks
        chunks = [
            TextChunk("Test chunk 1", "file1.txt"),
            TextChunk("Test chunk 2", "file1.txt")
        ]
        
        # Test embedding generation without progress manager
        result = generate_embeddings(chunks)
        
        assert len(result) == 2
        assert all(chunk.embedding is not None for chunk in result)
        
    @patch('src.insight_synthesizer.pipeline.ensure_ollama_ready')
    @patch('src.insight_synthesizer.pipeline.extract_text_from_file')
    @patch('src.insight_synthesizer.pipeline.generate_embeddings')
    @patch('src.insight_synthesizer.pipeline.perform_clustering') 
    @patch('src.insight_synthesizer.pipeline.synthesize_insights')
    @patch('src.insight_synthesizer.pipeline.generate_markdown_report')
    def test_pipeline_with_progress_manager(self, mock_report, mock_synthesis, 
                                          mock_clustering, mock_embeddings,
                                          mock_extract, mock_ollama):
        """Test full pipeline with progress manager integration."""
        # Set up mocks
        mock_ollama.return_value = None
        mock_extract.return_value = "Sample text content"
        mock_embeddings.return_value = []
        mock_clustering.return_value = ([], [])
        mock_synthesis.return_value = {"theme_name": "Test Theme"}
        mock_report.return_value = None
        
        # Mock classification and chunking
        mock_classification = Mock()
        mock_classification.content_type = Mock()
        mock_classification.content_type.value = "test"
        
        # Create test synthesizer
        synthesizer = InsightSynthesizer()
        
        # Mock the classifier and chunker to avoid complex setup
        synthesizer.classifier.classify_document = Mock(return_value=mock_classification)
        synthesizer.chunker.chunk_document = Mock(return_value=[])
        synthesizer.validator.validate_themes = Mock()
        synthesizer.validator.validate_themes.return_value = Mock(validation_summary="Test validation")
        
        # Test file paths
        test_files = [Path("test1.txt"), Path("test2.txt")]
        
        # Run the analysis
        result = synthesizer.analyze_files(test_files, "test_lens")
        
        # Verify the result
        assert result == "synthesis_report.md"
        
        # Verify mocks were called
        assert mock_extract.call_count == 2
        assert mock_embeddings.called
        assert mock_clustering.called
        
    def test_progress_manager_error_handling(self):
        """Test that progress manager handles errors gracefully."""
        console = Console(file=StringIO(), width=80)
        manager = UnifiedProgressManager(console=console)
        
        # Test operations without starting pipeline (should not crash)
        manager.update_stage(ProgressStage.CLUSTERING, 1)
        manager.complete_stage(ProgressStage.CLUSTERING)
        manager.set_stage_status(ProgressStage.CLUSTERING, "test")
        
        # Test multiple finish calls (should not crash)
        manager.start_pipeline()
        manager.finish()
        manager.finish()  # Second call should be safe
        
    def test_stage_progress_calculation(self):
        """Test stage progress calculation."""
        console = Console(file=StringIO(), width=80)
        manager = UnifiedProgressManager(console=console)
        manager.start_pipeline()
        
        # Start stage with known total
        task_id = manager.start_stage(ProgressStage.DOCUMENT_PROCESSING, 10)
        
        # Initially should be 0
        progress = manager.get_stage_progress(ProgressStage.DOCUMENT_PROCESSING)
        assert progress == 0.0
        
        # Update progress
        manager.update_stage(ProgressStage.DOCUMENT_PROCESSING, 3)
        progress = manager.get_stage_progress(ProgressStage.DOCUMENT_PROCESSING)
        assert progress == 0.3
        
        # Complete stage
        manager.complete_stage(ProgressStage.DOCUMENT_PROCESSING)
        progress = manager.get_stage_progress(ProgressStage.DOCUMENT_PROCESSING)
        assert progress == 1.0
        
        manager.finish()


if __name__ == "__main__":
    pytest.main([__file__])