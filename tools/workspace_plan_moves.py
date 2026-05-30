#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from _workspace_common import (
    detect_path_kind,
    load_yaml_like,
    now_iso_utc,
    relpath,
    resolve_root,
    serialized_root,
    sha256_path,
    write_csv,
    write_json,
)


BATCH_SUMMARIES = {
    "wave3_small_intake_files_initial": "Small loose root files into intake.",
    "wave3_small_structured_dirs_initial": "Small structured root directories into canonical reports/projects zones.",
    "wave3_staging_isolation_initial": "Sensitive or legacy root directories into _staging isolation.",
    "wave4_root_intake_cleanup_initial": "Late-discovered loose root files and collections into intake.",
}


def operation_key(operation: dict[str, object]) -> tuple[str, str, str]:
    return (
        str(operation["source"]),
        str(operation["destination"]),
        str(operation["operation"]),
    )


def load_existing_plan(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"batches": []}
    return load_yaml_like(path)


def merge_batch(existing: dict[str, object], generated: dict[str, object]) -> dict[str, object]:
    merged = dict(generated)
    previous_ops = {operation_key(op): op for op in existing.get("operations", [])}
    operations = []
    for operation in generated["operations"]:
        prior = previous_ops.get(operation_key(operation))
        candidate = dict(operation)
        if prior:
            candidate["approved"] = prior.get("approved", candidate["approved"])
            candidate["applied_at"] = prior.get("applied_at", candidate["applied_at"])
            if "path_kind" in prior and "path_kind" not in candidate:
                candidate["path_kind"] = prior["path_kind"]
        operations.append(candidate)
    merged["operations"] = operations
    prior_status = existing.get("status", generated.get("status", "planned"))
    if prior_status == "applied" and not all(op.get("applied_at") for op in operations):
        prior_status = generated.get("status", "planned")
    merged["status"] = prior_status
    return merged


def build_rollbacks(batch: dict[str, object]) -> dict[str, object]:
    rollback_ops = []
    for operation in batch["operations"]:
        rollback = {
            "batch_id": f"{batch['batch_id']}_rollback",
            "source": operation["destination"],
            "destination": operation["source"],
            "operation": "move",
            "pre_hash": operation["post_hash"],
            "post_hash": operation["pre_hash"],
            "rollback_source": operation["destination"],
            "reason": f"Rollback for {batch['batch_id']}",
            "approved": False,
            "applied_at": None,
        }
        if "path_kind" in operation:
            rollback["path_kind"] = operation["path_kind"]
        rollback_ops.append(rollback)
    return {
        "batch_id": f"{batch['batch_id']}_rollback",
        "for_batch": batch["batch_id"],
        "generated_at": now_iso_utc(),
        "operations": rollback_ops,
    }


def load_existing_aliases(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            (row["legacy_path"], row["canonical_path"]): row
            for row in csv.DictReader(handle)
        }


def merge_alias_rows(
    existing_rows: dict[tuple[str, str], dict[str, str]],
    generated_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    row_map = dict(existing_rows)
    for row in generated_rows:
        key = (row["legacy_path"], row["canonical_path"])
        prior = row_map.get(key)
        if prior:
            row["status"] = prior.get("status", row["status"])
        row_map[key] = row
    return sorted(row_map.values(), key=lambda item: (item["legacy_path"], item["canonical_path"]))


def summary_for_batch(batch_id: str) -> str:
    return BATCH_SUMMARIES.get(batch_id, f"Generated relocation batch for {batch_id}.")


def reason_for_entry(entry: dict[str, object]) -> str:
    notes = str(entry.get("notes", "")).strip()
    if notes:
        return notes
    return f"Relocate {entry['current_path']} into {entry['planned_path']}."


def build_generated_batches(root: Path, manifest: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    grouped_entries: dict[str, list[dict[str, object]]] = {}
    for entry in manifest["entries"]:
        if entry.get("status") != "planned_move":
            continue
        batch_id = str(entry.get("batch_id", "")).strip()
        if not batch_id:
            continue
        grouped_entries.setdefault(batch_id, []).append(entry)

    batches: list[dict[str, object]] = []
    alias_rows: list[dict[str, str]] = []
    for batch_id in sorted(grouped_entries):
        operations = []
        for entry in sorted(grouped_entries[batch_id], key=lambda item: str(item["current_path"])):
            source_path = root / str(entry["current_path"])
            if not source_path.exists():
                continue
            digest = sha256_path(source_path)
            operation = {
                "batch_id": batch_id,
                "source": str(entry["current_path"]),
                "destination": str(entry["planned_path"]),
                "operation": "move",
                "pre_hash": digest,
                "post_hash": digest,
                "rollback_source": str(entry["current_path"]),
                "reason": reason_for_entry(entry),
                "approved": False,
                "applied_at": None,
                "path_kind": detect_path_kind(source_path),
            }
            operations.append(operation)
            alias_rows.append(
                {
                    "legacy_path": str(entry["current_path"]),
                    "canonical_path": str(entry["planned_path"]),
                    "status": "pending",
                }
            )
        if not operations:
            continue
        batches.append(
            {
                "batch_id": batch_id,
                "status": "planned",
                "summary": summary_for_batch(batch_id),
                "rollback_manifest": f"catalog/rollback_{batch_id}.json",
                "operations": operations,
            }
        )
    return batches, alias_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate relocation batches.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--aliases-out", default=None)
    args = parser.parse_args()

    root = resolve_root(args.root)
    manifest_path = Path(args.manifest) if args.manifest else root / "catalog" / "workspace_manifest.yaml"
    manifest = load_yaml_like(manifest_path)
    plan_out = Path(args.out) if args.out else root / "catalog" / "relocation_plan.json"
    aliases_out = Path(args.aliases_out) if args.aliases_out else root / "catalog" / "path_aliases.csv"

    existing_plan = load_existing_plan(plan_out)
    existing_batches = {batch["batch_id"]: batch for batch in existing_plan.get("batches", [])}
    generated_batches, alias_rows = build_generated_batches(root, manifest)

    batches = []
    seen_batch_ids = set()
    for batch in generated_batches:
        batch_id = batch["batch_id"]
        if batch_id in existing_batches:
            batches.append(merge_batch(existing_batches[batch_id], batch))
        else:
            batches.append(batch)
        seen_batch_ids.add(batch_id)

    for batch_id, batch in existing_batches.items():
        if batch_id not in seen_batch_ids:
            batches.append(batch)

    batches.sort(key=lambda item: str(item["batch_id"]))

    relocation_plan = {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "policy": {
            "default_mode": "dry-run",
            "delete_allowed": False,
            "quarantine_required": True,
        },
        "manifest_generated_at": manifest["generated_at"],
        "batches": batches,
    }

    write_json(plan_out, relocation_plan)
    for batch in batches:
        rollback = build_rollbacks(batch)
        write_json(root / batch["rollback_manifest"], rollback)

    existing_aliases = load_existing_aliases(aliases_out)
    write_csv(
        aliases_out,
        merge_alias_rows(existing_aliases, alias_rows),
        fieldnames=["legacy_path", "canonical_path", "status"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
