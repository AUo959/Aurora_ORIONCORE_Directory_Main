#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from _workspace_common import (
    canonical_candidate,
    display_root,
    discover_nested_repos,
    dump_yaml_like,
    git,
    iter_archive_artifacts,
    load_classification_overrides,
    load_yaml_like,
    top_level_policy_records_with_redaction,
    normalize_family,
    now_iso_utc,
    repo_validation_command,
    relpath,
    resolve_root,
    serialized_root,
    sha256_file,
    write_json,
    write_jsonl,
)


def repo_registry_entry(root: Path, repo_rel: str) -> dict[str, str]:
    repo_path = root / repo_rel
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path).stdout.strip()
    head_sha = git(["rev-parse", "HEAD"], cwd=repo_path).stdout.strip()
    remotes = git(["remote"], cwd=repo_path).stdout.split()
    remote_status = "configured" if remotes else "no_remote_configured"
    return {
        "name": repo_path.name,
        "path": repo_rel,
        "branch": branch,
        "head_sha": head_sha,
        "remote_status": remote_status,
        "validation_command": repo_validation_command(repo_rel),
        "move_policy": "frozen_until_registry_adoption",
    }


def build_archive_inventory(
    root: Path,
    redacted_top_level_paths: set[str] | None = None,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    records: list[dict[str, object]] = []
    by_hash: defaultdict[str, list[str]] = defaultdict(list)
    by_family: defaultdict[str, list[str]] = defaultdict(list)
    stat_counter: Counter[str] = Counter()
    excluded_roots = redacted_top_level_paths or set()

    candidates = iter_archive_artifacts(root)
    for path in candidates:
        relative = relpath(path, root)
        top_level_name = Path(relative).parts[0]
        if top_level_name in excluded_roots:
            continue
        stat = path.stat()
        family = normalize_family(path.name)
        digest = sha256_file(path)
        record = {
            "path": relative,
            "size_bytes": stat.st_size,
            "sha256": digest,
            "mtime": int(stat.st_mtime),
            "family": family,
            "duplicate_class": "",
            "canonical_candidate": "",
            "quarantine_batch": "",
            "notes": "zero-byte artifact" if stat.st_size == 0 else "",
        }
        records.append(record)
        by_hash[digest].append(relative)
        by_family[family].append(relative)
        stat_counter["artifacts"] += 1
        stat_counter["bytes"] += stat.st_size

    for record in records:
        relative = str(record["path"])
        digest = str(record["sha256"])
        family = str(record["family"])
        if len(by_hash[digest]) > 1:
            record["duplicate_class"] = "hash_duplicate"
            record["canonical_candidate"] = canonical_candidate(by_hash[digest])
        elif len(by_family[family]) > 1:
            record["duplicate_class"] = "family_variant"
            record["canonical_candidate"] = canonical_candidate(by_family[family])
        else:
            record["duplicate_class"] = "unique"
            record["canonical_candidate"] = relative
    return records, dict(stat_counter)


def write_workspace_map(
    root: Path,
    path: Path,
    manifest: dict[str, object],
    repo_registry: dict[str, object],
    archive_inventory: list[dict[str, object]],
    overrides_path: Path,
    overrides_count: int,
    privacy_exclusion_counts: dict[str, int],
) -> None:
    entries = list(manifest["entries"])
    repos = list(repo_registry["repos"])
    zone_counts = Counter(entry["logical_zone"] for entry in entries)
    planned_moves = [entry for entry in entries if entry["status"] == "planned_move"]
    privacy_exclusion_total = sum(privacy_exclusion_counts.values())
    largest_archives = sorted(
        archive_inventory,
        key=lambda item: (-int(item["size_bytes"]), str(item["path"])),
    )[:10]

    lines = [
        "# Workspace Map",
        "",
        f"- Generated: `{manifest['generated_at']}`",
        f"- Root: `{display_root(root)}`",
        f"- Top-level entries cataloged: `{len(entries)}`",
        f"- Nested repos registered: `{len(repos)}`",
        f"- Archive or binary artifacts inventoried: `{len(archive_inventory)}`",
        f"- Classification overrides loaded: `{overrides_count}` from `{overrides_path.relative_to(root)}`",
        f"- Top-level paths excluded by privacy screen: `{privacy_exclusion_total}`",
        "",
        "## Zones",
        "",
    ]
    for zone, count in sorted(zone_counts.items()):
        lines.append(f"- `{zone}`: `{count}` top-level entries")

    lines.extend(["", "## Active Nested Repos", ""])
    for repo in repos:
        lines.append(
            f"- `{repo['name']}` at `{repo['path']}` "
            f"(branch `{repo['branch']}`, remote `{repo['remote_status']}`)"
        )

    lines.extend(["", "## Planned Move Candidates", ""])
    if planned_moves:
        for entry in planned_moves:
            lines.append(
                f"- `{entry['current_path']}` -> `{entry['planned_path']}` "
                f"({entry['kind']}"
                + (
                    f", batch `{entry['batch_id']}`"
                    if entry.get("batch_id")
                    else ""
                )
                + ")"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Privacy Screen", ""])
    if privacy_exclusion_counts:
        for reason, count in sorted(privacy_exclusion_counts.items()):
            lines.append(f"- `{reason}`: `{count}` top-level paths excluded")
    else:
        lines.append("- No top-level paths excluded")

    lines.extend(["", "## Largest Archive/Binary Artifacts", ""])
    for record in largest_archives:
        size_mb = int(record["size_bytes"]) / (1024 * 1024)
        lines.append(f"- `{record['path']}`: `{size_mb:.1f} MiB` [{record['duplicate_class']}]")

    lines.extend(
        [
            "",
            "## Reading Order",
            "",
            "1. `README.md` for the control-plane rules.",
            "2. `catalog/workspace_manifest.yaml` for top-level classification.",
            "3. `catalog/classification_overrides.yaml` for persistent non-default routing.",
            "4. `catalog/repo_registry.yaml` for nested repo validation boundaries.",
            "5. `catalog/relocation_plan.json` before any move execution.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Aurora workspace inventory.")
    parser.add_argument("--root", default=None)
    parser.add_argument(
        "--manifest-out",
        default=None,
    )
    parser.add_argument(
        "--inventory-out",
        default=None,
    )
    parser.add_argument(
        "--repo-registry-out",
        default=None,
    )
    parser.add_argument(
        "--workspace-map-out",
        default=None,
    )
    parser.add_argument(
        "--summary-out",
        default=None,
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    nested_repo_roots = discover_nested_repos(root)
    overrides_path = root / "catalog" / "classification_overrides.yaml"
    overrides = load_classification_overrides(overrides_path)

    entries, privacy_exclusion_counts, redacted_top_level_paths = top_level_policy_records_with_redaction(
        root,
        overrides=overrides,
        nested_repo_roots=set(nested_repo_roots),
    )
    entries = sorted(entries, key=lambda item: item["current_path"])

    manifest = {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "logical_taxonomy": [
            "repos",
            "projects",
            "archives",
            "reports",
            "docs",
            "catalog",
            "tools",
            "intake",
            "_staging",
        ],
        "entries": entries,
    }

    # Remote-only registry entries (spokes, registered-but-uncloned repos)
    # cannot be discovered locally, so regeneration must carry them over —
    # including any owner notes (e.g. security flags) they hold.
    preserved_remote_entries: list[dict[str, object]] = []
    existing_registry_path = root / "catalog" / "repo_registry.yaml"
    if existing_registry_path.exists():
        try:
            existing_registry = load_yaml_like(existing_registry_path) or {}
            preserved_remote_entries = [
                entry for entry in existing_registry.get("repos", [])
                if isinstance(entry, dict) and entry.get("remote_status") == "remote_only"
            ]
        except Exception:
            preserved_remote_entries = []

    repo_registry = {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "repos": [repo_registry_entry(root, repo_rel) for repo_rel in nested_repo_roots]
        + preserved_remote_entries,
    }

    archive_inventory, archive_stats = build_archive_inventory(
        root,
        redacted_top_level_paths=redacted_top_level_paths,
    )

    summary = {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "top_level_entry_count": len(entries),
        "logical_zone_counts": dict(Counter(entry["logical_zone"] for entry in entries)),
        "nested_repo_count": len(repo_registry["repos"]),
        "archive_artifact_count": archive_stats.get("artifacts", 0),
        "archive_artifact_bytes": archive_stats.get("bytes", 0),
        "planned_move_count": sum(1 for entry in entries if entry["status"] == "planned_move"),
        "override_count": len(overrides),
        "privacy_exclusion_count": sum(privacy_exclusion_counts.values()),
        "privacy_exclusion_reasons": privacy_exclusion_counts,
    }

    manifest_out = Path(args.manifest_out) if args.manifest_out else root / "catalog" / "workspace_manifest.yaml"
    inventory_out = Path(args.inventory_out) if args.inventory_out else root / "catalog" / "archive_inventory.jsonl"
    repo_registry_out = Path(args.repo_registry_out) if args.repo_registry_out else root / "catalog" / "repo_registry.yaml"
    workspace_map_out = Path(args.workspace_map_out) if args.workspace_map_out else root / "docs" / "workspace-map.md"
    summary_out = Path(args.summary_out) if args.summary_out else root / "reports" / "analysis" / "workspace_scan_summary.json"

    dump_yaml_like(manifest, manifest_out)
    dump_yaml_like(repo_registry, repo_registry_out)
    write_jsonl(inventory_out, archive_inventory)
    write_json(summary_out, summary)
    write_workspace_map(
        root,
        workspace_map_out,
        manifest,
        repo_registry,
        archive_inventory,
        overrides_path,
        len(overrides),
        privacy_exclusion_counts,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
