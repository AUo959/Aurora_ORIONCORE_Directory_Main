from __future__ import annotations

import copy
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import orion_progression as progression  # noqa: E402
from ace.core import ACEError  # noqa: E402

RUN_ID = "11111111-1111-4111-8111-111111111111"
# Restated here on purpose rather than read from the policy: this is an
# independent statement of the attestation, so reading it from the file under
# test would make the assertion tautological. Re-baselined 2026-08-20 for
# CloudBank a19870a5 / blob 5b6d9351 (was 9c34d8e9 / dd3ae6f7); see
# docs/ORION__ADR_LITE__ORION_V013_CLOUDBANK_REBASELINE__v1.0__2026-08-20.md.
CLOUDBANK_SHA = "a19870a576a4136fc7ee8c30a2a8d869f36156d9"
CANONREC_SHA = "dc629a566b2f42fa1c652140b9eef72a4fb0d58a"
OWNER_BLOB = "5b6d93515fb219cb26d267db6c6df6c052413ae1"
AUTHORITY_REF = "owner:orion-l1:test-authorization"


def _expect(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _policy() -> dict[str, Any]:
    return {
        "policy_id": "ace.policy.orion.l1.governed-single-tick.v1",
        "version": "0.13.0",
        "capability_id": progression.ORION_PROGRESSION_CAPABILITY_ID,
        "cloudbank_repository": "aurora-cloudbank-symbolic-main",
        "cloudbank_repository_sha": CLOUDBANK_SHA,
        "owner": {
            "path": "simulation/l1_runtime.py",
            "git_blob_sha": OWNER_BLOB,
            "class": "OrionL1Runtime",
            "preflight_method": "preflight",
            "load_method": "load_run",
            "advance_method": "advance",
            "export_method": "export_state",
        },
        "required_principal": "ORION.ROLE.PILOT",
        "require_existing_run": True,
        "require_preflight_ready": True,
        "require_resume_ready": True,
        "elapsed_minutes": 15,
        "ticks_per_authorization": 1,
        "init_allowed": False,
        "provider_activation_allowed": False,
        "remote_exposure_allowed": False,
        "mcp_exposure_allowed": False,
        "automatic_retry_allowed": False,
        "state_uncertain_requires_operator_reconciliation": True,
    }


def _state(*, tick: int = 7, minute: int = 21) -> dict[str, Any]:
    return {
        "manifest": {
            "run_id": RUN_ID,
            "seed": 808,
            "tick": tick,
            "station_cycle_minute": minute,
            "station_cycle_length_minutes": 1440,
            "status": "ACTIVE",
            "cloudbank_revision": CLOUDBANK_SHA,
            "canonrec_revision": CANONREC_SHA,
        },
        "world_state": {"station": "Orion Station", "test_marker": 0},
        "events": [
            {
                "event_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"test-event-{index}")
                ),
                "tick": index,
                "elapsed_minutes": 15,
                "cause": "autonomous_world_process",
                "kind": "test_event",
            }
            for index in range(1, tick + 1)
        ],
    }


def _write_state(run_root: Path, payload: dict[str, Any]) -> Path:
    path = run_root / RUN_ID / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


class FakeRuntime:
    """Minimal deterministic stand-in for the native Orion runtime owner."""

    resume_ready = True
    state: dict[str, Any] | None = None
    state_path: Path | None = None

    def preflight(self) -> dict[str, Any]:
        return {
            "ready": True,
            "resume_ready": self.resume_ready,
            "blockers": [],
            "embodiment": {
                "ready": self.resume_ready,
                "resume_blockers": [] if self.resume_ready else ["provider_unbound"],
            },
        }

    def load_run(self, run_id: str, *, run_root: Path) -> dict[str, Any]:
        self.state_path = run_root / run_id / "state.json"
        self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
        return copy.deepcopy(self.state)

    def export_state(self) -> dict[str, Any]:
        if self.state is None:
            raise RuntimeError("run not loaded")
        return copy.deepcopy(self.state)

    def advance(self, elapsed_minutes: int = 15) -> dict[str, Any]:
        if self.state is None or self.state_path is None:
            raise RuntimeError("run not loaded")
        manifest = self.state["manifest"]
        manifest["tick"] += 1
        manifest["station_cycle_minute"] = (
            manifest["station_cycle_minute"] + elapsed_minutes
        ) % manifest["station_cycle_length_minutes"]
        event = {
            "event_id": str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"fake-owner:{manifest['run_id']}:{manifest['tick']}",
                )
            ),
            "tick": manifest["tick"],
            "elapsed_minutes": elapsed_minutes,
            "cause": "autonomous_world_process",
            "kind": "fake_native_runtime_event",
        }
        self.state["events"].append(event)
        self.state_path.write_text(
            json.dumps(self.state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return copy.deepcopy(event)


class NotResumeReadyRuntime(FakeRuntime):
    """Synthetic owner whose provider/resume gate remains blocked."""

    resume_ready = False


class WriteThenRaiseRuntime(FakeRuntime):
    """Synthetic owner that persists a tick before raising an ambiguous failure."""

    def advance(self, elapsed_minutes: int = 15) -> dict[str, Any]:
        super().advance(elapsed_minutes)
        raise RuntimeError("synthetic post-write owner failure")


def _bind_fake(
    monkeypatch: pytest.MonkeyPatch,
    runtime_class: type[FakeRuntime],
) -> None:
    monkeypatch.setattr(
        progression,
        "_load_owner_runtime",
        lambda root: {
            "policy": _policy(),
            "runtime_class": runtime_class,
            "cloudbank_repo": root / "synthetic-cloudbank",
            "cloudbank_sha": CLOUDBANK_SHA,
            "owner_blob_sha": OWNER_BLOB,
        },
    )


def test_policy_forbids_init_provider_activation_and_remote_control() -> None:
    policy = progression._load_policy(REPO_ROOT)
    _expect(
        policy["require_existing_run"] is True,
        "v0.13 must require an existing L1 run",
    )
    _expect(
        policy["require_resume_ready"] is True,
        "v0.13 must honor the owner resume gate",
    )
    _expect(
        policy["ticks_per_authorization"] == 1,
        "one authorization must map to one tick",
    )
    _expect(
        policy["elapsed_minutes"] == 15,
        "v0.13 must not expose arbitrary elapsed time",
    )
    for field in (
        "init_allowed",
        "provider_activation_allowed",
        "remote_exposure_allowed",
        "mcp_exposure_allowed",
        "automatic_retry_allowed",
    ):
        _expect(policy[field] is False, f"v0.13 policy must keep {field}=false")


def test_preview_is_non_mutating_and_state_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "runs"
    state_path = _write_state(run_root, _state())
    before = state_path.read_bytes()
    _bind_fake(monkeypatch, FakeRuntime)

    preview = progression.preview_orion_advance(
        RUN_ID,
        AUTHORITY_REF,
        root=REPO_ROOT,
        run_root=run_root,
    )
    _expect(
        state_path.read_bytes() == before,
        "preview must not mutate persisted L1 state",
    )
    _expect(
        preview["status"] == "ready_for_authorization",
        "preview should be authorization-ready",
    )
    _expect(
        preview["authorization"]["run"]["tick"] == 7,
        "preview must bind current tick",
    )
    _expect(
        preview["authorization"]["run"]["station_cycle_minute"] == 21,
        "preview must bind station time",
    )
    _expect(
        preview["authorization"]["execution_owner"]["source_git_blob"]
        == OWNER_BLOB,
        "preview must bind exact owner blob",
    )

    changed = _state()
    changed["world_state"]["test_marker"] = 1
    _write_state(run_root, changed)
    second = progression.preview_orion_advance(
        RUN_ID,
        AUTHORITY_REF,
        root=REPO_ROOT,
        run_root=run_root,
    )
    _expect(
        second["authorization_token"] != preview["authorization_token"],
        "state drift must invalidate the preview token",
    )


def _commit_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, dict[str, Any], dict[str, Any]]:
    run_root = tmp_path / "runs"
    receipt_root = tmp_path / "receipts"
    state_path = _write_state(run_root, _state())
    _bind_fake(monkeypatch, FakeRuntime)
    preview = progression.preview_orion_advance(
        RUN_ID,
        AUTHORITY_REF,
        root=REPO_ROOT,
        run_root=run_root,
    )
    receipt = progression.commit_orion_advance(
        RUN_ID,
        preview["authorization_token"],
        AUTHORITY_REF,
        True,
        root=REPO_ROOT,
        run_root=run_root,
        receipt_root=receipt_root,
    )
    return run_root, receipt_root, state_path, preview, receipt


def test_commit_advances_exactly_one_tick(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_root, _receipt_root, state_path, _preview, receipt = _commit_once(
        tmp_path,
        monkeypatch,
    )
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    _expect(
        persisted["manifest"]["tick"] == 8,
        "commit must advance exactly one tick",
    )
    _expect(
        persisted["manifest"]["station_cycle_minute"] == 36,
        "commit must advance exactly fifteen minutes",
    )
    _expect(
        receipt["before"]["tick"] == 7 and receipt["after"]["tick"] == 8,
        "receipt must prove one tick",
    )
    _expect(receipt["ticks_consumed"] == 1, "receipt must consume one authorized tick")
    _expect(receipt["canon_mutated"] is False, "L1 run progression must not mutate canon")
    _expect(
        Path(receipt["receipt_path"]).is_file(),
        "successful advancement must seal an external receipt",
    )


def test_old_token_replay_refuses_before_second_tick(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root, receipt_root, state_path, preview, _receipt = _commit_once(
        tmp_path,
        monkeypatch,
    )
    with pytest.raises(ACEError, match="stale or invalid"):
        progression.commit_orion_advance(
            RUN_ID,
            preview["authorization_token"],
            AUTHORITY_REF,
            True,
            root=REPO_ROOT,
            run_root=run_root,
            receipt_root=receipt_root,
        )
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    _expect(
        persisted["manifest"]["tick"] == 8,
        "stale-token replay must refuse before another tick",
    )


def test_state_change_after_preview_refuses_before_advance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "runs"
    state_path = _write_state(run_root, _state())
    _bind_fake(monkeypatch, FakeRuntime)
    preview = progression.preview_orion_advance(
        RUN_ID,
        AUTHORITY_REF,
        root=REPO_ROOT,
        run_root=run_root,
    )
    drifted = json.loads(state_path.read_text(encoding="utf-8"))
    drifted["world_state"]["test_marker"] = 99
    _write_state(run_root, drifted)

    with pytest.raises(ACEError, match="stale or invalid"):
        progression.commit_orion_advance(
            RUN_ID,
            preview["authorization_token"],
            AUTHORITY_REF,
            True,
            root=REPO_ROOT,
            run_root=run_root,
            receipt_root=tmp_path / "receipts",
        )
    after = json.loads(state_path.read_text(encoding="utf-8"))
    _expect(
        after["manifest"]["tick"] == 7,
        "state drift must refuse before owner advance",
    )


def test_resume_not_ready_blocks_without_loading_or_advancing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "runs"
    state_path = _write_state(run_root, _state())
    before = state_path.read_bytes()
    _bind_fake(monkeypatch, NotResumeReadyRuntime)

    with pytest.raises(ACEError, match="resume gate is not ready"):
        progression.preview_orion_advance(
            RUN_ID,
            AUTHORITY_REF,
            root=REPO_ROOT,
            run_root=run_root,
        )
    _expect(
        state_path.read_bytes() == before,
        "failed resume gate must leave L1 state untouched",
    )


def test_post_write_owner_failure_is_state_uncertain_and_not_retried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "runs"
    state_path = _write_state(run_root, _state())
    _bind_fake(monkeypatch, WriteThenRaiseRuntime)
    preview = progression.preview_orion_advance(
        RUN_ID,
        AUTHORITY_REF,
        root=REPO_ROOT,
        run_root=run_root,
    )

    with pytest.raises(
        progression.OrionProgressionStateUncertain,
        match="automatic retry is forbidden",
    ):
        progression.commit_orion_advance(
            RUN_ID,
            preview["authorization_token"],
            AUTHORITY_REF,
            True,
            root=REPO_ROOT,
            run_root=run_root,
            receipt_root=tmp_path / "receipts",
        )
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    _expect(
        persisted["manifest"]["tick"] == 8,
        "uncertain state must preserve evidence of the written tick",
    )
    _expect(
        not (tmp_path / "receipts").exists(),
        "uncertain post-write failure must not fabricate success receipt",
    )


def test_side_effect_acknowledgement_and_pilot_principal_are_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "runs"
    state_path = _write_state(run_root, _state())
    _bind_fake(monkeypatch, FakeRuntime)
    preview = progression.preview_orion_advance(
        RUN_ID,
        AUTHORITY_REF,
        root=REPO_ROOT,
        run_root=run_root,
    )

    with pytest.raises(ACEError, match="side-effect acknowledgement"):
        progression.commit_orion_advance(
            RUN_ID,
            preview["authorization_token"],
            AUTHORITY_REF,
            False,
            root=REPO_ROOT,
            run_root=run_root,
            receipt_root=tmp_path / "receipts",
        )
    with pytest.raises(ACEError, match="Pilot principal"):
        progression.preview_orion_advance(
            RUN_ID,
            AUTHORITY_REF,
            principal_id="remote-agent",
            root=REPO_ROOT,
            run_root=run_root,
        )
    _expect(
        json.loads(state_path.read_text(encoding="utf-8"))["manifest"]["tick"] == 7,
        "authority failures must not advance L1",
    )


def test_runtime_progression_is_not_exposed_through_remote_or_mcp() -> None:
    capability = progression.ORION_PROGRESSION_CAPABILITY_ID
    remote = (REPO_ROOT / "tools/ace/remote_service.py").read_text(encoding="utf-8")
    mcp = (REPO_ROOT / "tools/ace/mcp_adapter.py").read_text(encoding="utf-8")
    _expect(
        capability not in remote,
        "v0.13 must not add Orion progression to remote HTTP",
    )
    _expect(
        capability not in mcp,
        "v0.13 must not add Orion progression to MCP",
    )


@pytest.mark.simulation
def test_registered_owner_binding_calls_preflight_only() -> None:
    result = progression.registered_owner_preflight(root=REPO_ROOT)
    _expect(
        result["owner_repository"] == "aurora-cloudbank-symbolic-main",
        "registered owner repository must match",
    )
    _expect(
        result["owner_repository_sha"] == CLOUDBANK_SHA,
        "registered owner SHA must match",
    )
    _expect(
        result["owner_source_git_blob"] == OWNER_BLOB,
        "registered owner blob must match",
    )
    _expect(
        result["run_loaded"] is False,
        "CI owner validation must not load a persisted run",
    )
    _expect(
        result["run_advanced"] is False,
        "CI owner validation must never advance Orion",
    )
    _expect(
        isinstance(result["preflight"], dict),
        "owner preflight must return structured evidence",
    )
