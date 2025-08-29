from pathlib import Path

from openfield.parse.transcripts import parse_transcript_file
from openfield.analysis.verify import verify_quotes
from openfield.models import Interview


SAMPLE = (
    "Aug 20, 2025\n"
    "Stephen Brown and Alex Turvy - Transcript\n"
    "00:00:00\n"
    "Alex Turvy: Hello there.\n"
    "Stephen: Hi.\n"
    "00:00:05\n"
    "Alex Turvy: Let's talk about neurons.\n"
    "Stephen: Action potentials are confusing for beginners.\n"
)


def test_parse_basic_transcript(tmp_path: Path) -> None:
    p = tmp_path / 'sample.txt'
    p.write_text(SAMPLE)
    iv = parse_transcript_file(p, SAMPLE)
    assert iv.title and 'Transcript' in iv.title
    assert iv.date == 'Aug 20, 2025'
    assert len(iv.utterances) >= 3
    # Ensure line numbers are 1-based and ordered
    for utt in iv.utterances:
        assert utt.start_line >= 1
        assert utt.end_line >= utt.start_line


def test_verify_exact_fragment(tmp_path: Path) -> None:
    p = tmp_path / 'sample.txt'
    p.write_text(SAMPLE)
    iv = parse_transcript_file(p, SAMPLE)
    potentials = [{
        'quote_fragment': 'action potentials are confusing',
        'speaker': None,
        'source': None,
        'relevance': 'test'
    }]
    res = verify_quotes(potentials, [iv])
    assert len(res) == 1
    v = res[0]
    assert 'Action potentials' in v['text'] or 'action potentials' in v['text'].lower()
    assert v['utterance_index'] >= 0
    assert v['start_line'] >= 1

