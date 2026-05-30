"""Stage [2] CLASSIFY — claim-type tagging against the taxonomy.

Pure function over the previous stage's output. The LLMClient call (if used)
is the ONLY model dependency in the pipeline — required to be swappable per
SPEC §11. v1 uses HeuristicClient by default.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config_loader import Taxonomy
from .llm_client import LLMClient
from .segment import Segment


@dataclass(frozen=True)
class ClassifiedSegment:
    segment: Segment
    claim_type: str
    makes_evidentiary_demand: bool


def classify(
    segments: list[Segment], taxonomy: Taxonomy, client: LLMClient
) -> list[ClassifiedSegment]:
    out: list[ClassifiedSegment] = []
    for seg in segments:
        claim_type = client.classify_claim(seg.text)
        # Defensive: if the client returns a type the taxonomy doesn't know,
        # treat it as unclassified rather than crash. Principle 6 + Principle 9.
        if claim_type not in taxonomy.claim_types:
            claim_type = "unclassified"
        demand = taxonomy.is_demanding(claim_type)
        out.append(
            ClassifiedSegment(
                segment=seg, claim_type=claim_type, makes_evidentiary_demand=demand
            )
        )
    return out
