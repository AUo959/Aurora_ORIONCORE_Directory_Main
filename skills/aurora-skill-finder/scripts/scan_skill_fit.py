#!/usr/bin/env python3
"""Aurora skill-to-module mapper with deterministic precision-first scoring."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCANNER_VERSION = "1.1.0"
BOOSTED_SINGLE_CHANNEL_CAP = 0.96

CANDIDATE_EXTENSIONS = {
    ".py",
    ".js",
    ".mjs",
    ".ts",
    ".sh",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".toml",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".mjs",
    ".ts",
    ".sh",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".toml",
    ".txt",
    ".csv",
}

EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

ARCHIVE_HINT_MARKERS = (
    "archive",
    "archives",
    "legacy",
    "redundant",
    "copy",
    "backup",
    "old",
)

NOISE_PATH_MARKERS = (
    "docs/operational/reports",
    "06_archives",
    "_redundant_files_archived",
)

FOCUSED_OPTIONAL_ROOTS = (
    "Aurora_New_11_9",
    "GUMAS_SIM_2.0",
    "GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19",
    "GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS",
)

STRUCTURAL_BOOSTS = (
    {
        "skill": "aurora-selective-integration",
        "path_fragment": "scripts/auto_selective_ingest_gate.py",
        "boost": 0.35,
        "reason": "selective ingest gate hotspot",
    },
    {
        "skill": "develop-web-game",
        "path_fragment": "duelsim_arena_game.html",
        "boost": 0.4,
        "reason": "duelsim playable web game hotspot",
    },
    {
        "skill": "aurora-python-ingest-autowire",
        "path_fragment": "pdp_v2_mvp/core/pneumatic_engine.py",
        "boost": 0.35,
        "reason": "pdp pneumatic engine hotspot",
    },
    {
        "skill": "aurora-canon-reconciler",
        "path_fragment": "canonrec",
        "boost": 0.28,
        "reason": "canonrec canonical hotspot",
    },
    {
        "skill": "aurora-quantum-forge-ops",
        "path_fragment": "gumas_sim_2.5/forge__gumas_v3.0__2026-02-19/charforge.py",
        "boost": 0.38,
        "reason": "quantum forge charforge hotspot",
    },
    {
        "skill": "aurora-quantum-forge-ops",
        "path_fragment": "gumas_sim_2.5/forge__gumas_v3.0__2026-02-19/forge_manifest.md",
        "boost": 0.32,
        "reason": "quantum forge manifest hotspot",
    },
    {
        "skill": "gumas-simulation-engine",
        "path_fragment": "gumas_sim_2.5/sim_engine_outputs/engine_base.py",
        "boost": 0.38,
        "reason": "simulation engine core hotspot",
    },
    {
        "skill": "gumas-simulation-engine",
        "path_fragment": "gumas_sim_2.5/sim_engine_outputs/models.py",
        "boost": 0.32,
        "reason": "simulation engine model hotspot",
    },
)

CATALOG_PROFILES = {
    "session": "session_skill_catalog.json",
    "aurora-core": "aurora_core_skill_catalog.json",
    "general-utility": "general_utility_skill_catalog.json",
}

GOVERNANCE_FAMILY_HINTS = {
    "threadcore": ("threadcore", "threadreflect", "beacon", "checkpoint", "continuity", "delta"),
    "zipwiz": ("zipwiz", "zipwizard", "bundle.manifest", "staging_manifest", "zipcomm"),
    "script_governor": ("script_governance", "branch_manager", "setup", "cleanup", "wrapper"),
    "narrative_tone": ("narrative linter", "anti-flourish", "cadence", "tone governance", "narrlint"),
    "repo_stabilizer": ("pre-commit", "pre-push", ".github/workflows", "hooks", "maintenance", "repo_health"),
}

GOVERNANCE_SPECIALISTS = {
    "threadcore-governor",
    "zipwiz-governor",
    "aurora-script-governor",
    "aurora-narrative-tone-governor",
    "aurora-repo-stabilizer",
}

OVERLAP_RULES = (
    {
        "skills": ("aurora-repo-stabilizer", "aurora-script-governor"),
        "prefer": "aurora-script-governor",
        "tokens": ("branch_manager.py", "script_governance_scan.py", "setup", "cleanup", "wrapper"),
        "boost": 0.12,
        "penalty": 0.1,
        "reason": "script-surface signals prefer script governor",
    },
    {
        "skills": ("aurora-repo-stabilizer", "aurora-script-governor"),
        "prefer": "aurora-repo-stabilizer",
        "tokens": ("pre-commit", "pre-push", ".github/workflows", "hooks", "maintenance", "validation loop"),
        "boost": 0.12,
        "penalty": 0.1,
        "reason": "repo-ops signals prefer repo stabilizer",
    },
    {
        "skills": ("aurora-exec-brief-pipeline", "aurora-selective-integration"),
        "prefer": "aurora-selective-integration",
        "tokens": ("selective_integration", "modules_manifest", "triage_overrides", "backup_only", "rollback"),
        "boost": 0.14,
        "penalty": 0.1,
        "reason": "selective intake signals prefer selective integration",
    },
    {
        "skills": ("aurora-exec-brief-pipeline", "aurora-selective-integration"),
        "prefer": "aurora-exec-brief-pipeline",
        "tokens": ("executive brief", "leadership summary", "decision snapshot", "risk summary", "workflow_output"),
        "boost": 0.14,
        "penalty": 0.1,
        "reason": "briefing signals prefer executive brief pipeline",
    },
)


@dataclass(frozen=True)
class SkillEntry:
    name: str
    description: str
    include_keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...]
    path_hints: tuple[str, ...]
    filetype_bias: dict[str, float]
    min_confidence_override: float | None = None


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_slashes(value: str) -> str:
    return value.replace("\\", "/")


def tokenize(value: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", value.lower()) if len(tok) >= 2}


def contains_keyword(text: str, keyword: str) -> bool:
    kw = keyword.strip().lower()
    if not kw:
        return False
    if " " in kw or "_" in kw or "-" in kw:
        return kw in text
    return re.search(rf"\b{re.escape(kw)}\b", text) is not None


def is_archive_like(path_lower: str) -> bool:
    return any(marker in path_lower for marker in ARCHIVE_HINT_MARKERS)


def is_noise_path(path_lower: str) -> bool:
    return any(marker in path_lower for marker in NOISE_PATH_MARKERS)


def confidence_band(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.60:
        return "medium"
    return "low"


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def load_catalog(path: Path) -> tuple[list[SkillEntry], dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw_skills = raw.get("skills", []) if isinstance(raw, dict) else []
    if not isinstance(raw_skills, list):
        raise ValueError("Catalog file must contain a top-level 'skills' array.")

    entries: list[SkillEntry] = []
    for row in raw_skills:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        description = str(row.get("description", "")).strip()
        include_keywords = tuple(str(x).lower() for x in row.get("include_keywords", []) if str(x).strip())
        exclude_keywords = tuple(str(x).lower() for x in row.get("exclude_keywords", []) if str(x).strip())
        path_hints = tuple(normalize_slashes(str(x).lower()) for x in row.get("path_hints", []) if str(x).strip())
        filetype_bias_raw = row.get("filetype_bias", {})
        filetype_bias = {}
        if isinstance(filetype_bias_raw, dict):
            for ext, bias in filetype_bias_raw.items():
                try:
                    filetype_bias[str(ext).lower()] = float(bias)
                except (TypeError, ValueError):
                    continue
        min_override = row.get("min_confidence_override")
        min_confidence_override = None
        if min_override is not None:
            try:
                min_confidence_override = float(min_override)
            except (TypeError, ValueError):
                min_confidence_override = None

        entries.append(
            SkillEntry(
                name=name,
                description=description,
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
                path_hints=path_hints,
                filetype_bias=filetype_bias,
                min_confidence_override=min_confidence_override,
            )
        )

    entries.sort(key=lambda item: item.name)
    metadata = {
        "catalog_path": str(path.resolve()),
        "catalog_version": raw.get("catalog_version") if isinstance(raw, dict) else None,
        "catalog_scope": raw.get("catalog_scope") if isinstance(raw, dict) else None,
        "skill_count": len(entries),
    }
    return entries, metadata


def discover_git_repos(root: Path) -> list[Path]:
    repos: set[Path] = set()

    for dirpath, dirnames, _ in os.walk(root, topdown=True):
        if ".git" in dirnames:
            repos.add(Path(dirpath).resolve())

        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIR_NAMES]

    return sorted(repos)


def resolve_scan_roots(root: Path, scope: str, include_archives: bool) -> list[Path]:
    if scope == "full":
        return [root.resolve()]

    repos = discover_git_repos(root)
    if scope == "repos-only":
        return repos if repos else [root.resolve()]

    resolved: list[Path] = list(repos)
    for child_name in FOCUSED_OPTIONAL_ROOTS:
        child = root / child_name
        if child.exists() and child.is_dir():
            resolved.append(child.resolve())

    if include_archives:
        for child in root.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                resolved.append(child.resolve())

    unique = sorted(set(resolved))
    return unique if unique else [root.resolve()]


def read_content_snippet(path: Path, max_bytes: int = 12000) -> str:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return ""

    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes)
        return raw.decode("utf-8", errors="ignore").lower()
    except OSError:
        return ""


def keyword_hits(path_text: str, content_text: str, keywords: tuple[str, ...]) -> tuple[list[str], list[str]]:
    path_matches: list[str] = []
    content_matches: list[str] = []

    for keyword in dict.fromkeys(keywords):
        if contains_keyword(path_text, keyword):
            path_matches.append(keyword)
        if contains_keyword(content_text, keyword):
            content_matches.append(keyword)

    return path_matches, content_matches


def hint_hits(path_text: str, hints: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for hint in dict.fromkeys(hints):
        if hint and hint in path_text:
            hits.append(hint)
    return hits


def structural_boost(skill_name: str, path_text: str) -> tuple[float, list[str]]:
    score = 0.0
    evidence: list[str] = []
    for row in STRUCTURAL_BOOSTS:
        if row["skill"] != skill_name:
            continue
        if str(row["path_fragment"]) in path_text:
            score += float(row["boost"])
            evidence.append(f"structural boost: {row['reason']} (+{row['boost']:.2f})")
    return score, evidence


def governance_family_hits(path_text: str, content_text: str) -> list[str]:
    haystack = f"{path_text} {content_text}"
    hits: list[str] = []
    for family, tokens in GOVERNANCE_FAMILY_HINTS.items():
        if any(token in haystack for token in tokens):
            hits.append(family)
    return hits


def overlap_adjustment(skill_name: str, path_text: str, content_text: str) -> tuple[float, list[str]]:
    haystack = f"{path_text} {content_text}"
    score = 0.0
    evidence: list[str] = []

    families = governance_family_hits(path_text, content_text)
    if len(families) >= 2:
        if skill_name == "aurora-governance-orchestrator":
            score += 0.18
            evidence.append(
                f"overlap boost: multi-domain governance context ({', '.join(families[:3])}) favors orchestrator (+0.18)"
            )
        elif skill_name in GOVERNANCE_SPECIALISTS:
            score -= 0.08
            evidence.append(
                f"overlap penalty: multi-domain governance context ({', '.join(families[:3])}) favors orchestrator (-0.08)"
            )

    for rule in OVERLAP_RULES:
        hits = [token for token in rule["tokens"] if token in haystack]
        if not hits:
            continue
        if skill_name == rule["prefer"]:
            score += float(rule["boost"])
            evidence.append(
                f"overlap boost: {rule['reason']} (+{float(rule['boost']):.2f})"
            )
        elif skill_name in rule["skills"]:
            score -= float(rule["penalty"])
            evidence.append(
                f"overlap penalty: {rule['reason']} (-{float(rule['penalty']):.2f})"
            )

    return score, evidence


def score_skill_match(
    *,
    entry: SkillEntry,
    relative_path: str,
    project_relative_path: str,
    content_text: str,
    extension: str,
    scope: str,
) -> dict[str, Any]:
    path_text = normalize_slashes(project_relative_path.lower())
    include_path_hits, include_content_hits = keyword_hits(path_text, content_text, entry.include_keywords)
    exclude_path_hits, exclude_content_hits = keyword_hits(path_text, content_text, entry.exclude_keywords)
    path_hint_hits = hint_hits(path_text, entry.path_hints)

    score = 0.0
    score += min(0.54, 0.18 * len(include_path_hits))
    score += min(0.24, 0.06 * len(include_content_hits))
    score += min(0.42, 0.14 * len(path_hint_hits))
    score += float(entry.filetype_bias.get(extension, 0.0))

    has_path_support = bool(include_path_hits or path_hint_hits)
    has_content_support = bool(include_content_hits)

    exclude_hit_count = len(set(exclude_path_hits + exclude_content_hits))
    score -= min(0.72, 0.24 * exclude_hit_count)

    if is_archive_like(path_text):
        score -= 0.1
    if is_noise_path(path_text):
        score -= 0.15
    if scope == "focused" and ("/archive" in path_text or "_archive" in path_text):
        score -= 0.04

    boost_value, boost_evidence = structural_boost(entry.name, path_text)
    score += boost_value
    single_channel_cap_applied = False
    if boost_value > 0 and not (has_path_support and has_content_support) and score > BOOSTED_SINGLE_CHANNEL_CAP:
        score = BOOSTED_SINGLE_CHANNEL_CAP
        single_channel_cap_applied = True

    overlap_value, overlap_evidence = overlap_adjustment(entry.name, path_text, content_text)
    score += overlap_value

    score = clamp_score(score)

    evidence: list[str] = []
    evidence.extend(boost_evidence)
    if single_channel_cap_applied:
        evidence.append(
            f"single-channel boost cap applied ({BOOSTED_SINGLE_CHANNEL_CAP:.2f} max without path+content support)"
        )
    evidence.extend(overlap_evidence)
    if exclude_hit_count:
        evidence.append(f"boundary penalty: {exclude_hit_count} exclude keyword hit(s)")
    if is_archive_like(path_text):
        evidence.append("archive penalty applied")
    if is_noise_path(path_text):
        evidence.append("noise-path penalty applied")
    evidence.extend([f"path hint: {hit}" for hit in path_hint_hits[:2]])
    evidence.extend([f"path keyword: {hit}" for hit in include_path_hits[:3]])
    evidence.extend([f"content keyword: {hit}" for hit in include_content_hits[:2]])
    if extension in entry.filetype_bias:
        evidence.append(f"filetype bias: {extension} ({entry.filetype_bias[extension]:+.2f})")

    return {
        "skill": entry.name,
        "score": score,
        "confidence": confidence_band(score) if score > 0 else "low",
        "evidence": evidence[:6],
    }


def iter_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    seen_dirs: set[Path] = set()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=True):
        current_dir = Path(dirpath)
        try:
            resolved_dir = current_dir.resolve()
        except OSError:
            dirnames[:] = []
            continue
        if resolved_dir in seen_dirs:
            dirnames[:] = []
            continue
        seen_dirs.add(resolved_dir)

        kept_dirnames: list[str] = []
        for dirname in dirnames:
            if dirname in EXCLUDED_DIR_NAMES:
                continue
            child_dir = current_dir / dirname
            try:
                resolved_child = child_dir.resolve()
            except OSError:
                continue
            if resolved_child in seen_dirs:
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in filenames:
            candidate = Path(dirpath) / filename
            if candidate.suffix.lower() in CANDIDATE_EXTENSIONS:
                files.append(candidate)

    files.sort()
    return files


def build_root_report(
    *,
    project_root: Path,
    scan_root: Path,
    entries: list[SkillEntry],
    catalog_meta: dict[str, Any],
    scope: str,
    min_score: float,
    max_skills_per_module: int,
    max_modules_per_skill: int,
) -> dict[str, Any]:
    started = time.perf_counter()

    modules_view: list[dict[str, Any]] = []
    ambiguity_queue: list[dict[str, Any]] = []
    per_skill_matches: dict[str, list[dict[str, Any]]] = defaultdict(list)

    candidate_files = iter_candidate_files(scan_root)

    for file_path in candidate_files:
        relative_path = normalize_slashes(str(file_path.relative_to(scan_root)))
        project_relative_path = normalize_slashes(str(file_path.relative_to(project_root)))
        extension = file_path.suffix.lower()
        content_text = read_content_snippet(file_path)

        scored_rows: list[dict[str, Any]] = []
        for entry in entries:
            row = score_skill_match(
                entry=entry,
                relative_path=relative_path,
                project_relative_path=project_relative_path,
                content_text=content_text,
                extension=extension,
                scope=scope,
            )
            if row["score"] <= 0:
                continue

            threshold = max(min_score, entry.min_confidence_override or 0.0)
            row["threshold"] = round(threshold, 4)
            row["accepted"] = row["score"] >= threshold
            scored_rows.append(row)

        scored_rows.sort(key=lambda item: (-item["score"], item["skill"]))
        accepted = [row for row in scored_rows if row["accepted"]]

        if accepted:
            accepted_top = accepted[:max_skills_per_module]
            module_entry = {
                "path": str(file_path.resolve()),
                "relative_path": relative_path,
                "scan_root": str(scan_root.resolve()),
                "matches": accepted_top,
                "best_score": accepted_top[0]["score"],
            }
            modules_view.append(module_entry)

            for match in accepted_top:
                per_skill_matches[match["skill"]].append(
                    {
                        "path": module_entry["path"],
                        "relative_path": module_entry["relative_path"],
                        "scan_root": module_entry["scan_root"],
                        "score": match["score"],
                        "confidence": match["confidence"],
                        "evidence": match["evidence"],
                    }
                )

        top_score = scored_rows[0]["score"] if scored_rows else 0.0
        second_score = scored_rows[1]["score"] if len(scored_rows) > 1 else 0.0
        score_delta = round(top_score - second_score, 4) if len(scored_rows) > 1 else None

        borderline_no_accept = not accepted and top_score >= round(min_score * 0.75, 4)
        close_conflict = bool(scored_rows) and len(scored_rows) > 1 and top_score >= round(min_score * 0.9, 4) and score_delta < 0.08
        close_accepted_conflict = len(accepted) > 1 and (accepted[0]["score"] - accepted[1]["score"]) < 0.08

        if borderline_no_accept or close_conflict or close_accepted_conflict:
            ambiguity_queue.append(
                {
                    "path": str(file_path.resolve()),
                    "relative_path": relative_path,
                    "scan_root": str(scan_root.resolve()),
                    "reason": (
                        "no accepted score above threshold"
                        if borderline_no_accept
                        else "top skill scores are close"
                    ),
                    "score_delta": score_delta,
                    "candidates": scored_rows[:5],
                }
            )

    modules_view.sort(key=lambda item: (-item["best_score"], item["path"]))
    ambiguity_queue.sort(
        key=lambda item: (
            -float(item["candidates"][0]["score"] if item["candidates"] else 0.0),
            item["path"],
        )
    )

    skills_view: list[dict[str, Any]] = []
    for entry in entries:
        skill_matches = per_skill_matches.get(entry.name, [])
        if not skill_matches:
            continue
        skill_matches.sort(key=lambda item: (-item["score"], item["path"]))
        skills_view.append(
            {
                "skill": entry.name,
                "description": entry.description,
                "matched_modules_count": len(skill_matches),
                "modules": skill_matches[:max_modules_per_skill],
            }
        )

    skills_view.sort(
        key=lambda item: (
            -float(item["modules"][0]["score"] if item["modules"] else 0.0),
            item["skill"],
        )
    )

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    report = {
        "metadata": {
            "scanner": "aurora-skill-finder",
            "version": SCANNER_VERSION,
            "generated_at_utc": now_utc(),
            "scope": scope,
            "mode": "single_root",
            "elapsed_ms": elapsed_ms,
            "min_score": min_score,
            "max_skills_per_module": max_skills_per_module,
            "max_modules_per_skill": max_modules_per_skill,
        },
        "scan_roots": [str(scan_root.resolve())],
        "catalog": {
            **catalog_meta,
            "skills": [
                {
                    "name": entry.name,
                    "description": entry.description,
                }
                for entry in entries
            ],
        },
        "excluded_paths": sorted(EXCLUDED_DIR_NAMES),
        "skills_view": skills_view,
        "modules_view": modules_view,
        "ambiguity_queue": ambiguity_queue,
        "stats": {
            "scan_root": str(scan_root.resolve()),
            "candidate_files": len(candidate_files),
            "matched_modules": len(modules_view),
            "skills_with_matches": len(skills_view),
            "ambiguity_count": len(ambiguity_queue),
        },
    }
    return report


def merge_reports(
    *,
    reports: list[dict[str, Any]],
    entries: list[SkillEntry],
    catalog_meta: dict[str, Any],
    scope: str,
    min_score: float,
    max_skills_per_module: int,
    max_modules_per_skill: int,
) -> dict[str, Any]:
    started = time.perf_counter()

    combined_modules: list[dict[str, Any]] = []
    combined_ambiguity: list[dict[str, Any]] = []
    per_skill_matches: dict[str, list[dict[str, Any]]] = defaultdict(list)

    total_candidates = 0
    total_matched = 0

    for report in reports:
        combined_modules.extend(report.get("modules_view", []))
        combined_ambiguity.extend(report.get("ambiguity_queue", []))
        stats = report.get("stats", {})
        total_candidates += int(stats.get("candidate_files", 0))
        total_matched += int(stats.get("matched_modules", 0))

        for skill_row in report.get("skills_view", []):
            skill_name = skill_row.get("skill")
            if not skill_name:
                continue
            per_skill_matches[skill_name].extend(skill_row.get("modules", []))

    combined_modules.sort(key=lambda item: (-float(item.get("best_score", 0.0)), item.get("path", "")))
    combined_ambiguity.sort(
        key=lambda item: (
            -float(item.get("candidates", [{}])[0].get("score", 0.0) if item.get("candidates") else 0.0),
            item.get("path", ""),
        )
    )

    skills_view: list[dict[str, Any]] = []
    for entry in entries:
        modules = per_skill_matches.get(entry.name, [])
        if not modules:
            continue
        modules.sort(key=lambda item: (-float(item.get("score", 0.0)), item.get("path", "")))
        skills_view.append(
            {
                "skill": entry.name,
                "description": entry.description,
                "matched_modules_count": len(modules),
                "modules": modules[:max_modules_per_skill],
            }
        )

    skills_view.sort(
        key=lambda item: (
            -float(item["modules"][0]["score"] if item["modules"] else 0.0),
            item["skill"],
        )
    )

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    scan_roots = [root for report in reports for root in report.get("scan_roots", [])]

    return {
        "metadata": {
            "scanner": "aurora-skill-finder",
            "version": SCANNER_VERSION,
            "generated_at_utc": now_utc(),
            "scope": scope,
            "mode": "combined",
            "elapsed_ms": elapsed_ms,
            "min_score": min_score,
            "max_skills_per_module": max_skills_per_module,
            "max_modules_per_skill": max_modules_per_skill,
        },
        "scan_roots": sorted(dict.fromkeys(scan_roots)),
        "catalog": {
            **catalog_meta,
            "skills": [
                {
                    "name": entry.name,
                    "description": entry.description,
                }
                for entry in entries
            ],
        },
        "excluded_paths": sorted(EXCLUDED_DIR_NAMES),
        "skills_view": skills_view,
        "modules_view": combined_modules,
        "ambiguity_queue": combined_ambiguity,
        "stats": {
            "candidate_files": total_candidates,
            "matched_modules": total_matched,
            "skills_with_matches": len(skills_view),
            "ambiguity_count": len(combined_ambiguity),
            "root_count": len(sorted(dict.fromkeys(scan_roots))),
            "per_root": [report.get("stats", {}) for report in reports],
        },
    }


def build_stats_block(stats: dict[str, Any]) -> str:
    lines = []
    for key in sorted(stats.keys()):
        value = stats[key]
        if isinstance(value, list):
            lines.append(f"- **{key}**: {len(value)} item(s)")
        else:
            lines.append(f"- **{key}**: {value}")
    return "\n".join(lines) if lines else "- No stats available"


def build_skills_block(skills_view: list[dict[str, Any]], max_items: int = 20) -> str:
    if not skills_view:
        return "No skill matches above threshold."

    lines: list[str] = []
    for row in skills_view[:max_items]:
        lines.append(f"### {row['skill']} ({row['matched_modules_count']} matches)")
        for module in row.get("modules", [])[:5]:
            lines.append(
                f"- `{module['relative_path']}` | score `{module['score']:.4f}` | confidence `{module['confidence']}`"
            )
        lines.append("")

    return "\n".join(lines).strip()


def build_modules_block(modules_view: list[dict[str, Any]], max_items: int = 40) -> str:
    if not modules_view:
        return "No module mappings above threshold."

    lines: list[str] = []
    for module in modules_view[:max_items]:
        match_preview = ", ".join(
            f"{match['skill']} ({match['score']:.3f})"
            for match in module.get("matches", [])[:3]
        )
        lines.append(f"- `{module['relative_path']}` -> {match_preview}")

    return "\n".join(lines)


def build_ambiguity_block(ambiguity_queue: list[dict[str, Any]], max_items: int = 30) -> str:
    if not ambiguity_queue:
        return "No ambiguity items."

    lines: list[str] = []
    for item in ambiguity_queue[:max_items]:
        top = item.get("candidates", [])[:3]
        candidate_preview = ", ".join(f"{cand['skill']} ({cand['score']:.3f})" for cand in top)
        lines.append(f"- `{item['relative_path']}` | {item['reason']} | {candidate_preview}")
    return "\n".join(lines)


def render_markdown_report(report: dict[str, Any], template_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    roots = report.get("scan_roots", [])
    root_list = "\n".join(f"- `{root}`" for root in roots) if roots else "- None"

    rendered = template.format(
        generated_at=report.get("metadata", {}).get("generated_at_utc", now_utc()),
        scope=report.get("metadata", {}).get("scope", "unknown"),
        root_count=len(roots),
        root_list=root_list,
        stats_block=build_stats_block(report.get("stats", {})),
        skills_block=build_skills_block(report.get("skills_view", [])),
        modules_block=build_modules_block(report.get("modules_view", [])),
        ambiguity_block=build_ambiguity_block(report.get("ambiguity_queue", [])),
    )
    return rendered


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_catalog_path(script_dir: Path, catalog: str | None, catalog_profile: str | None) -> Path:
    if catalog_profile:
        relative_name = CATALOG_PROFILES[catalog_profile]
        return (script_dir.parent / "references" / relative_name).resolve()
    if catalog:
        return Path(catalog).expanduser().resolve()
    return (script_dir.parent / "references" / CATALOG_PROFILES["session"]).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Map repository files to best matching Codex skills.")
    parser.add_argument("--root", required=True, help="Root path to scan")
    parser.add_argument(
        "--scope",
        choices=("focused", "repos-only", "full"),
        default="focused",
        help="Scan scope mode",
    )
    parser.add_argument(
        "--catalog",
        help="Optional explicit catalog JSON path",
    )
    parser.add_argument(
        "--catalog-profile",
        choices=tuple(CATALOG_PROFILES.keys()),
        help="Optional built-in catalog profile name",
    )
    parser.add_argument("--out-json", help="Optional JSON output path for merged report")
    parser.add_argument("--out-md", help="Optional Markdown output path for merged report")
    parser.add_argument("--min-score", type=float, default=0.45, help="Global minimum score threshold")
    parser.add_argument(
        "--max-skills-per-module",
        type=int,
        default=3,
        help="Max accepted skills stored per module/path",
    )
    parser.add_argument(
        "--max-modules-per-skill",
        type=int,
        default=25,
        help="Max modules stored under each skill",
    )
    parser.add_argument(
        "--include-archives",
        action="store_true",
        help="Include archive-heavy top-level directories in focused scope root resolution",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    return parser.parse_args()


def write_report_files(report: dict[str, Any], json_path: Path, md_path: Path, pretty: bool, template_path: Path) -> None:
    ensure_parent(json_path)
    ensure_parent(md_path)

    markdown = render_markdown_report(report, template_path)
    md_path.write_text(markdown + "\n", encoding="utf-8")

    indent = 2 if pretty else None
    payload = json.dumps(report, indent=indent, ensure_ascii=False, sort_keys=bool(indent))
    json_path.write_text(payload + "\n", encoding="utf-8")


def default_output_paths(scan_root: Path, timestamp: str) -> tuple[Path, Path]:
    output_dir = scan_root / "workflow_output" / "skill_finder"
    stem = f"skill_map_{timestamp}"
    return output_dir / f"{stem}.json", output_dir / f"{stem}.md"


def normalize_output_pair(out_json: str | None, out_md: str | None, timestamp: str) -> tuple[Path, Path]:
    if out_json and out_md:
        return Path(out_json).resolve(), Path(out_md).resolve()

    if out_json and not out_md:
        json_path = Path(out_json).resolve()
        return json_path, json_path.with_suffix(".md")

    if out_md and not out_json:
        md_path = Path(out_md).resolve()
        return md_path.with_suffix(".json"), md_path

    fallback = Path("/tmp") / f"skill_map_{timestamp}"
    return fallback.with_suffix(".json"), fallback.with_suffix(".md")


def main() -> int:
    args = parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root path does not exist or is not a directory: {root}")

    script_dir = Path(__file__).resolve().parent
    catalog_path = resolve_catalog_path(script_dir, args.catalog, args.catalog_profile)
    if not catalog_path.exists():
        raise SystemExit(f"Catalog file not found: {catalog_path}")

    template_path = Path(__file__).resolve().parent.parent / "assets" / "templates" / "skill_finder_report.md"
    if not template_path.exists():
        raise SystemExit(f"Report template not found: {template_path}")

    entries, catalog_meta = load_catalog(catalog_path)
    if not entries:
        raise SystemExit("Catalog has zero valid skills.")

    scan_roots = resolve_scan_roots(root, args.scope, args.include_archives)

    reports = [
        build_root_report(
            project_root=root,
            scan_root=scan_root,
            entries=entries,
            catalog_meta=catalog_meta,
            scope=args.scope,
            min_score=args.min_score,
            max_skills_per_module=max(1, args.max_skills_per_module),
            max_modules_per_skill=max(1, args.max_modules_per_skill),
        )
        for scan_root in scan_roots
    ]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    emitted: list[dict[str, str]] = []

    if args.out_json or args.out_md:
        combined = merge_reports(
            reports=reports,
            entries=entries,
            catalog_meta=catalog_meta,
            scope=args.scope,
            min_score=args.min_score,
            max_skills_per_module=max(1, args.max_skills_per_module),
            max_modules_per_skill=max(1, args.max_modules_per_skill),
        )
        out_json_path, out_md_path = normalize_output_pair(args.out_json, args.out_md, timestamp)
        write_report_files(combined, out_json_path, out_md_path, args.pretty, template_path)
        emitted.append({"scan_root": "<combined>", "json": str(out_json_path), "md": str(out_md_path)})
    else:
        for report in reports:
            scan_root = Path(report["scan_roots"][0])
            json_path, md_path = default_output_paths(scan_root, timestamp)
            write_report_files(report, json_path, md_path, args.pretty, template_path)
            emitted.append({"scan_root": str(scan_root), "json": str(json_path), "md": str(md_path)})

    summary = {
        "status": "ok",
        "scanner": "aurora-skill-finder",
        "version": SCANNER_VERSION,
        "scope": args.scope,
        "scan_root_count": len(scan_roots),
        "catalog_path": str(catalog_path),
        "outputs": emitted,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
