#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from _workspace_common import (
    ensure_parent,
    load_yaml_like,
    now_iso_utc,
    resolve_root,
    serialized_root,
    sha256_path,
    write_json,
)


def load_batch(plan: dict[str, object], batch_id: str) -> dict[str, object]:
    for batch in plan["batches"]:
        if batch["batch_id"] == batch_id:
            return batch
    raise SystemExit(f"Unknown batch_id: {batch_id}")


def update_alias_status(root: Path, rows: list[dict[str, str]]) -> None:
    alias_path = root / "catalog" / "path_aliases.csv"
    if not alias_path.exists():
        return
    with alias_path.open("r", encoding="utf-8", newline="") as handle:
        existing = list(csv.DictReader(handle))
    row_map = {(row["legacy_path"], row["canonical_path"]): row for row in existing}
    for row in rows:
        key = (row["legacy_path"], row["canonical_path"])
        if key in row_map:
            row_map[key]["status"] = row["status"]
    with alias_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["legacy_path", "canonical_path", "status"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(sorted(row_map.values(), key=lambda item: item["legacy_path"]))


def execute_operations(
    root: Path,
    operations: list[dict[str, object]],
    execute: bool,
) -> dict[str, object]:
    result = {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "dry_run": not execute,
        "moved": [],
        "skipped": [],
        "errors": [],
    }
    alias_updates = []
    for operation in operations:
        source = root / str(operation["source"])
        destination = root / str(operation["destination"])
        pre_hash = str(operation["pre_hash"])
        post_hash = str(operation["post_hash"])
        path_kind = str(operation.get("path_kind") or ("tree" if source.is_dir() else "file"))
        if not source.exists():
            result["errors"].append(
                {"source": str(operation["source"]), "error": "source_missing"}
            )
            continue
        current_hash = sha256_path(source)
        if current_hash != pre_hash:
            result["errors"].append(
                {
                    "source": str(operation["source"]),
                    "error": "pre_hash_mismatch",
                    "expected": pre_hash,
                    "actual": current_hash,
                }
            )
            continue
        if not execute:
            result["moved"].append(
                {
                    "source": str(operation["source"]),
                    "destination": str(operation["destination"]),
                    "path_kind": path_kind,
                }
            )
            continue
        ensure_parent(destination)
        if destination.exists():
            result["errors"].append(
                {"source": str(operation["source"]), "error": "destination_exists"}
            )
            continue
        shutil.move(str(source), str(destination))
        moved_hash = sha256_path(destination)
        if moved_hash != post_hash:
            result["errors"].append(
                {
                    "source": str(operation["source"]),
                    "error": "post_hash_mismatch",
                    "expected": post_hash,
                    "actual": moved_hash,
                }
            )
            continue
        operation["applied_at"] = now_iso_utc()
        result["moved"].append(
            {
                "source": str(operation["source"]),
                "destination": str(operation["destination"]),
                "path_kind": path_kind,
            }
        )
        alias_updates.append(
            {
                "legacy_path": str(operation["source"]),
                "canonical_path": str(operation["destination"]),
                "status": "active",
            }
        )
    if execute and alias_updates:
        update_alias_status(root, alias_updates)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply planned workspace moves.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--plan", default=None)
    parser.add_argument("--batch-id")
    parser.add_argument("--rollback-manifest")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-unapproved", action="store_true")
    parser.add_argument(
        "--report-out",
        default=None,
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    report_out = (
        Path(args.report_out)
        if args.report_out
        else root / "reports" / "analysis" / "workspace_apply_moves_latest.json"
    )
    if args.rollback_manifest:
        rollback = load_yaml_like(Path(args.rollback_manifest))
        operations = rollback["operations"]
        result = execute_operations(root, operations, execute=args.execute)
        result["mode"] = "rollback"
        result["batch_id"] = rollback["batch_id"]
        write_json(report_out, result)
        return 1 if result["errors"] else 0

    if not args.batch_id:
        raise SystemExit("A --batch-id is required unless --rollback-manifest is set.")

    plan_path = Path(args.plan) if args.plan else root / "catalog" / "relocation_plan.json"
    plan = load_yaml_like(plan_path)
    batch = load_batch(plan, args.batch_id)
    operations = batch["operations"]
    if not args.allow_unapproved and any(not op["approved"] for op in operations) and args.execute:
        raise SystemExit("Refusing to execute unapproved operations.")
    if any(op["operation"] != "move" for op in operations):
        raise SystemExit("Only move operations are supported in phase 1.")
    rollback_manifest = root / str(batch["rollback_manifest"])
    if not rollback_manifest.exists():
        raise SystemExit(f"Missing rollback manifest: {rollback_manifest}")

    result = execute_operations(root, operations, execute=args.execute)
    result["mode"] = "forward"
    result["batch_id"] = batch["batch_id"]
    if args.execute and not result["errors"]:
        batch["status"] = "applied"
        write_json(plan_path, plan)
    write_json(report_out, result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
