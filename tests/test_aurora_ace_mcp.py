from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import core  # noqa: E402
from ace import mcp_adapter  # noqa: E402


def invocation() -> dict[str, object]:
    return {
        "schema_version": "0.2.0",
        "record_type": "ace_invocation_envelope",
        "invocation_id": "ace.invocation.interactive.test",
        "query": {
            "record_type": "ace_query_envelope",
            "query_id": "ace.query.test",
        },
    }


def _ready_packet(tmp_path: Path) -> tuple[Path, Path, Path]:
    runtime = tmp_path / "runtime"
    packet = runtime / "packet-001"
    packet.mkdir(parents=True)
    receipt = {
        "record_type": "ace_determination_receipt",
        "determination_id": "ace.determination.test",
        "materialization": {"status": "commit_ready"},
        "baselines": [{"repository": "CanonRec", "commit_sha": "a" * 40}],
    }
    (packet / "determination_receipt.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )
    repo = tmp_path / "CanonRec"
    repo.mkdir()
    return runtime, packet, repo


def _clean_feature_git(repo: Path, *args: str) -> str:
    if args == ("rev-parse", "--is-inside-work-tree"):
        return "true"
    if args == ("status", "--porcelain"):
        return ""
    if args == ("branch", "--show-current"):
        return "agent/ace-test"
    if args == ("rev-parse", "HEAD"):
        return "a" * 40
    raise AssertionError(args)


def test_mcp_contract_declares_two_phase_bounded_materialization_surface() -> None:
    contract = json.loads(
        (REPO_ROOT / "catalog/contracts/aurora_ace_mcp_contract_v0_8.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["tool_surface"] == list(mcp_adapter.MCP_TOOL_NAMES)
    assert contract["transport"]["allowed"] == ["stdio"]
    assert contract["transport"]["network_listener_enabled"] is False
    assert contract["authority"]["canonical_materialization_exposed"] is True
    assert contract["authority"]["canonrec_git_mutation_exposed"] is True
    assert contract["authority"]["arbitrary_repository_path_exposed"] is False
    assert contract["authority"]["protected_branch_mutation_exposed"] is False
    assert contract["authority"]["dynamic_python_binding_exposed"] is False
    assert contract["materialization_gate"]["phases"] == ["preview", "commit"]
    assert contract["materialization_gate"]["authority_mode"] == "owner_gated_materialize"


def test_capabilities_wraps_manifest_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    expected = {"record_type": "ace_warm_capability_index", "capabilities": [{"capability_id": "x"}]}
    monkeypatch.setattr(mcp_adapter, "build_capability_index", lambda root: expected)

    result = mcp_adapter.ace_capabilities(root=tmp_path)

    assert result["capability_index"] == expected
    assert result["tools"] == list(mcp_adapter.MCP_TOOL_NAMES)
    assert result["materialization_exposed"] is True
    assert result["materialization_policy"] == "owner_gated_two_phase_registered_canonrec_only"


def test_plan_uses_normal_invocation_validation_and_manifest_router(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    payload = invocation()

    monkeypatch.setattr(
        mcp_adapter,
        "validate_invocation_envelope",
        lambda value: calls.append(("validate", value)),
    )
    monkeypatch.setattr(
        mcp_adapter,
        "select_invocation_capability",
        lambda query: {"capability_id": "ace.capability.invoke.character.retrieve"},
    )

    result = mcp_adapter.ace_plan(payload)

    assert calls == [("validate", payload)]
    assert result["selected_runtime_capability"]["capability_id"] == (
        "ace.capability.invoke.character.retrieve"
    )
    assert result["side_effect_class"] == "read_only"


@pytest.mark.parametrize(
    "output_name",
    [
        "../escape",
        "nested/packet",
        "nested\\packet",
        "/absolute",
        "..",
        ".",
        "",
        "x" * 129,
    ],
)
def test_resolve_rejects_path_like_output_names(output_name: str, tmp_path: Path) -> None:
    with pytest.raises(core.ACEError):
        mcp_adapter._safe_output_dir(
            output_name,
            root=tmp_path,
            runtime_root=tmp_path / "runtime",
        )


def test_resolve_is_bounded_and_delegates_to_shared_engine(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    payload = invocation()
    runtime = tmp_path / "runtime"
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(mcp_adapter, "validate_invocation_envelope", lambda value: None)

    def fake_resolve(
        value: dict[str, object],
        output_dir: Path,
        *,
        root: Path,
    ) -> dict[str, object]:
        calls.append({"value": value, "output_dir": output_dir, "root": root})
        return {
            "invocation": {"invocation_id": value["invocation_id"]},
            "determination": {
                "record_type": "ace_determination_receipt",
                "determination_id": "ace.determination.test",
            },
            "invocation_sidecar": str(runtime / "packet.ace-invocation.json"),
        }

    monkeypatch.setattr(mcp_adapter, "resolve_invocation", fake_resolve)
    result = mcp_adapter.ace_resolve(
        payload,
        "packet-001",
        root=tmp_path,
        runtime_root=runtime,
    )

    assert calls[0]["output_dir"] == (runtime / "packet-001").resolve()
    assert calls[0]["root"] == tmp_path
    assert result["packet_ref"] == str((runtime / "packet-001").resolve())
    assert result["side_effect_class"] == "bounded_runtime_artifact_write"


def test_registry_rejects_canonrec_path_escape(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    (catalog / "repo_registry.yaml").write_text(
        "repos:\n- name: CanonRec\n  path: ../outside\n  remote_status: configured\n",
        encoding="utf-8",
    )
    with pytest.raises(core.ACEError, match="unsafe"):
        mcp_adapter._registered_canonrec_repo(tmp_path)


def test_materialization_preview_is_state_bound_and_non_mutating(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime, packet, repo = _ready_packet(tmp_path)
    monkeypatch.setattr(mcp_adapter, "_git_read", _clean_feature_git)

    first = mcp_adapter.ace_materialize_preview(
        "packet-001",
        "owner-approval-001",
        root=tmp_path,
        runtime_root=runtime,
        target_repo=repo,
    )
    second = mcp_adapter.ace_materialize_preview(
        "packet-001",
        "owner-approval-002",
        root=tmp_path,
        runtime_root=runtime,
        target_repo=repo,
    )

    assert packet.exists()
    assert first["record_type"] == "ace_mcp_materialization_preview"
    assert first["confirmation_required"] is True
    assert first["target_repository"] == "CanonRec"
    assert first["target_branch"] == "agent/ace-test"
    assert first["authorization_token"].startswith("ace-mcp-auth:")
    assert first["authorization_token"] != second["authorization_token"]
    assert len(first["declared_side_effects"]) == 3


def test_materialization_preview_rejects_protected_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime, _, repo = _ready_packet(tmp_path)

    def protected(repo_path: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "main"
        return _clean_feature_git(repo_path, *args)

    monkeypatch.setattr(mcp_adapter, "_git_read", protected)
    with pytest.raises(core.ACEError, match="non-protected feature branch"):
        mcp_adapter.ace_materialize_preview(
            "packet-001",
            "owner-approval-001",
            root=tmp_path,
            runtime_root=runtime,
            target_repo=repo,
        )


def test_materialization_commit_requires_explicit_side_effect_acknowledgement() -> None:
    with pytest.raises(core.ACEError, match="acknowledgement"):
        mcp_adapter.ace_materialize_commit(
            "packet-001",
            "owner-approval-001",
            "ace-mcp-auth:abc",
            False,
        )


def test_materialization_commit_rejects_token_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packet = tmp_path / "packet"
    repo = tmp_path / "CanonRec"
    packet.mkdir()
    repo.mkdir()
    preview = {
        "authorization_token": "ace-mcp-auth:expected",
        "authority_ref": "owner-approval-001",
        "token_binding": "state",
    }
    monkeypatch.setattr(
        mcp_adapter,
        "_materialization_preview",
        lambda *args, **kwargs: (preview, packet, repo),
    )
    called = False

    def forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(mcp_adapter, "materialize_packet", forbidden)
    with pytest.raises(core.ACEError, match="does not match"):
        mcp_adapter.ace_materialize_commit(
            "packet-001",
            "owner-approval-001",
            "ace-mcp-auth:wrong",
            True,
            root=tmp_path,
        )
    assert called is False


def test_materialization_commit_delegates_only_to_native_materializer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packet = tmp_path / "packet"
    repo = tmp_path / "CanonRec"
    packet.mkdir()
    repo.mkdir()
    preview = {
        "authorization_token": "ace-mcp-auth:expected",
        "authority_ref": "owner-approval-001",
        "token_binding": "packet+authority+registered-target+feature-branch+baseline",
    }
    monkeypatch.setattr(
        mcp_adapter,
        "_materialization_preview",
        lambda *args, **kwargs: (preview, packet, repo),
    )
    calls: list[dict[str, object]] = []

    def fake_materialize(packet_dir: Path, target_repo: Path, **kwargs: object) -> dict[str, object]:
        calls.append({"packet": packet_dir, "repo": target_repo, **kwargs})
        return {"record_type": "ace_determination_receipt", "status": "GENERATED_CANON"}

    monkeypatch.setattr(mcp_adapter, "materialize_packet", fake_materialize)
    result = mcp_adapter.ace_materialize_commit(
        "packet-001",
        "owner-approval-001",
        "ace-mcp-auth:expected",
        True,
        "feat(canon): test",
        root=tmp_path,
    )

    assert calls == [
        {
            "packet": packet,
            "repo": repo,
            "authority_mode": "owner_gated_materialize",
            "authority_ref": "owner-approval-001",
            "root": tmp_path,
            "commit_message": "feat(canon): test",
        }
    ]
    assert result["materialized_determination"]["status"] == "GENERATED_CANON"
    assert result["authorization"]["side_effects_acknowledged"] is True


def test_inspect_finds_invocation_and_linked_determination_without_mutation(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    packet = runtime / "packet-001"
    packet.mkdir(parents=True)
    (runtime / "packet-001.ace-invocation.json").write_text(
        json.dumps(
            {
                "record_type": "ace_invocation_envelope",
                "invocation_id": "ace.invocation.interactive.test",
                "determination_ref": "ace.determination.test",
            }
        ),
        encoding="utf-8",
    )
    (packet / "receipt.json").write_text(
        json.dumps(
            {
                "record_type": "ace_determination_receipt",
                "determination_id": "ace.determination.test",
            }
        ),
        encoding="utf-8",
    )

    by_invocation = mcp_adapter.ace_inspect(
        invocation_id="ace.invocation.interactive.test",
        root=tmp_path,
        runtime_root=runtime,
    )
    assert by_invocation["found"] is True
    assert by_invocation["match_count"] == 1

    by_determination = mcp_adapter.ace_inspect(
        determination_id="ace.determination.test",
        root=tmp_path,
        runtime_root=runtime,
    )
    assert by_determination["found"] is True
    assert by_determination["match_count"] == 2
    assert {item["record_type"] for item in by_determination["matches"]} == {
        "ace_invocation_envelope",
        "ace_determination_receipt",
    }


def test_inspect_requires_exactly_one_reference(tmp_path: Path) -> None:
    with pytest.raises(core.ACEError, match="exactly one"):
        mcp_adapter.ace_inspect(root=tmp_path, runtime_root=tmp_path / "runtime")

    with pytest.raises(core.ACEError, match="exactly one"):
        mcp_adapter.ace_inspect(
            invocation_id="ace.invocation.x",
            determination_id="ace.determination.x",
            root=tmp_path,
            runtime_root=tmp_path / "runtime",
        )
