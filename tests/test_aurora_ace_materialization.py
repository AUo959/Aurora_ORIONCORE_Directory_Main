from __future__ import annotations

import copy
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

from ace import core, facility  # noqa: E402
from ace.ledger import append_determination, query_ledger  # noqa: E402
from ace.materialize import materialize_facility_packet  # noqa: E402

materialize_module = importlib.import_module("ace.materialize")


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


def _canonrec_repo(tmp_path: Path, *, feature_branch: bool = True) -> Path:
    repo = tmp_path / "CanonRec"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "ACE Test")
    _git(repo, "config", "user.email", "ace-test@aurora.local")
    (repo / "README.md").write_text("# CanonRec fixture\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "test: seed CanonRec fixture")
    if feature_branch:
        _git(repo, "checkout", "-b", "agent/ace-materialization-test")
    return repo


def _facility_target(repo: Path) -> Path:
    return repo / "canon/L1/station/facility_bindings/l1-emb-mcp-shuttle-bay.json"


def _seed_existing_facility_binding(repo: Path) -> Path:
    target = _facility_target(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "record_type": "l1_facility_binding",
                "subject_ref": "L1-EMB-MCP-SHUTTLE-BAY",
                "canonical_location": "legacy unresolved docking area",
                "certainty": "UNCONFIRMED",
                "causal_use_permitted": False,
                "activation_authority": False,
                "exact_geometry_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", target.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "test: seed prior facility binding")
    return target


def _facility_context() -> dict[str, object]:
    return {
        "subject_ref": "L1-EMB-MCP-SHUTTLE-BAY",
        "component": "MCP Security / Shuttle Bay",
        "l1_kind": "controlled_admission_facility",
        "current_location": "unresolved",
        "location_certainty": "UNCONFIRMED",
        "authority_class": "admission_and_security",
        "evidence_class": "recoverable_historical_implementation",
        "source_refs": ["owner_mcp_embodiment_ruling", "cloudbank_history:4f17e6c3"],
        "provider_status": "unbound",
        "required_for_resume": True,
        "causal_use_permitted": False,
        "blockers": [
            "canonical_location",
            "reviewed_routing_registry",
            "quarantine_state_machine",
            "actor_bound_approval",
        ],
    }


def _write_fixture_evidence(root: Path) -> None:
    contract = root / "catalog/contracts/orion_l1_embodiment_registry.v0_1.json"
    purpose = root / core.CANONREC_REL / facility.STATION_PURPOSE_REL
    physical = root / core.CANONREC_REL / facility.PHYSICAL_SPACE_README_REL
    technical = root / core.CANONREC_REL / facility.TECHNICAL_REFERENCE_REL
    for path in (contract, purpose, physical, technical):
        path.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        json.dumps(
            {
                "embodiments": [
                    {
                        "id": "L1-EMB-MCP-SHUTTLE-BAY",
                        "gaps": ["canonical location"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    purpose.write_text("Owner ruling: L1 is the chassis.\n", encoding="utf-8")
    physical.write_text(
        "STAGING topology: non-rotating core docking complex.\n",
        encoding="utf-8",
    )
    technical.write_text(
        "Reference constraint: docking remains in the non-rotating core.\n",
        encoding="utf-8",
    )


def _baselines(canon_sha: str) -> list[dict[str, str]]:
    return [
        {
            "repository": "root",
            "path": ".",
            "commit_sha": "a" * 40,
            "authority_role": "control_plane",
        },
        {
            "repository": "CanonRec",
            "path": core.CANONREC_REL.as_posix(),
            "commit_sha": canon_sha,
            "authority_role": "canon",
        },
        {
            "repository": "aurora-cloudbank-symbolic-main",
            "path": core.CLOUDBANK_REL.as_posix(),
            "commit_sha": "c" * 40,
            "authority_role": "runtime",
        },
    ]


def _capability_index(baselines: list[dict[str, str]]) -> dict[str, object]:
    return {
        "schema_version": core.SCHEMA_VERSION,
        "record_type": "ace_warm_capability_index",
        "engine_version": core.ENGINE_VERSION,
        "baselines": baselines,
        "capabilities": [
            {
                "capability_id": "ace.capability.context.resolve",
                "repository": "root",
                "manifest_sha256": "1" * 64,
                "lifecycle": "active",
            },
            {
                "capability_id": "ace.capability.canonrec.materialize.entity",
                "repository": "CanonRec",
                "manifest_sha256": "2" * 64,
                "lifecycle": "blocked",
            },
        ],
    }


def _packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    canon_sha: str,
) -> Path:
    root = tmp_path / "fixture-root"
    _write_fixture_evidence(root)
    baselines = _baselines(canon_sha)
    monkeypatch.setattr(facility, "repository_baselines", lambda _root: baselines)
    monkeypatch.setattr(facility, "build_capability_index", lambda _root: _capability_index(baselines))
    query = facility.compile_facility_query(
        "Where is the MCP Security / Shuttle Bay?",
        _facility_context(),
        subject_ref="L1-EMB-MCP-SHUTTLE-BAY",
        root=root,
    )
    out = tmp_path / "packets" / "mcp-location"
    receipt = facility.resolve_facility_query(query, out, root=root)
    assert receipt["status"] == "EXECUTION_BLOCKED"
    return out


def test_materializer_requires_explicit_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path)
    packet = _packet(tmp_path, monkeypatch, _git(canon, "rev-parse", "HEAD"))

    with pytest.raises(core.ACEError, match="non-empty authority_ref"):
        materialize_facility_packet(
            packet,
            canon,
            authority_mode="owner_gated_materialize",
            authority_ref="",
            ledger_dir=tmp_path / "ledger",
            root=REPO_ROOT,
        )
    assert not _facility_target(canon).exists()


def test_materializer_refuses_protected_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path, feature_branch=False)
    packet = _packet(tmp_path, monkeypatch, _git(canon, "rev-parse", "HEAD"))

    with pytest.raises(core.ACEError, match="refuses protected branch"):
        materialize_facility_packet(
            packet,
            canon,
            authority_mode="owner_gated_materialize",
            authority_ref="test.owner.approval",
            ledger_dir=tmp_path / "ledger",
            root=REPO_ROOT,
        )


def test_materializer_commits_facility_and_appends_both_determinations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path)
    baseline = _git(canon, "rev-parse", "HEAD")
    packet = _packet(tmp_path, monkeypatch, baseline)
    ledger = tmp_path / "ledger"

    final = materialize_facility_packet(
        packet,
        canon,
        authority_mode="owner_gated_materialize",
        authority_ref="test.owner.approval",
        ledger_dir=ledger,
        root=REPO_ROOT,
    )

    commit_sha = _git(canon, "rev-parse", "HEAD")
    assert commit_sha != baseline
    assert final["status"] == "GENERATED_CANON"
    assert final["materialization"]["status"] == "committed"
    assert final["materialization"]["commit_sha"] == commit_sha
    assert final["blockers"] == []
    assert final["integrity"]["prior_determination_digest"]
    assert final["answer"]["supersedes_determination_refs"]

    target = _facility_target(canon)
    canonical = json.loads(target.read_text(encoding="utf-8"))
    assert canonical["record_type"] == "l1_facility_binding"
    assert canonical["certainty"] == "CANON"
    assert canonical["causal_use_permitted"] is False
    assert canonical["activation_authority"] is False
    assert canonical["exact_geometry_authorized"] is False
    assert canonical["ace_provenance"]["materialization_authority_ref"] == "test.owner.approval"

    # The materializer identity is one-shot commit metadata, not persistent repo config.
    assert _git(canon, "config", "--local", "user.name") == "ACE Test"
    assert _git(canon, "config", "--local", "user.email") == "ace-test@aurora.local"

    original = json.loads((packet / "determination_receipt.json").read_text(encoding="utf-8"))
    assert original["status"] == "EXECUTION_BLOCKED"
    materialized = json.loads(
        (packet / "materialized_determination_receipt.json").read_text(encoding="utf-8")
    )
    assert materialized["determination_id"] == final["determination_id"]

    by_subject = query_ledger(ledger, root=REPO_ROOT, subject="L1-EMB-MCP-SHUTTLE-BAY")
    assert {item["status"] for item in by_subject} == {"EXECUTION_BLOCKED", "GENERATED_CANON"}
    by_commit = query_ledger(ledger, root=REPO_ROOT, commit=commit_sha)
    assert [item["determination_id"] for item in by_commit] == [final["determination_id"]]
    by_capability = query_ledger(
        ledger,
        root=REPO_ROOT,
        capability="ace.capability.canonrec.materialize.entity",
    )
    assert len(by_capability) == 2
    by_target = query_ledger(
        ledger,
        root=REPO_ROOT,
        canonical_target="canon/L1/station/facility_bindings/l1-emb-mcp-shuttle-bay.json",
    )
    assert len(by_target) == 2


def test_existing_facility_target_becomes_canon_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path)
    target = _seed_existing_facility_binding(canon)
    baseline = _git(canon, "rev-parse", "HEAD")
    packet = _packet(tmp_path, monkeypatch, baseline)

    final = materialize_facility_packet(
        packet,
        canon,
        authority_mode="delegated_materialize",
        authority_ref="test.delegation.revision",
        ledger_dir=tmp_path / "ledger",
        root=REPO_ROOT,
    )

    assert final["status"] == "CANON_REVISION"
    assert final["materialization"]["status"] == "committed"
    assert final["materialization"]["commit_sha"] == _git(canon, "rev-parse", "HEAD")
    canonical = json.loads(target.read_text(encoding="utf-8"))
    assert canonical["certainty"] == "CANON"
    assert canonical["causal_use_permitted"] is False
    assert canonical["activation_authority"] is False
    assert canonical["exact_geometry_authorized"] is False


def test_materializer_fails_closed_when_canonrec_baseline_advanced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path)
    baseline = _git(canon, "rev-parse", "HEAD")
    packet = _packet(tmp_path, monkeypatch, baseline)
    (canon / "ADVANCED.md").write_text("advanced\n", encoding="utf-8")
    _git(canon, "add", "ADVANCED.md")
    _git(canon, "commit", "-m", "test: advance baseline")

    with pytest.raises(core.ACEError, match="baseline advanced"):
        materialize_facility_packet(
            packet,
            canon,
            authority_mode="delegated_materialize",
            authority_ref="test.delegation.receipt",
            ledger_dir=tmp_path / "ledger",
            root=REPO_ROOT,
        )
    assert _git(canon, "rev-parse", "HEAD") != baseline
    assert not _facility_target(canon).exists()


def test_post_commit_failure_rolls_back_canon_and_removes_false_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path)
    baseline = _git(canon, "rev-parse", "HEAD")
    packet = _packet(tmp_path, monkeypatch, baseline)
    ledger = tmp_path / "ledger"
    real_append = materialize_module.append_determination
    calls = 0

    def fail_second_append(receipt, ledger_dir=None, *, root=core.ROOT):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise core.ACEError("synthetic final-ledger failure", code="runtime_failure")
        return real_append(receipt, ledger_dir, root=root)

    monkeypatch.setattr(materialize_module, "append_determination", fail_second_append)

    with pytest.raises(core.ACEError, match="synthetic final-ledger failure"):
        materialize_module.materialize_facility_packet(
            packet,
            canon,
            authority_mode="owner_gated_materialize",
            authority_ref="test.owner.rollback",
            ledger_dir=ledger,
            root=REPO_ROOT,
        )

    assert _git(canon, "rev-parse", "HEAD") == baseline
    assert not _facility_target(canon).exists()
    assert not (packet / "materialized_determination_receipt.json").exists()
    remaining = query_ledger(ledger, root=REPO_ROOT)
    assert len(remaining) == 1
    assert remaining[0]["status"] == "EXECUTION_BLOCKED"


def test_ledger_is_append_only_for_a_determination_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canon = _canonrec_repo(tmp_path)
    packet = _packet(tmp_path, monkeypatch, _git(canon, "rev-parse", "HEAD"))
    receipt = json.loads((packet / "determination_receipt.json").read_text(encoding="utf-8"))
    ledger = tmp_path / "ledger"

    first = append_determination(receipt, ledger, root=REPO_ROOT)
    second = append_determination(receipt, ledger, root=REPO_ROOT)
    assert first == second

    altered = copy.deepcopy(receipt)
    altered["answer"]["summary"] += " changed"
    with pytest.raises(core.ACEError, match="append-only ledger collision"):
        append_determination(altered, ledger, root=REPO_ROOT)
