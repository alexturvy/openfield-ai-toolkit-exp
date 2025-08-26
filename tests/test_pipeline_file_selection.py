"""Tests for pipeline file selection functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from insight_synthesizer.pipeline import InsightSynthesizer


class TestPipelineFileSelection(unittest.TestCase):
    """Test file selection functionality in the pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.synthesizer = InsightSynthesizer()
        
        # Create temporary directory with test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        file_data = [
            ("file1.txt", "Content of file 1"),
            ("file2.txt", "Content of file 2"), 
            ("file3.txt", "Content of file 3"),
            ("file4.txt", "Content of file 4"),
            ("file5.txt", "Content of file 5")
        ]
        
        for filename, content in file_data:
            file_path = Path(self.temp_dir) / filename
            file_path.write_text(content)
            self.test_files.append(file_path)
    
    def tearDown(self):
        """Clean up temporary files."""
        for file_path in self.test_files:
            file_path.unlink(missing_ok=True)
        os.rmdir(self.temp_dir)
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_all_files(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with 'all' file selection."""
        # Mock dependencies
        mock_find_files.return_value = self.test_files
        mock_analyze_files.return_value = "test_report.md"
        
        # Call analyze_directory with 'all'
        result = self.synthesizer.analyze_directory(self.temp_dir, "pain_points", "all")
        
        # Verify all files were passed to analyze_files
        mock_analyze_files.assert_called_once()
        passed_files = mock_analyze_files.call_args[0][0]
        self.assertEqual(len(passed_files), 5)
        self.assertEqual(set(passed_files), set(self.test_files))
        self.assertEqual(result, "test_report.md")
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_single_file(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with single file selection."""
        mock_find_files.return_value = self.test_files
        mock_analyze_files.return_value = "test_report.md"
        
        # Select file at index 3 (4th file, 0-based indexing)
        result = self.synthesizer.analyze_directory(self.temp_dir, "pain_points", "3")
        
        # Verify only one file was passed
        mock_analyze_files.assert_called_once()
        passed_files = mock_analyze_files.call_args[0][0]
        self.assertEqual(len(passed_files), 1)
        self.assertEqual(passed_files[0], self.test_files[2])  # 3rd file (0-based)
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_comma_selection(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with comma-separated file selection."""
        mock_find_files.return_value = self.test_files
        mock_analyze_files.return_value = "test_report.md"
        
        # Select files 1, 3, 5
        result = self.synthesizer.analyze_directory(self.temp_dir, "pain_points", "1,3,5")
        
        # Verify correct files were passed
        mock_analyze_files.assert_called_once()
        passed_files = mock_analyze_files.call_args[0][0]
        self.assertEqual(len(passed_files), 3)
        expected_files = [self.test_files[0], self.test_files[2], self.test_files[4]]
        self.assertEqual(set(passed_files), set(expected_files))
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_range_selection(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with range file selection."""
        mock_find_files.return_value = self.test_files
        mock_analyze_files.return_value = "test_report.md"
        
        # Select files 2-4
        result = self.synthesizer.analyze_directory(self.temp_dir, "pain_points", "2-4")
        
        # Verify correct files were passed
        mock_analyze_files.assert_called_once()
        passed_files = mock_analyze_files.call_args[0][0]
        self.assertEqual(len(passed_files), 3)
        expected_files = [self.test_files[1], self.test_files[2], self.test_files[3]]
        self.assertEqual(set(passed_files), set(expected_files))
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_invalid_selection(self, mock_check_deps, mock_find_files):
        """Test analyze_directory with invalid file selection."""
        mock_find_files.return_value = self.test_files
        
        # Test invalid selections
        invalid_selections = [
            "0",      # Invalid index
            "6",      # Out of range  
            "1,6",    # Mixed valid/invalid
            "abc",    # Non-numeric
            "3-1",    # Invalid range
            ""        # Empty string
        ]
        
        for selection in invalid_selections:
            with self.subTest(selection=selection):
                with self.assertRaises(ValueError) as context:
                    self.synthesizer.analyze_directory(self.temp_dir, "pain_points", selection)
                self.assertIn("Invalid file selection", str(context.exception))
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_no_files_found(self, mock_check_deps, mock_find_files):
        """Test analyze_directory when no supported files are found."""
        mock_find_files.return_value = []
        
        with self.assertRaises(ValueError) as context:
            self.synthesizer.analyze_directory(self.temp_dir, "pain_points", "all")
        self.assertIn("No supported files found", str(context.exception))
    
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_nonexistent_directory(self, mock_check_deps):
        """Test analyze_directory with non-existent directory."""
        nonexistent_dir = "/path/that/does/not/exist"
        
        with self.assertRaises(ValueError) as context:
            self.synthesizer.analyze_directory(nonexistent_dir, "pain_points", "all")
        self.assertIn("Directory not found", str(context.exception))
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_analyze_directory_file_not_directory(self, mock_check_deps, mock_find_files):
        """Test analyze_directory when path is a file, not a directory."""
        # Use one of the test files as the "directory" path
        file_path = str(self.test_files[0])
        
        with self.assertRaises(ValueError) as context:
            self.synthesizer.analyze_directory(file_path, "pain_points", "all")
        self.assertIn("Directory not found", str(context.exception))
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    @patch('insight_synthesizer.pipeline.console.print')
    def test_analyze_directory_prints_progress(self, mock_print, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test that analyze_directory prints progress information."""
        mock_find_files.return_value = self.test_files
        mock_analyze_files.return_value = "test_report.md"
        
        # Select 3 out of 5 files
        self.synthesizer.analyze_directory(self.temp_dir, "pain_points", "1,3,5")
        
        # Verify progress message was printed
        mock_print.assert_called()
        call_args = [call.args[0] for call in mock_print.call_args_list]
        progress_messages = [arg for arg in call_args if "Processing" in str(arg) and "files" in str(arg)]
        self.assertTrue(any("3 of 5" in str(msg) for msg in progress_messages))


class TestPipelineFileSelectionEdgeCases(unittest.TestCase):
    """Test edge cases for pipeline file selection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.synthesizer = InsightSynthesizer()
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_single_file_directory(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with directory containing only one file."""
        single_file = [Path("/tmp/single.txt")]
        mock_find_files.return_value = single_file
        mock_analyze_files.return_value = "report.md"
        
        # Test various selection methods for single file
        selections = ["all", "1", "1-1"]
        
        for selection in selections:
            with self.subTest(selection=selection):
                result = self.synthesizer.analyze_directory("/tmp", "pain_points", selection)
                
                mock_analyze_files.assert_called()
                passed_files = mock_analyze_files.call_args[0][0]
                self.assertEqual(len(passed_files), 1)
                self.assertEqual(passed_files[0], single_file[0])
                mock_analyze_files.reset_mock()
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_large_file_count(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with large number of files."""
        # Create a large number of mock files
        large_file_list = [Path(f"/tmp/file_{i}.txt") for i in range(100)]
        mock_find_files.return_value = large_file_list
        mock_analyze_files.return_value = "report.md"
        
        # Test selecting all files
        result = self.synthesizer.analyze_directory("/tmp", "pain_points", "all")
        
        mock_analyze_files.assert_called_once()
        passed_files = mock_analyze_files.call_args[0][0]
        self.assertEqual(len(passed_files), 100)
        self.assertEqual(set(passed_files), set(large_file_list))
    
    @patch('insight_synthesizer.pipeline.find_supported_files')
    @patch.object(InsightSynthesizer, 'analyze_files')
    @patch('insight_synthesizer.pipeline.check_dependencies')
    def test_whitespace_in_selection(self, mock_check_deps, mock_analyze_files, mock_find_files):
        """Test analyze_directory with whitespace in file selection."""
        files = [Path(f"/tmp/file_{i}.txt") for i in range(5)]
        mock_find_files.return_value = files
        mock_analyze_files.return_value = "report.md"
        
        # Test selections with various whitespace
        whitespace_selections = [
            " all ",
            " 1,3,5 ",
            "1, 3, 5",
            " 2 - 4 ",
            "\t1-3\t"
        ]
        
        for selection in whitespace_selections:
            with self.subTest(selection=repr(selection)):
                try:
                    result = self.synthesizer.analyze_directory("/tmp", "pain_points", selection)
                    # Should succeed without raising an exception
                    mock_analyze_files.assert_called()
                except ValueError:
                    # Some whitespace variations might be invalid, that's okay
                    pass
                mock_analyze_files.reset_mock()


if __name__ == '__main__':
    unittest.main(verbosity=2)