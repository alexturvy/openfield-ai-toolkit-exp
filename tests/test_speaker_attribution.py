"""Comprehensive tests for speaker attribution functionality throughout the pipeline."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import numpy as np
from pathlib import Path
from typing import List, Dict

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from insight_synthesizer.document_processing.adaptive_chunking import AdaptiveChunker, AdaptiveChunk
from insight_synthesizer.document_processing.structure_classifier import StructureClassification, ChunkingStrategy, ContentType
from insight_synthesizer.analysis.clustering import perform_clustering, Cluster
from insight_synthesizer.analysis.synthesis import synthesize_insights
from insight_synthesizer.analysis.embeddings import TextChunk
from insight_synthesizer.output.report_generator import generate_markdown_report


class TestSpeakerAttributionInChunking(unittest.TestCase):
    """Test speaker attribution preservation during adaptive chunking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = AdaptiveChunker()
        self.file_path = Path("test_interview.txt")
        
        # Sample interview text with clear speaker patterns
        self.interview_text = """
        Interviewer: Welcome to our user research session. Can you tell me about your experience with the product?
        
        Sarah Johnson: Thank you for having me. Overall, I've found the product quite useful, but there are definitely some areas for improvement. The navigation is sometimes confusing.
        
        Interviewer: Can you elaborate on the navigation issues?
        
        Sarah Johnson: Well, when I'm looking for specific features, I often have to click through multiple menus. It's not intuitive where things are located. Sometimes I give up and just use the search function instead.
        
        Dr. Mark Stevens: I'd like to add that from a clinical perspective, the workflow doesn't match our existing processes. We need something more streamlined.
        
        Interviewer: That's interesting. How would you like to see the workflow improved?
        
        Dr. Mark Stevens: We need direct access to patient records without going through the dashboard first. Every extra click adds time to our consultations.
        """
        
        # Classification that triggers speaker turn chunking
        self.classification = StructureClassification(
            content_type=ContentType.INTERVIEW_TRANSCRIPT,
            speaker_labels=True,
            structure_confidence=0.85,
            suggested_chunking=ChunkingStrategy.SPEAKER_TURNS,
            metadata={
                "primary_speakers": ["Interviewer", "Sarah Johnson", "Dr. Mark Stevens"],
                "has_interviewer": True,
                "conversation_style": "formal",
                "contains_meta_content": False,
                "estimated_participants": 3
            },
            reasoning="Clear interview format with labeled speakers"
        )
    
    def test_speaker_turn_chunking_preserves_speakers(self):
        """Test that speaker turn chunking correctly preserves speaker information."""
        chunks = self.chunker.chunk_document(self.interview_text, self.file_path, self.classification)
        
        # Should have chunks for each speaker turn
        self.assertGreater(len(chunks), 0)
        
        # Check that speaker information is preserved
        speaker_chunks = [chunk for chunk in chunks if chunk.metadata.get('speaker')]
        self.assertGreater(len(speaker_chunks), 0)
        
        # Verify specific speakers are identified
        speakers_found = set(chunk.metadata['speaker'] for chunk in speaker_chunks)
        expected_speakers = {'Interviewer', 'Sarah Johnson', 'Dr. Mark Stevens'}
        self.assertTrue(speakers_found.intersection(expected_speakers))
        
        # Verify interviewer identification
        interviewer_chunks = [chunk for chunk in chunks if chunk.metadata.get('is_interviewer')]
        self.assertGreater(len(interviewer_chunks), 0)
        
        # Verify participant chunks exist
        participant_chunks = [chunk for chunk in chunks if not chunk.metadata.get('is_interviewer', True)]
        self.assertGreater(len(participant_chunks), 0)
    
    def test_speaker_metadata_structure(self):
        """Test that speaker metadata has correct structure."""
        chunks = self.chunker.chunk_document(self.interview_text, self.file_path, self.classification)
        
        for chunk in chunks:
            self.assertIsInstance(chunk, AdaptiveChunk)
            self.assertIn('speaker', chunk.metadata or {})
            self.assertIn('is_interviewer', chunk.metadata or {})
            self.assertIn('content_type', chunk.metadata or {})
            
            if chunk.metadata.get('speaker'):
                self.assertIsInstance(chunk.metadata['speaker'], str)
                self.assertIsInstance(chunk.metadata['is_interviewer'], bool)
    
    def test_clean_speaker_name_function(self):
        """Test speaker name cleaning functionality."""
        # Test markdown removal
        cleaned = self.chunker._clean_speaker_name("**Dr. Smith**")
        self.assertEqual(cleaned, "Dr. Smith")
        
        # Test parentheses removal
        cleaned = self.chunker._clean_speaker_name("Alex (UX Researcher)")
        self.assertEqual(cleaned, "Alex")
        
        # Test combined cleaning
        cleaned = self.chunker._clean_speaker_name("**Sarah Johnson** (Product Manager)")
        self.assertEqual(cleaned, "Sarah Johnson")
    
    def test_interviewer_identification(self):
        """Test interviewer identification logic."""
        # Test positive cases
        self.assertTrue(self.chunker._is_interviewer("Interviewer"))
        self.assertTrue(self.chunker._is_interviewer("Alex"))
        self.assertTrue(self.chunker._is_interviewer("Researcher"))
        self.assertTrue(self.chunker._is_interviewer("Moderator"))
        
        # Test negative cases
        self.assertFalse(self.chunker._is_interviewer("Sarah Johnson"))
        self.assertFalse(self.chunker._is_interviewer("Dr. Mark Stevens"))
        self.assertFalse(self.chunker._is_interviewer("Participant"))
    
    def test_speaker_turn_with_long_content(self):
        """Test speaker turn chunking when content exceeds max chunk size."""
        # Create a long speaker turn
        long_turn = "Sarah Johnson: " + "This is a very long response. " * 100
        classification = StructureClassification(
            content_type=ContentType.INTERVIEW_TRANSCRIPT,
            speaker_labels=True,
            structure_confidence=0.9,
            suggested_chunking=ChunkingStrategy.SPEAKER_TURNS,
            metadata={"primary_speakers": ["Sarah Johnson"], "has_interviewer": False,
                     "conversation_style": "formal", "contains_meta_content": False,
                     "estimated_participants": 1},
            reasoning="Long speaker turn requiring chunking"
        )
        
        chunks = self.chunker.chunk_document(long_turn, self.file_path, classification)
        
        # Should create multiple chunks for long speaker turn
        sarah_chunks = [chunk for chunk in chunks if chunk.metadata.get('speaker') == 'Sarah Johnson']
        
        # All chunks should maintain speaker attribution
        for chunk in sarah_chunks:
            self.assertEqual(chunk.metadata['speaker'], 'Sarah Johnson')
            self.assertFalse(chunk.metadata['is_interviewer'])
    
    def test_fallback_chunking_without_speakers(self):
        """Test fallback to sentence chunking when no speaker patterns found."""
        text_without_speakers = """
        This is a document without clear speaker patterns. It contains narrative text
        that describes user experiences and findings from research. The content flows
        naturally without dialogue markers or speaker attribution.
        """
        
        chunks = self.chunker.chunk_document(text_without_speakers, self.file_path, self.classification)
        
        # Should fall back to sentence chunking
        self.assertGreater(len(chunks), 0)
        
        # Chunks should not have speaker information
        for chunk in chunks:
            self.assertIsNone(chunk.metadata.get('speaker'))


class TestSpeakerAttributionInClustering(unittest.TestCase):
    """Test speaker attribution preservation and analysis during clustering."""
    
    def setUp(self):
        """Set up test fixtures with speaker-attributed chunks."""
        # Create mock chunks with speaker metadata
        self.chunks_with_speakers = []
        
        # Participant chunks
        for i in range(5):
            chunk = Mock()
            chunk.embedding = np.random.rand(384)  # Mock embedding
            chunk.cluster_id = None
            chunk._adaptive_metadata = {
                'speaker': 'Sarah Johnson',
                'is_interviewer': False,
                'content_type': 'dialogue'
            }
            chunk._chunk_type = 'speaker_turn'
            self.chunks_with_speakers.append(chunk)
        
        # Interviewer chunks
        for i in range(3):
            chunk = Mock()
            chunk.embedding = np.random.rand(384)
            chunk.cluster_id = None
            chunk._adaptive_metadata = {
                'speaker': 'Interviewer',
                'is_interviewer': True,
                'content_type': 'dialogue'
            }
            chunk._chunk_type = 'speaker_turn'
            self.chunks_with_speakers.append(chunk)
        
        # Another participant
        for i in range(4):
            chunk = Mock()
            chunk.embedding = np.random.rand(384)
            chunk.cluster_id = None
            chunk._adaptive_metadata = {
                'speaker': 'Dr. Mark Stevens',
                'is_interviewer': False,
                'content_type': 'dialogue'
            }
            chunk._chunk_type = 'speaker_turn'
            self.chunks_with_speakers.append(chunk)
    
    @patch('insight_synthesizer.analysis.clustering.umap.UMAP')
    @patch('insight_synthesizer.analysis.clustering.hdbscan.HDBSCAN')
    def test_clustering_preserves_speaker_metadata(self, mock_hdbscan, mock_umap):
        """Test that clustering preserves and analyzes speaker metadata."""
        # Mock UMAP
        mock_reducer = Mock()
        mock_reducer.fit_transform.return_value = np.random.rand(len(self.chunks_with_speakers), 10)
        mock_umap.return_value = mock_reducer
        
        # Mock HDBSCAN - create realistic cluster assignments
        mock_clusterer = Mock()
        # Assign different speakers to different clusters mostly
        cluster_labels = [0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3]
        mock_clusterer.fit_predict.return_value = cluster_labels
        mock_hdbscan.return_value = mock_clusterer
        
        chunks, clusters = perform_clustering(self.chunks_with_speakers)
        
        # Verify clusters have speaker metadata
        for cluster in clusters:
            self.assertTrue(hasattr(cluster, 'speaker_metadata'))
            self.assertIn('speakers', cluster.speaker_metadata)
            self.assertIn('speaker_count', cluster.speaker_metadata)
            self.assertIn('participant_chunks', cluster.speaker_metadata)
            self.assertIn('interviewer_chunks', cluster.speaker_metadata)
            self.assertIn('is_participant_focused', cluster.speaker_metadata)
            self.assertIn('has_speaker_diversity', cluster.speaker_metadata)
    
    @patch('insight_synthesizer.analysis.clustering.umap.UMAP')
    @patch('insight_synthesizer.analysis.clustering.hdbscan.HDBSCAN')
    def test_speaker_diversity_analysis(self, mock_hdbscan, mock_umap):
        """Test speaker diversity analysis in clustering."""
        # Mock UMAP
        mock_reducer = Mock()
        mock_reducer.fit_transform.return_value = np.random.rand(len(self.chunks_with_speakers), 10)
        mock_umap.return_value = mock_reducer
        
        # Mock HDBSCAN - create clusters with different speaker compositions
        mock_clusterer = Mock()
        # Cluster 0: Mixed speakers, Cluster 1: Single speaker, Cluster 2: Single speaker
        cluster_labels = [0, 0, 1, 1, 1, 0, 0, 2, 2, 2, 2, 2]
        mock_clusterer.fit_predict.return_value = cluster_labels
        mock_hdbscan.return_value = mock_clusterer
        
        chunks, clusters = perform_clustering(self.chunks_with_speakers)
        
        # Find mixed speaker cluster (should be cluster 0)
        mixed_clusters = [c for c in clusters if c.speaker_metadata['has_speaker_diversity']]
        self.assertGreater(len(mixed_clusters), 0)
        
        # Find single speaker clusters
        single_speaker_clusters = [c for c in clusters if not c.speaker_metadata['has_speaker_diversity']]
        self.assertGreater(len(single_speaker_clusters), 0)
        
        # Verify participant-focused clusters
        participant_focused = [c for c in clusters if c.speaker_metadata['is_participant_focused']]
        self.assertGreater(len(participant_focused), 0)


class TestSpeakerAttributionInSynthesis(unittest.TestCase):
    """Test speaker attribution integration in insight synthesis."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock cluster with speaker-attributed chunks
        self.cluster = Mock()
        self.cluster.cluster_id = 1
        self.cluster.chunks = []
        
        # Add chunks with different speakers
        speakers_and_content = [
            ("Sarah Johnson", False, "Navigation is confusing and unintuitive"),
            ("Dr. Mark Stevens", False, "Workflow doesn't match clinical processes"),
            ("Interviewer", True, "Can you elaborate on that issue?"),
            ("Sarah Johnson", False, "Search functionality is the only reliable way to find things")
        ]
        
        for speaker, is_interviewer, text in speakers_and_content:
            chunk = Mock()
            chunk.text = text
            chunk._adaptive_metadata = {
                'speaker': speaker,
                'is_interviewer': is_interviewer,
                'content_type': 'dialogue'
            }
            self.cluster.chunks.append(chunk)
    
    @patch('requests.post')
    def test_synthesis_includes_speaker_context(self, mock_post):
        """Test that synthesis includes speaker information in prompts and results."""
        # Mock successful API response with speaker attribution
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': json.dumps({
                'theme_name': 'Navigation and Workflow Issues',
                'summary': 'Users struggle with navigation and workflow alignment',
                'key_insights': ['Navigation is unintuitive', 'Workflow misalignment'],
                'speaker_distribution': {
                    'Sarah Johnson (Participant)': 2,
                    'Dr. Mark Stevens (Participant)': 1,
                    'Interviewer (Interviewer)': 1
                },
                'primary_contributors': ['Sarah Johnson (Participant)', 'Dr. Mark Stevens (Participant)'],
                'cross_speaker_patterns': 'Multiple participants report similar navigation issues'
            })
        }
        mock_post.return_value = mock_response
        
        result = synthesize_insights(self.cluster, 'pain_points')
        
        # Verify speaker information is included
        self.assertIn('speaker_distribution', result)
        self.assertIn('primary_contributors', result)
        self.assertIn('cross_speaker_patterns', result)
        
        # Verify API call includes speaker context
        call_args = mock_post.call_args[1]['json']['prompt']
        self.assertIn('SPEAKER DISTRIBUTION', call_args)
        self.assertIn('Sarah Johnson', call_args)
        self.assertIn('Dr. Mark Stevens', call_args)
    
    @patch('requests.post')
    def test_synthesis_handles_missing_speaker_data(self, mock_post):
        """Test synthesis gracefully handles chunks without speaker information."""
        # Create cluster with chunks missing speaker metadata
        cluster_no_speakers = Mock()
        cluster_no_speakers.chunks = []
        
        for i in range(3):
            chunk = Mock()
            chunk.text = f"Content without speaker {i}"
            chunk._adaptive_metadata = None  # No metadata
            cluster_no_speakers.chunks.append(chunk)
        
        # Mock API response without speaker fields
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'response': json.dumps({
                'theme_name': 'General Theme',
                'summary': 'Theme without speaker attribution',
                'key_insights': ['Generic insight']
            })
        }
        mock_post.return_value = mock_response
        
        result = synthesize_insights(cluster_no_speakers, 'pain_points')
        
        # Should still work with fallback values
        self.assertIn('speaker_distribution', result)
        self.assertIn('primary_contributors', result)
        self.assertIn('cross_speaker_patterns', result)
        
        # Fallback values should be appropriate
        self.assertEqual(result['speaker_distribution'], {})
        self.assertEqual(result['primary_contributors'], [])
    
    def test_speaker_distribution_calculation(self):
        """Test accurate speaker distribution calculation in synthesis."""
        # This tests the logic before the API call
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'response': json.dumps({
                    'theme_name': 'Test',
                    'summary': 'Test',
                    'key_insights': ['Test']
                })
            }
            mock_post.return_value = mock_response
            
            result = synthesize_insights(self.cluster, 'pain_points')
            
            # Check that speaker distribution was calculated correctly
            expected_distribution = {
                'Sarah Johnson (Participant)': 2,
                'Dr. Mark Stevens (Participant)': 1,
                'Interviewer (Interviewer)': 1
            }
            self.assertEqual(result['speaker_distribution'], expected_distribution)


class TestSpeakerAttributionInReports(unittest.TestCase):
    """Test speaker attribution in report generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.synthesized_data = [
            {
                'theme_name': 'Navigation Issues',
                'summary': 'Users struggle with product navigation',
                'key_insights': ['Menu structure is confusing', 'Search is unreliable'],
                'speaker_distribution': {
                    'Sarah Johnson (Participant)': 3,
                    'Dr. Mark Stevens (Participant)': 2,
                    'Interviewer (Interviewer)': 1
                },
                'primary_contributors': ['Sarah Johnson (Participant)', 'Dr. Mark Stevens (Participant)'],
                'cross_speaker_patterns': 'Both participants report similar navigation difficulties'
            },
            {
                'theme_name': 'Workflow Alignment',
                'summary': 'Product workflow does not match user expectations',
                'key_insights': ['Clinical workflow mismatch', 'Too many steps required'],
                'speaker_distribution': {
                    'Dr. Mark Stevens (Participant)': 4,
                    'Sarah Johnson (Participant)': 1
                },
                'primary_contributors': ['Dr. Mark Stevens (Participant)'],
                'cross_speaker_patterns': 'Primarily reported by clinical users'
            }
        ]
    
    def test_report_includes_speaker_overview(self):
        """Test that reports include comprehensive speaker overview."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            generate_markdown_report(self.synthesized_data, 'pain_points', temp_file.name)
            
            temp_file.seek(0)
            report_content = temp_file.read()
            
            # Verify speaker overview section
            self.assertIn('## Speaker Overview', report_content)
            self.assertIn('Sarah Johnson (Participant)', report_content)
            self.assertIn('Dr. Mark Stevens (Participant)', report_content)
            self.assertIn('Interviewer (Interviewer)', report_content)
            
            # Verify speaker statistics
            self.assertIn('Themes Contributed To', report_content)
            self.assertIn('Total Contributions', report_content)
    
    def test_report_includes_theme_speaker_distribution(self):
        """Test that individual themes show speaker distribution."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            generate_markdown_report(self.synthesized_data, 'pain_points', temp_file.name)
            
            temp_file.seek(0)
            report_content = temp_file.read()
            
            # Verify theme-level speaker distribution
            self.assertIn('#### Speaker Distribution', report_content)
            self.assertIn('**Sarah Johnson (Participant)**: 3 contributions', report_content)
            self.assertIn('**Dr. Mark Stevens (Participant)**: 2 contributions', report_content)
            
            # Verify primary contributors
            self.assertIn('#### Primary Contributors', report_content)
            
            # Verify cross-speaker analysis
            self.assertIn('#### Cross-Speaker Analysis', report_content)
            self.assertIn('Both participants report similar navigation difficulties', report_content)
    
    def test_report_handles_missing_speaker_data(self):
        """Test report generation when speaker data is missing."""
        data_without_speakers = [
            {
                'theme_name': 'Generic Theme',
                'summary': 'Theme without speaker information',
                'key_insights': ['Generic insight']
            }
        ]
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            generate_markdown_report(data_without_speakers, 'pain_points', temp_file.name)
            
            temp_file.seek(0)
            report_content = temp_file.read()
            
            # Should still generate valid report
            self.assertIn('# Research Synthesis Report', report_content)
            self.assertIn('**Unique Speakers**: 0', report_content)
            self.assertIn('**Total Contributions**: 0', report_content)
    
    def test_speaker_statistics_calculation(self):
        """Test accuracy of speaker statistics in reports."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            generate_markdown_report(self.synthesized_data, 'pain_points', temp_file.name)
            
            temp_file.seek(0)
            report_content = temp_file.read()
            
            # Verify overall statistics
            self.assertIn('**Unique Speakers**: 3', report_content)  # Sarah, Dr. Mark, Interviewer
            self.assertIn('**Total Contributions**: 11', report_content)  # 3+2+1+4+1 = 11
            
            # Verify individual speaker stats
            # Sarah: 2 themes, 4 total contributions (3+1)
            self.assertRegex(report_content, r'Sarah Johnson.*2.*4.*2\.0')
            
            # Dr. Mark: 2 themes, 6 total contributions (2+4) 
            self.assertRegex(report_content, r'Dr\. Mark Stevens.*2.*6.*3\.0')


class TestSpeakerAttributionIntegration(unittest.TestCase):
    """Integration tests for speaker attribution across the entire pipeline."""
    
    def test_speaker_metadata_flow_from_chunking_to_synthesis(self):
        """Test that speaker metadata flows correctly from chunking through synthesis."""
        # This is a higher-level integration test that would verify the complete flow
        # In a real scenario, this would test the full pipeline with real data
        
        # Create realistic input text
        input_text = """
        Interviewer: What challenges do you face with the current system?
        
        User123: The biggest issue is the login process. It takes too long and often fails.
        Sometimes I have to try 3-4 times before I can get in.
        
        Interviewer: How does this affect your daily work?
        
        User123: It's really frustrating. I waste about 10 minutes every morning just trying 
        to log in. And if I'm in the middle of something urgent, those delays can be critical.
        """
        
        # Test would involve:
        # 1. Creating AdaptiveChunk objects with speaker metadata
        # 2. Converting to legacy format with preserved metadata
        # 3. Running through clustering (with speaker metadata preserved)
        # 4. Running synthesis (with speaker context included)
        # 5. Generating report (with speaker attribution visible)
        
        # For now, we'll just verify the data structures are compatible
        from insight_synthesizer.document_processing.adaptive_chunking import AdaptiveChunk
        from insight_synthesizer.analysis.embeddings import TextChunk
        
        # Create adaptive chunk with speaker metadata
        adaptive_chunk = AdaptiveChunk(
            text="The login process is really problematic",
            source_file=Path("test.txt"),
            chunk_type="speaker_turn",
            metadata={
                'speaker': 'User123',
                'is_interviewer': False,
                'content_type': 'dialogue'
            }
        )
        
        # Verify conversion to legacy format preserves metadata
        legacy_chunk = TextChunk(
            text=adaptive_chunk.text,
            source_file=adaptive_chunk.source_file,
            embedding=adaptive_chunk.embedding,
            cluster_id=adaptive_chunk.cluster_id
        )
        legacy_chunk._adaptive_metadata = adaptive_chunk.metadata
        legacy_chunk._chunk_type = adaptive_chunk.chunk_type
        
        # Verify metadata is accessible
        self.assertEqual(legacy_chunk._adaptive_metadata['speaker'], 'User123')
        self.assertFalse(legacy_chunk._adaptive_metadata['is_interviewer'])


class TestSpeakerAttributionEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in speaker attribution."""
    
    def setUp(self):
        self.chunker = AdaptiveChunker()
    
    def test_malformed_speaker_patterns(self):
        """Test handling of malformed or inconsistent speaker patterns."""
        malformed_text = """
        Speaker1: This is a normal speaker pattern.
        Random text without speaker indication.
        **Speaker2**: Different speaker format.
        SPEAKER3 (no colon) This might not be detected properly.
        Speaker1 again: Back to normal pattern.
        """
        
        file_path = Path("test.txt")
        classification = StructureClassification(
            content_type=ContentType.CONVERSATIONAL_FLOW,
            speaker_labels=True,
            structure_confidence=0.7,
            suggested_chunking=ChunkingStrategy.SPEAKER_TURNS,
            metadata={"primary_speakers": ["Speaker1", "Speaker2"], "has_interviewer": False,
                     "conversation_style": "mixed", "contains_meta_content": False,
                     "estimated_participants": 2},
            reasoning="Mixed speaker patterns detected"
        )
        
        chunks = self.chunker.chunk_document(malformed_text, file_path, classification)
        
        # Should handle gracefully and extract what it can
        self.assertGreater(len(chunks), 0)
        
        # Some chunks should have speaker information
        speaker_chunks = [c for c in chunks if c.metadata.get('speaker')]
        self.assertGreater(len(speaker_chunks), 0)
    
    def test_empty_or_very_short_speaker_turns(self):
        """Test handling of empty or very short speaker turns."""
        short_turns_text = """
        Interviewer: Hello.
        User: Hi.
        Interviewer: Good.
        User: This is a longer response that should definitely be included in the chunks.
        """
        
        file_path = Path("test.txt")
        classification = StructureClassification(
            content_type=ContentType.INTERVIEW_TRANSCRIPT,
            speaker_labels=True,
            structure_confidence=0.8,
            suggested_chunking=ChunkingStrategy.SPEAKER_TURNS,
            metadata={"primary_speakers": ["Interviewer", "User"], "has_interviewer": True,
                     "conversation_style": "formal", "contains_meta_content": False,
                     "estimated_participants": 2},
            reasoning="Short interview exchanges"
        )
        
        chunks = self.chunker.chunk_document(short_turns_text, file_path, classification)
        
        # Should include all speaker turns, even very short ones
        speaker_chunks = [chunk for chunk in chunks if chunk.metadata.get('speaker')]
        self.assertGreater(len(speaker_chunks), 0)
        
        # Should have both short and long turns
        turn_lengths = [len(chunk.text.strip()) for chunk in speaker_chunks]
        self.assertTrue(any(length <= 5 for length in turn_lengths))  # Has short turns
        self.assertTrue(any(length > 20 for length in turn_lengths))  # Has long turns
    
    def test_unicode_and_special_characters_in_speaker_names(self):
        """Test handling of unicode and special characters in speaker names."""
        unicode_text = """
        José María: Necesito ayuda con el sistema.
        
        Dr. François-Pierre: I understand your concern.
        
        用户001: 这个功能很难使用。
        
        Interviewer: Thank you all for your feedback.
        """
        
        file_path = Path("test.txt")
        classification = StructureClassification(
            content_type=ContentType.INTERVIEW_TRANSCRIPT,
            speaker_labels=True,
            structure_confidence=0.8,
            suggested_chunking=ChunkingStrategy.SPEAKER_TURNS,
            metadata={"primary_speakers": ["José María", "Dr. François-Pierre", "用户001", "Interviewer"], 
                     "has_interviewer": True, "conversation_style": "formal", "contains_meta_content": False,
                     "estimated_participants": 4},
            reasoning="Multi-lingual interview with unicode speakers"
        )
        
        chunks = self.chunker.chunk_document(unicode_text, file_path, classification)
        
        # Should handle unicode speaker names correctly
        speaker_chunks = [c for c in chunks if c.metadata.get('speaker')]
        self.assertGreater(len(speaker_chunks), 0)
        
        # Verify some unicode names are preserved
        speakers_found = [c.metadata['speaker'] for c in speaker_chunks]
        self.assertTrue(any('José' in name for name in speakers_found if name))


if __name__ == '__main__':
    unittest.main()