"""Client benchmark — run a corpus through TWO LLMClients and diff outcomes.

Designed to answer ONE question: how much of the "unclassified" tail (and how
many of the per-claim disagreements) does the AnthropicClient recover that
HeuristicClient leaves on the table?

That signal drives the v1.x vs v2 prioritisation call: if the LLM closes most
of the gap, harden heuristics less and move to v2 dialogic; if it doesn't,
keep iterating on the heuristic.

Outputs:
  - <prefix>.benchmark.json  — machine-readable per-claim comparison
  - <prefix>.benchmark.md    — leadership-readable markdown summary

Both clients are run with the SAME taxonomy / fit_table / contexts so the
only varying input is the LLMClient implementation. Restatement quality is
also captured, though the metric there is weaker (paraphrases are not
exact-comparable).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from .config_loader import (
    AppConfig,
    FitTable,
    Taxonomy,
    load_app_config,
    load_fit_table,
    load_taxonomy,
)
from .llm_client import LLMClient
from .pipeline import analyze
from .warrant import ClaimContext


@dataclass(frozen=True)
class ClaimComparison:
    claim_id: str
    claim_text: str
    a_type: str
    b_type: str
    a_flagged: bool
    b_flagged: bool
    a_reason: Optional[str]
    b_reason: Optional[str]
    type_agree: bool
    flag_agree: bool


@dataclass(frozen=True)
class BenchmarkReport:
    client_a_name: str
    client_b_name: str
    n_claims: int
    n_type_agree: int
    n_flag_agree: int
    type_disagreements: list[ClaimComparison] = field(default_factory=list)
    flag_disagreements: list[ClaimComparison] = field(default_factory=list)
    a_unclassified: int = 0
    b_unclassified: int = 0
    a_flagged_total: int = 0
    b_flagged_total: int = 0
    timestamp: str = ""

    @property
    def type_agreement_rate(self) -> float:
        return self.n_type_agree / self.n_claims if self.n_claims else 0.0

    @property
    def flag_agreement_rate(self) -> float:
        return self.n_flag_agree / self.n_claims if self.n_claims else 0.0

    def to_dict(self) -> dict:
        return {
            "client_a_name": self.client_a_name,
            "client_b_name": self.client_b_name,
            "n_claims": self.n_claims,
            "n_type_agree": self.n_type_agree,
            "n_flag_agree": self.n_flag_agree,
            "type_agreement_rate": self.type_agreement_rate,
            "flag_agreement_rate": self.flag_agreement_rate,
            "a_unclassified": self.a_unclassified,
            "b_unclassified": self.b_unclassified,
            "a_flagged_total": self.a_flagged_total,
            "b_flagged_total": self.b_flagged_total,
            "timestamp": self.timestamp,
            "type_disagreements": [asdict(c) for c in self.type_disagreements],
            "flag_disagreements": [asdict(c) for c in self.flag_disagreements],
        }


def run_benchmark(
    text: str,
    *,
    client_a: LLMClient,
    client_b: LLMClient,
    client_a_name: str = "client_a",
    client_b_name: str = "client_b",
    contexts: Optional[dict[int, ClaimContext]] = None,
    taxonomy: Optional[Taxonomy] = None,
    fit_table: Optional[FitTable] = None,
    app_config: Optional[AppConfig] = None,
) -> BenchmarkReport:
    """Run both clients over the same input. Return a structured comparison."""
    taxonomy = taxonomy or load_taxonomy()
    fit_table = fit_table or load_fit_table()
    app_config = app_config or load_app_config()
    contexts = contexts or {}

    result_a = analyze(
        text,
        client=client_a,
        contexts=contexts,
        taxonomy=taxonomy,
        fit_table=fit_table,
        app_config=app_config,
    )
    result_b = analyze(
        text,
        client=client_b,
        contexts=contexts,
        taxonomy=taxonomy,
        fit_table=fit_table,
        app_config=app_config,
    )

    # Align by claim_id (which is derived from span position, so deterministic
    # given the same segmentation).
    a_by_id = {r.claim_id: r for r in result_a.records}
    b_by_id = {r.claim_id: r for r in result_b.records}

    # Defensive: if the two clients caused different segmentation upstream
    # (they shouldn't — segment runs before classify), only compare the
    # intersection. This is a forward-compatibility hedge for v2 when
    # classify might influence span boundaries.
    common_ids = sorted(set(a_by_id) & set(b_by_id), key=lambda c: a_by_id[c].span.start)

    comparisons: list[ClaimComparison] = []
    type_disagreements: list[ClaimComparison] = []
    flag_disagreements: list[ClaimComparison] = []
    n_type_agree = 0
    n_flag_agree = 0
    a_unclassified = 0
    b_unclassified = 0
    a_flagged_total = 0
    b_flagged_total = 0

    for cid in common_ids:
        ra = a_by_id[cid]
        rb = b_by_id[cid]
        type_agree = ra.claim_type == rb.claim_type
        flag_agree = ra.attention_flag.raised == rb.attention_flag.raised
        cmp = ClaimComparison(
            claim_id=cid,
            claim_text=ra.claim_text,
            a_type=ra.claim_type,
            b_type=rb.claim_type,
            a_flagged=ra.attention_flag.raised,
            b_flagged=rb.attention_flag.raised,
            a_reason=ra.attention_flag.reason_code,
            b_reason=rb.attention_flag.reason_code,
            type_agree=type_agree,
            flag_agree=flag_agree,
        )
        comparisons.append(cmp)
        if type_agree:
            n_type_agree += 1
        else:
            type_disagreements.append(cmp)
        if flag_agree:
            n_flag_agree += 1
        else:
            flag_disagreements.append(cmp)
        if ra.claim_type == "unclassified":
            a_unclassified += 1
        if rb.claim_type == "unclassified":
            b_unclassified += 1
        if ra.attention_flag.raised:
            a_flagged_total += 1
        if rb.attention_flag.raised:
            b_flagged_total += 1

    return BenchmarkReport(
        client_a_name=client_a_name,
        client_b_name=client_b_name,
        n_claims=len(common_ids),
        n_type_agree=n_type_agree,
        n_flag_agree=n_flag_agree,
        type_disagreements=type_disagreements,
        flag_disagreements=flag_disagreements,
        a_unclassified=a_unclassified,
        b_unclassified=b_unclassified,
        a_flagged_total=a_flagged_total,
        b_flagged_total=b_flagged_total,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def write_benchmark(
    report: BenchmarkReport,
    out_dir: Path,
    *,
    prefix: str = "BENCHMARK",
    topic: str = "untopiced",
) -> tuple[Path, Path]:
    """Write JSON + markdown reports. Returns (json_path, md_path).

    Filename convention mirrors the trace convention so artefacts stay
    consistent across the toolchain."""
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_topic = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in topic).strip("-")
    today = date.today().isoformat()
    base = f"WARRANTLENS__{prefix}__{safe_topic}__v1.0__{today}"
    json_path = out_dir / f"{base}.json"
    md_path = out_dir / f"{base}.md"

    json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(r: BenchmarkReport) -> str:
    """Leadership-readable markdown. Most important number first."""
    lines: list[str] = []
    lines.append(f"# Warrant Lens — Client Benchmark ({r.client_a_name} vs {r.client_b_name})")
    lines.append("")
    lines.append(f"**Date:** {r.timestamp}")
    lines.append("")

    lines.append("## Headline numbers")
    lines.append("")
    lines.append("| Metric | " + r.client_a_name + " | " + r.client_b_name + " |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Total claims | {r.n_claims} | {r.n_claims} |")
    lines.append(f"| Unclassified | {r.a_unclassified} | {r.b_unclassified} |")
    lines.append(f"| Flagged | {r.a_flagged_total} | {r.b_flagged_total} |")
    lines.append("")
    lines.append(
        f"- **Claim-type agreement:** {r.n_type_agree}/{r.n_claims} "
        f"({r.type_agreement_rate:.1%})"
    )
    lines.append(
        f"- **Flag-raised agreement:** {r.n_flag_agree}/{r.n_claims} "
        f"({r.flag_agreement_rate:.1%})"
    )
    lines.append("")

    if r.type_disagreements:
        lines.append(f"## Claim-type disagreements ({len(r.type_disagreements)})")
        lines.append("")
        lines.append(f"| claim_id | text | {r.client_a_name} | {r.client_b_name} |")
        lines.append("|---|---|---|---|")
        for c in r.type_disagreements:
            snippet = c.claim_text.replace("|", "\\|")[:80]
            if len(c.claim_text) > 80:
                snippet += "…"
            lines.append(f"| `{c.claim_id}` | {snippet} | `{c.a_type}` | `{c.b_type}` |")
        lines.append("")

    if r.flag_disagreements:
        lines.append(f"## Flag-raised disagreements ({len(r.flag_disagreements)})")
        lines.append("")
        lines.append(f"| claim_id | text | {r.client_a_name} flag | {r.client_b_name} flag |")
        lines.append("|---|---|---|---|")
        for c in r.flag_disagreements:
            snippet = c.claim_text.replace("|", "\\|")[:80]
            if len(c.claim_text) > 80:
                snippet += "…"
            a_label = c.a_reason or "—"
            b_label = c.b_reason or "—"
            if not c.a_flagged:
                a_label = "(silent)"
            if not c.b_flagged:
                b_label = "(silent)"
            lines.append(f"| `{c.claim_id}` | {snippet} | {a_label} | {b_label} |")
        lines.append("")

    lines.append("## Reading guide")
    lines.append("")
    lines.append(
        "- Higher agreement rate ≠ higher accuracy. Both clients can be "
        "wrong in the same way. The disagreement tables are the actionable "
        "signal — they're where one client is plausibly catching what the "
        "other misses."
    )
    lines.append(
        "- This benchmark does NOT measure truth. It measures classification "
        "and flag-raising parity. Truth verification is out of scope (Principle 2)."
    )
    return "\n".join(lines)
