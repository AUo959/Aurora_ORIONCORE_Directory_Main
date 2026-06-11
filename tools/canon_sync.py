#!/usr/bin/env python3
"""
canon_sync.py — Canon propagation with drift detection.

Usage:
    python3 tools/canon_sync.py --check    # drift report; exit 2 if any payload drifted
    python3 tools/canon_sync.py --apply    # stage updates into destination WORKING TREES
    python3 tools/canon_sync.py            # dry-run (same as --check, with summary)

Sources of truth: CanonRec (contracts) and the newest L1 Entity Ledger
(persona memories). Destinations live in OTHER repos (CloudBank), so --apply
deliberately stops at the working tree: it never commits or pushes. After an
apply, take the staged changes through the destination repo's normal
branch + PR + CI path — the canon consistency gate validates them there.

Payloads are declared in catalog/canon_sync_payloads.yaml. Receipts are
written to reports/automation/canon_sync_latest.json on apply.

Persona-memory linkage: a managed memory file carries
    <!-- Canon: ORION.ENTITY.NNNN | <canon_file> | generated <date> from ledger v2 -->
The entity id joins the file to its ledger record; the generated-date portion
is volatile and ignored during comparison. Files without the linkage comment
are hand-authored and never touched.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAYLOADS_REGISTRY = REPO_ROOT / "catalog" / "canon_sync_payloads.yaml"
RECEIPT_PATH = REPO_ROOT / "reports" / "automation" / "canon_sync_latest.json"

CANON_COMMENT_RE = re.compile(
    r"<!-- Canon: (ORION\.ENTITY\.\d+) \| ([^|]+) \| generated [0-9-]+ from ledger v2 -->"
)
VOLATILE_DATE_RE = re.compile(r"generated [0-9-]+ from ledger v2")


def load_payloads(root: Path = REPO_ROOT) -> list[dict]:
    registry = root / "catalog" / "canon_sync_payloads.yaml"
    if not registry.exists():
        return []
    sys.path.insert(0, str(root / "tools"))
    from _workspace_common import load_yaml_like

    payload = load_yaml_like(registry) or {}
    entries = payload.get("payloads") or []
    return [p for p in entries if isinstance(p, dict) and p.get("enabled")]


def newest_ledger(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def render_memory(entity: dict, generated_on: str) -> str:
    """Deterministic persona-memory body from a ledger entity (boarding template)."""
    summary = str(entity.get("primary_summary", "")).strip()
    return (
        f"# {entity['name']}\n\n"
        f"{entity['role']} — {entity['division']}.\n\n"
        f"{summary}\n\n"
        "Respond in character per the role above. Prioritize system coherence over flourish.\n\n"
        f"<!-- Canon: {entity['entity_id']} | {entity['canon_file']} | "
        f"generated {generated_on} from ledger v2 -->\n"
    )


def normalize_volatile(text: str) -> str:
    return VOLATILE_DATE_RE.sub("generated <date> from ledger v2", text).strip() + "\n"


def check_file_copy(payload: dict, root: Path) -> dict:
    source = root / str(payload["source"])
    dest = root / str(payload["dest"])
    result = {"payload": payload["name"], "kind": "file_copy", "drift": [], "errors": []}
    if not source.exists():
        result["errors"].append(f"source missing: {payload['source']}")
        return result
    if not dest.exists():
        result["drift"].append(f"dest missing: {payload['dest']}")
        return result
    if source.read_bytes() != dest.read_bytes():
        result["drift"].append(f"content differs: {payload['dest']}")
    return result


def apply_file_copy(payload: dict, root: Path) -> list[str]:
    source = root / str(payload["source"])
    dest = root / str(payload["dest"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return [f"staged: {payload['dest']}"]


def managed_memories(dest_dir: Path) -> dict[str, tuple[Path, str]]:
    """Map entity_id -> (memory path, current text) for linkage-bearing files."""
    managed: dict[str, tuple[Path, str]] = {}
    if not dest_dir.is_dir():
        return managed
    for path in sorted(dest_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = CANON_COMMENT_RE.search(text)
        if match:
            managed[match.group(1)] = (path, text)
    return managed


def check_generated_memory(payload: dict, root: Path) -> dict:
    result = {"payload": payload["name"], "kind": "generated_memory", "drift": [], "errors": []}
    ledger_path = newest_ledger(root, str(payload["ledger_glob"]))
    if ledger_path is None:
        result["errors"].append(f"no ledger matches {payload['ledger_glob']}")
        return result
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    entities = {h["entity_id"]: h for h in ledger.get("humans", []) if h.get("canon_file")}
    dest_dir = root / str(payload["dest_dir"])
    for entity_id, (path, current) in managed_memories(dest_dir).items():
        entity = entities.get(entity_id)
        if entity is None:
            result["drift"].append(f"{path.name}: entity {entity_id} absent from {ledger_path.name}")
            continue
        expected = render_memory(entity, "0000-00-00")
        if normalize_volatile(expected) != normalize_volatile(current):
            result["drift"].append(f"{path.name}: stale vs {ledger_path.name} ({entity_id})")
    return result


def apply_generated_memory(payload: dict, root: Path) -> list[str]:
    staged: list[str] = []
    ledger_path = newest_ledger(root, str(payload["ledger_glob"]))
    if ledger_path is None:
        return staged
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    entities = {h["entity_id"]: h for h in ledger.get("humans", []) if h.get("canon_file")}
    dest_dir = root / str(payload["dest_dir"])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for entity_id, (path, current) in managed_memories(dest_dir).items():
        entity = entities.get(entity_id)
        if entity is None:
            continue
        expected = render_memory(entity, today)
        if normalize_volatile(expected) != normalize_volatile(current):
            path.write_text(expected, encoding="utf-8")
            staged.append(f"staged: {path.relative_to(root)}")
    return staged


CHECKERS = {"file_copy": check_file_copy, "generated_memory": check_generated_memory}
APPLIERS = {"file_copy": apply_file_copy, "generated_memory": apply_generated_memory}


def collect_drift(root: Path = REPO_ROOT) -> dict[str, list[str]]:
    """Return {payload_name: [drift summaries]} across enabled payloads."""
    drift: dict[str, list[str]] = {}
    for payload in load_payloads(root):
        checker = CHECKERS.get(str(payload.get("kind")))
        if checker is None:
            drift[payload["name"]] = [f"unknown payload kind: {payload.get('kind')}"]
            continue
        result = checker(payload, root)
        entries = result["drift"] + result["errors"]
        if entries:
            drift[payload["name"]] = entries
    return drift


def write_receipt(staged: dict[str, list[str]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "posture": "working-tree staging only; destination changes ride branch + PR + CI",
        "payloads": staged,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n")


def stage_drifted_payloads(drift: dict[str, list[str]]) -> dict[str, list[str]]:
    """Apply every drifted payload into its destination working tree; print progress."""
    staged: dict[str, list[str]] = {}
    for payload in load_payloads():
        if payload["name"] not in drift:
            print(f"  ✅ {payload['name']}: in sync")
            continue
        applier = APPLIERS.get(str(payload.get("kind")))
        if applier is None:
            print(f"  ❌ {payload['name']}: unknown kind {payload.get('kind')}")
            continue
        entries = applier(payload, REPO_ROOT)
        staged[payload["name"]] = entries
        print(f"  🔄 {payload['name']}: {len(entries)} file(s) staged")
        for entry in entries:
            print(f"       {entry}")
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="Drift check: exit 2 if any payload drifted")
    parser.add_argument("--apply", action="store_true", help="Stage updates into destination working trees")
    args = parser.parse_args()

    drift = collect_drift()
    if not args.apply:
        if not drift:
            print("All enabled canon payloads are in sync.")
            return 0
        for name, entries in drift.items():
            print(f"DRIFT {name}:")
            for entry in entries:
                print(f"  - {entry}")
        if not args.check:
            print("\nDry run — pass --apply to stage updates into the destination working trees.")
        return 2

    staged = stage_drifted_payloads(drift)
    if staged:
        write_receipt(staged)
        print("\nStaged into destination working trees ONLY — no commits made.")
        print("Take the changes through the destination repo's branch + PR + CI path.")
    else:
        print("\nNothing to stage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
