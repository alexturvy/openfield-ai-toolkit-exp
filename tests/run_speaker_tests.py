#!/usr/bin/env python3
"""Test runner for speaker attribution functionality."""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

if __name__ == '__main__':
    # Discover and run all tests in the speaker attribution test file
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    
    # Load specific test file
    suite = loader.loadTestsFromName('test_speaker_attribution')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)