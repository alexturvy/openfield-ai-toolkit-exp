from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def discover_files(patterns: Iterable[str]) -> List[Path]:
    results: List[Path] = []
    for pat in patterns:
        # Use glob from current working directory
        for p in Path().glob(pat):
            if p.is_file():
                results.append(p)
    results.sort()
    return results


def read_text_file(path: Path) -> str:
    return path.read_text(errors='replace')


