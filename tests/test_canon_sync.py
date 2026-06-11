"""Tests for tools/canon_sync.py — canon propagation with drift detection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import canon_sync  # noqa: E402


ENTITY = {
    "entity_id": "ORION.ENTITY.9999",
    "name": "Test Officer",
    "display_name": "Test Officer",
    "role": "Test Role",
    "division": "Test Division",
    "primary_summary": "A test entity.",
    "canon_file": "canon/L1/characters/ORION.ENTITY.9999__test-officer.md",
}


def build_workspace(tmp_path: Path) -> Path:
    root = tmp_path
    (root / "catalog").mkdir()
    (root / "tools").mkdir()
    # canon_sync loads the yaml via the real workspace helper; reuse it.
    real_common = TOOLS_DIR / "_workspace_common.py"
    (root / "tools" / "_workspace_common.py").write_text(real_common.read_text())
    (root / "catalog" / "canon_sync_payloads.yaml").write_text(
        """version: 1
payloads:
- name: contract
  kind: file_copy
  enabled: true
  source: source/contract.yaml
  dest: consumer/contract.yaml
- name: memories
  kind: generated_memory
  enabled: true
  ledger_glob: ledgers/L1_ENTITY_LEDGER__*.json
  dest_dir: consumer/memory
"""
    )
    (root / "source").mkdir()
    (root / "source" / "contract.yaml").write_text("anchor: EOS_SEED_ORION\n")
    (root / "consumer").mkdir()
    (root / "consumer" / "contract.yaml").write_text("anchor: EOS_SEED_ORION\n")
    (root / "ledgers").mkdir()
    (root / "ledgers" / "L1_ENTITY_LEDGER__2026-06-10.json").write_text(
        json.dumps({"humans": [ENTITY]})
    )
    (root / "consumer" / "memory").mkdir()
    (root / "consumer" / "memory" / "test_officer.md").write_text(
        canon_sync.render_memory(ENTITY, "2026-06-10")
    )
    (root / "consumer" / "memory" / "hand_authored.md").write_text(
        "# Hand Authored\n\nNo canon linkage comment here.\n"
    )
    return root


def test_clean_workspace_reports_no_drift(tmp_path: Path) -> None:
    root = build_workspace(tmp_path)
    assert canon_sync.collect_drift(root) == {}


def test_render_memory_is_deterministic_modulo_date() -> None:
    a = canon_sync.render_memory(ENTITY, "2026-06-10")
    b = canon_sync.render_memory(ENTITY, "2027-01-01")
    assert a != b
    assert canon_sync.normalize_volatile(a) == canon_sync.normalize_volatile(b)


def test_file_copy_drift_detected_and_staged(tmp_path: Path) -> None:
    root = build_workspace(tmp_path)
    (root / "consumer" / "contract.yaml").write_text("anchor: TAMPERED\n")
    drift = canon_sync.collect_drift(root)
    assert "contract" in drift
    payload = canon_sync.load_payloads(root)[0]
    canon_sync.apply_file_copy(payload, root)
    assert canon_sync.collect_drift(root) == {}


def test_memory_drift_detected_and_staged(tmp_path: Path) -> None:
    root = build_workspace(tmp_path)
    target = root / "consumer" / "memory" / "test_officer.md"
    target.write_text(target.read_text() + "tampered\n")
    drift = canon_sync.collect_drift(root)
    assert "memories" in drift
    payload = [p for p in canon_sync.load_payloads(root) if p["name"] == "memories"][0]
    staged = canon_sync.apply_generated_memory(payload, root)
    assert staged
    assert canon_sync.collect_drift(root) == {}


def test_hand_authored_memory_is_never_touched(tmp_path: Path) -> None:
    root = build_workspace(tmp_path)
    hand = root / "consumer" / "memory" / "hand_authored.md"
    before = hand.read_text()
    payload = [p for p in canon_sync.load_payloads(root) if p["name"] == "memories"][0]
    canon_sync.apply_generated_memory(payload, root)
    assert hand.read_text() == before


def test_canon_change_propagates_to_memory(tmp_path: Path) -> None:
    root = build_workspace(tmp_path)
    evolved = dict(ENTITY, role="Promoted Role")
    (root / "ledgers" / "L1_ENTITY_LEDGER__2026-06-11.json").write_text(
        json.dumps({"humans": [evolved]})
    )
    drift = canon_sync.collect_drift(root)
    assert "memories" in drift, "newest ledger should win and reveal drift"
    payload = [p for p in canon_sync.load_payloads(root) if p["name"] == "memories"][0]
    canon_sync.apply_generated_memory(payload, root)
    text = (root / "consumer" / "memory" / "test_officer.md").read_text()
    assert "Promoted Role" in text
    assert canon_sync.collect_drift(root) == {}
