from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import core  # noqa: E402
from ace.character_materialize import materialize_character_packet, materialize_packet  # noqa: E402
from ace.engine import resolve_character_query  # noqa: E402
from ace.ledger import query_ledger  # noqa: E402

character_materialize = importlib.import_module("ace.character_materialize")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _require_live_nested_repos() -> None:
    missing = [
        path
        for path in (REPO_ROOT / core.CANONREC_REL, REPO_ROOT / core.CLOUDBANK_REL)
        if not (path / ".git").exists()
    ]
    if missing:
        pytest.skip("requires provisioned CanonRec + CloudBank repositories")


def _character_packet(tmp_path: Path) -> tuple[Path, str]:
    _require_live_nested_repos()
    context = {
        "role": "ACE Atomic Materialization Test Officer 99173",
        "faction_id": "galactic_union",
        "location_type": "test_fixture",
        "observed_behavior": ["reported a deterministic fixture status"],
        "existence_status": "confirmed_unrecorded",
        "contextual_refs": ["ace.test.character.materialization.v0.5"],
    }
    query = core.compile_character_query(
        "Complete the isolated ACE atomic materialization test officer.",
        context,
        seed=99173,
        mode="commit_ready",
        requester_kind="system",
        requester_id="ace.test",
        root=REPO_ROOT,
    )
    assert query["query_kind"] == "complete"
    packet = tmp_path / "packet"
    receipt = resolve_character_query(query, packet, root=REPO_ROOT)
    assert receipt["status"] == "EXECUTION_BLOCKED"
    entity_id = receipt["subject_refs"][0]
    assert entity_id.startswith("char_")
    return packet, entity_id


def _canonrec_feature_clone(tmp_path: Path) -> Path:
    source = REPO_ROOT / core.CANONREC_REL
    target = tmp_path / "CanonRec-target"
    completed = subprocess.run(
        ["git", "clone", "--no-local", str(source), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    _git(target, "checkout", "-b", "agent/ace-character-materialization-test")
    return target


def _assert_native_character(target: Path, entity_id: str) -> None:
    entity_root = target / "canon/L2/entities" / entity_id
    capsule = entity_root / "capsule"
    expected_capsule = {
        "identity.json",
        "traits.json",
        "knowledge.jsonl",
        "cns.yaml",
        "state.bin",
        "runtime.py",
        "manifest.json",
    }
    assert {path.name for path in capsule.iterdir() if path.is_file()} == expected_capsule
    assert (entity_root / "bundle.manifest.json").is_file()
    assert (entity_root / "BUILD_RECEIPT.json").is_file()
    assert (entity_root / "naming_receipt.json").is_file()

    identity = json.loads((capsule / "identity.json").read_text(encoding="utf-8"))
    assert identity["capsule_id"] == entity_id
    assert identity["certainty"] == "CANON"
    assert identity["governance_verdict"] == "PROMOTE"
    assert identity["ace_materialization"]["source_determination_id"]

    manifest = json.loads((capsule / "manifest.json").read_text(encoding="utf-8"))
    records = {item["path"]: item["sha256"] for item in manifest["records"]}
    for name, digest in records.items():
        assert core.file_sha256(capsule / name) == digest

    flat = json.loads(
        (target / "canon/L2/entities/characters" / f"{entity_id}.json").read_text(encoding="utf-8")
    )
    assert flat["entity_kind"] == "character"
    assert flat["entity_id"] == entity_id
    assert flat["certainty"] == "CANON"
    assert flat["capsule_id"] == entity_id
    assert flat["capsule_ref"] == f"canon/L2/entities/{entity_id}/capsule/"
    assert flat["naming_receipt_ref"] == f"canon/L2/entities/{entity_id}/naming_receipt.json"


def test_native_character_materialization_is_one_atomic_commit(tmp_path: Path) -> None:
    packet, entity_id = _character_packet(tmp_path)
    canon = _canonrec_feature_clone(tmp_path)
    baseline = _git(canon, "rev-parse", "HEAD")
    ledger = tmp_path / "ledger"

    final = materialize_character_packet(
        packet,
        canon,
        authority_mode="owner_gated_materialize",
        authority_ref="ace.test.owner.character-materialization",
        ledger_dir=ledger,
        root=REPO_ROOT,
    )

    commit_sha = _git(canon, "rev-parse", "HEAD")
    assert commit_sha != baseline
    assert len(_git(canon, "rev-list", "--count", f"{baseline}..HEAD")) > 0
    assert _git(canon, "rev-list", "--count", f"{baseline}..HEAD") == "1"
    assert final["status"] == "GENERATED_CANON"
    assert final["materialization"]["status"] == "committed"
    assert final["materialization"]["commit_sha"] == commit_sha
    assert len(final["materialization"]["target_paths"]) == 11
    assert final["blockers"] == []
    _assert_native_character(canon, entity_id)

    original = json.loads((packet / "determination_receipt.json").read_text(encoding="utf-8"))
    assert original["status"] == "EXECUTION_BLOCKED"
    materialized = json.loads(
        (packet / "materialized_determination_receipt.json").read_text(encoding="utf-8")
    )
    assert materialized["determination_id"] == final["determination_id"]
    assert {item["status"] for item in query_ledger(ledger, root=REPO_ROOT)} == {
        "EXECUTION_BLOCKED",
        "GENERATED_CANON",
    }


def test_generic_materializer_dispatches_character_packet(tmp_path: Path) -> None:
    packet, entity_id = _character_packet(tmp_path)
    canon = _canonrec_feature_clone(tmp_path)
    final = materialize_packet(
        packet,
        canon,
        authority_mode="delegated_materialize",
        authority_ref="ace.test.delegation.character-materialization",
        ledger_dir=tmp_path / "ledger",
        root=REPO_ROOT,
    )
    assert final["status"] == "GENERATED_CANON"
    _assert_native_character(canon, entity_id)


def test_existing_character_target_fails_closed_before_commit(tmp_path: Path) -> None:
    packet, entity_id = _character_packet(tmp_path)
    canon = _canonrec_feature_clone(tmp_path)
    baseline = _git(canon, "rev-parse", "HEAD")
    target = canon / "canon/L2/entities" / entity_id
    target.mkdir(parents=True)

    with pytest.raises(core.ACEError, match="new-character-only"):
        materialize_character_packet(
            packet,
            canon,
            authority_mode="delegated_materialize",
            authority_ref="ace.test.delegation.character-materialization",
            ledger_dir=tmp_path / "ledger",
            root=REPO_ROOT,
        )
    assert _git(canon, "rev-parse", "HEAD") == baseline
    assert not (packet / "materialized_determination_receipt.json").exists()


def test_post_commit_failure_rolls_back_all_character_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet, entity_id = _character_packet(tmp_path)
    canon = _canonrec_feature_clone(tmp_path)
    baseline = _git(canon, "rev-parse", "HEAD")
    ledger = tmp_path / "ledger"
    real_append = character_materialize.append_determination
    calls = 0

    def fail_second_append(receipt, ledger_dir=None, *, root=core.ROOT):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise core.ACEError("synthetic final-ledger failure", code="runtime_failure")
        return real_append(receipt, ledger_dir, root=root)

    monkeypatch.setattr(character_materialize, "append_determination", fail_second_append)

    with pytest.raises(core.ACEError, match="synthetic final-ledger failure"):
        character_materialize.materialize_character_packet(
            packet,
            canon,
            authority_mode="owner_gated_materialize",
            authority_ref="ace.test.owner.rollback",
            ledger_dir=ledger,
            root=REPO_ROOT,
        )

    assert _git(canon, "rev-parse", "HEAD") == baseline
    assert not (canon / "canon/L2/entities" / entity_id).exists()
    assert not (canon / "canon/L2/entities/characters" / f"{entity_id}.json").exists()
    assert not (packet / "materialized_determination_receipt.json").exists()
    remaining = query_ledger(ledger, root=REPO_ROOT)
    assert len(remaining) == 1
    assert remaining[0]["status"] == "EXECUTION_BLOCKED"
