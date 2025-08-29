from __future__ import annotations

from typing import List, Dict

from openfield.models import Interview, PotentialQuote


def extract_relevant_quotes_heuristic(interviews: List[Interview], question: str) -> List[Dict]:
    """
    Extremely simple heuristic: select utterances containing any keyword from the question.
    This is a placeholder until LLM adapters are wired.
    """
    keywords = [w.lower() for w in question.split() if len(w) > 4]
    results: List[Dict] = []
    for interview in interviews:
        for utt in interview.utterances:
            lt = utt.text.lower()
            if any(k in lt for k in keywords):
                results.append({
                    'quote_fragment': ' '.join(utt.text.split()[:8]),
                    'speaker': utt.speaker_canonical,
                    'source': interview.filepath.name,
                    'relevance': 'keyword match'
                })
    return results


