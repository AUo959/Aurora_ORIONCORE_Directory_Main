#!/usr/bin/env python3
"""brief_scaffold.py — make writing the next executive brief cheap.

The workspace's reporting layer has no scheduler, so brief cadence depends on
someone remembering. The 2026-07-25 brief found the cost of that: two P1s had
been resolved weeks earlier and were still being carried as open, because no
brief had run to notice. Closure is signal, and an unrun brief suppresses it.

This tool does the mechanical half — the part that is identical every time and
that nobody should be retyping:

- works out how far the newest brief has fallen behind, in commits landed
- pre-fills the header block: date, scope, HEAD, staleness datum, gap
- carries forward the previous brief's risk table as a checklist, so each item
  is explicitly confirmed, closed, or re-aged rather than silently dropped
- lists the evidence commands so the appendix is not reconstructed from memory

It deliberately does not write findings. Synthesis is the judgement half and
belongs to whoever runs it.

Writes nothing unless --write is passed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIEF_DIR = REPO_ROOT / "reports" / "state_briefs"
EXEMPT_FILE = REPO_ROOT / "catalog" / "brief_freshness_exemption.yaml"

# Kept in step with tools/workspace_verify.py.
WARN_COMMITS = 60
BLOCKING_COMMITS = 150

EVIDENCE_COMMANDS = [
    ("Blocking findings", "python3 tools/workspace_verify.py"),
    ("Operator inbox, build lanes", "python3 tools/aurora_mission_control.py --summary"),
    ("Publication debt", "python3 tools/publication_debt.py scan --json"),
    ("Recovery candidates", "python3 tools/workspace_recovery_index.py --summary"),
    ("Nested repo states", "git -C <path> status --short  # per catalog/repo_registry.yaml"),
    ("Root sync state", "git rev-list --count origin/main..HEAD"),
]


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=REPO_ROOT, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def newest_brief() -> Path | None:
    if not BRIEF_DIR.is_dir():
        return None
    briefs = sorted(BRIEF_DIR.glob("executive_brief__*.md"))
    return briefs[-1] if briefs else None


def commits_since(brief: Path) -> int | None:
    rel = brief.relative_to(REPO_ROOT)
    sha = _git("log", "-1", "--format=%H", "--", str(rel))
    if not sha:
        return None
    count = _git("rev-list", "--count", f"{sha}..HEAD")
    return int(count) if count.isdigit() else None


def carried_risks(brief: Path) -> list[str]:
    """Pull risk lines out of the previous brief's Top Risks table."""
    rows: list[str] = []
    in_table = False
    for line in brief.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("## Top Risks"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table and line.startswith("| ") and not re.match(r"^\|\s*[-#]", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0].isdigit():
                summary = re.sub(r"\*\*", "", cells[1])
                rows.append(summary[:110])
    return rows


def scaffold(brief: Path | None, ahead: int | None) -> str:
    now = datetime.now(timezone.utc)
    head = _git("rev-parse", "--short", "HEAD")
    head_date = _git("log", "-1", "--format=%cI")
    unpushed = _git("rev-list", "--count", "origin/main..HEAD") or "?"

    lines = [
        "# Aurora / ORIONCORE — Executive Decision Brief",
        "",
        f"- **Generated:** {now:%Y-%m-%dT%H:%M}Z",
        "- **Scope:** Root control-plane repo + local nested repos, at "
        "`~/dev/Aurora_ORIONCORE_Directory_Main`",
        "- **Pipeline:** `aurora-exec-brief-pipeline` contract (Decision Snapshot / "
        "Top Risks / Operational Signals / Recommended Actions / Evidence Appendix)",
        "- **Posture:** Read-only synthesis unless an Actions-taken section says otherwise.",
        f"- **Staleness datum:** current root HEAD `{head}` committed `{head_date}`; "
        "artifacts generated before that are flagged stale.",
    ]
    if brief and ahead is not None:
        lines.append(
            f"- **Gap since last brief:** {ahead} commit(s) since `{brief.name}`."
        )
    lines += [
        f"- **Unpushed on main:** {unpushed} commit(s).",
        "",
        "---",
        "",
        "## Decision Snapshot",
        "",
        "<!-- One paragraph: what changed, and the single thing the reader must decide. -->",
        "",
        "| Dimension | State | Read |",
        "|---|---|---|",
        "",
        "**One-line:** ",
        "",
        "---",
        "",
        "## Top Risks",
        "",
        "| # | Risk | Severity | Evidence |",
        "|---|---|---|---|",
        "",
    ]

    if brief:
        carried = carried_risks(brief)
        if carried:
            lines += [
                "---",
                "",
                f"## Carried from {brief.name} — resolve each explicitly",
                "",
                "<!-- Rule 5: report age and trajectory, not existence. Mark every line "
                "confirmed / known-and-aging / regressed / closed. Do not drop one "
                "silently — an unmentioned risk reads as an unchecked one. -->",
                "",
            ]
            lines += [f"- [ ] {risk}" for risk in carried]
            lines.append("")

    lines += [
        "---",
        "",
        "## Closures recorded this brief",
        "",
        "<!-- Closure is signal. If nothing closed, say so. -->",
        "",
        "| Item | Last brief said | Actual |",
        "|---|---|---|",
        "",
        "---",
        "",
        "## Operational Signals",
        "",
        "<!-- Paste from `make brief` output above. -->",
        "",
        "---",
        "",
        "## Recommended Actions",
        "",
        "| Priority | Action | Owner |",
        "|---|---|---|",
        "",
        "---",
        "",
        "## Evidence Appendix",
        "",
        "| Claim | Command |",
        "|---|---|",
    ]
    lines += [f"| {label} | `{cmd}` |" for label, cmd in EVIDENCE_COMMANDS]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold the next executive brief, or check brief freshness."
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Report freshness only; exit 1 when a brief is overdue.",
    )
    parser.add_argument(
        "--exit-on-warn", action="store_true",
        help=("With --check, also exit 1 at the warn threshold, not just the "
              "blocking one. For schedulers that alert on exit status."),
    )
    parser.add_argument(
        "--write", action="store_true",
        help="Write the scaffold to reports/state_briefs/ instead of stdout.",
    )
    args = parser.parse_args()

    brief = newest_brief()
    ahead = commits_since(brief) if brief else None

    if args.check:
        if EXEMPT_FILE.exists():
            print(f"brief freshness: exempted by {EXEMPT_FILE.relative_to(REPO_ROOT)}")
            return 0
        if brief is None or ahead is None:
            print("brief freshness: no committed brief to measure against")
            return 0
        if ahead >= BLOCKING_COMMITS:
            print(f"brief freshness: OVERDUE — {ahead} commits since {brief.name} "
                  f"(blocks at {BLOCKING_COMMITS}). Run `make brief`.")
            return 1
        if ahead >= WARN_COMMITS:
            print(f"brief freshness: due — {ahead} commits since {brief.name} "
                  f"(warns at {WARN_COMMITS}, blocks at {BLOCKING_COMMITS}).")
            # A scheduler that alerts only on the blocking tier alerts at the
            # moment commits start failing — which is not a warning, it is the
            # incident. --exit-on-warn moves the alert to the warn tier without
            # changing what `make brief-check` means for existing callers.
            return 1 if args.exit_on_warn else 0
        print(f"brief freshness: ok — {ahead} commits since {brief.name} "
              f"(warns at {WARN_COMMITS}).")
        return 0

    text = scaffold(brief, ahead)

    if args.write:
        out = BRIEF_DIR / f"executive_brief__{datetime.now(timezone.utc):%Y-%m-%d}.md"
        if out.exists():
            print(f"refusing to overwrite existing {out.relative_to(REPO_ROOT)}",
                  file=sys.stderr)
            return 1
        out.write_text(text, encoding="utf-8")
        print(f"scaffold written to {out.relative_to(REPO_ROOT)}")
        return 0

    if brief and ahead is not None:
        print(f"── Brief scaffold ── ({ahead} commits since {brief.name}; "
              f"warns at {WARN_COMMITS}, blocks at {BLOCKING_COMMITS})")
        print("Write it to disk with: python3 tools/brief_scaffold.py --write\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
