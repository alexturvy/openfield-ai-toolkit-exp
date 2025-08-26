"""Comprehensive tests for the ThemeValidator class."""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import tempfile
from pathlib import Path
from typing import List, Dict
import requests

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from insight_synthesizer.validation.theme_validator import (
    ThemeValidator, 
    QuoteEvidence, 
    ThemeCoverage, 
    ValidationResult
)
from insight_synthesizer.utils.progress_reporter import ProgressReporter


class TestQuoteEvidence(unittest.TestCase):
    """Test the QuoteEvidence dataclass."""
    
    def test_quote_evidence_creation(self):
        """Test creating QuoteEvidence objects."""
        quote = QuoteEvidence(
            text="This is a sample quote.",
            source_file="interview_1.txt",
            speaker="John Doe",
            confidence=0.85,
            context="Discussing project challenges"
        )
        
        self.assertEqual(quote.text, "This is a sample quote.")
        self.assertEqual(quote.source_file, "interview_1.txt")
        self.assertEqual(quote.speaker, "John Doe")
        self.assertEqual(quote.confidence, 0.85)
        self.assertEqual(quote.context, "Discussing project challenges")
    
    def test_quote_evidence_defaults(self):
        """Test QuoteEvidence with default values."""
        quote = QuoteEvidence(
            text="Another quote",
            source_file="interview_2.txt"
        )
        
        self.assertEqual(quote.text, "Another quote")
        self.assertEqual(quote.source_file, "interview_2.txt")
        self.assertIsNone(quote.speaker)
        self.assertEqual(quote.confidence, 0.0)
        self.assertIsNone(quote.context)


class TestThemeCoverage(unittest.TestCase):
    """Test the ThemeCoverage dataclass."""
    
    def test_theme_coverage_creation(self):
        """Test creating ThemeCoverage objects."""
        quotes = [
            QuoteEvidence("Quote 1", "file1.txt", "Speaker A", 0.8),
            QuoteEvidence("Quote 2", "file2.txt", "Speaker B", 0.7)
        ]
        
        coverage = ThemeCoverage(
            theme_name="Communication Issues",
            quotes=quotes,
            speakers_covered=["Speaker A", "Speaker B"],
            files_covered=["file1.txt", "file2.txt"],
            coverage_score=0.85,
            distribution_quality="good"
        )
        
        self.assertEqual(coverage.theme_name, "Communication Issues")
        self.assertEqual(len(coverage.quotes), 2)
        self.assertEqual(coverage.speakers_covered, ["Speaker A", "Speaker B"])
        self.assertEqual(coverage.files_covered, ["file1.txt", "file2.txt"])
        self.assertEqual(coverage.coverage_score, 0.85)
        self.assertEqual(coverage.distribution_quality, "good")


class TestValidationResult(unittest.TestCase):
    """Test the ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult objects."""
        theme_coverages = [Mock(), Mock()]
        
        result = ValidationResult(
            theme_coverages=theme_coverages,
            overall_quality="excellent",
            total_quotes_extracted=10,
            avg_coverage_score=0.75,
            validation_summary="All themes well supported"
        )
        
        self.assertEqual(len(result.theme_coverages), 2)
        self.assertEqual(result.overall_quality, "excellent")
        self.assertEqual(result.total_quotes_extracted, 10)
        self.assertEqual(result.avg_coverage_score, 0.75)
        self.assertEqual(result.validation_summary, "All themes well supported")


class TestThemeValidator(unittest.TestCase):
    """Comprehensive tests for ThemeValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ThemeValidator()
        self.mock_progress_reporter = Mock(spec=ProgressReporter)
        
        # Sample themes for testing
        self.sample_themes = [
            {
                "theme_name": "Communication Challenges",
                "summary": "Issues with team communication and coordination"
            },
            {
                "theme_name": "Resource Constraints", 
                "summary": "Limited budget and personnel affecting project delivery"
            }
        ]
        
        # Sample file content
        self.sample_content = {
            "interview_1.txt": """
            Interviewer: How has the project been going?
            John: Well, we've had some significant communication challenges. The team 
            doesn't seem to be on the same page, and information isn't flowing properly.
            Sometimes I feel like we're all working in silos.
            
            Interviewer: What about resources?
            John: The budget constraints have been really tough. We simply don't have 
            enough people or money to do everything we want to do.
            """,
            "interview_2.txt": """
            Interviewer: What are the main obstacles you're facing?
            Sarah: Communication is definitely a big issue. We have meetings, but they're
            not effective. People leave confused about what they're supposed to do.
            
            Mary: I agree with Sarah. And we're constantly being asked to do more with less.
            The resource limitations are becoming impossible to work around.
            """
        }
    
    def test_init_without_progress_reporter(self):
        """Test ThemeValidator initialization without progress reporter."""
        validator = ThemeValidator()
        self.assertIsNone(validator.progress_reporter)
        self.assertEqual(validator.original_files, {})
    
    def test_init_with_progress_reporter(self):
        """Test ThemeValidator initialization with progress reporter."""
        validator = ThemeValidator(self.mock_progress_reporter)
        self.assertEqual(validator.progress_reporter, self.mock_progress_reporter)
        self.assertEqual(validator.original_files, {})
    
    @patch('insight_synthesizer.document_processing.file_handlers.extract_text_from_file')
    def test_load_original_files_success(self, mock_extract):
        """Test successful loading of original files."""
        # Setup mock
        mock_extract.side_effect = [
            self.sample_content["interview_1.txt"],
            self.sample_content["interview_2.txt"]
        ]
        
        file_paths = [Path("interview_1.txt"), Path("interview_2.txt")]
        self.validator._load_original_files(file_paths)
        
        self.assertEqual(len(self.validator.original_files), 2)
        self.assertEqual(self.validator.original_files["interview_1.txt"], self.sample_content["interview_1.txt"])
        self.assertEqual(self.validator.original_files["interview_2.txt"], self.sample_content["interview_2.txt"])
        self.assertEqual(mock_extract.call_count, 2)
    
    @patch('insight_synthesizer.document_processing.file_handlers.extract_text_from_file')
    @patch('insight_synthesizer.validation.theme_validator.console.print')
    def test_load_original_files_error(self, mock_console, mock_extract):
        """Test handling of file loading errors."""
        # Setup mock to raise exception
        mock_extract.side_effect = [
            self.sample_content["interview_1.txt"],
            Exception("File not found")
        ]
        
        file_paths = [Path("interview_1.txt"), Path("interview_2.txt")]
        self.validator._load_original_files(file_paths)
        
        # Only first file should be loaded
        self.assertEqual(len(self.validator.original_files), 1)
        self.assertEqual(self.validator.original_files["interview_1.txt"], self.sample_content["interview_1.txt"])
        
        # Error message should be printed
        mock_console.assert_called_once()
        call_args = mock_console.call_args[0][0]
        self.assertIn("Warning: Could not load interview_2.txt", call_args)
    
    def test_calculate_coverage_score_no_quotes(self):
        """Test coverage score calculation with no quotes."""
        score = self.validator._calculate_coverage_score([], [], [])
        self.assertEqual(score, 0.0)
    
    def test_calculate_coverage_score_basic(self):
        """Test basic coverage score calculation."""
        quotes = [
            QuoteEvidence("Quote 1", "file1.txt", "Speaker A", 0.8),
            QuoteEvidence("Quote 2", "file1.txt", "Speaker B", 0.6),
            QuoteEvidence("Quote 3", "file2.txt", "Speaker A", 0.9)
        ]
        speakers = ["Speaker A", "Speaker B"]
        files = ["file1.txt", "file2.txt"]
        
        # Set up original files for file bonus calculation
        self.validator.original_files = {"file1.txt": "content", "file2.txt": "content"}
        
        score = self.validator._calculate_coverage_score(quotes, speakers, files)
        
        # Score should be between 0 and 1
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # With 3 quotes, good confidence, 2 speakers, 2/2 files, should be relatively high
        self.assertGreater(score, 0.6)
    
    def test_calculate_coverage_score_max_values(self):
        """Test coverage score calculation with optimal values."""
        quotes = [QuoteEvidence(f"Quote {i}", f"file{i}.txt", f"Speaker {i}", 1.0) for i in range(5)]
        speakers = [f"Speaker {i}" for i in range(5)]
        files = [f"file{i}.txt" for i in range(3)]
        
        # Set up original files
        self.validator.original_files = {f"file{i}.txt": "content" for i in range(3)}
        
        score = self.validator._calculate_coverage_score(quotes, speakers, files)
        
        # Should be very high with optimal inputs
        self.assertGreater(score, 0.8)
        self.assertLessEqual(score, 1.0)
    
    def test_assess_distribution_quality(self):
        """Test distribution quality assessment."""
        # Excellent case
        quality = self.validator._assess_distribution_quality(0.85, 3, 3)
        self.assertEqual(quality, "excellent")
        
        # Good case
        quality = self.validator._assess_distribution_quality(0.7, 2, 2)
        self.assertEqual(quality, "good")
        
        # Limited case
        quality = self.validator._assess_distribution_quality(0.5, 1, 1)
        self.assertEqual(quality, "limited")
        
        # Poor case
        quality = self.validator._assess_distribution_quality(0.2, 0, 1)
        self.assertEqual(quality, "poor")
    
    def test_calculate_overall_metrics_empty(self):
        """Test overall metrics calculation with empty theme coverages."""
        result = self.validator._calculate_overall_metrics([])
        
        self.assertEqual(result.theme_coverages, [])
        self.assertEqual(result.overall_quality, "poor")
        self.assertEqual(result.total_quotes_extracted, 0)
        self.assertEqual(result.avg_coverage_score, 0.0)
        self.assertEqual(result.validation_summary, "No themes to validate")
    
    def test_calculate_overall_metrics_with_themes(self):
        """Test overall metrics calculation with theme coverages."""
        # Create mock theme coverages
        theme_coverages = [
            Mock(quotes=[Mock(), Mock()], coverage_score=0.8, distribution_quality="excellent"),
            Mock(quotes=[Mock(), Mock(), Mock()], coverage_score=0.7, distribution_quality="good"),
            Mock(quotes=[Mock()], coverage_score=0.5, distribution_quality="limited")
        ]
        
        result = self.validator._calculate_overall_metrics(theme_coverages)
        
        self.assertEqual(len(result.theme_coverages), 3)
        self.assertEqual(result.total_quotes_extracted, 6)  # 2 + 3 + 1
        self.assertAlmostEqual(result.avg_coverage_score, 0.667, places=2)  # (0.8 + 0.7 + 0.5) / 3
        self.assertIn(result.overall_quality, ["excellent", "good", "adequate", "needs_improvement"])
    
    def test_generate_validation_summary(self):
        """Test validation summary generation."""
        theme_coverages = [
            Mock(coverage_score=0.8),
            Mock(coverage_score=0.6),
            Mock(coverage_score=0.4)
        ]
        
        summary = self.validator._generate_validation_summary(theme_coverages, 0.6, "good")
        
        self.assertIsInstance(summary, str)
        self.assertIn("1/3 themes are well-supported", summary)  # Only first theme >= 0.7
        self.assertIn("60.0%", summary)  # Average coverage
        self.assertIn("good coverage", summary)  # Quality description
    
    @patch('requests.post')
    def test_extract_quotes_for_theme_success(self, mock_post):
        """Test successful quote extraction from LLM."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': json.dumps({
                'quotes': [
                    {
                        'text': 'Communication is definitely a big issue.',
                        'speaker': 'Sarah',
                        'confidence': 0.85,
                        'context': 'Discussing project obstacles'
                    },
                    {
                        'text': 'We have meetings, but they are not effective.',
                        'speaker': 'Sarah',
                        'confidence': 0.75,
                        'context': 'Meeting effectiveness concerns'
                    }
                ]
            })
        }
        mock_post.return_value = mock_response
        
        quotes = self.validator._extract_quotes_for_theme(
            "Communication Challenges",
            "Issues with team communication",
            self.sample_content["interview_2.txt"],
            "interview_2.txt"
        )
        
        self.assertEqual(len(quotes), 2)
        self.assertEqual(quotes[0].text, 'Communication is definitely a big issue.')
        self.assertEqual(quotes[0].speaker, 'Sarah')
        self.assertEqual(quotes[0].confidence, 0.85)
        self.assertEqual(quotes[0].source_file, 'interview_2.txt')
        self.assertEqual(quotes[0].context, 'Discussing project obstacles')
        
        # Verify API call was made with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('/api/generate', call_args[0][0])
        self.assertIn('Communication Challenges', call_args[1]['json']['prompt'])
    
    @patch('requests.post')
    @patch('insight_synthesizer.validation.theme_validator.console.print')
    def test_extract_quotes_for_theme_api_error(self, mock_console, mock_post):
        """Test quote extraction with API error."""
        # Mock API error
        mock_post.side_effect = requests.RequestException("API Error")
        
        quotes = self.validator._extract_quotes_for_theme(
            "Communication Challenges",
            "Issues with team communication",
            self.sample_content["interview_2.txt"],
            "interview_2.txt"
        )
        
        self.assertEqual(quotes, [])
        mock_console.assert_called_once()
        call_args = mock_console.call_args[0][0]
        self.assertIn("Warning: Quote extraction failed", call_args)
    
    @patch('requests.post')
    @patch('insight_synthesizer.validation.theme_validator.console.print')
    def test_extract_quotes_for_theme_json_error(self, mock_console, mock_post):
        """Test quote extraction with JSON parsing error."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'response': 'invalid json'}
        mock_post.return_value = mock_response
        
        quotes = self.validator._extract_quotes_for_theme(
            "Communication Challenges",
            "Issues with team communication",
            self.sample_content["interview_2.txt"],
            "interview_2.txt"
        )
        
        self.assertEqual(quotes, [])
        mock_console.assert_called_once()
    
    @patch('requests.post')
    def test_extract_quotes_long_content(self, mock_post):
        """Test quote extraction with long content (> 8000 chars)."""
        # Create long content
        long_content = "A" * 10000
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'response': json.dumps({'quotes': []})}
        mock_post.return_value = mock_response
        
        self.validator._extract_quotes_for_theme(
            "Test Theme",
            "Test summary",
            long_content,
            "test_file.txt"
        )
        
        # Verify content was truncated to 8000 chars in the prompt
        call_args = mock_post.call_args[1]['json']['prompt']
        content_in_prompt = call_args.split('TRANSCRIPT CONTENT:\n')[1].split('\n\nFind and extract')[0]
        self.assertEqual(len(content_in_prompt), 8000)
    
    @patch.object(ThemeValidator, '_extract_quotes_for_theme')
    @patch.object(ThemeValidator, '_load_original_files')
    def test_validate_single_theme(self, mock_load, mock_extract):
        """Test validation of a single theme."""
        # Setup mocks
        self.validator.original_files = self.sample_content
        mock_extract.side_effect = [
            [QuoteEvidence("Quote 1", "interview_1.txt", "John", 0.8)],
            [QuoteEvidence("Quote 2", "interview_2.txt", "Sarah", 0.7)]
        ]
        
        theme = {
            "theme_name": "Communication Challenges",
            "summary": "Issues with team communication and coordination"
        }
        
        coverage = self.validator._validate_single_theme(theme, 1)
        
        self.assertEqual(coverage.theme_name, "Communication Challenges")
        self.assertEqual(len(coverage.quotes), 2)
        self.assertEqual(set(coverage.speakers_covered), {"John", "Sarah"})
        self.assertEqual(set(coverage.files_covered), {"interview_1.txt", "interview_2.txt"})
        self.assertGreater(coverage.coverage_score, 0)
        self.assertIn(coverage.distribution_quality, ["excellent", "good", "limited", "poor"])
    
    @patch.object(ThemeValidator, '_validate_single_theme')
    @patch.object(ThemeValidator, '_load_original_files')
    def test_validate_themes_integration(self, mock_load, mock_validate):
        """Test full theme validation integration."""
        # Setup validator with progress reporter
        validator = ThemeValidator(self.mock_progress_reporter)
        
        # Mock single theme validation
        mock_coverage1 = Mock(quotes=[Mock(), Mock()], coverage_score=0.8, distribution_quality="excellent")
        mock_coverage2 = Mock(quotes=[Mock()], coverage_score=0.6, distribution_quality="good")
        mock_validate.side_effect = [mock_coverage1, mock_coverage2]
        
        file_paths = [Path("interview_1.txt"), Path("interview_2.txt")]
        
        result = validator.validate_themes(self.sample_themes, file_paths)
        
        # Verify result structure
        self.assertIsInstance(result, ValidationResult)
        self.assertEqual(len(result.theme_coverages), 2)
        self.assertEqual(result.total_quotes_extracted, 3)  # 2 + 1
        self.assertGreater(result.avg_coverage_score, 0)
        
        # Verify progress reporter calls
        self.mock_progress_reporter.start_process.assert_called_once()
        self.mock_progress_reporter.update_metrics.assert_called_once()
        self.mock_progress_reporter.complete_process.assert_called_once()
    
    def test_validate_themes_no_progress_reporter(self):
        """Test theme validation without progress reporter."""
        with patch.object(self.validator, '_load_original_files') as mock_load, \
             patch.object(self.validator, '_validate_single_theme') as mock_validate:
            
            # Mock single theme validation
            mock_coverage = Mock(quotes=[Mock()], coverage_score=0.5, distribution_quality="limited")
            mock_validate.return_value = mock_coverage
            
            file_paths = [Path("test.txt")]
            result = self.validator.validate_themes(self.sample_themes, file_paths)
            
            self.assertIsInstance(result, ValidationResult)
            # No progress reporter calls should be made
            # (No assertions needed since no mock progress reporter was set up)


class TestThemeValidatorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        self.validator = ThemeValidator()
    
    def test_empty_theme_name(self):
        """Test validation with empty theme name."""
        theme = {"summary": "Some summary"}
        coverage = self.validator._validate_single_theme(theme, 1)
        self.assertEqual(coverage.theme_name, "Theme 1")  # Should use fallback
    
    def test_missing_theme_summary(self):
        """Test validation with missing theme summary."""
        theme = {"theme_name": "Test Theme"}
        # Should not crash, should use empty string for summary
        coverage = self.validator._validate_single_theme(theme, 1)
        self.assertEqual(coverage.theme_name, "Test Theme")
    
    def test_no_quotes_extracted(self):
        """Test behavior when no quotes are extracted."""
        with patch.object(self.validator, '_extract_quotes_for_theme', return_value=[]):
            self.validator.original_files = {"test.txt": "content"}
            
            theme = {"theme_name": "Test Theme", "summary": "Test"}
            coverage = self.validator._validate_single_theme(theme, 1)
            
            self.assertEqual(len(coverage.quotes), 0)
            self.assertEqual(coverage.speakers_covered, [])
            self.assertEqual(coverage.files_covered, [])
            self.assertEqual(coverage.coverage_score, 0.0)
            self.assertEqual(coverage.distribution_quality, "poor")
    
    def test_quotes_without_speakers(self):
        """Test handling of quotes without speaker information."""
        quotes = [
            QuoteEvidence("Anonymous quote 1", "file1.txt", None, 0.7),
            QuoteEvidence("Anonymous quote 2", "file1.txt", "", 0.6)
        ]
        
        speakers = [q.speaker for q in quotes if q.speaker]  # Should be empty
        files = ["file1.txt"]
        
        self.validator.original_files = {"file1.txt": "content"}
        coverage_score = self.validator._calculate_coverage_score(quotes, speakers, files)
        
        # Should still calculate a reasonable score even without speakers
        self.assertGreater(coverage_score, 0.0)
    
    def test_malformed_quote_data(self):
        """Test handling of malformed quote data from LLM."""
        with patch('requests.post') as mock_post:
            # Mock response with missing fields
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'response': json.dumps({
                    'quotes': [
                        {'text': 'Valid quote', 'confidence': 0.8},  # Missing speaker
                        {'speaker': 'John'},  # Missing text
                        {}  # Empty quote object
                    ]
                })
            }
            mock_post.return_value = mock_response
            
            quotes = self.validator._extract_quotes_for_theme(
                "Test Theme", "Test summary", "content", "file.txt"
            )
            
            # Should handle malformed data gracefully
            self.assertEqual(len(quotes), 3)
            self.assertEqual(quotes[0].text, 'Valid quote')
            self.assertEqual(quotes[1].text, '')  # Default value
            self.assertEqual(quotes[2].text, '')  # Default value


class TestIntegrationWithRealData(unittest.TestCase):
    """Integration tests with realistic data scenarios."""
    
    def setUp(self):
        self.validator = ThemeValidator()
    
    def create_temp_files(self) -> List[Path]:
        """Create temporary files for testing."""
        temp_files = []
        
        # Create realistic interview content
        interview_contents = [
            """
            Interview with Project Manager Sarah Johnson
            
            Interviewer: What have been the biggest challenges in this project?
            
            Sarah: The main issue has been communication breakdowns. We have team 
            members in different time zones, and information doesn't flow smoothly. 
            Sometimes decisions are made in meetings that not everyone can attend.
            
            Interviewer: How has this affected project delivery?
            
            Sarah: We've had several delays because people weren't clear on 
            requirements. The lack of proper documentation has made things worse.
            """,
            """
            Interview with Developer Mike Chen
            
            Interviewer: What's your perspective on the current project state?
            
            Mike: From a technical standpoint, we're dealing with a lot of technical debt.
            The codebase is becoming harder to maintain, and we're spending more time
            on bug fixes than new features.
            
            Interviewer: What about team dynamics?
            
            Mike: Communication could be better. Sometimes I implement something, and 
            then find out the requirements changed without anyone telling the dev team.
            """
        ]
        
        for i, content in enumerate(interview_contents):
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(content)
            temp_file.close()
            temp_files.append(Path(temp_file.name))
        
        return temp_files
    
    def tearDown(self):
        """Clean up temporary files."""
        # Note: In a real test, you'd clean up temp files here
        pass
    
    @patch('insight_synthesizer.document_processing.file_handlers.extract_text_from_file')
    @patch('requests.post')
    def test_realistic_validation_scenario(self, mock_post, mock_extract):
        """Test validation with realistic themes and content."""
        # Setup file extraction mock
        interview_contents = [
            "Sarah: Communication breakdowns are our main issue...",
            "Mike: Technical debt is becoming a serious problem..."
        ]
        mock_extract.side_effect = interview_contents
        
        # Mock realistic LLM responses
        def mock_api_call(*args, **kwargs):
            prompt = kwargs['json']['prompt']
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if 'Communication' in prompt:
                mock_response.json.return_value = {
                    'response': json.dumps({
                        'quotes': [
                            {
                                'text': 'Communication breakdowns are our main issue',
                                'speaker': 'Sarah',
                                'confidence': 0.9,
                                'context': 'Discussing project challenges'
                            }
                        ]
                    })
                }
            else:  # Technical debt theme
                mock_response.json.return_value = {
                    'response': json.dumps({
                        'quotes': [
                            {
                                'text': 'Technical debt is becoming a serious problem',
                                'speaker': 'Mike', 
                                'confidence': 0.85,
                                'context': 'Code quality concerns'
                            }
                        ]
                    })
                }
            return mock_response
        
        mock_post.side_effect = mock_api_call
        
        # Realistic themes
        themes = [
            {
                'theme_name': 'Communication Issues',
                'summary': 'Breakdown in team communication affecting project coordination'
            },
            {
                'theme_name': 'Technical Debt',
                'summary': 'Accumulating technical debt impacting development velocity'
            }
        ]
        
        file_paths = [Path('interview1.txt'), Path('interview2.txt')]
        
        result = self.validator.validate_themes(themes, file_paths)
        
        # Verify realistic results
        self.assertEqual(len(result.theme_coverages), 2)
        self.assertGreater(result.total_quotes_extracted, 0)
        self.assertGreater(result.avg_coverage_score, 0)
        self.assertIn(result.overall_quality, ['excellent', 'good', 'adequate', 'needs_improvement'])
        
        # Verify each theme has appropriate coverage
        for coverage in result.theme_coverages:
            self.assertIsInstance(coverage.theme_name, str)
            self.assertIsInstance(coverage.quotes, list)
            self.assertIsInstance(coverage.coverage_score, float)
            self.assertIn(coverage.distribution_quality, ['excellent', 'good', 'limited', 'poor'])


if __name__ == '__main__':
    unittest.main()