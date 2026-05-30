"""Stage [6a] EMIT inline annotations.

SPEC §8.1: subtle span highlight on flagged claims only; unflagged text is
unmarked. Hover/expand metadata: tool_restatement, reason_code in plain
language, human_handoff, standard_invoked, blind_spot_note.

Directness toggle (Principle 3, §10): affects PHRASING ONLY. Identical set of
flagged claims either way — enforced by test T-DELIVERY.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .config_loader import DeliveryConfig
from .model import ClaimRecord


# Plain-language for each reason code. Direct vs gentle changes the voice,
# not the substance.
_REASON_PHRASES = {
    "NO_SOURCE": {
        "gentle": "no source cited for an evidentiary claim",
        "direct": "evidentiary claim with no source",
    },
    "SOURCE_NOT_LOCATABLE": {
        "gentle": "source gestured at but not nameable / linkable",
        "direct": "vague source — not locatable",
    },
    "SOURCE_CATEGORY_MISMATCH": {
        "gentle": "source category is typically weak for this claim type",
        "direct": "source category mismatched to claim type",
    },
    "SOURCE_ROLE_MISMATCH": {
        "gentle": "this shape of source isn't right for a claim treated as settled",
        "direct": "role mismatch — single primary for settled claim",
    },
    "CHAIN_BROKEN": {
        "gentle": "chain to a primary source isn't traceable",
        "direct": "source chain broken",
    },
    "FRONTIER_HANDOFF": {
        "gentle": "may be a frontier question — single source may be insufficient",
        "direct": "frontier? — verify single-source sufficiency",
    },
    "UNKNOWN_DOMAIN": {
        "gentle": "domain isn't encoded; what counts as strong here is your call",
        "direct": "unknown domain — fit table does not cover this",
    },
}


@dataclass(frozen=True)
class InlineAnnotation:
    span_start: int
    span_end: int
    headline: str
    metadata: dict


def render(
    text: str,
    records: Iterable[ClaimRecord],
    delivery: DeliveryConfig,
) -> tuple[str, list[InlineAnnotation]]:
    """Return (annotated_text, annotation_objects).

    annotated_text wraps flagged spans with markers; the structured
    annotations list carries the metadata for UI rendering.
    """
    directness = delivery.directness if delivery.directness in {"gentle", "direct"} else "gentle"
    flagged = [r for r in records if r.attention_flag.raised]
    flagged.sort(key=lambda r: r.span.start)

    annotations: list[InlineAnnotation] = []
    for r in flagged:
        rc = r.attention_flag.reason_code or "SOURCE_CATEGORY_MISMATCH"
        headline = _REASON_PHRASES.get(rc, {}).get(directness, rc)
        metadata = {
            "claim_id": r.claim_id,
            "reason_code": r.attention_flag.reason_code,
            "headline": headline,
            "tool_restatement": r.tool_restatement,
            "tool_extensions": list(r.tool_extensions),
            "human_handoff": r.attention_flag.human_handoff,
            "standard_invoked": r.standard_invoked,
            "blind_spot_note": r.blind_spot_note,
            "show_restatement": delivery.show_restatement,
        }
        annotations.append(
            InlineAnnotation(
                span_start=r.span.start,
                span_end=r.span.end,
                headline=headline,
                metadata=metadata,
            )
        )

    annotated_text = _wrap_spans(text, annotations)
    return annotated_text, annotations


def _wrap_spans(text: str, annotations: list[InlineAnnotation]) -> str:
    """Inline marker syntax: ⟦flag: headline⟧claim text⟦/⟧."""
    if not annotations:
        return text
    parts: list[str] = []
    cursor = 0
    for a in annotations:
        parts.append(text[cursor : a.span_start])
        parts.append(f"⟦flag: {a.headline}⟧")
        parts.append(text[a.span_start : a.span_end])
        parts.append("⟦/⟧")
        cursor = a.span_end
    parts.append(text[cursor:])
    return "".join(parts)
