"""Prepare an offline character promotion review using existing ACE owners."""
# Only a new output directory and its independent rehearsal clone are writable. This
# module neither publishes a branch nor grants source-world canon authority.

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path

from .character_materialize import (
    CAPSULE_FILES,
    OUTER_BUNDLE_FILES,
    _packet_sources,
    materialize_character_packet,
)
from .character_retrieval import discover_character_candidates
from .core import (
    ACEError,
    CANONREC_REL,
    ROOT,
    file_sha256,
    load_module,
    semantic_sha256,
)
from .materialize import _canonrec_baseline, _validate_receipt
from .sandbox import REQUEST_ID, World, atomic_json, atomic_text, fail, git, read_json


def _separate_output(output: Path, protected: list[Path]) -> Path:
    output = output.expanduser().absolute()
    if output.resolve() != output or output.exists():
        fail("Review output must be a new directory without symlinks")
    for path in protected:
        path = path.resolve()
        if output == path or path in output.parents or output in path.parents:
            fail("Review output must be separate from source workspaces")
    return output


def _snapshot(repo: Path) -> dict:
    return {
        "head": git(repo, "rev-parse", "HEAD"),
        "status": git(repo, "status", "--porcelain"),
        "diff": semantic_sha256(git(repo, "diff", "HEAD", "--binary")),
    }


def _clone(source: Path, destination: Path, head: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    git(
        source,
        "clone",
        "--no-hardlinks",
        "--no-checkout",
        str(source),
        str(destination),
    )
    git(destination, "checkout", "-B", "review/character-promotion", head)
    for remote in git(destination, "remote").splitlines():
        git(destination, "remote", "remove", remote)
    hooks = destination / ".git/review-empty-hooks"
    hooks.mkdir()
    git(destination, "config", "core.hooksPath", str(hooks))
    git(destination, "config", "commit.gpgsign", "false")
    if any(p.is_symlink() for p in destination.rglob("*") if ".git" not in p.parts):
        fail("Rehearsal source contains symlinks")


def _run(script: Path, args: list[str], cwd: Path, output: Path) -> tuple[dict, int]:
    env = dict(os.environ, PYTHONPYCACHEPREFIX=str(output / "python-cache"))
    result = subprocess.run(  # noqa: S603 -- pinned local validator, fixed argv, no shell. # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit # nosec B603, B607
        [sys.executable, str(script), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )  # nosec B603, B607
    try:
        return json.loads(result.stdout), result.returncode
    except ValueError as exc:
        raise ACEError(
            f"Validator {script.name} failed: {result.stderr}",
            code="output_validation_failed",
        ) from exc


def _source(world: World, request_id: str, root: Path) -> tuple[Path, dict, dict]:
    if not REQUEST_ID.fullmatch(request_id):
        fail("Invalid creation request ID")
    record = read_json(world.requests / f"{request_id}.json")
    result = record.get("result", {})
    if (
        record.get("phase") != "complete"
        or record.get("operation") != "create"
        or result.get("origin") != "sandbox_created"
    ):
        fail("Promotion requires a completed sandbox creation")
    name = record.get("output_name", "")
    if not REQUEST_ID.fullmatch(name):
        fail("Unsafe packet reference")
    packet = world.runtime / name
    world._inside(packet)
    original = _validate_receipt(packet / "determination_receipt.json", root=root)
    final = _validate_receipt(
        packet / "materialized_determination_receipt.json", root=root
    )
    commit = final["materialization"]["commit_sha"]
    if result.get("creation_determination_id") != final["determination_id"] or final[
        "integrity"
    ]["prior_determination_digest"] != semantic_sha256(original):
        fail("Creation history does not match the original packet")
    _assert_packet_integrity(packet, result["entity_id"], original)
    _verify_committed_artifacts(world, final, commit)
    return packet, original, final


def _assert_packet_integrity(packet: Path, entity: str, original: dict) -> None:
    if not isinstance(entity, str) or not re.fullmatch(r"char_[A-Za-z0-9_-]+", entity):
        fail("Unsafe character identity")
    candidate, bundle, query, naming = _packet_sources(packet, entity)
    required = [
        candidate,
        query,
        naming,
        *(bundle / name for name in OUTER_BUNDLE_FILES),
        *(bundle / "capsule" / name for name in CAPSULE_FILES),
    ]
    for artifact in required:
        if file_sha256(artifact) not in original["integrity"]["artifact_sha256s"]:
            fail(f"Source packet artifact changed: {artifact.relative_to(packet)}")


def _validate_candidate(packet: Path, view: Path, output: Path, entity: str) -> dict:
    repo = view / CANONREC_REL
    scripts = repo / "aurora-canon-reconciler/scripts"
    candidate_path = packet / "candidate" / f"{entity}.json"
    candidate = read_json(candidate_path)
    discovery = discover_character_candidates(
        {
            "subject_ref": entity,
            "canonical_name": candidate["canonical_name"],
            "aliases": candidate.get("aliases", []),
        },
        root=view,
    )
    registry, rc = _run(
        scripts / "export_name_registry.py", ["--repo-root", str(repo)], repo, output
    )
    if rc:
        fail("CanonRec name registry export failed")
    atomic_json(output / "name_registry.json", registry)
    validation, entity_rc, naming, naming_rc = _candidate_validators(
        scripts, candidate_path, repo, output
    )
    atomic_json(output / "validation_run.json", validation)
    atomic_json(output / "naming_validation.json", naming)
    _candidate_advice(scripts, output, candidate, validation, discovery, entity)
    return {
        "identity_discovery": discovery,
        "entity_passed": entity_rc == 0 and not validation["validation_run"]["blocked"],
        "naming_passed": naming_rc == 0 and not naming["blocks"],
        "advisor_ref": "reconciliation_advice.json",
        "evidence_ref": "evidence_receipt.json",
    }


def prepare(
    world_directory: Path,
    request_id: str,
    target_root: Path,
    output: Path,
    *,
    root: Path = ROOT,
) -> dict:
    """Revalidate and rehearse one original creation; preserve source baselines."""
    world = World(world_directory)
    target_root = target_root.resolve()
    target = target_root / CANONREC_REL
    output = _review_output(output, world, target_root, root)
    with world.locked():
        world.verify()
        source_before = _snapshot(world.canon)
        target_before = _snapshot(target)
        if target_before["status"]:
            fail(
                "Target CanonRec must be clean; uncommitted content cannot be promoted against"
            )
        packet, original, final = _source(world, request_id, root)
        output.mkdir(parents=True)
        review = _review_metadata(
            world, request_id, final, target_root, target_before, original, root
        )
        try:
            _rehearse(
                world,
                target,
                packet,
                output,
                final,
                original,
                review,
                root,
            )
        except (ACEError, OSError, ValueError, KeyError) as exc:
            review["status"] = "blocked"
            review["blockers"].append(str(exc))
        finally:
            _verify_review_sources(review, world, target, source_before, target_before)
            _write_review(output, review)
        return review


def verify(output: Path) -> dict:
    output = output.expanduser().absolute()
    if output.resolve() != output:
        fail("Review path must not contain symlinks")
    review = read_json(output / "promotion_review.json")
    _verify_review_artifacts(output, review)
    target = Path(review["target_root"]) / CANONREC_REL
    if git(target, "rev-parse", "HEAD") != review["target_baseline"] or git(
        target, "status", "--porcelain"
    ):
        fail("Target CanonRec changed; prepare a fresh review")
    return {
        "status": review["status"],
        "artifacts_verified": True,
        "target_baseline_current": True,
        "authority": "offline_review_only",
    }


def _verify_committed_artifacts(world: World, final: dict, commit: str) -> None:
    # Read the native committed evidence, never use working-tree candidates as canon.
    git(world.canon, "merge-base", "--is-ancestor", commit, "HEAD")
    paths = final["materialization"]["target_paths"]
    hashes = {}
    for rel in paths:
        path = world.canon / rel
        world._inside(path)
        if not path.is_file():
            fail("Committed creation artifact is missing")
        hashes[rel] = file_sha256(path)
    transactions = [t for t in final["transactions"] if t["kind"] == "materialization"]
    if not transactions or transactions[-1]["result_sha256"] != semantic_sha256(hashes):
        fail("Creation artifacts no longer match the native transaction receipt")


def _candidate_advice(
    scripts: Path,
    output: Path,
    candidate: dict,
    validation: dict,
    discovery: dict,
    entity: str,
) -> None:
    advisor = load_module(
        scripts / "reconciliation_advisor.py", "ace_promotion_advisor"
    )
    reports = validation.get("reports", [])
    advice = advisor.recommend_from_validation(
        candidate,
        [finding for report in reports for finding in report.get("findings", [])],
        "L2",
        "character",
        entity_name=candidate["canonical_name"],
        has_conflicts=bool(discovery["direct_candidates"]),
        user_reviewed=False,
    )
    atomic_json(output / "reconciliation_advice.json", advice)
    emitter = load_module(
        scripts / "emit_evidence_receipt.py", "ace_promotion_evidence"
    )
    atomic_json(
        output / "evidence_receipt.json",
        emitter.build_evidence_receipt(
            validation,
            output / "validation_run.json",
            canon_targets=[f"CanonRec:canon/L2/entities/{entity}"],
        ),
    )


def _candidate_validators(
    scripts: Path, candidate_path: Path, repo: Path, output: Path
) -> tuple:
    validation, entity_rc = _run(
        scripts / "validate_entity.py",
        [
            "--input",
            str(candidate_path),
            "--layer",
            "L2",
            "--type",
            "character",
            "--format",
            "json",
            "--context-root",
            str(repo),
        ],
        repo,
        output,
    )
    naming, naming_rc = _run(
        scripts / "validate_naming_receipts.py",
        [
            str(candidate_path),
            "--registry",
            str(output / "name_registry.json"),
            "--require-receipt",
            "--json",
        ],
        repo,
        output,
    )
    return validation, entity_rc, naming, naming_rc


def _review_metadata(
    world: World,
    request_id: str,
    final: dict,
    target_root: Path,
    target_before: dict,
    original: dict,
    root: Path,
) -> dict:
    return {
        "schema_version": 1,
        "record_type": "ace_character_promotion_review",
        "status": "preparing",
        "world_id": world.metadata["world_id"],
        "request_id": request_id,
        "source_determination_id": final["determination_id"],
        "source_commit": final["materialization"]["commit_sha"],
        "target_root": str(target_root),
        "target_baseline": target_before["head"],
        "packet_baseline": _canonrec_baseline(original),
        "authority": "offline_review_only",
        "canonical_workspace_mutated": False,
        "publication_performed": False,
        "blockers": [],
        "implementation_sha256s": {
            str(rel): file_sha256(root / rel)
            for rel in (
                Path("tools/ace/promotion.py"),
                Path("tools/ace/character_materialize.py"),
                Path("tools/ace/character_retrieval.py"),
            )
        },
    }


def _rehearse(
    world: World,
    target: Path,
    packet: Path,
    output: Path,
    final: dict,
    original: dict,
    review: dict,
    root: Path,
) -> None:
    view = output / "rehearsal"
    repo = view / CANONREC_REL
    _clone(target, repo, review["target_baseline"])
    copied = output / "packet"
    shutil.copytree(packet, copied)
    (copied / "materialized_determination_receipt.json").unlink()
    atomic_json(output / "source_materialized_determination.json", final)
    entity = original["materialization"]["target_paths"][0].split("/")[-1]
    if not re.fullmatch(r"char_[A-Za-z0-9_-]+", entity):
        fail("Unsafe character identity")
    review["entity_id"] = entity
    checks = _validate_candidate(copied, view, output, entity)
    review["checks"] = checks
    _review_blockers(review, checks)
    if not review["blockers"]:
        _materialize_rehearsal(
            copied, repo, world, review["request_id"], root, output, entity, review
        )
    else:
        review["status"] = "blocked"


def _write_review(output: Path, review: dict) -> None:
    # Pin review artifacts for later inspection without trusting a stale ready flag.
    review["artifact_sha256s"] = {
        p.relative_to(output).as_posix(): file_sha256(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
        and "rehearsal" not in p.relative_to(output).parts
        and "python-cache" not in p.relative_to(output).parts
        and "__pycache__" not in p.parts
    }
    atomic_text(
        output / "REVIEW.md",
        "# Character promotion review\n\n"
        f"Status: **{review['status']}**. Scope: offline review only.\n\n"
        f"Source world: `{review['world_id']}`. Creation: `{review['source_commit']}`.\n\n"
        f"Target CanonRec baseline: `{review['target_baseline']}` (local committed state).\n\n"
        "Read `promotion_review.json`, `validation_run.json`, `naming_validation.json`, "
        "`reconciliation_advice.json`, and `evidence_receipt.json` for findings. "
        "When present, `proposal.patch` is the exact native-materializer rehearsal diff.\n\n"
        "The existing ACE delegated-publication path remains the publication owner. "
        "A review receipt is not publication authority; target freshness and the "
        "publisher's authenticated authority checks must pass at publication time.\n\n"
        + "\n".join(f"- {b}" for b in review["blockers"])
        + "\n",
    )
    atomic_json(output / "promotion_review.json", review)


def _review_blockers(review: dict, checks: dict) -> None:
    if checks["identity_discovery"]["direct_candidates"]:
        review["blockers"].append(
            "Existing target identity/name requires ACE retrieval and reconciliation"
        )
    if not checks["entity_passed"] or not checks["naming_passed"]:
        review["blockers"].append("CanonRec validation refused the candidate")
    if review["packet_baseline"] != review["target_baseline"]:
        review["blockers"].append(
            "Target baseline differs from creation packet; ACE revalidation must issue a new determination"
        )


def _materialize_rehearsal(
    copied: Path,
    repo: Path,
    world: World,
    request_id: str,
    root: Path,
    output: Path,
    entity: str,
    review: dict,
) -> None:
    rehearsal = materialize_character_packet(
        copied,
        repo,
        authority_mode="delegated_materialize",
        authority_ref=f"offline-review:{world.metadata['world_id']}:{request_id}",
        root=root,
        ledger_dir=output / "ledger",
        commit_message=f"review(character): rehearse {entity}",
    )
    review["rehearsal_commit"] = rehearsal["materialization"]["commit_sha"]
    review["rehearsal_determination_id"] = rehearsal["determination_id"]
    git(
        repo,
        "diff",
        "--binary",
        f"--output={output / 'proposal.patch'}",
        review["target_baseline"],
        "HEAD",
    )
    review["patch_ref"] = "proposal.patch"
    review["status"] = "review_ready"


def _verify_review_artifacts(output: Path, review: dict) -> None:
    for rel, expected in review["artifact_sha256s"].items():
        path = output / rel
        if (
            path.resolve() != path
            or not path.is_relative_to(output)
            or ".." in Path(rel).parts
        ):
            fail("Unsafe review artifact path")
        if not path.is_file() or file_sha256(path) != expected:
            fail(f"Review artifact changed: {rel}")


def _verify_review_sources(
    review: dict, world: World, target: Path, source_before: dict, target_before: dict
) -> None:
    review["sources_unchanged"] = source_before == _snapshot(
        world.canon
    ) and target_before == _snapshot(target)
    if not review["sources_unchanged"]:
        review["status"] = "blocked"
        review["blockers"].append(
            "Source or target changed during review; discard this proposal"
        )


def _review_output(output: Path, world: World, target_root: Path, root: Path) -> Path:
    return _separate_output(
        output,
        [
            world.directory,
            target_root,
            root,
            Path.home() / "dev/Aurora_ORIONCORE_Directory_Main",
        ],
    )
