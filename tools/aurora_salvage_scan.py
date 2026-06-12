#!/usr/bin/env python3
"""
Aurora Salvage Scan — root control-plane derelict survey.

Cross-references the recovery index against the official system of record
(registered nested repos + root Git) to identify salvage: mature, valuable
work that exists locally but is absent from any official manifest on GitHub.

Position in the control plane:
- Evidence source: reports/analysis/workspace_recovery_index_latest.json
  (read-only routing evidence per docs/RECOVERY_INDEX_WORKFLOW_v1.md).
- Registry source: catalog/repo_registry.yaml (registered vessels).
- Output: reports/analysis/aurora_salvage_report_latest.{json,md} — the
  JSON is the ingestion interface for the CloudBank sensor array's
  SalvageSensor (src/sensors/external/salvage.py).

This tool is READ-ONLY. It does not promote candidates, mutate nested
repos, or alter promotion_status: everything stays pending_review /
not_promoted until the explicit promotion gate (AGENTS.md §Recovery
Indexing).

Station terms (L1 abstraction): registered repos are the fleet registry;
tracked+committed files are cargo on a vessel's manifest; untracked mature
work adrift in the field is a derelict or recoverable cargo; artifacts
carrying anchors/DLP/version identity are transmitting beacons; uncommitted
files inside a registered repo are cargo aboard but off-manifest; unpushed
commits are vessels loaded and awaiting departure clearance.

Usage:
    python3 tools/aurora_salvage_scan.py                  # print summary
    python3 tools/aurora_salvage_scan.py --persist-report # write reports
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECOVERY_REPORT = ROOT / "reports/analysis/workspace_recovery_index_latest.json"
REPO_REGISTRY = ROOT / "catalog/repo_registry.yaml"
REPORT_JSON = ROOT / "reports/analysis/aurora_salvage_report_latest.json"
REPORT_MD = ROOT / "reports/analysis/aurora_salvage_report_latest.md"

GIT_ENV_STRIP = ["env", "-u", "GIT_DIR", "-u", "GIT_WORK_TREE",
                 "-u", "GIT_INDEX_FILE", "-u", "GIT_PREFIX"]

# Maturity/classification heuristics — mirrors CloudBank
# src/sensors/external/salvage.py (kept standalone: report file is the
# interface; the control plane does not import nested-repo code).
MATURITY_WEIGHTS = {"tests": 0.25, "structure": 0.20, "version_marker": 0.20,
                    "documentation": 0.15, "substance": 0.20}
HIGH_VALUE_SCORE = 15
MATURITY_THRESHOLD = 0.6
_VERSION_RE = re.compile(r"v\d+[._]\d+|__v\d|_v\d", re.IGNORECASE)
_BEACON_MARKERS = ("EOS_SEED_ORION", "PICARD_DELTA_3", "DLP", "ANCHOR",
                   "THREADCORE", "ZIPWIZ", "CANON")
_BEACON_SIGNALS = {"governance_or_control_plane", "narrative_or_agent_logic"}


def _git(repo: Path, *args: str) -> str:
    cmd = GIT_ENV_STRIP + ["git", "-C", str(repo)] + list(args)
    # S603: inputs are fixed git args + repo paths from catalog/repo_registry.yaml
    # (control-plane-owned), never user input.
    out = subprocess.run(  # noqa: S603
        cmd, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout


def load_registered_repos() -> list[dict]:
    """Minimal YAML walk for name/path pairs (control plane is stdlib-only)."""
    repos = []
    current: dict = {}
    for line in REPO_REGISTRY.read_text().splitlines():
        m = re.match(r"^- name:\s*(.+)$", line)
        if m:
            if current.get("name") and current.get("path"):
                repos.append(current)
            current = {"name": m.group(1).strip()}
        m = re.match(r"^\s+path:\s*(.+)$", line)
        if m and current:
            current["path"] = m.group(1).strip()
    if current.get("name") and current.get("path"):
        repos.append(current)
    return repos


def repo_divergence(repos: list[dict]) -> dict:
    """Per registered vessel: cargo aboard off-manifest, departure queue."""
    out = {}
    for repo in repos:
        path = ROOT / repo["path"]
        if not (path / ".git").exists():
            out[repo["name"]] = {"error": "no .git", "uncommitted": 0,
                                 "unpushed_commits": 0}
            continue
        entry = {"uncommitted": 0, "unpushed_commits": 0}
        try:
            status = _git(path, "status", "--porcelain")
            entry["uncommitted"] = sum(1 for ln in status.splitlines() if ln)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            entry["status_error"] = str(e)[:120]
        try:
            entry["unpushed_commits"] = int(
                _git(path, "rev-list", "--count", "@{u}..HEAD").strip())
        except (RuntimeError, subprocess.TimeoutExpired, ValueError):
            entry["unpushed_commits"] = 0
            entry["upstream"] = "unknown"
        out[repo["name"]] = entry
    return out


def build_tracked_sets(repos: list[dict]) -> list[tuple[str, set]]:
    """(repo_rel_prefix, tracked_relpaths) for manifest membership checks.
    Root repo included: control-plane-tracked files count as registered."""
    sets = []
    for repo in repos + [{"name": "root", "path": "."}]:
        path = ROOT / repo["path"]
        if not (path / ".git").exists():
            continue
        try:
            tracked = set(_git(path, "ls-files").splitlines())
        except (RuntimeError, subprocess.TimeoutExpired):
            continue
        prefix = "" if repo["path"] == "." else repo["path"].rstrip("/") + "/"
        sets.append((prefix, tracked))
    return sets


def on_official_manifest(rel_path: str, tracked_sets: list[tuple[str, set]]) -> bool:
    for prefix, tracked in tracked_sets:
        if prefix and rel_path.startswith(prefix):
            if rel_path[len(prefix):] in tracked:
                return True
        elif not prefix and rel_path in tracked:
            return True
    return False


def score_maturity(rec: dict) -> float:
    w = MATURITY_WEIGHTS
    sig = set(rec.get("signals", []))
    path = rec.get("path", "")
    lines = int(rec.get("line_count") or 0)
    size = int(rec.get("size_bytes") or 0)
    ext = rec.get("extension", "")
    score = 0.0
    if "test_or_fixture" in sig:
        score += w["tests"]
    if {"contract_or_schema", "code_logic"} & sig:
        score += w["structure"]
    if _VERSION_RE.search(path):
        score += w["version_marker"]
    if ext in (".md", ".txt") and lines >= 100:
        score += w["documentation"]
    elif {"cloudbank_runtime", "qgia_or_forecast"} & sig:
        score += w["documentation"] * 0.5
    if lines >= 50 or size >= 4096:
        score += w["substance"]
    return min(score, 1.0)


def is_beacon(rec: dict) -> bool:
    upper = rec.get("path", "").upper()
    if any(m in upper for m in _BEACON_MARKERS):
        return True
    return bool(_BEACON_SIGNALS & set(rec.get("signals", []))) and bool(
        _VERSION_RE.search(rec.get("path", "")))


def classify(rec: dict) -> str:
    if rec["on_official_manifest"]:
        return "registered"
    if rec["is_beacon"]:
        return "beacon"
    if rec["maturity"] >= MATURITY_THRESHOLD and \
            float(rec.get("value_score", 0)) >= HIGH_VALUE_SCORE:
        return "cargo"
    if rec["maturity"] >= 0.3:
        return "derelict"
    return "debris"


def run_scan() -> dict:
    recovery = json.loads(RECOVERY_REPORT.read_text())
    repos = load_registered_repos()
    divergence = repo_divergence(repos)
    tracked_sets = build_tracked_sets(repos)

    candidates = []
    for rec in recovery.get("candidates", []):
        c = dict(rec)
        c["on_official_manifest"] = on_official_manifest(c["path"], tracked_sets)
        c["maturity"] = round(score_maturity(c), 3)
        c["is_beacon"] = is_beacon(c)
        c["classification"] = classify(c)
        # READ-ONLY guarantee: promotion status is passed through untouched.
        c["promotion_status"] = rec.get("promotion_status", "pending_review")
        candidates.append(c)

    adrift = [c for c in candidates if not c["on_official_manifest"]]
    by_class = {}
    for c in candidates:
        by_class.setdefault(c["classification"], []).append(c)

    def _slim(c):
        return {"path": c["path"], "maturity": c["maturity"],
                "value_score": c["value_score"],
                "classification": c["classification"],
                "is_beacon": c["is_beacon"],
                "target_repo_hint": c.get("target_repo_hint"),
                "promotion_status": c["promotion_status"],
                "sha256": c.get("sha256", "")[:16]}

    return {
        "schema_version": 1,
        "tool": "tools/aurora_salvage_scan.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only",
        "evidence_source": str(RECOVERY_REPORT.relative_to(ROOT)),
        "summary": {
            "surveyed": len(candidates),
            "salvage_contacts_adrift": len(adrift),
            "high_value_cargo": len(by_class.get("cargo", [])),
            "beacon_signals": len(by_class.get("beacon", [])),
            "derelicts": len(by_class.get("derelict", [])),
            "debris": len(by_class.get("debris", [])),
            "registered": len(by_class.get("registered", [])),
            "registry_match_rate": round(
                (len(candidates) - len(adrift)) / len(candidates), 3)
                if candidates else 1.0,
            "uncommitted_in_repos": sum(
                d.get("uncommitted", 0) for d in divergence.values()),
            "unpushed_commits": sum(
                d.get("unpushed_commits", 0) for d in divergence.values()),
        },
        "repo_divergence": divergence,
        "candidates": [_slim(c) for c in sorted(
            candidates, key=lambda c: c["maturity"] * float(c["value_score"]),
            reverse=True)],
        "promotion_note": (
            "All candidates remain pending_review/not_promoted. Promotion "
            "requires the explicit control-plane gate; this report is "
            "routing evidence only."),
    }


def render_md(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# Aurora Salvage Report",
        f"**Generated:** {report['generated_at']}  ",
        f"**Mode:** read-only survey  ",
        f"**Evidence:** {report['evidence_source']}",
        "",
        "## Survey Summary (station terms)",
        "",
        "|Survey Metric|Count|",
        "|---|---|",
        f"|Contacts surveyed|{s['surveyed']}|",
        f"|Adrift (no official manifest)|{s['salvage_contacts_adrift']}|",
        f"|High-value cargo (recover)|{s['high_value_cargo']}|",
        f"|Distress beacons (investigate)|{s['beacon_signals']}|",
        f"|Derelicts (assess)|{s['derelicts']}|",
        f"|Debris (advisory)|{s['debris']}|",
        f"|Registry match rate|{s['registry_match_rate']}|",
        f"|Cargo aboard, off-manifest (uncommitted in repos)|{s['uncommitted_in_repos']}|",
        f"|Awaiting departure clearance (unpushed commits)|{s['unpushed_commits']}|",
        "",
        "## Top Salvage Candidates",
        "",
        "|Path|Class|Maturity|Value|Target Hint|",
        "|---|---|---|---|---|",
    ]
    for c in report["candidates"][:20]:
        if c["classification"] in ("cargo", "beacon"):
            lines.append(
                f"|{c['path']}|{c['classification']}|{c['maturity']}"
                f"|{c['value_score']}|{c.get('target_repo_hint') or '-'}|")
    lines += ["", f"_{report['promotion_note']}_", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only salvage survey: mature local work absent "
                    "from the official system of record.")
    parser.add_argument("--persist-report", action="store_true",
                        help="Write JSON+MD reports to reports/analysis/.")
    args = parser.parse_args(argv)

    report = run_scan()
    print(json.dumps(report["summary"], indent=2))
    if args.persist_report:
        REPORT_JSON.write_text(json.dumps(report, indent=1))
        REPORT_MD.write_text(render_md(report))
        print(f"\nwrote {REPORT_JSON.relative_to(ROOT)}")
        print(f"wrote {REPORT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
