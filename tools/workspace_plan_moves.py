#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path

from _workspace_common import (
    CATALOG_DIR,
    dump_yaml_like,
    load_yaml_like,
    now_iso_utc,
    relpath,
    resolve_root,
    sha256_file,
    write_csv,
    write_json,
)


def operation_key(operation: dict[str, object]) -> tuple[str, str, str]:
    return (
        str(operation["source"]),
        str(operation["destination"]),
        str(operation["operation"]),
    )


def automation_id_for(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("archive_entropy_guard"):
        return "archive-entropy-guard"
    return "legacy-import"


def date_for(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else date.today().isoformat()


def build_automation_reports_batch(root: Path) -> dict[str, object] | None:
    source_dir = root / "Automation_Reports"
    if not source_dir.exists():
        return None

    operations: list[dict[str, object]] = []
    for source_path in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        automation_id = automation_id_for(source_path)
        report_date = date_for(source_path)
        destination = (
            Path("reports")
            / "automation"
            / automation_id
            / report_date
            / source_path.name
        )
        digest = sha256_file(source_path)
        operations.append(
            {
                "batch_id": "wave2_automation_reports_initial",
                "source": relpath(source_path, root),
                "destination": destination.as_posix(),
                "operation": "move",
                "pre_hash": digest,
                "post_hash": digest,
                "rollback_source": relpath(source_path, root),
                "reason": "Migrate legacy automation outputs into canonical reports/automation storage.",
                "approved": False,
                "applied_at": None,
            }
        )

    if not operations:
        return None

    return {
        "batch_id": "wave2_automation_reports_initial",
        "status": "planned",
        "summary": "Low-risk migration candidate for legacy Automation_Reports markdown files.",
        "rollback_manifest": "catalog/rollback_wave2_automation_reports_initial.json",
        "operations": operations,
    }


def build_root_docs_and_analysis_batch(
    root: Path,
    manifest: dict[str, object],
) -> dict[str, object] | None:
    operations: list[dict[str, object]] = []
    for entry in manifest["entries"]:
        if entry["kind"] not in {"workspace_doc", "analysis_report"}:
            continue
        if entry["status"] != "planned_move":
            continue
        source_path = root / str(entry["current_path"])
        if not source_path.exists() or not source_path.is_file():
            continue
        digest = sha256_file(source_path)
        operations.append(
            {
                "batch_id": "wave2_root_docs_and_analysis_initial",
                "source": str(entry["current_path"]),
                "destination": str(entry["planned_path"]),
                "operation": "move",
                "pre_hash": digest,
                "post_hash": digest,
                "rollback_source": str(entry["current_path"]),
                "reason": "Migrate low-risk root docs and analysis reports into canonical control-plane zones.",
                "approved": False,
                "applied_at": None,
            }
        )

    if not operations:
        return None

    return {
        "batch_id": "wave2_root_docs_and_analysis_initial",
        "status": "planned",
        "summary": "Low-risk migration candidate for root docs and analysis markdown files.",
        "rollback_manifest": "catalog/rollback_wave2_root_docs_and_analysis_initial.json",
        "operations": sorted(operations, key=lambda item: str(item["source"])),
    }


def build_rollbacks(batch: dict[str, object]) -> dict[str, object]:
    rollback_ops = []
    for operation in batch["operations"]:
        rollback_ops.append(
            {
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
        )
    return {
        "batch_id": f"{batch['batch_id']}_rollback",
        "for_batch": batch["batch_id"],
        "generated_at": now_iso_utc(),
        "operations": rollback_ops,
    }


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
        operations.append(candidate)
    merged["operations"] = operations
    merged["status"] = existing.get("status", generated.get("status", "planned"))
    return merged


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate relocation batches.")
    parser.add_argument("--root", default=None)
    parser.add_argument(
        "--manifest",
        default=None,
    )
    parser.add_argument(
        "--out",
        default=None,
    )
    parser.add_argument(
        "--aliases-out",
        default=None,
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    manifest_path = Path(args.manifest) if args.manifest else root / "catalog" / "workspace_manifest.yaml"
    manifest = load_yaml_like(manifest_path)
    plan_out = Path(args.out) if args.out else root / "catalog" / "relocation_plan.json"
    aliases_out = Path(args.aliases_out) if args.aliases_out else root / "catalog" / "path_aliases.csv"
    existing_plan = load_existing_plan(plan_out)
    existing_batches = {batch["batch_id"]: batch for batch in existing_plan.get("batches", [])}
    batches = []
    generated_batches: list[dict[str, object]] = []
    alias_rows = []

    automation_reports = build_automation_reports_batch(root)
    if automation_reports:
        generated_batches.append(automation_reports)
        for operation in automation_reports["operations"]:
            alias_rows.append(
                {
                    "legacy_path": str(operation["source"]),
                    "canonical_path": str(operation["destination"]),
                    "status": "pending",
                }
            )

    root_docs = build_root_docs_and_analysis_batch(root, manifest)
    if root_docs:
        generated_batches.append(root_docs)
        for operation in root_docs["operations"]:
            alias_rows.append(
                {
                    "legacy_path": str(operation["source"]),
                    "canonical_path": str(operation["destination"]),
                    "status": "pending",
                }
            )

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
        "root": str(root),
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
