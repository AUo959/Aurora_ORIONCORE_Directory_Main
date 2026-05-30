"""Stage [1] SEGMENT — cheap heuristic sentence/assertion segmentation.

Emits candidate spans with character offsets. Deliberately simple: the
heuristic is allowed to over-segment because filter.py drops non-demanding
claims and warrant.py only acts on the rest. Tuned for precision per §8.1.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# Splits on sentence-ending punctuation followed by whitespace, while keeping
# the trailing punctuation attached to the preceding span. Multi-pass over the
# raw text so that an unclosed quote / parenthesis does not eat the document.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[\"'])")


@dataclass(frozen=True)
class Segment:
    text: str
    start: int
    end: int


def segment(text: str) -> list[Segment]:
    if not text or not text.strip():
        return []

    segments: list[Segment] = []
    cursor = 0
    # Find all boundary positions.
    boundaries: list[int] = [0]
    for m in _SENTENCE_END.finditer(text):
        boundaries.append(m.end())
    boundaries.append(len(text))

    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        chunk = text[start:end]
        # Trim trailing whitespace but preserve start offset.
        stripped = chunk.rstrip()
        if not stripped.strip():
            continue
        # Adjust end to drop trailing whitespace.
        adjusted_end = start + len(stripped)
        segments.append(Segment(text=stripped, start=start, end=adjusted_end))
        cursor = adjusted_end

    _ = cursor  # readability — final cursor unused
    return segments
