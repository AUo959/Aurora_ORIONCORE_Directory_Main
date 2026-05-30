"""Stage [5] RESTATE — emit the tool's own restatement of each flagged claim.

Principle 7 (chain-of-custody on the tool's own first move): before the tool
pushes on a claim, it emits its own restatement. This is a first-class output
the user can reject. Rejection voids the flag.

This module is the SEAM where the LLM call (if any) lives — keep it small,
make the protocol the only externally-facing contract.
"""
from __future__ import annotations

from .classify import ClassifiedSegment
from .llm_client import LLMClient, Restatement


def restate(cs: ClassifiedSegment, client: LLMClient) -> Restatement:
    """Always produce a restatement before any flag is rendered. Even on a
    claim that ultimately won't be flagged, the restatement is cheap and
    keeps the path uniform — flagging logic should never have to decide
    whether to call this."""
    return client.restate_claim(cs.segment.text)
