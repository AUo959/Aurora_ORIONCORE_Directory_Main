from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import core, invocation, mcp_adapter  # noqa: E402
from ace import mcp_operator_transaction as operator  # noqa: E402


def _resolution() -> dict[str, object]:
    return {
        "packet_ref": "/tmp/runtime/packet-001",
        "invocation": {"invocation_id": "ace.invocation.interactive.operator-test"},
        "determination": {
            "record_type": "ace_determination_receipt",
            "determination_id": "ace.determination.operator-test",
        },
    }


def _preview() -> dict[str, object]:
    return {
        "record_type": "ace_mcp_materialization_preview",
        "packet_digest": "1" * 64,
        "authority_mode": "owner_gated_materialize",
        "authority_ref": "owner-approval-009",
        "target_repository": "CanonRec",
        "target_branch": "agent/operator-test",
        "target_head": "a" * 40,
        "expected_baseline": "a" * 40,
        "authorization_token": "ace-mcp-auth:" + "b" * 64,
        "declared_side_effects": [
            "write_declared_canonical_target(s)_inside_registered_CanonRec",
            "create_one_CanonRec_git_commit",
            "append_pre_and_post_materialization_ACE_determinations",
        ],
    }


def _prepare(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, object]:
    monkeypatch.setattr(operator, "ace_resolve", lambda *args, **kwargs: _resolution())
    monkeypatch.setattr(operator, "ace_materialize_preview", lambda *args, **kwargs: _preview())
    return operator.prepare_operator_transaction(
        {"record_type": "ace_invocation_envelope"},
        "packet-001",
        "owner-approval-009",
        root=tmp_path,
        transaction_root=tmp_path / "transactions",
    )


def test_prepare_persists_awaiting_confirmation_receipt_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first = _prepare(monkeypatch, tmp_path)
    second = _prepare(monkeypatch, tmp_path)
    assert first == second
    assert first["status"] == "awaiting_confirmation"
    assert first["transaction_id"].startswith("ace.mcp.operator.")
    assert first["authorization"]["side_effects_acknowledged"] is False
    assert first["replay_guard"]["closed"] is False
    assert (tmp_path / "transactions" / f"{first['transaction_id']}.json").is_file()


def test_commit_requires_exact_token_and_acknowledgement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prepared = _prepare(monkeypatch, tmp_path)
    transaction_id = str(prepared["transaction_id"])
    token = str(prepared["preview"]["authorization_token"])

    with pytest.raises(core.ACEError, match="acknowledgement"):
        operator.commit_operator_transaction(
            transaction_id,
            token,
            False,
            root=tmp_path,
            transaction_root=tmp_path / "transactions",
        )
    with pytest.raises(core.ACEError, match="does not match"):
        operator.commit_operator_transaction(
            transaction_id,
            "ace-mcp-auth:wrong",
            True,
            root=tmp_path,
            transaction_root=tmp_path / "transactions",
        )

    unchanged = operator.inspect_operator_transaction(
        transaction_id,
        root=tmp_path,
        transaction_root=tmp_path / "transactions",
    )
    assert unchanged["status"] == "awaiting_confirmation"


def test_commit_records_post_commit_inspection_and_closes_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prepared = _prepare(monkeypatch, tmp_path)
    transaction_id = str(prepared["transaction_id"])
    token = str(prepared["preview"]["authorization_token"])
    calls: list[str] = []

    def fake_commit(*args: object, **kwargs: object) -> dict[str, object]:
        calls.append("commit")
        return {
            "record_type": "ace_mcp_materialization_result",
            "materialized_determination": {
                "record_type": "ace_determination_receipt",
                "determination_id": "ace.determination.operator-test.materialized.123456789abc",
                "status": "GENERATED_CANON",
                "materialization": {"commit_sha": "c" * 40},
            },
        }

    monkeypatch.setattr(operator, "ace_materialize_commit", fake_commit)

    def fake_inspect(**kwargs: object) -> dict[str, object]:
        return {
            "record_type": "ace_mcp_inspection",
            "found": True,
            "match_count": 1,
            "lookup": {
                "determination_id": str(kwargs["determination_id"]),
            },
        }

    monkeypatch.setattr(operator, "ace_inspect", fake_inspect)
    committed = operator.commit_operator_transaction(
        transaction_id,
        token,
        True,
        root=tmp_path,
        transaction_root=tmp_path / "transactions",
    )

    assert committed["status"] == "committed"
    assert committed["post_commit_inspection"]["found"] is True
    assert committed["replay_guard"]["closed"] is True
    assert calls == ["commit"]

    with pytest.raises(core.ACEError, match="not awaiting confirmation"):
        operator.commit_operator_transaction(
            transaction_id,
            token,
            True,
            root=tmp_path,
            transaction_root=tmp_path / "transactions",
        )
    assert calls == ["commit"]


def test_native_refusal_is_durable_and_closes_transaction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prepared = _prepare(monkeypatch, tmp_path)
    transaction_id = str(prepared["transaction_id"])
    token = str(prepared["preview"]["authorization_token"])

    def refused(*args: object, **kwargs: object) -> dict[str, object]:
        raise core.ACEError("baseline advanced", code="registry_baseline_advanced")

    monkeypatch.setattr(operator, "ace_materialize_commit", refused)
    with pytest.raises(core.ACEError, match="baseline advanced"):
        operator.commit_operator_transaction(
            transaction_id,
            token,
            True,
            root=tmp_path,
            transaction_root=tmp_path / "transactions",
        )

    refused_receipt = operator.inspect_operator_transaction(
        transaction_id,
        root=tmp_path,
        transaction_root=tmp_path / "transactions",
    )
    assert refused_receipt["status"] == "refused"
    assert refused_receipt["refusal"]["error_code"] == "registry_baseline_advanced"
    assert refused_receipt["replay_guard"]["closed"] is True


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


@pytest.mark.skipif(
    os.environ.get("ACE_MCP_E2E") != "1",
    reason="requires provisioned registered CloudBank and CanonRec checkouts",
)
def test_end_to_end_operator_transaction_materializes_inspects_and_refuses_replay(
    tmp_path: Path,
) -> None:
    canonrec = REPO_ROOT / core.CANONREC_REL
    cloudbank = REPO_ROOT / core.CLOUDBANK_REL
    assert (canonrec / ".git").exists()
    assert (cloudbank / ".git").exists()

    original_branch = subprocess.check_output(
        ["git", "-C", str(canonrec), "branch", "--show-current"], text=True
    ).strip() or "main"
    baseline = subprocess.check_output(
        ["git", "-C", str(canonrec), "rev-parse", "HEAD"], text=True
    ).strip()
    ledger = REPO_ROOT / "reports/ace/determinations"
    before_ledger = set(ledger.rglob("*.json")) if ledger.exists() else set()

    subprocess.run(
        ["git", "-C", str(canonrec), "checkout", "-B", "validation/ace-mcp-v0-9", baseline],
        check=True,
        capture_output=True,
        text=True,
    )

    runtime_root = tmp_path / "runtime"
    transaction_root = tmp_path / "transactions"
    try:
        envelope = invocation.compile_facility_invocation(
            "Determine the canonical L1 facility location for MCP Security / Shuttle Bay.",
            _facility_context(),
            subject_ref="L1-EMB-MCP-SHUTTLE-BAY",
            root=REPO_ROOT,
        )
        prepared = operator.prepare_operator_transaction(
            envelope,
            "e2e-mcp-shuttle-bay",
            "owner-e2e-validation-009",
            root=REPO_ROOT,
            runtime_root=runtime_root,
            transaction_root=transaction_root,
        )
        assert prepared["status"] == "awaiting_confirmation"
        assert prepared["preview"]["target_head"] == baseline
        assert prepared["preview"]["target_branch"] == "validation/ace-mcp-v0-9"

        token = str(prepared["preview"]["authorization_token"])
        committed = operator.commit_operator_transaction(
            str(prepared["transaction_id"]),
            token,
            True,
            "test(canon): ACE v0.9 operator e2e validation",
            root=REPO_ROOT,
            runtime_root=runtime_root,
            transaction_root=transaction_root,
        )
        assert committed["status"] == "committed"
        assert committed["post_commit_inspection"]["found"] is True
        materialized = committed["result"]["materialized_determination"]
        commit_sha = materialized["materialization"]["commit_sha"]
        assert materialized["status"] in {"GENERATED_CANON", "CANON_REVISION"}
        assert subprocess.check_output(
            ["git", "-C", str(canonrec), "rev-parse", "HEAD"], text=True
        ).strip() == commit_sha
        assert commit_sha != baseline
        assert subprocess.check_output(
            ["git", "-C", str(canonrec), "rev-list", "--count", f"{baseline}..HEAD"], text=True
        ).strip() == "1"
        assert subprocess.check_output(
            ["git", "-C", str(canonrec), "status", "--porcelain"], text=True
        ).strip() == ""

        with pytest.raises(core.ACEError, match="not awaiting confirmation"):
            operator.commit_operator_transaction(
                str(prepared["transaction_id"]),
                token,
                True,
                root=REPO_ROOT,
                runtime_root=runtime_root,
                transaction_root=transaction_root,
            )
        with pytest.raises(core.ACEError, match="baseline advanced"):
            mcp_adapter.ace_materialize_commit(
                "e2e-mcp-shuttle-bay",
                "owner-e2e-validation-009",
                token,
                True,
                root=REPO_ROOT,
                runtime_root=runtime_root,
            )
    finally:
        subprocess.run(
            ["git", "-C", str(canonrec), "reset", "--hard", baseline],
            check=False,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(canonrec), "clean", "-fd"],
            check=False,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(canonrec), "checkout", "-B", original_branch, baseline],
            check=False,
            capture_output=True,
            text=True,
        )
        if ledger.exists():
            for path in sorted(set(ledger.rglob("*.json")) - before_ledger, reverse=True):
                path.unlink(missing_ok=True)
