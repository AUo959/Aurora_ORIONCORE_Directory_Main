"""Persistent, local-only ACE character world; never an authority over its source."""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

import yaml

from .core import ACEError, CANONREC_REL, CLOUDBANK_REL, semantic_sha256

WORLD_FILE = "world.json"
BRANCH = "sandbox/character-continuity"
POLICY = "sandbox-explicit-character-create-v1"
REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z")
REGISTRY = "catalog/repo_registry.yaml"


def fail(message: str, code: str = "sandbox_integrity_failed") -> None:
    raise ACEError(message, code=code)


def git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_LFS_SKIP_SMUDGE"] = "1"
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        check=False, timeout=120, env=env,
    )
    if result.returncode:
        fail(f"Git operation failed: {result.stderr.strip()}")
    return result.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        fail("Sandbox metadata cannot be a symlink")
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        fail(f"Cannot read sandbox metadata: {exc}")
    if not isinstance(data, dict):
        fail("Sandbox metadata must be an object")
    return data


def atomic_json(path: Path, data: Mapping[str, Any]) -> None:
    atomic_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def atomic_text(path: Path, data: str) -> None:
    if path.is_symlink():
        fail("Refusing symlink output")
    fd, temporary = tempfile.mkstemp(prefix=".ace-write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class World:
    def __init__(self, directory: Path):
        directory = directory.expanduser().absolute()
        if directory.resolve() != directory:
            fail("World path must be an absolute real path without symlinks")
        self.directory = directory
        self.root = directory / "workspace"
        self.canon = self.root / CANONREC_REL
        self.cloudbank = self.root / CLOUDBANK_REL
        self.state = directory / "state"
        self.requests = self.state / "requests"
        self.runtime = self.root / "reports/ace/mcp_runtime"
        self.metadata = read_json(directory / WORLD_FILE)
        if (self.metadata.get("record_type") != "aurora_ace_sandbox_world"
                or self.metadata.get("schema_version") != 1
                or self.metadata.get("directory") != str(directory)
                or self.metadata.get("policy") != POLICY):
            fail("Not a provisioned ACE sandbox world")
        for source in self.metadata["sources"].values():
            source_path = Path(source["path"]).resolve()
            if directory == source_path or source_path in directory.parents:
                fail("Sandbox cannot live inside a source repository")
        for path in (self.root, self.state, self.requests, self.runtime):
            self._inside(path)

    def _inside(self, path: Path) -> None:
        if path.resolve() != path or self.directory not in path.parents:
            fail("Sandbox path escaped its isolated world")
        # Relevant trees must contain no links that a native resolver could follow.
        if path.exists():
            for base, dirs, files in os.walk(path, followlinks=False):
                dirs[:] = [d for d in dirs if d not in {".git", ".venv", "__pycache__"}]
                for name in dirs + files:
                    if (Path(base) / name).is_symlink():
                        fail(f"Sandbox tree contains a symlink: {Path(base) / name}")

    @contextmanager
    def locked(self) -> Iterator[None]:
        path = self.state / "world.lock"
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            self.metadata = read_json(self.directory / WORLD_FILE)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def _registry(self, head: str) -> dict[str, Any]:
        registry = json.loads(json.dumps(self.metadata["source_registry"]))
        for row in registry["repos"]:
            if row["name"] == "CanonRec":
                row.update(head_sha=head, branch=BRANCH)
        return registry

    def verify(self, *, pending: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read-only inspection; pending permits only a journaled native commit."""
        for name, repo in (("root", self.root), ("CanonRec", self.canon),
                           ("aurora-cloudbank-symbolic-main", self.cloudbank)):
            self._inside(repo)
            dotgit = repo / ".git"
            if not dotgit.is_dir() or dotgit.is_symlink():
                fail("Sandbox requires independent Git clones")
            common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
            if common != dotgit.resolve() or (dotgit / "objects/info/alternates").exists():
                fail("Sandbox Git storage must not be shared")
            if git(repo, "remote"):
                fail("Sandbox repository has a remote")
            expected = self.metadata["canon_head"] if name == "CanonRec" else self.metadata["sources"][name]["commit"]
            observed = git(repo, "rev-parse", "HEAD")
            if observed != expected:
                if not (name == "CanonRec" and pending and self._committed_receipt(pending, observed)):
                    fail(f"Unexpected repository HEAD: {name}", "sandbox_baseline_changed")
            changes = git(repo, "diff", "HEAD", "--name-only").splitlines()
            unknown = git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
            if name == "root":
                if set(changes) - {REGISTRY} or any(not p.startswith("reports/ace/") for p in unknown):
                    fail("Unexpected sandbox control-plane changes")
            elif changes or unknown:
                fail(f"Unexpected sandbox repository changes: {name}")
        if git(self.canon, "branch", "--show-current") != BRANCH:
            fail("Sandbox canon branch changed")
        registry = yaml.safe_load((self.root / REGISTRY).read_text())
        allowed = [self._registry(self.metadata["canon_head"])]
        if pending:
            allowed.append(self._registry(git(self.canon, "rev-parse", "HEAD")))
        if registry not in allowed:
            fail("Unexpected sandbox registry change")
        return {"world_id": self.metadata["world_id"], "status": "ready",
                "world_scope": "isolated_aurora_world", "canonical_workspace_authority": False,
                "canon_head": git(self.canon, "rev-parse", "HEAD"),
                "sources": self.metadata["sources"], "permitted_operations": ["retrieve", "preview", "create"]}

    def _committed_receipt(self, record: dict[str, Any], head: str) -> dict[str, Any] | None:
        path = self.runtime / record["output_name"] / "materialized_determination_receipt.json"
        if not path.is_file():
            return None
        receipt = read_json(path)
        if receipt.get("materialization", {}).get("commit_sha") != head:
            return None
        if git(self.canon, "rev-parse", head + "^") != record["baseline"]:
            fail("Journaled commit is not a single native transaction")
        expected_message = f"feat(sandbox): {self.metadata['world_id']} {record['request_id']}"
        if git(self.canon, "log", "-1", "--format=%s") != expected_message:
            fail("Journaled commit identity mismatch")
        return receipt

    def _finish(self, record: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
        head = receipt["materialization"]["commit_sha"]
        atomic_text(self.root / REGISTRY, yaml.safe_dump(self._registry(head), sort_keys=False))
        # Existing manifest policy permits data changes only if specialist sources remain unchanged.
        from .capability_discovery import build_capability_index
        build_capability_index(self.root)
        self.metadata["canon_head"] = head
        atomic_json(self.directory / WORLD_FILE, self.metadata)
        record["result"] = self._result(receipt, record)
        record["phase"] = "complete"
        atomic_json(self.requests / (record["request_id"] + ".json"), record)
        return record["result"]

    def _recover(self) -> None:
        pending = [read_json(p) for p in sorted(self.requests.glob("*.json"))
                   if read_json(p).get("phase") == "committing"]
        if len(pending) > 1:
            fail("Multiple pending sandbox commits require inspection")
        for record in pending:
            self.verify(pending=record)
            head = git(self.canon, "rev-parse", "HEAD")
            receipt = self._committed_receipt(record, head)
            if receipt:
                self._finish(record, receipt)
            elif head != record["baseline"]:
                fail("Unreceipted commit requires inspection; refusing automatic replay")
            else:
                record["phase"] = "resolved"
                atomic_json(self.requests / (record["request_id"] + ".json"), record)

    def status(self) -> dict[str, Any]:
        with self.locked():
            result = self.verify()
            result["pending_requests"] = [p.stem for p in self.requests.glob("*.json")
                                          if read_json(p).get("phase") != "complete"]
            return result

    def _result(self, receipt: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
        created = receipt.get("status") == "GENERATED_CANON"
        entity_id = next(iter(receipt.get("subject_refs", [])), None)
        creation = receipt if created else None
        for path in self.requests.glob("*.json"):
            previous = read_json(path).get("result", {})
            if previous.get("entity_id") == entity_id and previous.get("status") == "GENERATED_CANON":
                creation = previous
                break
        return {"world_id": self.metadata["world_id"], "world_scope": "isolated_aurora_world",
                "notice": "Canon in this sandbox only; the source Aurora world is unchanged.",
                "request_id": record["request_id"], "operation": record["operation"],
                "status": receipt["status"], "invocation_id": record.get("invocation_id"),
                "determination_id": receipt["determination_id"],
                "entity_id": entity_id,
                "subject_refs": receipt.get("subject_refs", []),
                "answer": receipt.get("answer"), "blockers": receipt.get("blockers", []),
                "materialization": receipt.get("materialization"),
                "origin": "sandbox_created" if creation else (
                    "inherited_canon" if receipt["status"] == "RETRIEVED_CANON" else "prepared_or_unresolved"),
                "creation_determination_id": creation.get("determination_id") if creation else None,
                "packet_ref": str(self.runtime / record["output_name"])}

    def character(self, question: str, context: dict[str, Any], request_id: str,
                  operation: str = "retrieve") -> dict[str, Any]:
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            fail("Invalid request ID", "input_validation_failed")
        if operation not in {"retrieve", "preview", "create"}:
            fail("Unsupported character operation", "input_validation_failed")
        if not isinstance(question, str) or not question.strip() or not isinstance(context, dict):
            fail("A question and character context object are required", "input_validation_failed")
        fingerprint = semantic_sha256({"question": question, "context": context, "operation": operation})
        with self.locked():
            self._recover()
            self.verify()
            path = self.requests / (request_id + ".json")
            if path.exists():
                record = read_json(path)
                if record["fingerprint"] != fingerprint:
                    fail("Request ID already belongs to different input", "transaction_conflict")
                if record["phase"] == "complete":
                    return record["result"]
                if record["baseline"] != self.metadata["canon_head"]:
                    fail("Pending request baseline changed; use a new request ID", "sandbox_baseline_changed")
            else:
                record = {"request_id": request_id, "fingerprint": fingerprint, "operation": operation,
                          "phase": "prepared", "output_name": "sandbox-" + request_id,
                          "baseline": self.metadata["canon_head"]}
                atomic_json(path, record)
            from .invocation import compile_character_invocation
            from .mcp_adapter import ace_resolve, ace_materialize_preview, ace_materialize_commit
            effective = dict(context)
            if "canonical_id" in effective:
                if effective.get("subject_ref", effective["canonical_id"]) != effective["canonical_id"]:
                    fail("Character identity anchors disagree", "input_validation_failed")
                effective["subject_ref"] = effective.pop("canonical_id")
            if operation == "retrieve":
                effective["existence_status"] = "existing"
            if "receipt" not in record:
                invocation = compile_character_invocation(
                    question, effective, root=self.root, session_ref=request_id,
                    caller_ref=f"sandbox:{self.metadata['world_id']}",
                )
                record["invocation_id"] = invocation["invocation_id"]
                resolution = ace_resolve(invocation, record["output_name"], root=self.root)
                record.update(receipt=resolution["determination"], phase="resolved")
                atomic_json(path, record)
            receipt = record["receipt"]
            if operation == "create" and receipt.get("materialization", {}).get("status") == "commit_ready":
                authority = f"{POLICY}:{self.metadata['world_id']}:{request_id}"
                preview = ace_materialize_preview(record["output_name"], authority, root=self.root)
                record["phase"] = "committing"
                atomic_json(path, record)
                committed = ace_materialize_commit(
                    record["output_name"], authority, preview["authorization_token"], True,
                    f"feat(sandbox): {self.metadata['world_id']} {request_id}", root=self.root,
                )
                return self._finish(record, committed["materialized_determination"])
            record.update(phase="complete", result=self._result(receipt, record))
            atomic_json(path, record)
            return record["result"]

    def inspect(self, invocation_id: str | None = None,
                determination_id: str | None = None) -> dict[str, Any]:
        from .mcp_adapter import ace_inspect
        with self.locked():
            self._recover()
            self.verify()
            return {"world_id": self.metadata["world_id"], "world_scope": "isolated_aurora_world",
                    **ace_inspect(invocation_id=invocation_id, determination_id=determination_id, root=self.root)}
