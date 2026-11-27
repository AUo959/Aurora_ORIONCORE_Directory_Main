"""Accept typed Canon Operations requests into an offline staging journal."""

from __future__ import annotations

import argparse
import json
import re
import runpy
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

if __package__:
    from . import canon_ops_events as events
    from . import canon_ops_journal as journal
    from . import canon_ops_reconciliation as reconciliation
    from .canon_ops_query import CONTRACT_COMMIT, CONTRACT_PATH, SOURCE_REPOSITORY, CanonRec, query
else:
    import canon_ops_events as events
    import canon_ops_journal as journal
    import canon_ops_reconciliation as reconciliation
    from canon_ops_query import CONTRACT_COMMIT, CONTRACT_PATH, SOURCE_REPOSITORY, CanonRec, query


VALIDATOR_FILE = "aurora-canon-reconciler/scripts/canon_ops.py"
VALIDATOR_SCHEMAS = ("common", "gate-receipt-set", "mutation-request")
STATE_OPERATIONS = {
    "create_staging_claim": "STAGING",
    "amend_staging_claim": "STAGING",
    "supersede_staging_record": "SUPERSEDED",
}
Reader = Callable[[dict], bytes]
Validator = Callable[[dict, Reader], None]
TargetLookup = Callable[[dict], Optional[dict]]


class IntakeError(ValueError):
    """The bridge cannot accept the request or establish its authority."""


def _require_commit(repo: CanonRec, revision: str) -> None:
    if not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", revision):
        raise IntakeError("Expected a full Git commit ID")
    if repo.git("cat-file", "-t", revision).strip() != b"commit":
        raise IntakeError("Pinned artifact revision must identify a Git commit")


@contextmanager
def pinned_validator(repo: CanonRec) -> Iterator[Validator]:
    """Load the previously reviewed validator and schemas from the fixed CanonRec commit."""
    with TemporaryDirectory(prefix="canon-ops-contract-") as directory:
        root = Path(directory)
        files = [VALIDATOR_FILE] + [
            f"{CONTRACT_PATH}/{schema}.schema.json" for schema in VALIDATOR_SCHEMAS
        ]
        for relative in files:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(repo.blob(f"{CONTRACT_COMMIT}:{relative}"))
        # Only the fixed published validator runs. Requests and references are data.
        yield runpy.run_path(str(root / VALIDATOR_FILE))["validate_mutation"]


def read_artifact_from(repositories: Mapping[str, CanonRec]) -> Reader:
    """Resolve artifact references against the operator's local repository mappings."""
    @cache
    def pinned_repo(repository: str, commit: str) -> CanonRec:
        repo = repositories[repository]
        _require_commit(repo, commit)
        return repo

    @cache
    def pinned_blob(repository: str, commit: str, path: str) -> bytes:
        return pinned_repo(repository, commit).blob(f"{commit}:{path}")

    def read(reference: dict) -> bytes:
        return pinned_blob(reference["repository"], reference["commit"], reference["path"])

    return read


def subject_digest(request: dict) -> str:
    """Hash the subject that each gate reviewed without hashing its own receipt reference."""
    return journal.digest({
        key: value for key, value in request.items() if key not in {"content_hash", "gate_receipts"}
    })


def _authorize_submitter(request: dict, principal: str, policy: dict) -> None:
    submitter = request["submitter"]
    if principal != submitter.get("relay_id", submitter["actor_id"]):
        raise IntakeError("/submitter: authenticated identity differs from the request")
    grant = {
        "principal": principal,
        "actor_id": submitter["actor_id"],
        "system": submitter["system"],
        "layer": request["layer"],
        "operation": request["operation"],
    }
    if grant not in policy["grants"]:
        raise IntakeError("/submitter: identity lacks the configured staging grant")


def _gate_references(request: dict) -> Iterator[tuple[str, dict]]:
    for gate, receipt in request["gate_receipts"].items():
        if gate == "naming":
            if "exemption" in receipt:
                yield "naming_exemption", receipt["exemption"]
            else:
                yield "naming", receipt["receipt"]
        else:
            yield gate, receipt


def _trusted_gates(request: dict, policy: dict, read_artifact: Reader) -> dict:
    expected_subject = subject_digest(request)
    evidence = {}
    for gate, receipt in _gate_references(request):
        artifact = receipt["artifact"]
        origin = {key: artifact[key] for key in ("repository", "commit")}
        if origin not in policy["gate_origins"].get(gate, []):
            raise IntakeError(f"/gate_receipts/{gate}: origin lacks a configured trust pin")
        payload = json.loads(read_artifact(artifact))
        if payload.get("subject_sha256") != expected_subject:
            raise IntakeError(f"/gate_receipts/{gate}: receipt is bound to another request subject")
        evidence[gate] = payload
    return evidence


def _approval(request: dict, policy: dict, gates: dict) -> str:
    approval = request["approval"]
    recorded = gates["authorization_approval"]
    state = approval["state"]
    if (recorded.get("decision"), recorded.get("authority")) != (state, approval.get("authority")):
        raise IntakeError("/approval: decision or authority differs from its receipt")
    if state != "pending" and approval["authority"] not in policy["approvers"].get(request["layer"], []):
        raise IntakeError("/approval/authority: authority lacks approval scope for the layer")
    return state


def _gate_disposition(request: dict, approval: str, gates: dict) -> tuple[str, str]:
    if approval == "rejected":
        return "REJECTED", "approval rejected"
    if approval == "pending":
        return "NEEDS_REVIEW", "approval pending"
    if any(gate.get("verdict") != "PASS" for gate in gates.values()):
        return "REJECTED", "a required gate did not pass"
    if request["operation"] == "request_promotion_review":
        return "NEEDS_REVIEW", "promotion requires separate CanonRec review"
    if gates["final_reconciliation"].get("recommendation") != "STAGING":
        return "NEEDS_REVIEW", "reconciliation did not recommend staging"
    return "ACCEPTED", "approved for local staging"


def _snapshot_records(repo: CanonRec, policy: dict) -> TargetLookup:
    snapshot = policy["canon_commit"]
    _require_commit(repo, snapshot)

    def lookup(target: dict) -> dict | None:
        layer = target["layer"]
        response = query(repo, {
            "version": "1.0",
            "query_id": "staging-target",
            "idempotency_key": "target-" + journal.digest(target),
            "layer": layer,
            "commit": snapshot,
            "source_paths": policy["target_paths"][layer],
            "filters": {"entity_kinds": [target["kind"]], "entity_ids": [target["record_id"]]},
            "page": {"limit": 2},
        })
        matches = [record for collection in response["results"].values() for record in collection]
        if len(matches) > 1 or response["next_after"] is not None:
            raise IntakeError(f"/targets: ambiguous pinned record {target['record_id']}")
        return matches[0] if matches else None

    return lookup


def snapshot_targets(repo: CanonRec, policy: dict) -> TargetLookup:
    """Resolve target revisions against the pinned CanonRec snapshot and scope."""
    read_record = _snapshot_records(repo, policy)

    def lookup(target: dict) -> dict | None:
        record = read_record(target)
        if record is None:
            return None
        return {"revision": record["source"]["sha256"], "certainty": record["certainty"]}

    return lookup


def record_provenance(repo: CanonRec, policy: dict, path: Path, target: dict) -> dict:
    """Read the pinned record and its verified staging history for one target."""
    snapshot = policy["canon_commit"]
    history = journal.read_entries(path)
    if history and history[0]["receipt"]["canon_commit"] != snapshot:
        raise IntakeError("The journal uses a different CanonRec snapshot")
    record = _snapshot_records(repo, policy)(target)
    entries = journal.entries_for_target(history, target)
    if record is None and not entries:
        raise IntakeError("Record is absent from the pinned snapshot and staging journal")
    return {"target": target, "canon_commit": snapshot, "record": record, "entries": entries}


def _target_updates(
    request: dict, staged: dict[tuple[str, str, str], dict], fallback: TargetLookup
) -> list[dict]:
    updates = []
    certainty = STATE_OPERATIONS.get(request["operation"])
    for index, target in enumerate(request["targets"]):
        identity = (target["layer"], target["kind"], target["record_id"])
        current = staged[identity] if identity in staged else fallback(target)
        if current != target["expected_state"]:
            raise IntakeError(f"/targets/{index}/expected_state: stale CanonRec or staging revision")
        if certainty is not None:
            updates.append({
                "layer": target["layer"],
                "kind": target["kind"],
                "record_id": target["record_id"],
                "state": {"revision": request["content_hash"], "certainty": certainty},
            })
    return updates


def submit(
    request: dict, *, policy: dict, principal: str, journal_path: Path,
    validate: Validator, read_artifact: Reader, resolve_target: TargetLookup,
    advisor: reconciliation.Advisory | None = None,
) -> dict:
    """Validate authority and append one durable disposition to the staging journal."""
    if policy["version"] != "1.0":
        raise IntakeError("Unsupported bridge authorization policy version")
    validate(request, read_artifact)
    _authorize_submitter(request, principal, policy)
    gates = _trusted_gates(request, policy, read_artifact)
    approval = _approval(request, policy, gates)
    status, reason = _gate_disposition(request, approval, gates)

    def evaluate(staged: dict[tuple[str, str, str], dict]) -> dict:
        updates = _target_updates(request, staged, resolve_target) if status == "ACCEPTED" else []
        receipt = {
            "version": "1.0",
            "request_id": request["request_id"],
            "content_hash": request["content_hash"],
            "canon_commit": policy["canon_commit"],
            "status": status,
            "reason": reason,
            "gate_receipts": request["gate_receipts"],
            "recommendation": gates["final_reconciliation"].get("recommendation"),
            "target_updates": updates,
        }
        if status != "REJECTED":
            advisory = reconciliation.assess_gate(request, gates["final_reconciliation"], advisor)
            if advisory is not None:
                receipt["reconciliation_advisory"] = advisory
        return receipt

    return journal.append_request(
        journal_path, policy["canon_commit"], request, evaluate,
        project_events=lambda history: events.link_outcome(request, gates, history, read_artifact),
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise IntakeError(f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def _object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(payload, dict):
        raise IntakeError(f"{path}: expected a JSON object")
    return payload


def _submission(args: argparse.Namespace) -> dict:
    canonrec = CanonRec(args.canonrec)
    repositories = {
        name: CanonRec(Path(path)) for name, path in (value.split("=", 1) for value in args.repository)
    }
    repositories[SOURCE_REPOSITORY] = canonrec
    if any(args.journal.resolve().is_relative_to(repo.path.resolve()) for repo in repositories.values()):
        raise IntakeError("The staging journal must be outside the source checkouts")
    policy = _object(args.policy)

    def advise(profile: dict, name: str) -> dict:
        return reconciliation.pinned_advisor(canonrec)(profile, name)

    with pinned_validator(canonrec) as validate:
        return submit(
            _object(args.request), policy=policy, principal=args.principal, journal_path=args.journal,
            validate=validate, read_artifact=read_artifact_from(repositories),
            resolve_target=snapshot_targets(canonrec, policy),
            advisor=advise,
        )


def main() -> int:
    """Run a staging intake, journal read, or reconstruction command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    submission = commands.add_parser("submit")
    submission.add_argument("request", type=Path)
    submission.add_argument("--canonrec", type=Path, required=True)
    submission.add_argument("--policy", type=Path, required=True)
    submission.add_argument("--principal", required=True)
    submission.add_argument("--repository", action="append", default=[], metavar="OWNER/REPO=PATH")
    status = commands.add_parser("status")
    status.add_argument("request_id")
    provenance = commands.add_parser("provenance")
    provenance.add_argument("layer", choices=("L1", "L2", "L3"))
    provenance.add_argument("kind")
    provenance.add_argument("record_id")
    provenance.add_argument("--canonrec", type=Path, required=True)
    provenance.add_argument("--policy", type=Path, required=True)
    commands.add_parser("export")
    commands.add_parser("chronicle")
    restore = commands.add_parser("rebuild")
    restore.add_argument("export", type=Path)
    restore.add_argument("--expected-tip", required=True)
    args = parser.parse_args()
    try:
        if args.action == "submit":
            payload = _submission(args)
        elif args.action == "status":
            payload = journal.read_request(args.journal, args.request_id)
            if payload is None:
                raise IntakeError("Request is absent from the staging journal")
        elif args.action == "provenance":
            payload = record_provenance(
                CanonRec(args.canonrec), _object(args.policy), args.journal,
                {"layer": args.layer, "kind": args.kind, "record_id": args.record_id},
            )
        elif args.action == "export":
            payload = journal.read_entries(args.journal)
        elif args.action == "chronicle":
            for entry in events.chronicle_atoms(journal.read_entries(args.journal)):
                print(journal.canonical_json(entry))
            return 0
        else:
            entries = json.loads(args.export.read_text(encoding="utf-8"))
            journal.rebuild(args.journal, entries, expected_tip=args.expected_tip)
            payload = {"status": "REBUILT", "entries": len(entries), "tip": args.expected_tip}
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(journal.canonical_json({"status": "REJECTED", "reason": str(exc)}))
        return 1
    print(journal.canonical_json(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
