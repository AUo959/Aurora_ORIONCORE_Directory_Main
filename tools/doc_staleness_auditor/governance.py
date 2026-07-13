"""CanonRec-style governance routing (Drift Containment Protocol).

For repos whose ``governance_mode`` is ``canon_promotion_queue`` we never edit
canon content or open a PR against it. Instead each STALE finding is routed into
the existing drift flow:

1. A quarantined draft file capturing the proposed change + its evidence.
2. An appended entry to ``DRIFT_LOG.md`` (matching the repo's existing
   ``## Drift Entry — YYYY-MM-DD`` block format).
3. An appended proposal bullet to the promotion queue's
   "Needs review (decision required)" section.

This module produces the *text artifacts* (so it is testable and safe to run in
a dry run); writing them into a real CanonRec checkout is the executor's job.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from .config import RepoConfig
from .planner import PlannedEdit


@dataclass
class GovernanceArtifacts:
    quarantine_path: str
    quarantine_body: str
    drift_log_entry: str
    promotion_queue_entry: str


def _today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def build_artifacts(
    edits: list[PlannedEdit], cfg: RepoConfig, today: str | None = None
) -> GovernanceArtifacts:
    day = today or _today()
    quarantine_path = f"{cfg.quarantine_dir}/DRIFT_DRAFT__doc_audit__{day}.md"

    body_lines = [
        f"# Drift Containment Draft — doc-audit — {day}",
        "",
        "Proposed doc corrections quarantined pending canon-promotion review.",
        "Not canon. Do not merge into canon content directly.",
        "",
    ]
    for e in edits:
        body_lines += [
            f"## {e.doc_path}:{e.line}",
            f"- **Old:** `{e.old_text}`",
            f"- **Proposed:** `{e.new_text}`",
            f"- **Evidence:** {e.rationale}",
            "",
        ]

    drift_log_entry = _drift_entry(edits, day)
    promo_entry = _promotion_entry(quarantine_path, len(edits), day)

    return GovernanceArtifacts(
        quarantine_path=quarantine_path,
        quarantine_body="\n".join(body_lines),
        drift_log_entry=drift_log_entry,
        promotion_queue_entry=promo_entry,
    )


def _drift_entry(edits: list[PlannedEdit], day: str) -> str:
    docs = sorted({e.doc_path for e in edits})
    affected = ", ".join(docs[:6]) + (" ..." if len(docs) > 6 else "")
    lines = [
        "",
        f"## Drift Entry — {day}",
        "- **Source:** doc-staleness-auditor automated verification against "
        "primary ground truth (git tree / source content / config files)",
        "- **Type:** doc drift (documentation contradicts observed repo state)",
        f"- **Entities affected:** {affected or 'documentation'}",
        f"- **Description:** {len(edits)} doc claim(s) diverged from observed "
        "ground truth; each proposed correction carries an inline evidence "
        "citation (file:line@sha).",
        "- **Resolution:** Quarantined as draft; promotion-queue entry appended "
        "for human review. No canon change applied automatically.",
    ]
    return "\n".join(lines) + "\n"


def _promotion_entry(quarantine_path: str, n: int, day: str) -> str:
    return (
        f"- `{quarantine_path}` — doc-audit drift corrections ({n} item(s), "
        f"{day}); evidence-backed, needs canon-owner decision before promotion.\n"
    )
