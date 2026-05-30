"""ClaimRecord — the single source of truth contract between pipeline stages.

Matches SPEC §4 verbatim. Every pipeline stage is a pure function whose
input and/or output is a list[ClaimRecord]. Renderings (inline / JSONL)
operate on the same records — build once, render twice.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal, Optional

from . import TOOL_VERSION


# ---- enumerations (kept as Literal types so schema stays inspectable) ----

ClaimType = Literal[
    # evidentiary_demand: true
    "specific_statistic",
    "named_citation",
    "temporal_fact",
    "causal_mechanism",
    "code_api_signature",
    "consequential_empirical",
    # evidentiary_demand: false
    "definition",
    "opinion_normative",
    "hedge_uncertainty",
    # fallback when classifier cannot decide
    "unclassified",
]

SourceRole = Literal["primary", "secondary", "unknown", "none"]

FitVerdict = Literal[
    "fit",
    "category_mismatch",
    "role_mismatch",      # e.g. lone primary asserting a settled body
    "chain_broken",
    "no_source",
    "unknown_domain",     # config doesn't encode this domain — handoff required
]

ReasonCode = Literal[
    "NO_SOURCE",
    "SOURCE_NOT_LOCATABLE",
    "SOURCE_CATEGORY_MISMATCH",
    "SOURCE_ROLE_MISMATCH",
    "CHAIN_BROKEN",
    "FRONTIER_HANDOFF",
    "UNKNOWN_DOMAIN",
]


@dataclass(frozen=True)
class Span:
    """Character offsets into the original input text."""
    start: int
    end: int


@dataclass(frozen=True)
class FitAssessment:
    expected_source_classes: tuple[str, ...]
    observed_source_class: Optional[str]
    fit_verdict: FitVerdict


@dataclass(frozen=True)
class Warrant:
    source_present: bool
    source_locatable: bool
    source_text: Optional[str]
    source_role: SourceRole
    chain_intact: bool
    fit: FitAssessment


@dataclass(frozen=True)
class AttentionFlag:
    raised: bool
    reason_code: Optional[ReasonCode]
    human_handoff: Optional[str]
    """human_handoff names what's structural and explicitly cedes the judgment
    call. Never a verdict. Required when raised=True (Principle 4)."""


@dataclass(frozen=True)
class ClaimRecord:
    """Atomic unit of analysis. See SPEC §4."""
    claim_id: str
    span: Span
    claim_text: str
    tool_restatement: str
    """Required. Populated BEFORE any flag is rendered (Principle 7). Empty
    string is permitted only when attention_flag.raised is False."""

    claim_type: ClaimType
    makes_evidentiary_demand: bool
    warrant: Optional[Warrant]
    """None for filtered (non-demanding) claims."""

    attention_flag: AttentionFlag
    standard_invoked: str
    """Which evidentiary convention was applied (Principle 8) — assessment is
    objective relative to THIS stated standard, not in the abstract."""

    confidence_signal: Optional[float] = None
    """v1 leaves null. v2 logprob-enrichment slot — schema-stable for forward
    compatibility (Principle 9 / §4 field notes)."""

    blind_spot_note: str = (
        "Structural checks passed cannot rule out a well-formed but false warrant."
    )
    """Principle 9: honest about the residual. Always present, even on clean
    claims — the tool's limit is not contingent on whether it flagged this one."""

    tool_extensions: tuple[str, ...] = field(default_factory=tuple)
    """Principle 7 self-seam marking: places where the tool extended rather
    than restated the claim. Empty when the restatement is purely a paraphrase."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    tool_version: str = TOOL_VERSION

    # ---- helpers ----

    def to_dict(self) -> dict:
        """Render to the JSONL-friendly dict shape from SPEC §4."""
        return asdict(self)


# ---- factory helpers (keep construction sites consistent) ----

def make_unflagged_record(
    *,
    claim_id: str,
    span: Span,
    claim_text: str,
    claim_type: ClaimType,
    makes_evidentiary_demand: bool,
    standard_invoked: str,
) -> ClaimRecord:
    """Build a record that explicitly was not flagged. Restatement is omitted
    (empty string) because Principle 7 only requires it BEFORE pushing on a
    claim — non-demanding claims are never pushed on."""
    return ClaimRecord(
        claim_id=claim_id,
        span=span,
        claim_text=claim_text,
        tool_restatement="",
        claim_type=claim_type,
        makes_evidentiary_demand=makes_evidentiary_demand,
        warrant=None,
        attention_flag=AttentionFlag(raised=False, reason_code=None, human_handoff=None),
        standard_invoked=standard_invoked,
    )
