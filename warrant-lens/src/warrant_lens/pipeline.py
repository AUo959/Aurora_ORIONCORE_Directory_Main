"""End-to-end pipeline orchestration.

Composes the six stages as pure functions over each prior stage's output. The
caller may pass per-claim ClaimContext via `contexts` (keyed by span index)
to inject domain / settled / source-class metadata that the in-text
heuristics can't recover. Callers that don't supply context fall through to
the in-text source extractor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .classify import classify
from .config_loader import (
    AppConfig,
    FitTable,
    Taxonomy,
    load_app_config,
    load_fit_table,
    load_taxonomy,
)
from .filter import filter_demanding
from .llm_client import HeuristicClient, LLMClient
from .model import (
    AttentionFlag,
    ClaimRecord,
    Span,
    make_unflagged_record,
)
from .restate import restate
from .segment import segment
from .warrant import ClaimContext, check_warrant


@dataclass(frozen=True)
class PipelineResult:
    records: list[ClaimRecord]
    standard_invoked: str


def analyze(
    text: str,
    *,
    contexts: Optional[dict[int, ClaimContext]] = None,
    taxonomy: Optional[Taxonomy] = None,
    fit_table: Optional[FitTable] = None,
    app_config: Optional[AppConfig] = None,
    client: Optional[LLMClient] = None,
) -> PipelineResult:
    """Run the full pipeline.

    contexts maps a *segment index* (0-based, in segmentation order over
    demanding claims) to a ClaimContext. Indices that aren't supplied fall
    through to the in-text extractor.
    """
    taxonomy = taxonomy or load_taxonomy()
    fit_table = fit_table or load_fit_table()
    app_config = app_config or load_app_config()
    client = client or HeuristicClient()
    contexts = contexts or {}

    standard = app_config.default_standard

    # [1] segment
    segments = segment(text)
    # [2] classify
    classified = classify(segments, taxonomy, client)
    # [3] filter
    flt = filter_demanding(classified)

    records: list[ClaimRecord] = []

    # Non-demanding claims: silent in inline view, present in trace for
    # offline calibration (T-CALIB).
    for cs in flt.silent:
        records.append(
            make_unflagged_record(
                claim_id=_claim_id(cs.segment.start, cs.segment.end),
                span=Span(start=cs.segment.start, end=cs.segment.end),
                claim_text=cs.segment.text,
                claim_type=cs.claim_type,  # type: ignore[arg-type]
                makes_evidentiary_demand=False,
                standard_invoked=standard,
            )
        )

    # Demanding claims: [5] restate before [4] warrant flag is rendered (P7).
    for idx, cs in enumerate(flt.demanding):
        restated = restate(cs, client)
        ctx = contexts.get(idx, ClaimContext())
        warrant, flag = check_warrant(cs, fit_table, ctx)
        records.append(
            ClaimRecord(
                claim_id=_claim_id(cs.segment.start, cs.segment.end),
                span=Span(start=cs.segment.start, end=cs.segment.end),
                claim_text=cs.segment.text,
                tool_restatement=restated.text,
                claim_type=cs.claim_type,  # type: ignore[arg-type]
                makes_evidentiary_demand=True,
                warrant=warrant,
                attention_flag=flag,
                standard_invoked=standard,
                tool_extensions=restated.extensions,
            )
        )

    # Stable order by span position for deterministic output.
    records.sort(key=lambda r: (r.span.start, r.span.end))
    return PipelineResult(records=records, standard_invoked=standard)


def _claim_id(start: int, end: int) -> str:
    return f"c_{start:05d}_{end:05d}"


def demanding_segment_indices(
    text: str,
    *,
    taxonomy: Optional[Taxonomy] = None,
    client: Optional[LLMClient] = None,
) -> list[int]:
    """Helper for callers that need to know which segment indices count as
    demanding (so they can build the `contexts` dict).
    Returns indices in segmentation order."""
    taxonomy = taxonomy or load_taxonomy()
    client = client or HeuristicClient()
    segments = segment(text)
    classified = classify(segments, taxonomy, client)
    out: list[int] = []
    j = 0
    for cs in classified:
        if cs.makes_evidentiary_demand:
            out.append(j)
            j += 1
        else:
            # silent claims don't get an index in the demanding stream
            pass
    return out


def flagged_claims(records: Iterable[ClaimRecord]) -> list[ClaimRecord]:
    return [r for r in records if r.attention_flag.raised]
