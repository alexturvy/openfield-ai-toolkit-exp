"""Tests for research plan parser."""

import unittest
from pathlib import Path
import tempfile
from src.insight_synthesizer.research.plan_parser import ResearchPlanParser, ParsedResearchPlan

class TestResearchPlanParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = ResearchPlanParser()
        self.test_dir = tempfile.mkdtemp()
    
    def test_parse_structured_plan(self):
        """Test parsing a well-structured research plan."""
        plan_content = """
        Research Plan: User Navigation Study
        
        Background:
        Users are struggling with our navigation system. Reports indicate high bounce rates
        and frequent complaints about finding features.
        
        Research Questions:
        1. Why do users find the navigation confusing?
        2. What mental models do users have about our information architecture?
        3. How can we improve discoverability of key features?
        
        Assumptions:
        - Users want quick access to frequently used features
        - Current information architecture doesn't match user expectations
        - Visual hierarchy is not clear enough
        
        Methodology:
        Conduct 12 user interviews over 2 weeks using semi-structured format.
        Include task-based observation sessions.
        """
        
        plan_file = Path(self.test_dir) / "structured_plan.txt"
        plan_file.write_text(plan_content)
        
        parsed = self.parser.parse_document(plan_file)
        
        self.assertEqual(len(parsed.research_questions), 3)
        self.assertEqual(len(parsed.assumptions), 3)
        self.assertIsNotNone(parsed.background)
        self.assertIsNotNone(parsed.methodology)
        self.assertIn("navigation", parsed.background.lower())
    
    def test_parse_informal_plan(self):
        """Test parsing an informal research plan."""
        plan_content = """
        Hey team,
        
        We need to figure out why people are dropping off during checkout.
        
        What we want to learn:
        - Where exactly are people abandoning their carts?
        - Is it a trust issue or a UX issue?
        - What would make them complete the purchase?
        
        I think the main problem is that our checkout flow is too long,
        but we should validate this assumption through user testing.
        
        Let's do some session recordings and follow-up interviews.
        """
        
        plan_file = Path(self.test_dir) / "informal_plan.txt"
        plan_file.write_text(plan_content)
        
        parsed = self.parser.parse_document(plan_file)
        
        self.assertGreater(len(parsed.research_questions), 0)
        self.assertIn("checkout", parsed.raw_text.lower())
        # Should extract questions from "What we want to learn" section
        self.assertTrue(any("abandoning" in q.lower() for q in parsed.research_questions))
    
    def test_parse_academic_format(self):
        """Test parsing academic-style research plan."""
        plan_content = """
        Research Study: Trust in AI Systems
        
        RQ1: What factors influence user trust in AI-powered recommendations?
        RQ2: How does transparency in AI decision-making affect adoption rates?
        RQ3: What role does user expertise play in trust formation?
        
        H1: Users with more AI exposure will demonstrate higher initial trust levels
        H2: Transparent AI systems will see 30% better adoption rates than black-box systems
        H3: Technical expertise correlates negatively with trust in complex AI outputs
        
        Method: Mixed methods approach with n=50 participants
        - Quantitative: Trust scale measurements pre/post interaction
        - Qualitative: Semi-structured interviews about trust factors
        """
        
        plan_file = Path(self.test_dir) / "academic_plan.txt"
        plan_file.write_text(plan_content)
        
        parsed = self.parser.parse_document(plan_file)
        
        self.assertEqual(len(parsed.research_questions), 3)
        self.assertEqual(len(parsed.hypotheses), 3)
        self.assertIsNotNone(parsed.methodology)
        # Check RQ format was parsed correctly
        self.assertTrue(any("trust" in q.lower() for q in parsed.research_questions))
        self.assertTrue(any("transparency" in q.lower() for q in parsed.research_questions))
    
    def test_pattern_extraction(self):
        """Test pattern-based extraction independently."""
        content = """
        Background:
        This is the background information about the study.
        
        Research Questions:
        - Question one about the topic?
        - Question two about another aspect?
        
        Assumptions:
        • We assume users want efficiency
        • We believe the current system is too slow
        """
        
        plan = self.parser._extract_with_patterns(content)
        
        self.assertEqual(len(plan.research_questions), 2)
        self.assertEqual(len(plan.assumptions), 2)
        self.assertIsNotNone(plan.background)
    
    def test_deduplication(self):
        """Test that duplicate questions are removed."""
        items = [
            "How do users navigate the system?",
            "How do users navigate the system?",
            "HOW DO USERS NAVIGATE THE SYSTEM?",
            "What features do they use?"
        ]
        
        deduped = self.parser._deduplicate_list(items)
        
        self.assertEqual(len(deduped), 2)
        self.assertIn("How do users navigate the system?", deduped)
        self.assertIn("What features do they use?", deduped)
    
    def test_goal_to_question_conversion(self):
        """Test converting goal statements to questions."""
        test_cases = [
            ("To understand user behavior", "What user behavior?"),
            ("To identify pain points", "What are pain points?"),
            ("To determine the best approach", "How the best approach?"),
            ("Improve user satisfaction", "How can we improve user satisfaction?"),
            ("Why do users leave?", "Why do users leave?")  # Already a question
        ]
        
        for goal, expected_pattern in test_cases:
            result = self.parser._goal_to_question(goal)
            self.assertIsNotNone(result)
            self.assertIn("?", result)
    
    def test_empty_document(self):
        """Test handling of empty or minimal documents."""
        plan_content = "This document has no clear structure."
        
        plan_file = Path(self.test_dir) / "empty_plan.txt"
        plan_file.write_text(plan_content)
        
        parsed = self.parser.parse_document(plan_file)
        
        # Should not crash, should return empty lists
        self.assertEqual(len(parsed.research_questions), 0)
        self.assertEqual(len(parsed.assumptions), 0)
        self.assertEqual(parsed.raw_text, plan_content)
    
    def test_confidence_scoring(self):
        """Test that confidence scores are generated."""
        plan_content = """
        Research Questions:
        1. How do users interact with the dashboard?
        2. What features are most valuable?
        
        Background:
        We need to improve the dashboard experience.
        """
        
        plan_file = Path(self.test_dir) / "confidence_test.txt"
        plan_file.write_text(plan_content)
        
        parsed = self.parser.parse_document(plan_file)
        
        # Should have confidence scores
        self.assertIsNotNone(parsed.confidence_scores)
        if parsed.confidence_scores:
            # Pattern-based extraction should have high confidence
            self.assertGreater(parsed.confidence_scores.get('research_questions', 0), 0.7)


class TestParserIntegration(unittest.TestCase):
    """Integration tests for parser with goal manager."""
    
    def test_parsed_plan_to_research_goal(self):
        """Test converting ParsedResearchPlan to ResearchGoal."""
        from src.insight_synthesizer.research.goal_manager import ResearchGoal
        
        parsed = ParsedResearchPlan(
            background="Test background",
            research_questions=["Q1?", "Q2?"],
            assumptions=["A1", "A2"],
            methodology="Test method"
        )
        
        # This will be implemented when we update goal_manager.py
        # goal = ResearchGoal.from_parsed_plan(parsed)
        # self.assertEqual(goal.research_questions, parsed.research_questions)
        # self.assertEqual(goal.background, parsed.background)


if __name__ == '__main__':
    unittest.main()