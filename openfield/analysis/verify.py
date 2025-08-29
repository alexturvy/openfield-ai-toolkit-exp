from __future__ import annotations

import re
from typing import Dict, List

from openfield.models import Interview, VerifiedQuote


SPACE_RE = re.compile(r'\s+')


def _normalize_text(s: str) -> str:
    s = s.lower()
    s = SPACE_RE.sub(' ', s).strip()
    return s


def verify_quotes(potential_quotes: List[Dict], interviews: List[Interview]) -> List[Dict]:
    verified: List[Dict] = []
    for cand in potential_quotes:
        fragment_norm = _normalize_text(cand.get('quote_fragment', ''))
        if not fragment_norm:
            continue
        # Search utterances for the fragment
        found = False
        for iv in interviews:
            for utt in iv.utterances:
                if fragment_norm and fragment_norm in _normalize_text(utt.text):
                    verified.append({
                        'text': utt.text,
                        'speaker': utt.speaker_canonical,
                        'speaker_original': utt.speaker_original,
                        'source': iv.filepath.name,
                        'utterance_index': utt.utterance_index,
                        'start_line': utt.start_line,
                        'end_line': utt.end_line,
                        'start_char': utt.start_char,
                        'end_char': utt.end_char,
                        'relevance': cand.get('relevance', ''),
                        'confidence': 1.0,
                        'match_method': 'exact'
                    })
                    found = True
                    break
            if found:
                break
    return verified


