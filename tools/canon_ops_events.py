"""Link accepted outcome artifacts and build reproducible Chronicle input."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone

from jsonschema import Draft202012Validator, FormatChecker

if __package__:
    from .canon_ops_journal import JournalError, digest
    from .station_chronicle import atom
else:
    from canon_ops_journal import JournalError, digest
    from station_chronicle import atom


RUN_FIELDS = {
    "version": {"const": "1.0"},
    "run_id": {"type": "string", "minLength": 1, "maxLength": 256},
    "origin_request_id": {"type": "string", "minLength": 1, "maxLength": 256},
    "origin_content_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "engine_commit": {"type": "string", "pattern": "^(?:[a-f0-9]{40}|[a-f0-9]{64})$"},
    "seed": {"type": "integer"},
    "event_count": {"type": "integer", "minimum": 0},
    "completed_at": {"type": "string", "format": "date-time"},
}
RUN_VALIDATOR = Draft202012Validator(
    {
        "type": "object",
        "properties": RUN_FIELDS,
        "required": list(RUN_FIELDS),
        "additionalProperties": False,
    },
    format_checker=FormatChecker(),
)


def _identity(value: dict) -> tuple[str, str, str, str]:
    return value["layer"], value["kind"], value["record_id"], value["state"]["revision"]


def _accepted_origins(history: list[dict]) -> dict[tuple[str, str, str, str], dict]:
    origins = {}
    for entry in history:
        receipt = entry["receipt"]
        for update in receipt["target_updates"]:
            identity = _identity(update)
            origins[identity] = {
                "request_id": receipt["request_id"],
                "content_hash": receipt["content_hash"],
                "approving_actor": entry["request"]["approval"]["authority"],
            }
    return origins


def _outcome_origins(request: dict, history: list[dict]) -> list[dict]:
    known = _accepted_origins(history)
    references = []
    for target in request["targets"]:
        identity = _identity({**target, "state": target["expected_state"]})
        origin = known.get(identity)
        if origin:
            references.append({**origin, "target": {
                key: target[key] for key in ("layer", "kind", "record_id")
            }})
    return references


def _run_time(run: dict) -> str:
    try:
        completed = datetime.fromisoformat(run["completed_at"].upper().replace("Z", "+00:00"))
    except ValueError as exc:
        raise JournalError("/gate_receipts/deterministic_run/run/completed_at: invalid instant") from exc
    if completed.tzinfo is None:
        raise JournalError("/gate_receipts/deterministic_run/run/completed_at: time zone required")
    return completed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _native_reference(
    request: dict, gate: dict, run: dict, origin: dict, read_artifact: Callable[[dict], bytes],
) -> dict:
    reference = gate["run_receipt"]
    if reference not in request["sources"]:
        raise JournalError("/gate_receipts/deterministic_run: native receipt must be a verified request source")
    native = json.loads(read_artifact(reference))
    semantic = native.pop("semantic_sha256")
    if digest(native) != semantic:
        raise JournalError("/gate_receipts/deterministic_run: native receipt fails its semantic digest")
    actual = {
        "run_id": native["run_id"], "origin_request_id": native["origin_request_id"],
        "origin_content_hash": native["origin_content_hash"], "engine_commit": native["seed"]["engine"]["commit"],
        "seed": native["seed"]["parameters"]["seed"], "event_count": native["layer_gate"]["event_count"],
    }
    approval = native["approval"]
    matches = (
        actual == {key: run[key] for key in actual}, native["layer"] == "L2",
        native["canonical_promotion"] is False, native["layer_gate"]["status"] == "PASS",
        approval["actor"] == origin["approving_actor"],
    )
    if not all(matches):
        raise JournalError("/gate_receipts/deterministic_run: native receipt differs from the approved run")
    return {
        "source": reference, "semantic_sha256": semantic,
        "participants": list(dict.fromkeys((approval["actor"], approval["relay"]))),
    }


def _run_registration(
    request: dict, gate: dict, history: list[dict], origins: list[dict],
    read_artifact: Callable[[dict], bytes],
) -> dict:
    run = gate.get("run")
    error = next(RUN_VALIDATOR.iter_errors(run), None)
    if error:
        field = "/".join(map(str, error.absolute_path))
        raise JournalError(f"/gate_receipts/deterministic_run/run/{field}: {error.message}")
    if request["layer"] != "L2":
        raise JournalError("/layer: GUMAS run registration requires L2")
    parent = (run["origin_request_id"], run["origin_content_hash"])
    links = {(origin["request_id"], origin["content_hash"]) for origin in origins}
    if links != {parent} or len(origins) != len(request["targets"]):
        raise JournalError("/gate_receipts/deterministic_run: origin must match all staged targets")
    _check_run_id(run["run_id"], history)
    gate_reference = request["gate_receipts"]["deterministic_run"]["artifact"]
    registration = {
        "kind": "gumas_run",
        "run": run,
        "completed_at": _run_time(run),
        "origin": origins[0],
        "source": gate_reference,
    }
    if "run_receipt" in gate:
        registration.update(_native_reference(request, gate, run, origins[0], read_artifact))
        registration["registration_gate"] = gate_reference
    return registration


def _check_run_id(run_id: str, history: list[dict]) -> None:
    for entry in history:
        for event in entry["receipt"].get("events", []):
            if event["kind"] == "gumas_run" and event["run"]["run_id"] == run_id:
                raise JournalError("GUMAS run ID is already registered")


def link_outcome(
    request: dict, gates: dict, history: list[dict], read_artifact: Callable[[dict], bytes],
) -> list[dict]:
    """Link sources to the prior approved staging revision when one is recorded."""
    if request["operation"] != "attach_outcome":
        return []
    origins = _outcome_origins(request, history)
    run_receipt = gates.get("deterministic_run", {})
    if request["execution_mode"] == "deterministic_simulation" and "run" in run_receipt:
        return [_run_registration(request, run_receipt, history, origins, read_artifact)]
    return [{
        "kind": "outcome_attachment",
        "origins": origins,
        "targets": request["targets"],
        "sources": request["sources"],
    }]


def _run_atom(event: dict) -> dict:
    run = event["run"]
    reference = event["source"]
    source = (
        f"{reference['repository']}:{reference['path']}@{reference['commit']}"
        f"#sha256={reference['sha256']}"
    )
    return atom(
        event["completed_at"], "STAGING", "simulation", "gumas_run_registered",
        f"Registered GUMAS run {run['run_id']} with {run['event_count']} events.",
        event.get("participants", [event["origin"]["approving_actor"]]), source, event,
    )


def chronicle_atoms(history: list[dict]) -> list[dict]:
    """Project stored run registrations through the Station Chronicle atom format."""
    events = (
        event for entry in history
        for event in entry["receipt"].get("events", [])
        if event["kind"] == "gumas_run"
    )
    return sorted((_run_atom(event) for event in events), key=_atom_order)


def _atom_order(value: dict) -> tuple[datetime, str]:
    occurred = datetime.fromisoformat(value["occurred_at"].replace("Z", "+00:00"))
    return occurred, value["event_id"]
