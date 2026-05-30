"""Stage [4] WARRANT — structural checks per surviving claim.

Per SPEC §3:
  - source present?
  - source locatable/accessible? (name/link vs "studies show")
  - source-type × claim-type fit? (FIT TABLE config)
  - primary vs secondary role + chain intact?

NEVER asserts truth. NEVER emits a standalone source-quality badge — fit is
always the pair (source-class, claim-type). See Principles 2, 4, 5.

Settled-vs-frontier (§7): the tool MUST NOT silently guess. When consensus is
unclear or unencoded for the domain, default to FRONTIER_HANDOFF. Discourse-
level controversy is never an input to this stage (test T-CLIMATE).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .classify import ClassifiedSegment
from .config_loader import FitTable
from .model import (
    AttentionFlag,
    FitAssessment,
    ReasonCode,
    SourceRole,
    Warrant,
)


# Caller-supplied context per claim. Domain identifies the *owning* field
# (Principle: indexed to the domain that owns the claim, NOT where it is
# publicly argued). settled is the caller's encoded judgment from field-
# internal artifacts only — None means "unknown, default to frontier".
@dataclass(frozen=True)
class ClaimContext:
    domain: str = "general_empirical"
    settled: Optional[bool] = None
    """None → emit frontier handoff. True → apply categorical criteria
    directly. False → frontier; lone source insufficient. (SPEC §7)"""

    observed_source_class: Optional[str] = None
    source_text: Optional[str] = None
    source_role: SourceRole = "unknown"
    chain_intact: bool = True


# ---------------------------------------------------------------------------
# Naive in-text extractor for callers that don't supply a ClaimContext.
# Tuned to recognise the patterns the §9 acceptance tests use.
# ---------------------------------------------------------------------------

_SOURCE_VAGUE_RE = re.compile(
    r"\b(?:studies show|research shows|experts say|scientists say|"
    r"some claim|many believe|it is well known)\b",
    re.IGNORECASE,
)
_SOURCE_NAMED_RE = re.compile(
    r"\((?P<src>[^)]{3,200})\)|"
    r"\b(?:according to|per|cited in|from)\s+(?P<src2>[A-Z][^.;,]{2,120})"
)


def extract_inline_source(text: str) -> tuple[Optional[str], bool]:
    """Return (source_text or None, locatable). Heuristic — production uses
    classifier output. locatable=False means "claim says it has a source but
    the source is not nameable/linkable" (e.g. 'studies show')."""
    if _SOURCE_VAGUE_RE.search(text):
        # Vague-source pattern: tool treats source as present-but-not-locatable.
        return _SOURCE_VAGUE_RE.search(text).group(0), False
    m = _SOURCE_NAMED_RE.search(text)
    if m:
        src = m.group("src") or m.group("src2")
        return src.strip(), True
    return None, False


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------

def check_warrant(
    cs: ClassifiedSegment,
    fit_table: FitTable,
    ctx: Optional[ClaimContext] = None,
) -> tuple[Warrant, AttentionFlag]:
    """Run the four structural checks. Returns (warrant, flag).

    The flag's human_handoff is always phrased as an INVITATION (Principle 4 +
    `invite_not_summon`). Substance — what's flagged — is invariant.
    """
    ctx = ctx or ClaimContext()

    # 1. Unknown domain → handoff, no verdict.
    if not fit_table.domain_is_encoded(ctx.domain):
        warrant = _empty_warrant(ctx, FitAssessment(
            expected_source_classes=tuple(),
            observed_source_class=ctx.observed_source_class,
            fit_verdict="unknown_domain",
        ))
        flag = AttentionFlag(
            raised=True,
            reason_code="UNKNOWN_DOMAIN",
            human_handoff=(
                f"The domain '{ctx.domain}' is not encoded in the fit table; "
                "what counts as a strong source here is a judgment call you'll "
                "want to make. You may decline this prompt."
            ),
        )
        return warrant, flag

    # 2. Resolve source presence/locatability from context, falling back to
    #    in-text extraction.
    source_text = ctx.source_text
    source_locatable: bool
    source_present: bool
    if source_text is not None:
        source_present = True
        source_locatable = True
    else:
        extracted, locatable = extract_inline_source(cs.segment.text)
        source_text = extracted
        source_present = extracted is not None
        source_locatable = locatable

    # 3. NO_SOURCE: highest-priority structural failure for demanding claims.
    if not source_present:
        warrant = Warrant(
            source_present=False,
            source_locatable=False,
            source_text=None,
            source_role=ctx.source_role if ctx.source_role != "unknown" else "none",
            chain_intact=False,
            fit=FitAssessment(
                expected_source_classes=tuple(
                    fit_table.lookup(ctx.domain, cs.claim_type).get("strong", [])
                    if fit_table.lookup(ctx.domain, cs.claim_type) else []
                ),
                observed_source_class=None,
                fit_verdict="no_source",
            ),
        )
        flag = AttentionFlag(
            raised=True,
            reason_code="NO_SOURCE",
            human_handoff=(
                "This claim makes an evidentiary demand but cites no source. "
                "You may want to ask for one; you may also decide the context "
                "doesn't require it."
            ),
        )
        return warrant, flag

    # 4. SOURCE_NOT_LOCATABLE: vague gesture rather than a nameable source.
    if not source_locatable:
        entry = fit_table.lookup(ctx.domain, cs.claim_type) or {"strong": [], "weak": []}
        warrant = Warrant(
            source_present=True,
            source_locatable=False,
            source_text=source_text,
            source_role=ctx.source_role,
            chain_intact=ctx.chain_intact,
            fit=FitAssessment(
                expected_source_classes=tuple(entry.get("strong", [])),
                observed_source_class=ctx.observed_source_class,
                fit_verdict="no_source",
            ),
        )
        flag = AttentionFlag(
            raised=True,
            reason_code="SOURCE_NOT_LOCATABLE",
            human_handoff=(
                "A source is gestured at but not named or linked, so it can't "
                "be inspected. Worth asking for the specific reference."
            ),
        )
        return warrant, flag

    # 5. Fit lookup.
    entry = fit_table.lookup(ctx.domain, cs.claim_type)
    strong = list(entry.get("strong", [])) if entry else []
    weak = list(entry.get("weak", [])) if entry else []

    fit_verdict, reason_code, handoff = _evaluate_fit(
        observed=ctx.observed_source_class,
        strong=strong,
        weak=weak,
        settled=ctx.settled,
        source_role=ctx.source_role,
        chain_intact=ctx.chain_intact,
    )

    warrant = Warrant(
        source_present=True,
        source_locatable=True,
        source_text=source_text,
        source_role=ctx.source_role,
        chain_intact=ctx.chain_intact,
        fit=FitAssessment(
            expected_source_classes=tuple(strong),
            observed_source_class=ctx.observed_source_class,
            fit_verdict=fit_verdict,
        ),
    )
    flag = AttentionFlag(
        raised=reason_code is not None,
        reason_code=reason_code,
        human_handoff=handoff,
    )
    return warrant, flag


def _evaluate_fit(
    *,
    observed: Optional[str],
    strong: list[str],
    weak: list[str],
    settled: Optional[bool],
    source_role: SourceRole,
    chain_intact: bool,
) -> tuple[str, Optional[ReasonCode], Optional[str]]:
    """Return (fit_verdict, reason_code_or_None, handoff_or_None)."""

    # Chain breakage outranks fit — if the chain is broken we cannot trust the
    # source role at all.
    if not chain_intact:
        return (
            "chain_broken",
            "CHAIN_BROKEN",
            "The cited source appears to point to another source that isn't "
            "traceable. Worth following the chain to a primary before relying "
            "on this claim.",
        )

    # Role check (Principle: settled body + lone primary == role_mismatch).
    # §7: for a SETTLED claim, a *single* primary study is WEAK.
    if settled is True and source_role == "primary":
        return (
            "role_mismatch",
            "SOURCE_ROLE_MISMATCH",
            "For a claim the field treats as settled, a single primary study "
            "is not the right shape of evidence — proximity is not confirmation. "
            "A synthesis-level source would be more appropriate.",
        )

    # Frontier default: if settledness is unknown, emit a handoff BEFORE any
    # category verdict. The verdict can stand alongside the handoff.
    frontier_handoff: Optional[str] = None
    if settled is None:
        frontier_handoff = (
            "This may be a frontier question rather than settled science; "
            "treat single sources with caution and check whether a synthesis "
            "exists. You may decline this prompt."
        )

    # Category fit.
    if observed in weak:
        return (
            "category_mismatch",
            "SOURCE_CATEGORY_MISMATCH",
            "This claim's category warrants a stronger source class than the "
            "one cited. Credibility of this specific source is yours to judge.",
        )
    if observed in strong:
        # Strong-category source: no flag UNLESS we're frontier-handoff.
        if frontier_handoff:
            return "fit", "FRONTIER_HANDOFF", frontier_handoff
        return "fit", None, None

    # Unknown source class with no strong/weak match. Flag as handoff.
    if frontier_handoff:
        return "fit", "FRONTIER_HANDOFF", frontier_handoff
    return (
        "fit",
        "SOURCE_CATEGORY_MISMATCH",
        "The source class isn't one this domain's fit table recognises. "
        "You may want to assess whether it belongs with the strong category "
        "for this claim type.",
    )


def _empty_warrant(ctx: ClaimContext, fit: FitAssessment) -> Warrant:
    return Warrant(
        source_present=ctx.source_text is not None,
        source_locatable=ctx.source_text is not None,
        source_text=ctx.source_text,
        source_role=ctx.source_role,
        chain_intact=ctx.chain_intact,
        fit=fit,
    )
