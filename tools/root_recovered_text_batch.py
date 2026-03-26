#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from _workspace_common import REPORTS_ANALYSIS_DIR, ROOT, ensure_parent, now_iso_utc, write_json


CHAT_PATTERNS = [
    re.compile(r"\bChatGPT said:\b", re.IGNORECASE),
    re.compile(r"\bGitHub Copilot:\b", re.IGNORECASE),
    re.compile(r"\bYou said:\b", re.IGNORECASE),
    re.compile(r"\bUser:\b", re.IGNORECASE),
    re.compile(r"^\s*AUo959:\s*", re.IGNORECASE),
    re.compile(r"^\s*Made changes\.\s*$", re.IGNORECASE),
]

PYTHON_PATTERNS = [
    re.compile(r"^\s*from\s+\w+\s+import\b"),
    re.compile(r"^\s*import\s+\w+"),
    re.compile(r"^\s*class\s+\w+"),
    re.compile(r"^\s*def\s+\w+\s*\("),
    re.compile(r"^\s*if __name__ == [\"']__main__[\"']"),
]

JAVASCRIPT_PATTERNS = [
    re.compile(r"^\s*const\s+\w+\s*="),
    re.compile(r"^\s*function\s+\w+\s*\("),
    re.compile(r"^\s*module\.exports\s*="),
    re.compile(r"^\s*export\s+(default|const|function|class)\b"),
]

CONFIG_PATTERNS = [
    re.compile(r"^\s*name:\s+"),
    re.compile(r"^\s*on:\s*$"),
    re.compile(r"^\s*jobs:\s*$"),
    re.compile(r"^\s*\"[A-Za-z0-9_-]+\"\s*:\s*"),
    re.compile(r"^\s*factions_registry:\s*$"),
]

FORMULA_PATTERNS = [
    re.compile(r"\\alpha|\\beta|\\gamma|\\lambda|\\delta"),
    re.compile(r"\bP\("),
    re.compile(r"\bQ\("),
    re.compile(r"^[A-Za-z0-9_{}'\-\s]+\s*=\s*.+$"),
]

PROMPT_PATTERNS = [
    re.compile(r"^\s*###\s+"),
    re.compile(r"^\s*##\s+"),
    re.compile(r"^\s*please\b", re.IGNORECASE),
    re.compile(r"\bOUTPUT FORMAT\b", re.IGNORECASE),
    re.compile(r"\bTRIGGER SHORTCUT\b", re.IGNORECASE),
    re.compile(r"\bAgent\b"),
    re.compile(r"```"),
]

SENSITIVE_PATTERNS = [
    re.compile(r"AES_KEY", re.IGNORECASE),
    re.compile(r"\bapi[_ -]?key\b", re.IGNORECASE),
    re.compile(r"\bprivate key\b", re.IGNORECASE),
    re.compile(r"\boverride authorization\b", re.IGNORECASE),
    re.compile(r"\binvoke .* key\b", re.IGNORECASE),
]

THEME_KEYWORDS = {
    "git_deploy": [
        "git",
        "github",
        "deploy",
        "repo",
        "branch",
        "commit",
        "codespace",
        "package",
        "workflow",
    ],
    "threadcore_continuity": [
        "threadcore",
        "threadreflect",
        "continuity",
        "anchor",
        "drift",
        "zipwiz",
        "patchweaver",
        "seal",
    ],
    "aurora_interface": [
        "aurora",
        "diagnostic",
        "session transfer",
        "middleware",
        "layer 1",
        "layer 2",
        "steward",
    ],
    "memory_system": [
        "memory",
        "archive",
        "registry",
        "retrieve",
        "decay",
        "store",
        "agent",
    ],
    "gumas_worldbuilding": [
        "galactic union",
        "chancellor",
        "separatist",
        "fleet",
        "zylox",
        "faction",
        "imperium",
        "pmc",
    ],
    "research_education": [
        "research",
        "report",
        "architecture",
        "overview",
        "students",
        "historical",
        "simulation management",
    ],
    "prompt_agent": [
        "prompt",
        "template",
        "agent",
        "inject",
        "companion",
        "markdown template",
    ],
    "security_sensitive": [
        "aes_key",
        "auth",
        "secure",
        "protection",
        "overwrite",
        "key ",
    ],
}

CATEGORY_BUCKETS = {
    "sensitive_or_auth": "_entropy_quarantine or security review",
    "python_prototype": "tools/prototypes/python",
    "javascript_module": "tools/prototypes/javascript",
    "config_manifest": "catalog/draft_manifests or .github/workflows",
    "simulation_logic": "GUMAS_SIM_2.5/draft_logic",
    "conversation_or_chat_export": "archives/conversation_recovery",
    "worldbuilding_registry": "GUMAS_SIM_2.5/draft_worldbuilding",
    "blueprint_or_protocol": "docs/draft_protocols",
    "research_brief": "reports/analysis/non_can_reports",
    "prompt_template_or_agent": "archives/prompt_recovery",
    "fragment_or_note": "manual_review_or_discard",
}


@dataclass(frozen=True)
class ExtractionSpec:
    source_name: str
    relative_output: str
    transform: str = "identity"


EXTRACTION_SPECS = [
    ExtractionSpec("text_mem_system_py.txt", "extracted_logic/python/memory_system_prototype.py"),
    ExtractionSpec("text_tagging_agent.txt", "extracted_logic/python/thread_context_tagging_agent.py"),
    ExtractionSpec("text_threadcore_3_6.txt", "extracted_logic/javascript/threadcore_v3_6_macrodrift.js"),
    ExtractionSpec("text_node_js_webpack.txt", "extracted_logic/config/github_actions_nodejs_webpack.yml"),
    ExtractionSpec("text_factions_reg.txt", "extracted_logic/config/factions_registry_draft.yaml"),
    ExtractionSpec("text_GitDeploy_root.txt", "extracted_logic/config/root_deploy_inventory_draft.json"),
    ExtractionSpec("text_early_sim_logic.txt", "extracted_logic/logic/early_simulation_formulas.md", "wrap_text_block"),
    ExtractionSpec("text_early_logic.txt", "extracted_logic/logic/galactic_union_state_variables.md", "wrap_text_block"),
    ExtractionSpec("text_Au_mod_core.txt", "extracted_logic/blueprints/aurora_modular_core_v2_3.md"),
    ExtractionSpec("text_Au_mod_core_first.txt", "extracted_logic/blueprints/aurora_modular_core_v2_1.md"),
    ExtractionSpec("text_GitIngestion.txt", "extracted_logic/blueprints/aurora_system_ingestion_pipeline_capsule_v1.md"),
    ExtractionSpec("text_Au_lite_agent.txt", "extracted_logic/blueprints/auroralite_bridge_agent.md"),
]


def iter_root_text_artifacts(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt"
    )


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalized_duplicate_key(text: str) -> str:
    normalized = normalize_whitespace(text).lower()
    normalized = re.sub(r"[\u2013\u2014\u2015]", "-", normalized)
    return normalized


def count_matches(lines: list[str], patterns: list[re.Pattern[str]]) -> int:
    score = 0
    for line in lines:
        if any(pattern.search(line) for pattern in patterns):
            score += 1
    return score


def detect_theme_scores(text: str) -> dict[str, int]:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        scores[theme] = sum(lowered.count(keyword) for keyword in keywords)
    return scores


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return normalize_whitespace(stripped)[:160]
    return ""


def detect_category(path: Path, text: str) -> tuple[str, dict[str, int], list[str]]:
    lines = text.splitlines()[:600]
    nonempty_lines = [line for line in text.splitlines() if line.strip()][:120]
    scores = {
        "python": count_matches(lines, PYTHON_PATTERNS),
        "javascript": count_matches(lines, JAVASCRIPT_PATTERNS),
        "config": count_matches(lines, CONFIG_PATTERNS),
        "formula": count_matches(lines, FORMULA_PATTERNS),
        "prompt": count_matches(lines, PROMPT_PATTERNS),
        "chat": count_matches(lines, CHAT_PATTERNS),
        "sensitive": count_matches(lines, SENSITIVE_PATTERNS),
    }
    themes = detect_theme_scores(text)
    top_themes = [
        theme
        for theme, score in sorted(themes.items(), key=lambda item: (-item[1], item[0]))
        if score > 0
    ][:3]
    lowered_name = path.name.lower()
    structured_config_lines = sum(
        1
        for line in nonempty_lines[:60]
        if re.match(r'^\s*"?[A-Za-z0-9_. -]+"?\s*:\s*(.+)?$', line)
    )
    registry_lines = sum(
        1
        for line in nonempty_lines[:80]
        if re.match(r'^\s*-\s+name:\s+', line) or re.match(r'^\s*factions_registry:\s*$', line)
    )
    blueprint_markers = sum(
        marker in text.lower()
        for marker in (
            "blueprint",
            "capsule metadata",
            "core functional layers",
            "core capabilities",
            "portability guide",
            "identity & role",
        )
    )
    is_json_blob = text.strip().startswith("{") and text.strip().endswith("}")

    if scores["sensitive"] > 0 or any(token in lowered_name for token in ("key", "auth", "aes")):
        category = "sensitive_or_auth"
    elif scores["chat"] >= 2:
        category = "conversation_or_chat_export"
    elif scores["python"] >= 2 and scores["python"] >= scores["javascript"]:
        category = "python_prototype"
    elif scores["javascript"] >= 2:
        category = "javascript_module"
    elif is_json_blob or (scores["config"] >= 2 and structured_config_lines >= 6):
        category = "config_manifest"
    elif scores["formula"] >= 3:
        category = "simulation_logic"
    elif blueprint_markers >= 2:
        category = "blueprint_or_protocol"
    elif registry_lines >= 2 or (themes["gumas_worldbuilding"] >= 4 and structured_config_lines >= 4):
        category = "worldbuilding_registry"
    elif themes["research_education"] >= 3:
        category = "research_brief"
    elif scores["prompt"] >= 3 or themes["prompt_agent"] >= 2:
        category = "prompt_template_or_agent"
    else:
        category = "fragment_or_note"

    return category, scores, top_themes


def usefulness_level(category: str, scores: dict[str, int], size_bytes: int) -> str:
    if category in {
        "python_prototype",
        "javascript_module",
        "config_manifest",
        "simulation_logic",
        "worldbuilding_registry",
        "blueprint_or_protocol",
    }:
        return "high"
    if category == "sensitive_or_auth":
        return "review"
    if category == "conversation_or_chat_export" and size_bytes > 20_000:
        return "medium"
    if category in {"research_brief", "prompt_template_or_agent"}:
        return "medium"
    return "low"


def action_label(category: str, usefulness: str, duplicate_group: str, normalized_duplicate_group: str) -> str:
    if category == "sensitive_or_auth":
        return "quarantine_and_review"
    if duplicate_group or normalized_duplicate_group:
        return "dedupe_then_review"
    if usefulness == "high":
        return "extract_and_route"
    if usefulness == "medium":
        return "review_for_naming"
    return "archive_or_discard"


def wrap_text_block(source_name: str, text: str) -> str:
    title = source_name.removesuffix(".txt").replace("_", " ")
    return (
        f"# {title}\n\n"
        f"Source: `{source_name}`\n\n"
        "```text\n"
        f"{text.rstrip()}\n"
        "```\n"
    )


TRANSFORMS: dict[str, Callable[[str, str], str]] = {
    "identity": lambda _source_name, text: text.rstrip() + "\n",
    "wrap_text_block": wrap_text_block,
}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    ensure_parent(path)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_readme(
    generated_at: str,
    artifact_count: int,
    category_counts: Counter[str],
    exact_duplicate_count: int,
    normalized_duplicate_count: int,
    extracted: list[dict[str, str]],
    high_priority_rows: list[dict[str, object]],
    sensitive_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Root Recovered Text Batch",
        "",
        "Status: staged, non-canon",
        f"Prepared: {generated_at}",
        "Source scope: top-level root `.txt` artifacts only",
        "",
        "## Purpose",
        "",
        "This bundle sorts and indexes the recovered root text artifacts without",
        "renaming or relocating the original files. The originals remain untouched",
        "at the repo root; this bundle provides the review surface we can use to",
        "name, dedupe, and move them safely in a later pass.",
        "",
        "## Inventory Snapshot",
        "",
        f"- Artifacts indexed: `{artifact_count}`",
        f"- Exact duplicate groups: `{exact_duplicate_count}`",
        f"- Normalized duplicate groups: `{normalized_duplicate_count}`",
        f"- Extracted logic/code files: `{len(extracted)}`",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in sorted(category_counts.items()):
        lines.append(f"- `{category}`: `{count}`")

    lines.extend(["", "## High-Priority Salvage Candidates", ""])
    for row in high_priority_rows[:20]:
        extracted_to = row.get("extracted_to") or "not auto-extracted"
        lines.append(
            f"- `{row['source_file']}` -> `{row['category']}` "
            f"[future bucket: `{row['future_bucket']}`; extracted: `{extracted_to}`]"
        )

    if sensitive_rows:
        lines.extend(["", "## Sensitive Review", ""])
        for row in sensitive_rows[:20]:
            lines.append(f"- `{row['source_file']}` [{row['action']}]")

    lines.extend(["", "## Outputs", ""])
    lines.append("- `artifact_index.csv`: full sortable review index")
    lines.append("- `artifact_inventory.json`: machine-readable inventory")
    lines.append("- `duplicate_groups.json`: exact and normalized duplicate clusters")
    lines.append("- `extraction_manifest.json`: provenance for extracted logic/code")
    lines.append("- `NAMING_AND_ROUTING_QUEUE.md`: curated shortlist for the rename-and-move pass")
    lines.append("- `extracted_logic/`: staged code, config, and blueprint recoveries")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Index recovered root text artifacts.")
    parser.add_argument("--root", default=None)
    parser.add_argument(
        "--output-dir",
        default=str(REPORTS_ANALYSIS_DIR / "recovered_root_text_batch__2026-03-20"),
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve() if args.root else ROOT
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = now_iso_utc()
    source_files = iter_root_text_artifacts(root)

    exact_hash_groups: defaultdict[str, list[str]] = defaultdict(list)
    normalized_groups: defaultdict[str, list[str]] = defaultdict(list)
    raw_text_by_name: dict[str, str] = {}

    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        raw_text_by_name[path.name] = text
        exact_hash_groups[text].append(path.name)
        normalized_groups[normalized_duplicate_key(text)].append(path.name)

    exact_group_ids: dict[str, str] = {}
    normalized_group_ids: dict[str, str] = {}

    exact_counter = 0
    for names in sorted((group for group in exact_hash_groups.values() if len(group) > 1), key=lambda item: item[0]):
        exact_counter += 1
        group_id = f"exact-{exact_counter:03d}"
        for name in names:
            exact_group_ids[name] = group_id

    normalized_counter = 0
    for key, names in sorted(normalized_groups.items(), key=lambda item: item[1][0]):
        if len(names) <= 1:
            continue
        exact_members = {exact_group_ids.get(name, "") for name in names}
        if len(exact_members) == 1 and "" not in exact_members:
            continue
        normalized_counter += 1
        group_id = f"normalized-{normalized_counter:03d}"
        for name in names:
            normalized_group_ids[name] = group_id

    extraction_manifest: list[dict[str, str]] = []
    extracted_map = {spec.source_name: spec for spec in EXTRACTION_SPECS}

    inventory_rows: list[dict[str, object]] = []
    category_counts: Counter[str] = Counter()

    for path in source_files:
        text = raw_text_by_name[path.name]
        category, scores, theme_tags = detect_category(path, text)
        usefulness = usefulness_level(category, scores, path.stat().st_size)
        exact_group = exact_group_ids.get(path.name, "")
        normalized_group = normalized_group_ids.get(path.name, "")
        action = action_label(category, usefulness, exact_group, normalized_group)
        extracted_to = ""
        if path.name in extracted_map:
            spec = extracted_map[path.name]
            transform = TRANSFORMS[spec.transform]
            rendered = transform(path.name, text)
            output_path = output_dir / spec.relative_output
            ensure_parent(output_path)
            output_path.write_text(rendered, encoding="utf-8")
            extracted_to = spec.relative_output
            extraction_manifest.append(
                {
                    "source_file": path.name,
                    "extracted_to": spec.relative_output,
                    "transform": spec.transform,
                }
            )

        row = {
            "source_file": path.name,
            "size_bytes": path.stat().st_size,
            "line_count": len(text.splitlines()),
            "category": category,
            "theme_tags": ",".join(theme_tags),
            "python_score": scores["python"],
            "javascript_score": scores["javascript"],
            "config_score": scores["config"],
            "formula_score": scores["formula"],
            "prompt_score": scores["prompt"],
            "chat_score": scores["chat"],
            "sensitive_score": scores["sensitive"],
            "usefulness": usefulness,
            "action": action,
            "future_bucket": CATEGORY_BUCKETS[category],
            "exact_duplicate_group": exact_group,
            "normalized_duplicate_group": normalized_group,
            "extracted_to": extracted_to,
            "first_line": first_nonempty_line(text),
        }
        inventory_rows.append(row)
        category_counts[category] += 1

    inventory_rows.sort(key=lambda row: (str(row["category"]), str(row["source_file"])))

    duplicate_groups = {
        "exact_duplicate_groups": [
            {
                "group_id": group_id,
                "members": sorted([name for name, assigned in exact_group_ids.items() if assigned == group_id]),
            }
            for group_id in sorted(set(exact_group_ids.values()))
        ],
        "normalized_duplicate_groups": [
            {
                "group_id": group_id,
                "members": sorted([name for name, assigned in normalized_group_ids.items() if assigned == group_id]),
            }
            for group_id in sorted(set(normalized_group_ids.values()))
        ],
    }

    high_priority_rows = [
        row
        for row in inventory_rows
        if row["usefulness"] == "high" or str(row["extracted_to"])
    ]
    sensitive_rows = [row for row in inventory_rows if row["category"] == "sensitive_or_auth"]

    write_csv(output_dir / "artifact_index.csv", inventory_rows)
    write_json(output_dir / "artifact_inventory.json", inventory_rows)
    write_json(output_dir / "duplicate_groups.json", duplicate_groups)
    write_json(output_dir / "extraction_manifest.json", extraction_manifest)

    readme = build_readme(
        generated_at=generated_at,
        artifact_count=len(inventory_rows),
        category_counts=category_counts,
        exact_duplicate_count=len(duplicate_groups["exact_duplicate_groups"]),
        normalized_duplicate_count=len(duplicate_groups["normalized_duplicate_groups"]),
        extracted=extraction_manifest,
        high_priority_rows=high_priority_rows,
        sensitive_rows=sensitive_rows,
    )
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
