from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from openfield.models import Interview, Utterance
from openfield.preprocess.normalize import normalize_text_with_offsets


SPEAKER_RE = re.compile(r'^([A-Za-z][\w .\'-]+)\s*:\s*(.*)$')
TIMECODE_RE = re.compile(r'^(\d{2}:\d{2}:\d{2})$')


def _canonicalize_speaker(name: str, full_seen: Optional[str]) -> str:
    if full_seen:
        return full_seen
    return ' '.join([w.capitalize() for w in name.strip().split() if w])


def parse_transcript_file(path: Path, raw_text: str) -> Interview:
    text, offsets, line_starts = normalize_text_with_offsets(raw_text)
    lines = text.split('\n')

    title: Optional[str] = None
    date: Optional[str] = None
    participants: List[str] = []
    utterances: List[Utterance] = []

    current_speaker_original: str = 'Unknown'
    current_speaker_canonical: str = 'Unknown'
    current_utterance_lines: List[str] = []
    current_start_line: Optional[int] = None
    last_timecode: Optional[str] = None
    speaker_alias_full: dict[str, str] = {}

    def flush_utterance(end_line_idx: int) -> None:
        nonlocal current_utterance_lines, current_start_line
        if not current_utterance_lines or current_start_line is None:
            return
        text_block = ' '.join(s.strip() for s in current_utterance_lines if s.strip())
        if not text_block:
            current_utterance_lines = []
            current_start_line = None
            return
        utter_index = len(utterances)
        start_line = current_start_line
        end_line = end_line_idx
        start_char = line_starts[start_line] if start_line < len(line_starts) else 0
        end_char = line_starts[end_line] - 1 if end_line < len(line_starts) else len(text)
        utterances.append(Utterance(
            utterance_index=utter_index,
            speaker_original=current_speaker_original,
            speaker_canonical=current_speaker_canonical,
            text=text_block,
            start_line=start_line + 1,
            end_line=end_line,
            start_char=start_char,
            end_char=end_char,
            approx_timestamp=last_timecode
        ))
        current_utterance_lines = []
        current_start_line = None

    # Basic header gleaning
    if lines and re.match(r'^[A-Za-z]{3} \d{1,2}, \d{4}$', lines[0].strip()):
        date = lines[0].strip()
    if len(lines) > 1 and 'Transcript' in lines[1]:
        title = lines[1].strip()

    for i, line in enumerate(lines):
        s = line.rstrip()
        if not s:
            continue
        m_time = TIMECODE_RE.match(s)
        if m_time:
            last_timecode = m_time.group(1)
            continue
        m = SPEAKER_RE.match(s)
        if m:
            # flush previous utterance ending before this line
            flush_utterance(i)
            speaker = m.group(1).strip()
            content = m.group(2).strip()
            # First time we see a multi-word proper name, store as full
            if ' ' in speaker and speaker.lower() != 'interviewer':
                speaker_alias_full[speaker.split()[0].lower()] = speaker
            canon = speaker_alias_full.get(speaker.lower(), _canonicalize_speaker(speaker, None))
            # Map first names to full if available
            first = speaker.split()[0].lower()
            if first in speaker_alias_full:
                canon = speaker_alias_full[first]
            current_speaker_original = speaker
            current_speaker_canonical = canon
            if current_start_line is None:
                current_start_line = i
            current_utterance_lines = [content] if content else []
            if speaker not in participants:
                participants.append(speaker)
            continue
        # Continuation of current utterance
        if current_start_line is None:
            current_start_line = i
        current_utterance_lines.append(s)

    # Flush last
    flush_utterance(len(lines))

    return Interview(
        filepath=path,
        title=title,
        date=date,
        participants=participants,
        utterances=utterances
    )


