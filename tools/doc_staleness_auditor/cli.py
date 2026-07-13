"""``doc-audit`` command-line interface: scan / verify / plan / execute."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .config import resolve_repo_config
from .executor import execute as run_execute
from .extractors import extract_claims
from .models import Claim, Finding, Status
from .planner import plan_fixes
from .repo_reader import make_reader
from .verifiers import Verifier


def _cmd_scan(args: argparse.Namespace) -> int:
    reader = make_reader(args.repo, backend=args.backend)
    claims: list[Claim] = []
    for doc in reader.list_docs():
        content = reader.read(doc)
        if content is None:
            continue
        claims.extend(extract_claims(doc, content))
    ledger = {
        "repo": args.repo,
        "head_sha": reader.head_sha(),
        "claim_count": len(claims),
        "claims": [c.to_dict() for c in claims],
    }
    out = args.out or "claims_ledger.json"
    Path(out).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    by_type = Counter(c.type.value for c in claims)
    print(f"scanned {len(reader.list_docs())} docs @ {reader.head_sha()[:12]}")
    print(f"extracted {len(claims)} claims -> {out}")
    for t, n in sorted(by_type.items()):
        print(f"  {t:8} {n}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    ledger = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    repo = args.repo or ledger["repo"]
    reader = make_reader(repo, backend=args.backend)
    verifier = Verifier(reader)
    claims = [Claim.from_dict(c) for c in ledger["claims"]]
    findings = verifier.verify_all(claims)

    report = {
        "repo": repo,
        "head_sha": reader.head_sha(),
        "summary": dict(Counter(f.status.value for f in findings)),
        "findings": [f.to_dict() for f in findings],
    }
    out = args.out or "findings_report.json"
    Path(out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(findings, report, (args.md or "findings_report.md"))
    print(f"verified {len(findings)} claims @ {reader.head_sha()[:12]}")
    for status in (Status.CONFIRMED, Status.STALE, Status.UNVERIFIABLE):
        print(f"  {status.value:26} {report['summary'].get(status.value, 0)}")
    print(f"-> {out}  /  {args.md or 'findings_report.md'}")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.findings).read_text(encoding="utf-8"))
    findings = [_finding_from_dict(d) for d in report["findings"]]
    edits = plan_fixes(findings)
    out = args.out or "fix_plan.json"
    Path(out).write_text(
        json.dumps([e.to_dict() for e in edits], indent=2), encoding="utf-8")
    print(f"drafted {len(edits)} fix(es) for STALE findings -> {out}\n")
    for e in edits:
        print(e.diff())
        print()
    return 0


def _cmd_execute(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.findings).read_text(encoding="utf-8"))
    findings = [_finding_from_dict(d) for d in report["findings"]]
    cfg = resolve_repo_config(args.repo, path=args.config)
    result = run_execute(
        findings, cfg, repo_root=args.repo_root or ".",
        apply=args.apply, branch=args.branch,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "preview"}, indent=2))
    if not args.apply:
        print("\n[dry run] re-run with --apply to write changes.")
        if result.get("mode") == "standard_pr":
            print("\n--- PR body preview ---\n" + result["pr_body"])
        elif "preview" in result:
            p = result["preview"]
            print("\n--- DRIFT_LOG.md append ---\n" + p["drift_log_entry"])
            print("--- promotion queue append ---\n" + p["promotion_queue_entry"])
    return 0


# ---- markdown / (de)serialisation helpers ----------------------------------
def _write_markdown(findings: list[Finding], report: dict, path: str) -> None:
    lines = [
        f"# Doc staleness findings — {report['repo']}",
        f"HEAD `{report['head_sha']}`",
        "",
        "| status | count |", "|---|---|",
    ]
    for k, v in sorted(report["summary"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    for status in (Status.STALE, Status.CONFIRMED, Status.UNVERIFIABLE):
        subset = [f for f in findings if f.status is status]
        if not subset:
            continue
        lines.append(f"## {status.value} ({len(subset)})")
        for f in subset[: (None if status is Status.STALE else 40)]:
            c, e = f.claim, f.evidence
            loc = ", ".join(
                f"{p}:{ln}" for p, ln in zip(e.files, e.lines, strict=False)
            ) or ", ".join(e.files) or "-"
            lines.append(
                f"- **{c.type.value}** `{c.value}` — {c.doc_path}:{c.doc_line}\n"
                f"  - observed: `{f.observed}`\n"
                f"  - evidence: [{e.method}] {e.detail} ({loc}"
                f"{'@'+e.sha[:12] if e.sha else ''})"
            )
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _finding_from_dict(d: dict) -> Finding:
    from .models import Evidence
    return Finding(
        claim=Claim.from_dict(d["claim"]),
        status=Status(d["status"]),
        observed=d.get("observed"),
        evidence=Evidence(**d["evidence"]),
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="doc-audit", description=__doc__)
    p.add_argument("--backend", choices=["auto", "git", "fs"], default="auto",
                   help="how to read the target repo (default: auto)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="extract verifiable claims from .md files")
    s.add_argument("--repo", required=True, help="path to the target repo")
    s.add_argument("--out", help="claims ledger output (json)")
    s.set_defaults(func=_cmd_scan)

    v = sub.add_parser("verify", help="verify claims against ground truth")
    v.add_argument("--claims", required=True, help="claims ledger json")
    v.add_argument("--repo", help="override repo path (default: ledger's)")
    v.add_argument("--out", help="findings report output (json)")
    v.add_argument("--md", help="findings report output (markdown)")
    v.set_defaults(func=_cmd_verify)

    pl = sub.add_parser("plan", help="draft fixes for STALE findings")
    pl.add_argument("--findings", required=True, help="findings report json")
    pl.add_argument("--out", help="fix plan output (json)")
    pl.set_defaults(func=_cmd_plan)

    e = sub.add_parser("execute", help="apply fixes per repo governance mode")
    e.add_argument("--findings", required=True)
    e.add_argument("--repo", required=True, help="repo NAME (keys repos.yaml)")
    e.add_argument("--repo-root", help="repo working tree to edit (default: .)")
    e.add_argument("--config", help="path to repos.yaml")
    e.add_argument("--branch", help="branch name for standard_pr mode")
    e.add_argument("--apply", action="store_true", help="actually write changes")
    e.set_defaults(func=_cmd_execute)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
