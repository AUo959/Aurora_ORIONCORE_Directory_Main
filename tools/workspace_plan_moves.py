#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    batches = []
    alias_rows = []

    automation_reports = build_automation_reports_batch(root)
    if automation_reports:
        batches.append(automation_reports)
        for operation in automation_reports["operations"]:
            alias_rows.append(
                {
                    "legacy_path": str(operation["source"]),
                    "canonical_path": str(operation["destination"]),
                    "status": "pending",
                }
            )

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

    plan_out = Path(args.out) if args.out else root / "catalog" / "relocation_plan.json"
    write_json(plan_out, relocation_plan)
    for batch in batches:
        rollback = build_rollbacks(batch)
        write_json(root / batch["rollback_manifest"], rollback)
    write_csv(
        Path(args.aliases_out) if args.aliases_out else root / "catalog" / "path_aliases.csv",
        alias_rows,
        fieldnames=["legacy_path", "canonical_path", "status"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
