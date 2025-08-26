from src.insight_synthesizer.validation.theme_validator import ThemeValidator, QuoteEvidence


def test_calculate_coverage_score():
    validator = ThemeValidator()
    validator.original_files = {'file1': 'a', 'file2': 'b'}
    quotes = [
        QuoteEvidence(text='q1', source_file='file1', confidence=0.8),
        QuoteEvidence(text='q2', source_file='file2', confidence=0.9),
    ]
    score = validator._calculate_coverage_score(quotes, ['speaker'], ['file1', 'file2'])
    assert 0 < score <= 1
