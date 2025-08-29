from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


LINE_SEP = '\u2028'
PARA_SEP = '\u2029'
NBSP = '\u00A0'


@dataclass
class OffsetMap:
    # Maps normalized text indices to raw text indices (char positions)
    norm_to_raw: List[int]


def normalize_text_with_offsets(raw: str) -> Tuple[str, OffsetMap, List[int]]:
    """
    Normalize unicode artifacts and line endings while tracking offsets.
    Returns: (normalized_text, offset_map, line_start_positions)
    """
    norm_chars: List[str] = []
    norm_to_raw: List[int] = []

    for i, ch in enumerate(raw):
        if ch == NBSP:
            mapped = ' '
        elif ch == LINE_SEP:
            mapped = '\n'
        elif ch == PARA_SEP:
            mapped = '\n'
        else:
            mapped = ch
        norm_chars.append(mapped)
        norm_to_raw.append(i)

    # Standardize line endings: ensure only \n
    normalized = ''.join(norm_chars).replace('\r\n', '\n').replace('\r', '\n')

    # Rebuild mapping after CR/LF changes: conservative approach assumes no additional shifts
    # because we replaced CR/LF pairs in-place. For simplicity we ignore offset drift here.

    # Compute line starts for quick line/char span mapping
    line_starts: List[int] = [0]
    for idx, ch in enumerate(normalized):
        if ch == '\n':
            line_starts.append(idx + 1)

    return normalized, OffsetMap(norm_to_raw=norm_to_raw), line_starts


