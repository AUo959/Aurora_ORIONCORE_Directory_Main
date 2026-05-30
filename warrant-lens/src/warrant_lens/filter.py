"""Stage [3] FILTER — drop non-load-bearing claims.

Rule (taxonomy.yaml): if evidentiary_demand is False, the claim is filtered
here and never flagged. A human can't usefully verify an opinion or
definition; flagging it is noise. See SPEC §5.1 + §9 test T-FILTER.

The filtered claims are NOT discarded outright — they're returned in the
"silent" bucket so that emit_trace.py can record their existence for offline
calibration (§9 T-CALIB), while emit_inline.py omits them from highlights.
"""
from __future__ import annotations

from dataclasses import dataclass

from .classify import ClassifiedSegment


@dataclass(frozen=True)
class FilterOutput:
    demanding: list[ClassifiedSegment]
    silent: list[ClassifiedSegment]


def filter_demanding(classified: list[ClassifiedSegment]) -> FilterOutput:
    demanding: list[ClassifiedSegment] = []
    silent: list[ClassifiedSegment] = []
    for cs in classified:
        (demanding if cs.makes_evidentiary_demand else silent).append(cs)
    return FilterOutput(demanding=demanding, silent=silent)
