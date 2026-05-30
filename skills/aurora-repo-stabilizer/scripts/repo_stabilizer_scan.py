#!/usr/bin/env python3
"""Repository script-surface scanner for Aurora repo stabilization."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

PLACEHOLDER_PATTERNS = [
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"mock[_ ]", re.IGNORECASE),
    re.compile(r"TODO", re.IGNORECASE),
    re.compile(r"return\s+[\"'].*placeholder", re.IGNORECASE),
]

HAZARD_PATTERNS = [
    re.compile(r"\bgit\s+di\b"),
    re.compile(r"[\"']git[\"']\s*,\s*[\"']di[\"']"),
    re.compile(r"print\(\"[^\n]*\{[^\n]*\}[^\n]*\"\)"),
]

SCRIPT_SUFFIXES = {".py", ".sh", ".js", ".cjs", ".mjs", ".ts", ".bash", ".zsh"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def normalize_stem(stem: str) -> str:
    normalized = stem.lower()
    normalized = re.sub(r"(?:[_-]v?\d+)$", "", normalized)
    normalized = re.sub(r"(?:[_-](?:enhanced|backup|final|clean|old|new|copy))$", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized or stem.lower()


def scan_file(path: Path, root: Path) -> Dict:
    text = read_text(path)
    rel = str(path.relative_to(root))
    size = path.stat().st_size
    lower_name = path.name.lower()

    placeholder_hits = [p.pattern for p in PLACEHOLDER_PATTERNS if p.search(text)]
    hazard_hits = [p.pattern for p in HAZARD_PATTERNS if p.search(text)]

    if size == 0:
        tier = "stub"
    elif lower_name.endswith(".disabled"):
        tier = "disabled"
    elif placeholder_hits or hazard_hits:
        tier = "risky"
    else:
        tier = "candidate"

    return {
        "path": rel,
        "bytes": size,
        "tier": tier,
        "placeholder_hits": placeholder_hits,
        "hazard_hits": hazard_hits,
        "normalized_stem": normalize_stem(path.stem),
    }


def find_script_files(repo_root: Path) -> List[Path]:
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.exists() or not scripts_dir.is_dir():
        return []

    files: List[Path] = []
    for path in scripts_dir.rglob("*"):
        if not path.is_file():
            continue
        lower = path.name.lower()
        if lower.endswith(".disabled"):
            files.append(path)
            continue
        if path.suffix.lower() in SCRIPT_SUFFIXES:
            files.append(path)
    return sorted(files)


def build_report(repo_root: Path) -> Dict:
    files = find_script_files(repo_root)
    scanned = [scan_file(path, repo_root) for path in files]

    by_tier = defaultdict(int)
    by_ext = defaultdict(int)
    stems = defaultdict(list)

    for item in scanned:
        by_tier[item["tier"]] += 1
        suffix = Path(item["path"]).suffix.lower() or "<none>"
        by_ext[suffix] += 1
        stems[item["normalized_stem"]].append(item["path"])

    potential_duplicates = [
        {"normalized_stem": stem, "paths": paths}
        for stem, paths in stems.items()
        if len(paths) > 1
    ]
    potential_duplicates.sort(key=lambda x: (-len(x["paths"]), x["normalized_stem"]))

    top_risky = [
        {
            "path": item["path"],
            "placeholder_hits": item["placeholder_hits"],
            "hazard_hits": item["hazard_hits"],
        }
        for item in scanned
        if item["tier"] == "risky"
    ]

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "scripts_dir": str(repo_root / "scripts"),
        "summary": {
            "total_script_files": len(scanned),
            "tier_counts": dict(sorted(by_tier.items())),
            "extension_counts": dict(sorted(by_ext.items())),
            "potential_duplicate_families": len(potential_duplicates),
        },
        "zero_byte_scripts": [item["path"] for item in scanned if item["bytes"] == 0],
        "disabled_scripts": [item["path"] for item in scanned if item["tier"] == "disabled"],
        "top_risky_scripts": top_risky[:30],
        "duplicate_families": potential_duplicates[:30],
        "files": scanned,
    }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Aurora repository scripts for stabilization risks.")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--out", help="Optional output JSON file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    report = build_report(repo_root)

    indent = 2 if args.pretty else None
    payload = json.dumps(report, indent=indent, sort_keys=bool(indent))

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")

    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
