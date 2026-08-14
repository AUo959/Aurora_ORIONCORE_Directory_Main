from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import generic_entity, generic_entity_gate  # noqa: E402
from ace.capability_discovery import select_invocation_capability  # noqa: E402
from ace.core import ACEError  # noqa: E402
from ace.generic_entity_runtime import _manifest_digest  # noqa: E402
from ace.generic_entity_validation import (  # noqa: E402
    assert_native_entity_tree_readable,
    payload_validator_binding,
    validate_json_payload,
)


def test_generic_entity_kinds_match_native_l2_vocab_without_character() -> None:
    assert "character" not in generic_entity.GENERIC_L2_KINDS
    assert {
        "organization", "ship", "location", "equipment", "event", "report",
        "mobile_asset", "ship_class", "polity", "species",
    }.issubset(generic_entity.GENERIC_L2_KINDS)


def test_compile_is_deterministic_and_preserves_specialist_character_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generic_entity, "repository_baselines", lambda root: [{"repository": "root", "commit_sha": "a" * 40, "authority_role": "control_plane"}])
    context = {"source_refs": ["test:source"], "canonical_fields": {}}
    first = generic_entity.compile_generic_entity_query("Create the organization", "organization", context, seed=42)
    second = generic_entity.compile_generic_entity_query("Create the organization", "organization", context, seed=42)
    assert first["subject"]["subject_ref"] == second["subject"]["subject_ref"]
    assert first["subject"]["context"]["name"] == second["subject"]["context"]["name"]
    assert first["scope"]["target_paths"] == second["scope"]["target_paths"]
    with pytest.raises(ACEError):
        generic_entity.compile_generic_entity_query("Create character", "character", context)


def test_specialists_outrank_generic_fallback() -> None:
    def query(kind: str, query_kind: str = "complete") -> dict:
        return {"subject": {"entity_type": kind}, "query_kind": query_kind}
    assert select_invocation_capability(query("character"))["capability_id"] == "ace.capability.invoke.character.complete"
    assert select_invocation_capability(query("facility"))["capability_id"] == "ace.capability.invoke.facility"
    assert select_invocation_capability(query("organization"))["capability_id"] == "ace.capability.invoke.entity.complete"
    assert select_invocation_capability(query("equipment"))["capability_id"] == "ace.capability.invoke.entity.complete"


def test_generic_runtime_uses_real_manifest_digests() -> None:
    assert _manifest_digest(generic_entity.GENERIC_RESOLVER_CAPABILITY, root=REPO_ROOT) == "383eb106419f020eadd8c335a6b9a3769746d8ce6c461b0ae237423efbaaedc1"
    assert _manifest_digest(generic_entity.GENERIC_MATERIALIZER_CAPABILITY, root=REPO_ROOT) == "0cb48c541d88d4be6ee0596a5c5a5f22d6a39d6c5fc1401a169fc968dbe4bacb"


def test_payload_validator_binding_is_scoped_and_restored() -> None:
    original = generic_entity.validate_json_schema
    with payload_validator_binding(generic_entity):
        assert generic_entity.validate_json_schema is validate_json_payload
    assert generic_entity.validate_json_schema is original


def test_native_entity_tree_integrity_fails_closed(tmp_path: Path) -> None:
    entity_root = tmp_path / "canon/L2/entities"
    entity_root.mkdir(parents=True)
    (entity_root / "broken.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(ACEError, match="unreadable"):
        assert_native_entity_tree_readable(tmp_path)


@pytest.mark.parametrize("kind", sorted(generic_entity.GENERIC_L2_KINDS))
def test_generated_native_candidates_pass_existing_canon_reconciler(kind: str) -> None:
    context = {"name": f"ACE Validation {kind}", "entity_id": f"{kind}_ace_validation", "source_refs": ["ACE:test"], "canonical_fields": {}}
    query = {"query_id": f"ace.query.entity.test_{kind}", "subject": {"entity_type": kind, "context": context}}
    candidate = generic_entity._candidate_from_query(query)
    report = generic_entity._validator_report(candidate, kind, root=REPO_ROOT)
    assert isinstance(report, dict)


@pytest.mark.skipif(os.environ.get("ACE_GENERIC_E2E") != "1", reason="requires registry-pinned CanonRec checkout")
def test_generic_entity_end_to_end_commit_and_replay_refusal(tmp_path: Path) -> None:
    canonrec = REPO_ROOT / generic_entity.CANONREC_REL
    baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=canonrec, check=True, capture_output=True, text=True).stdout.strip()
    branch = "validation/ace-generic-v0-11"
    subprocess.run(["git", "checkout", "-B", branch], cwd=canonrec, check=True, capture_output=True, text=True)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    try:
        query = generic_entity.compile_generic_entity_query(
            "Create a bounded validation organization",
            "organization",
            {
                "name": "ACE E2E Validation Organization",
                "entity_id": "organization_ace_e2e_validation_v011",
                "source_refs": ["ACE:E2E:v0.11"],
                "canonical_fields": {},
            },
            seed=1100,
            root=REPO_ROOT,
        )
        output = runtime / "generic-e2e"
        from ace.generic_entity_runtime import resolve_generic_entity_query
        receipt = resolve_generic_entity_query(query, output, root=REPO_ROOT)
        assert receipt["status"] == "EXECUTION_BLOCKED"
        authority = "owner:e2e:ace-v0.11"
        preview = generic_entity_gate.generic_entity_preview(
            "generic-e2e", authority, root=REPO_ROOT, runtime_root=runtime, target_repo=canonrec
        )
        result = generic_entity_gate.generic_entity_commit(
            "generic-e2e", authority, preview["authorization_token"], True,
            root=REPO_ROOT, runtime_root=runtime, target_repo=canonrec,
        )
        final = result["materialized_determination"]
        assert final["status"] == "GENERATED_CANON"
        assert final["materialization"]["commit_sha"] == subprocess.run(["git", "rev-parse", "HEAD"], cwd=canonrec, check=True, capture_output=True, text=True).stdout.strip()
        assert subprocess.run(["git", "status", "--porcelain"], cwd=canonrec, check=True, capture_output=True, text=True).stdout.strip() == ""
        with pytest.raises(ACEError):
            generic_entity_gate.generic_entity_commit(
                "generic-e2e", authority, preview["authorization_token"], True,
                root=REPO_ROOT, runtime_root=runtime, target_repo=canonrec,
            )
    finally:
        subprocess.run(["git", "reset", "--hard", baseline], cwd=canonrec, check=True, capture_output=True, text=True)
        subprocess.run(["git", "clean", "-fd"], cwd=canonrec, check=True, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "-B", "main"], cwd=canonrec, check=True, capture_output=True, text=True)
