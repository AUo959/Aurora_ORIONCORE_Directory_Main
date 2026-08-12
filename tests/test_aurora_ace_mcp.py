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


def test_mcp_contract_declares_exact_non_materializing_surface() -> None:
    contract = json.loads(
        (REPO_ROOT / "catalog/contracts/aurora_ace_mcp_contract_v0_7.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["tool_surface"] == list(mcp_adapter.MCP_TOOL_NAMES)
    assert contract["transport"]["allowed"] == ["stdio"]
    assert contract["transport"]["network_listener_enabled"] is False
    assert contract["authority"]["canonical_materialization_exposed"] is False
    assert contract["authority"]["canonrec_git_mutation_exposed"] is False
    assert contract["authority"]["dynamic_python_binding_exposed"] is False


def test_capabilities_wraps_manifest_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    expected = {"record_type": "ace_warm_capability_index", "capabilities": [{"capability_id": "x"}]}
    monkeypatch.setattr(mcp_adapter, "build_capability_index", lambda root: expected)

    result = mcp_adapter.ace_capabilities(root=tmp_path)

    assert result["capability_index"] == expected
    assert result["tools"] == list(mcp_adapter.MCP_TOOL_NAMES)
    assert result["materialization_exposed"] is False


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
    assert result["materialization_exposed"] is False


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
    assert result["materialization_exposed"] is False


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
