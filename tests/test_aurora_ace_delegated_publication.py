from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import delegated_publication as publication  # noqa: E402
from ace.core import ACEError  # noqa: E402

AUTHORITY_REF = "owner:test:delegated-publication"
PRINCIPAL = {
    "principal": "test-agent",
    "scopes": ["ace:publish", "ace:autonomic", "ace:materialize"],
    "authority_refs": [AUTHORITY_REF],
}


def _expect(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _git(repo: Path, *args: str) -> str:
    return publication._git(repo, *args)


def _repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "CanonRec"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(
        repo,
        "-c",
        "user.name=ACE Test",
        "-c",
        "user.email=ace-test@aurora.local",
        "commit",
        "-m",
        "baseline",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


def _packet(runtime: Path, baseline: str) -> Path:
    packet = runtime / "packet"
    packet.mkdir(parents=True)
    (packet / "candidate_facility_binding.json").write_text("{}\n", encoding="utf-8")
    receipt = {
        "determination_id": "ace.determination.test.publication",
        "query_id": "ace.query.test.publication",
        "subject_refs": ["facility_test_publication"],
        "baselines": [{"repository": "CanonRec", "commit_sha": baseline}],
        "materialization": {"status": "commit_ready", "target_repository": "CanonRec"},
    }
    (packet / "determination_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    return packet


def _expected_branch(packet: Path) -> str:
    receipt = json.loads((packet / "determination_receipt.json").read_text(encoding="utf-8"))
    return publication._branch_name("facility", receipt, publication._load_policy(REPO_ROOT))


def _fake_materialize(packet: Path, repo: Path, packet_kind: str, authority_ref: str, *, root: Path):
    target = repo / "canon" / "proposal.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"kind": packet_kind, "authority": authority_ref}) + "\n", encoding="utf-8")
    _git(repo, "add", target.relative_to(repo).as_posix())
    _git(
        repo,
        "-c",
        "user.name=ACE Test",
        "-c",
        "user.email=ace-test@aurora.local",
        "commit",
        "-m",
        "proposal",
    )
    return {
        "determination_id": "ace.determination.test.publication.materialized",
        "status": "GENERATED_CANON",
        "subject_refs": ["facility_test_publication"],
    }


def _wire_test_boundary(monkeypatch: pytest.MonkeyPatch, repo: Path, baseline: str) -> None:
    monkeypatch.setattr(publication, "_registered_canonrec_repo", lambda root: repo)
    monkeypatch.setattr(publication, "_registered_canonrec_baseline", lambda root: baseline)
    monkeypatch.setattr(publication, "_assert_remote_identity", lambda repo, policy: None)
    monkeypatch.setattr(publication, "_remote_main_sha", lambda repo: baseline)
    monkeypatch.setattr(publication, "_remote_branch_exists", lambda repo, branch: False)
    monkeypatch.setattr(publication, "_push_branch", lambda repo, branch: None)
    monkeypatch.setattr(publication, "_materialize", _fake_materialize)


def test_publication_policy_is_review_gated() -> None:
    policy = publication._load_policy(REPO_ROOT)
    _expect(policy["target_repository"] == "CanonRec", "policy must target CanonRec")
    _expect(policy["base_branch"] == "main", "policy base must be main")
    _expect(policy["pull_request_draft"] is True, "publication PR must be draft")
    _expect(policy["auto_merge_allowed"] is False, "auto-merge must remain disabled")
    _expect(policy["max_naming_warnings"] == 0, "autonomous naming warning budget must be zero")
    _expect(
        set(policy["required_remote_scopes"]) == {"ace:publish", "ace:autonomic", "ace:materialize"},
        "publication must require the complete remote scope intersection",
    )


def test_publication_helper_bindings_fail_stale_on_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    publication._assert_helper_dependencies(REPO_ROOT)
    monkeypatch.setattr(publication, "_git_blob_sha", lambda source: "0" * 40)
    with pytest.raises(ACEError, match="dependency changed"):
        publication._assert_helper_dependencies(REPO_ROOT)


def test_publication_principal_requires_all_scopes_and_authority() -> None:
    policy = publication._load_policy(REPO_ROOT)
    with pytest.raises(ACEError):
        publication._principal_gate(
            {"principal": "agent", "scopes": ["ace:publish"], "authority_refs": [AUTHORITY_REF]},
            AUTHORITY_REF,
            policy,
        )
    with pytest.raises(ACEError):
        publication._principal_gate(
            {"principal": "agent", "scopes": list(PRINCIPAL["scopes"]), "authority_refs": []},
            AUTHORITY_REF,
            policy,
        )
    with pytest.raises(ACEError):
        publication._principal_gate(PRINCIPAL, "owner:test:\nforged", policy)


def test_branch_name_is_deterministic_and_policy_scoped() -> None:
    policy = publication._load_policy(REPO_ROOT)
    receipt = {
        "determination_id": "ace.determination.test",
        "query_id": "ace.query.test",
        "subject_refs": ["org_example"],
    }
    first = publication._branch_name("generic_entity", receipt, policy)
    second = publication._branch_name("generic_entity", receipt, policy)
    _expect(first == second, "proposal branch naming must be deterministic")
    _expect(first.startswith("ace/canon/generic_entity/org_example-"), "proposal branch must stay in policy namespace")


def test_delegated_publication_creates_review_pending_receipt_and_restores_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, baseline = _repo(tmp_path)
    runtime = tmp_path / "runtime"
    packet = _packet(runtime, baseline)
    branch = _expected_branch(packet)
    _wire_test_boundary(monkeypatch, repo, baseline)
    monkeypatch.setattr(
        publication,
        "open_pull_request",
        lambda *args, **kwargs: (321, "https://github.com/AUo959/CanonRec/pull/321"),
    )

    result = publication.publish_delegated_packet(
        "packet",
        AUTHORITY_REF,
        PRINCIPAL,
        root=REPO_ROOT,
        runtime_root=runtime,
    )

    _expect(result["status"] == "review_pending", "successful delegated publication must remain review pending")
    _expect(result["pull_request"]["draft"] is True, "delegated PR must be draft")
    _expect(result["pull_request"]["auto_merge_allowed"] is False, "delegated PR must not auto-merge")
    _expect(result["mainline_canon_advanced"] is False, "delegated publication must not advance main")
    _expect(result["proposal_commit"] != baseline, "proposal must have one new commit")
    _expect((packet / "delegated_publication_receipt.json").is_file(), "publication receipt must persist")
    _expect(_git(repo, "branch", "--show-current") == "main", "local CanonRec must return to main")
    _expect(_git(repo, "rev-parse", "HEAD") == baseline, "local CanonRec must return to baseline")
    _expect(_git(repo, "status", "--porcelain") == "", "restored CanonRec must be clean")
    _expect(not publication._local_branch_exists(repo, branch), "proposal branch must be removed locally after success")


def test_delegated_publication_deletes_orphan_remote_branch_when_pr_open_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, baseline = _repo(tmp_path)
    runtime = tmp_path / "runtime"
    packet = _packet(runtime, baseline)
    branch = _expected_branch(packet)
    _wire_test_boundary(monkeypatch, repo, baseline)
    deleted: list[str] = []
    monkeypatch.setattr(publication, "_delete_remote_branch", lambda repo, candidate: deleted.append(candidate))

    def fail_pr(*args, **kwargs):
        raise ACEError("synthetic PR failure", code="runtime_failure")

    monkeypatch.setattr(publication, "open_pull_request", fail_pr)
    with pytest.raises(ACEError, match="synthetic PR failure"):
        publication.publish_delegated_packet(
            "packet",
            AUTHORITY_REF,
            PRINCIPAL,
            root=REPO_ROOT,
            runtime_root=runtime,
        )
    _expect(deleted == [branch], "pushed orphan branch must be deleted after PR-open failure")
    _expect(_git(repo, "branch", "--show-current") == "main", "failed attempt must restore main")
    _expect(_git(repo, "rev-parse", "HEAD") == baseline, "failed attempt must restore baseline")
    _expect(not publication._local_branch_exists(repo, branch), "failed proposal branch must be removed locally")


def test_uncertain_pr_state_preserves_remote_branch_for_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, baseline = _repo(tmp_path)
    runtime = tmp_path / "runtime"
    packet = _packet(runtime, baseline)
    branch = _expected_branch(packet)
    _wire_test_boundary(monkeypatch, repo, baseline)
    deleted: list[str] = []
    monkeypatch.setattr(publication, "_delete_remote_branch", lambda repo, candidate: deleted.append(candidate))

    def uncertain_pr(*args, **kwargs):
        raise publication.PublicationStateUncertain("synthetic uncertain state", code="runtime_failure")

    monkeypatch.setattr(publication, "open_pull_request", uncertain_pr)
    with pytest.raises(publication.PublicationStateUncertain):
        publication.publish_delegated_packet(
            "packet",
            AUTHORITY_REF,
            PRINCIPAL,
            root=REPO_ROOT,
            runtime_root=runtime,
        )
    _expect(deleted == [], "uncertain GitHub state must preserve the remote proposal branch")
    progress = json.loads((packet / "delegated_publication_receipt.json").read_text(encoding="utf-8"))
    _expect(progress["status"] == "publication_in_progress", "uncertain state must retain the durable progress receipt")
    _expect(_git(repo, "branch", "--show-current") == "main", "uncertain attempt must restore local main")
    _expect(not publication._local_branch_exists(repo, branch), "uncertain attempt must remove only the local proposal branch")


def test_delegated_publication_refuses_existing_remote_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, baseline = _repo(tmp_path)
    runtime = tmp_path / "runtime"
    _packet(runtime, baseline)
    _wire_test_boundary(monkeypatch, repo, baseline)
    monkeypatch.setattr(publication, "_remote_branch_exists", lambda repo, branch: True)
    with pytest.raises(ACEError, match="replay is refused"):
        publication.publish_delegated_packet(
            "packet",
            AUTHORITY_REF,
            PRINCIPAL,
            root=REPO_ROOT,
            runtime_root=runtime,
        )


def test_delegated_publication_refuses_remote_main_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, baseline = _repo(tmp_path)
    runtime = tmp_path / "runtime"
    _packet(runtime, baseline)
    _wire_test_boundary(monkeypatch, repo, baseline)
    monkeypatch.setattr(publication, "_remote_main_sha", lambda repo: "f" * 40)
    with pytest.raises(ACEError, match="remote main advanced"):
        publication.publish_delegated_packet(
            "packet",
            AUTHORITY_REF,
            PRINCIPAL,
            root=REPO_ROOT,
            runtime_root=runtime,
        )
