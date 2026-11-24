"""Link accepted outcome artifacts and build reproducible Chronicle input."""

from __future__ import annotations

from datetime import datetime, timezone

from jsonschema import Draft202012Validator, FormatChecker

if __package__:
    from .canon_ops_journal import JournalError
    from .station_chronicle import atom
else:
    from canon_ops_journal import JournalError
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


def _run_registration(request: dict, gates: dict, history: list[dict], origins: list[dict]) -> dict:
    run = gates["deterministic_run"].get("run")
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
    return {
        "kind": "gumas_run",
        "run": run,
        "completed_at": _run_time(run),
        "origin": origins[0],
        "source": request["gate_receipts"]["deterministic_run"]["artifact"],
    }


def _check_run_id(run_id: str, history: list[dict]) -> None:
    for entry in history:
        for event in entry["receipt"].get("events", []):
            if event["kind"] == "gumas_run" and event["run"]["run_id"] == run_id:
                raise JournalError("GUMAS run ID is already registered")


def link_outcome(request: dict, gates: dict, history: list[dict]) -> list[dict]:
    """Link sources to the prior approved staging revision when one is recorded."""
    if request["operation"] != "attach_outcome":
        return []
    origins = _outcome_origins(request, history)
    run_receipt = gates.get("deterministic_run", {})
    if request["execution_mode"] == "deterministic_simulation" and "run" in run_receipt:
        return [_run_registration(request, gates, history, origins)]
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
        [event["origin"]["approving_actor"]], source, event,
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
