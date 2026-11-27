"""Execute an approved L2 scenario seed using the pinned GUMAS runtime."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from jsonschema import Draft202012Validator

if __package__:
    from . import canon_ops_journal as journal
    from .aurora_simulation_readiness import run_command
    from .canon_ops_intake import Reader, _object, _require_commit, _unique_object, read_artifact_from, subject_digest
    from .canon_ops_query import CanonRec
else:
    import canon_ops_journal as journal
    from aurora_simulation_readiness import run_command
    from canon_ops_intake import Reader, _object, _require_commit, _unique_object, read_artifact_from, subject_digest
    from canon_ops_query import CanonRec


ENGINE_VERSION = "4.0.0-synth"
SCENARIO_ID = "gumas_canonical_v1"
ENGINE_RUNNER = "skills/gumas-simulation-engine/scripts/run_gumas_advanced.py"
ENGINE_SOURCE_PATHS = (
    ENGINE_RUNNER, "GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS", "GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19",
    "GUMAS_SIM_2.0",
)
RUN_ARTIFACTS = ("initial-state.json", "state.json", "advanced_event_ledger.ndjson")
IDENTIFIER = {"type": "string", "minLength": 1}
SHA256 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
GIT_COMMIT = {"type": "string", "pattern": "^(?:[0-9a-f]{40}|[0-9a-f]{64})$"}


class RunError(ValueError):
    """The requested run could not be approved, executed, or verified."""


def _schema(properties: dict, *, optional: tuple[str, ...] = ()) -> dict:
    return {
        "type": "object", "additionalProperties": False, "properties": properties,
        "required": [name for name in properties if name not in optional],
    }


ARTIFACT = _schema({
    "repository": IDENTIFIER, "commit": GIT_COMMIT, "path": IDENTIFIER,
    "sha256": SHA256, "layer": {"const": "L2"},
})
RUN_REQUEST = Draft202012Validator(_schema({
    "version": {"const": "1.0"}, "layer": {"const": "L2"},
    "origin_request_id": IDENTIFIER, "origin_content_hash": SHA256,
    "scenario_seed": ARTIFACT,
}))
APPROVED_SEED = Draft202012Validator(_schema({
    "version": {"const": "1.0"}, "seed_id": IDENTIFIER, "forecast_id": IDENTIFIER,
    "parameters": _schema({
        "scenario_id": {"const": SCENARIO_ID}, "seed": {"type": "integer"},
        "turns": {"type": "integer", "minimum": 1},
    }),
    "engine": _schema({"version": {"const": ENGINE_VERSION}, "commit": GIT_COMMIT}),
}, optional=("forecast_id",)))


def _validate(validator: Draft202012Validator, payload: dict, label: str) -> None:
    error = next(validator.iter_errors(payload), None)
    if error:
        pointer = "/".join(map(str, error.absolute_path))
        raise RunError(f"{label}/{pointer}: {error.message}")


def _verified_bytes(reference: dict, read_artifact: Reader) -> bytes:
    data = read_artifact(reference)
    if hashlib.sha256(data).hexdigest() != reference["sha256"]:
        raise RunError(f"Artifact digest mismatch for {reference['path']}")
    return data


def _staged_origin(entries: list[dict], run: dict) -> dict:
    origin = next((entry for entry in entries if entry["request"]["request_id"] == run["origin_request_id"]), None)
    if origin is None or origin["receipt"]["status"] != "ACCEPTED":
        raise RunError("The origin lacks an accepted staging receipt")
    proposal = origin["request"]
    if proposal["layer"] != "L2" or proposal["content_hash"] != run["origin_content_hash"]:
        raise RunError("The origin differs from the requested L2 staging revision")
    if run["scenario_seed"] not in proposal["sources"]:
        raise RunError("The seed was not included in the approved staging sources")
    return proposal


def _verify_authority(proposal: dict, policy: dict, read_artifact: Reader) -> dict:
    submitter, decision = proposal["submitter"], proposal["approval"]
    relay = submitter.get("relay_id", submitter["actor_id"])
    direct_qgia = submitter["system"].casefold() == "qgia" and relay == submitter["actor_id"]
    if direct_qgia or relay not in policy["l1_relays"]:
        raise RunError("An approved L1 actor or relay must mediate the scenario seed")
    approval = proposal["gate_receipts"]["authorization_approval"]["artifact"]
    gate_origin = {key: approval[key] for key in ("repository", "commit")}
    if gate_origin not in policy["gate_origins"]["authorization_approval"]:
        raise RunError("The approval origin lacks an authorization trust pin")
    attestation = json.loads(_verified_bytes(approval, read_artifact), object_pairs_hook=_unique_object)
    if not isinstance(attestation, dict) or attestation.get("subject_sha256") != subject_digest(proposal):
        raise RunError("The approval receipt covers a different request subject")
    authority = decision.get("authority")
    if (decision["state"] != "approved" or authority not in policy["approvers"]["L2"]
            or (attestation.get("decision"), attestation.get("authority")) != ("approved", authority)):
        raise RunError("The scenario seed lacks approval from an authorized actor")
    return {"actor": authority, "relay": relay, "receipt": approval}


def prepare_run(run: dict, policy: dict, path: Path, tip: str, read_artifact: Reader) -> dict:
    """Return the approved execution inputs without executing the engine."""
    _validate(RUN_REQUEST, run, "run")
    entries = journal.read_entries(path)
    if not entries or entries[-1]["sha256"] != tip:
        raise RunError("The staging journal does not match the trusted terminal digest")
    if entries[-1]["receipt"]["canon_commit"] != policy["canon_commit"]:
        raise RunError("The staging journal does not match the approved CanonRec snapshot")
    proposal = _staged_origin(entries, run)
    approval = _verify_authority(proposal, policy, read_artifact)
    seed = json.loads(_verified_bytes(run["scenario_seed"], read_artifact), object_pairs_hook=_unique_object)
    _validate(APPROVED_SEED, seed, "scenario_seed")
    if seed["engine"]["commit"] != policy["engine_commit"]:
        raise RunError("The seed does not pin the allowed GUMAS engine commit")
    current = journal.staging_state(entries).get(("L2", "scenario_seed", seed["seed_id"]))
    if current != {"revision": proposal["content_hash"], "certainty": "STAGING"}:
        raise RunError("The approved scenario seed is absent or stale")
    for reference in proposal["sources"]:
        if reference != run["scenario_seed"]:
            _verified_bytes(reference, read_artifact)

    identity = {
        "version": "1.0", "layer": "L2", "canon_commit": policy["canon_commit"],
        "origin_request_id": proposal["request_id"], "origin_content_hash": proposal["content_hash"],
        "scenario_seed": run["scenario_seed"], "seed": seed, "approval": approval,
        "input_sources": proposal["sources"],
    }
    return {**identity, "run_id": "gumas-" + journal.digest(identity)}


def _engine_files(repo: CanonRec, revision: str, workspace: Path) -> dict:
    _require_commit(repo, revision)
    tree = repo.git("ls-tree", "-rz", "--full-tree", revision, "--", *ENGINE_SOURCE_PATHS)
    inventory = {}
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        attributes, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = attributes.decode("ascii").split()
        path = Path(raw_path.decode("utf-8"))
        if path.is_absolute() or ".." in path.parts or path.suffix not in {".py", ".json", ".md", ".csv"}:
            continue
        if kind != "blob" or mode == "120000":
            raise RunError(f"GUMAS input is not a regular Git blob: {path}")
        data = repo.blob(oid)
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        inventory[path.as_posix()] = hashlib.sha256(data).hexdigest()
    if ENGINE_RUNNER not in inventory:
        raise RunError("The approved GUMAS commit does not contain the replay runner")
    return inventory


def _run_engine(workspace: Path, output: Path, seed: int, turns: int) -> None:
    result = run_command([
        sys.executable, "-I", str(workspace / ENGINE_RUNNER), "--workspace", str(workspace),
        "--seed", str(seed), "--turns", str(turns), "--replay-artifacts", "--output", str(output),
    ], workspace, timeout=120, env={})
    if result.returncode != 0:
        raise RunError(f"Pinned GUMAS runner failed ({result.returncode}): {result.stderr.strip()}")


def _verify_native_output(directory: Path, seed: dict) -> tuple[dict, dict]:
    initial = _object(directory / "initial-state.json")
    state = _object(directory / "state.json")
    parameters = seed["parameters"]
    for expected_turn, snapshot in ((0, initial), (parameters["turns"], state)):
        base = snapshot["base_state"]
        if (snapshot["version"], snapshot["turn"], base["seed"], base["scenario_id"]) != (
            ENGINE_VERSION, expected_turn, parameters["seed"], parameters["scenario_id"],
        ):
            raise RunError("The GUMAS output differs from the approved seed, scenario, engine, or turn range")

    ledger = directory / "advanced_event_ledger.ndjson"
    count, turn, seen = 0, 0, set()
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line, object_pairs_hook=_unique_object)
            event_id = event["event_id"]
            if (event_id in seen or not max(1, turn) <= event["turn"] <= parameters["turns"]
                    or event["seed"] != parameters["seed"] or event["engine_version"] != ENGINE_VERSION):
                raise RunError("The GUMAS ledger contains a repeated identity or an out-of-scope event")
            if event["scenario_id"] != parameters["scenario_id"] or event["schema_version"] != "event-ledger-v1":
                raise RunError("The GUMAS ledger declares a different scenario or schema")
            payload = event["payload"]
            if (payload["event_id"], payload["payload_hash"], payload["event_ordinal"]) != (
                event_id, event["payload_hash"], event["ordinal"],
            ):
                raise RunError("The GUMAS event envelope differs from its payload")
            seen.add(event_id)
            count += 1
            turn = event["turn"]
    if state["event_ledger"] != {
        "schema_version": "event-ledger-v1", "record_count": count, "path": ledger.name,
    }:
        raise RunError("The exported ledger reference or record count differs from the ledger")
    return {
        "start": {"turn": 0, "artifact": "initial-state.json"},
        "end": {"turn": parameters["turns"], "artifact": "state.json", "metrics": state["latest_metrics"]},
    }, {
        "status": "PASS", "method": "verified seed, version, turn interval, event envelopes and ledger count",
        "limit": "Native fixture output only. CanonRec fabric and promotion gates require separate evidence.",
        "event_count": count,
    }


def _inventory(directory: Path) -> dict:
    return {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in RUN_ARTIFACTS}


def _receipt(directory: Path, scope: dict, engine_files: dict) -> dict:
    summaries, checks = _verify_native_output(directory, scope["seed"])
    payload = {
        **scope, "engine_inputs": engine_files, "output_artifacts": _inventory(directory),
        "states": summaries, "layer_gate": checks, "canonical_promotion": False,
    }
    return {**payload, "semantic_sha256": journal.digest(payload)}


def _read_published(path: Path, scope: dict, engine_files: dict) -> dict:
    if path.is_symlink() or any((path / name).is_symlink() for name in (*RUN_ARTIFACTS, "receipt.json")):
        raise RunError("Run output paths must refer to files in the run directory")
    recorded = _object(path / "receipt.json")
    if _receipt(path, scope, engine_files) != recorded:
        raise RunError("Published run output differs from its receipt")
    return recorded


def execute(scope: dict, engine_repo: CanonRec, root: Path, *, replay: bool = False) -> dict:
    """Publish a verified run only after all artifacts have been written and validated."""
    final_path = root / scope["run_id"]
    parameters = scope["seed"]["parameters"]
    root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=root, prefix=".gumas-") as scratch:
        workspace, output = (Path(scratch) / name for name in ("source", "result"))
        engine_files = _engine_files(engine_repo, scope["seed"]["engine"]["commit"], workspace)
        prior = _read_published(final_path, scope, engine_files) if final_path.exists() else None
        if prior is not None and not replay:
            return {"status": "DUPLICATE", "receipt": prior}
        initial = Path(scratch) / "initial" / "state.json"
        _run_engine(workspace, initial, parameters["seed"], 0)
        _run_engine(workspace, output / "state.json", parameters["seed"], parameters["turns"])
        initial.rename(output / "initial-state.json")
        receipt = _receipt(output, scope, engine_files)
        if prior is not None:
            if prior != receipt:
                raise RunError("Replay did not match the prior run receipt")
            return {"status": "REPLAY_MATCH", "receipt": receipt}
        (output / "receipt.json").write_text(journal.canonical_json(receipt) + "\n", encoding="utf-8")
        try:
            output.rename(final_path)
        except OSError as exc:
            if exc.errno not in {errno.EEXIST, errno.ENOTEMPTY}:
                raise
            if _read_published(final_path, scope, engine_files) != receipt:
                raise RunError("Replay did not match the prior run receipt") from exc
            return {"status": "REPLAY_MATCH" if replay else "DUPLICATE", "receipt": receipt}
    return {"status": "COMPLETED", "receipt": receipt}


def main() -> int:
    """Run the local approved-scenario adapter."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--journal-tip", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--engine-repository", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--repository", action="append", default=[], metavar="OWNER/REPO=PATH")
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    try:
        engine = CanonRec(args.engine_repository)
        sources = {name: CanonRec(Path(path)) for name, path in (item.split("=", 1) for item in args.repository)}
        root = args.run_root.resolve()
        checkouts = [repo.path.resolve() for repo in (*sources.values(), engine)]
        checkouts.append(Path(__file__).resolve().parent.parent)
        if any(root.is_relative_to(checkout) for checkout in checkouts):
            raise RunError("The run workspace must be outside the source checkouts")
        scope = prepare_run(
            _object(args.request), _object(args.policy), args.journal, args.journal_tip,
            read_artifact_from(sources),
        )
        result = execute(scope, engine, root, replay=args.replay)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(journal.canonical_json({"status": "REJECTED", "reason": str(exc)}))
        return 1
    print(journal.canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
