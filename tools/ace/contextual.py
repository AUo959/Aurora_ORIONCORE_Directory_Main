"""L3-governed assignments and durable background needs for isolated ACE worlds."""
# Assignments are granted by the local operator CLI, never by model-supplied tool
# arguments. The queue reuses ACE autonomic invocations and native transactions.

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import ROOT, ACEError, semantic_sha256
from .invocation import compile_canon_invocation
from .mcp_adapter import ace_resolve
from .materialize import _validate_receipt
from .sandbox import REQUEST_ID, World, atomic_json, fail, read_json

POLICY_REL = Path("catalog/ace/policies/contextual_truth_v1.json")
POLICY_ID = "ace.policy.l3.contextual-truth.v1"
TERMINAL = {"complete", "blocked", "conflict"}


def identifier(value: str) -> str:
    if not isinstance(value, str) or not REQUEST_ID.fullmatch(value):
        fail("Expected a bounded identifier", "input_validation_failed")
    return value


def _strings(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(
            not isinstance(item, str) or not item.strip() or len(item) > 256
            for item in value
        )
    ):
        fail(
            f"{label} must be a nonempty list of bounded strings",
            "input_validation_failed",
        )
    return value


def validate_settings(layer: str, settings: dict) -> None:
    if not isinstance(settings, dict):
        fail("Settings must be an object", "input_validation_failed")
    if layer == "L2":
        if set(settings) != {"roles", "faction_id", "location_type"}:
            fail(
                "L2 settings support only roles, faction_id, and location_type",
                "input_validation_failed",
            )
        _strings(settings["roles"], "roles")
        for key in ("faction_id", "location_type"):
            identifier(settings[key])
    elif layer == "L1":
        _validate_l1_settings(settings)
    else:
        fail(
            "Assignments target L1 or L2; L3 supplies governance",
            "input_validation_failed",
        )


def world_settings(settings: dict) -> dict:
    """Role permissions are assignment scope; environment settings define the truth domain."""
    return {key: settings[key] for key in ("faction_id", "location_type")}


class ContextQueue:
    def __init__(self, directory: Path, *, policy_root: Path = ROOT):
        """Bind the durable queue to its world and controller policy."""
        self.world = World(directory)
        self.base = self.world.state / "contexts"
        self.assignments = self.base / "assignments"
        self.jobs = self.base / "jobs"
        self.revocations = self.base / "revocations"
        self.policy = read_json(policy_root / POLICY_REL)
        if self.policy.get("policy_id") != POLICY_ID:
            fail("Unrecognized contextual truth policy")
        self.policy_digest = semantic_sha256(self.policy)

    def _initialize(self) -> None:
        for directory in (self.assignments, self.jobs, self.revocations):
            directory.mkdir(parents=True, exist_ok=True)

    def _assignment(self, assignment_id: str, *, active: bool = True) -> dict:
        record = read_json(self.assignments / f"{identifier(assignment_id)}.json")
        if record["digest"] != semantic_sha256(record["spec"]):
            fail("Assignment settings changed; authorization is invalid")
        spec = record["spec"]
        if (
            spec["world_id"] != self.world.metadata["world_id"]
            or spec["policy_digest"] != self.policy_digest
        ):
            fail("Assignment world or L3 policy changed")
        validate_settings(spec["target_layer"], spec["settings"])
        if active and (self.revocations / f"{assignment_id}.json").exists():
            fail("Assignment has been revoked", "context_revoked")
        if spec["target_layer"] == "L2":
            binding = read_json(self.base / "l2_settings.json")
            if binding["settings_digest"] != semantic_sha256(
                world_settings(spec["settings"])
            ):
                fail("World settings changed; queued work cannot change truth domains")
        return record

    def authorize(
        self,
        assignment_id: str,
        purpose: str,
        target_layer: str,
        settings: dict,
        authority_ref: str,
        max_jobs: int = 20,
    ) -> dict:
        """Operator-only grant; deliberately absent from the MCP interface."""
        identifier(assignment_id)
        validate_settings(target_layer, settings)
        self._validate_grant(purpose, authority_ref, max_jobs)
        with self.world.locked():
            self.world.verify()
            self._initialize()
            spec = {
                "assignment_id": assignment_id,
                "world_id": self.world.metadata["world_id"],
                "operator_layer": "L1",
                "target_layer": target_layer,
                "purpose": purpose,
                "settings": settings,
                "policy_id": POLICY_ID,
                "policy_digest": self.policy_digest,
                "authority_ref": authority_ref,
                "max_jobs": max_jobs,
                "runtime_activation_authority": False,
            }
            path = self.assignments / f"{assignment_id}.json"
            record = {"spec": spec, "digest": semantic_sha256(spec)}
            if path.exists():
                if read_json(path) != record:
                    fail(
                        "Assignment ID already has different settings",
                        "transaction_conflict",
                    )
                self._assignment(assignment_id)
                return record
            self._bind_l2_settings(spec, settings)
            atomic_json(path, record)
            return record

    def revoke(self, assignment_id: str, reason: str) -> dict:
        with self.world.locked():
            record = self._assignment(assignment_id, active=False)
            receipt = {
                "assignment_digest": record["digest"],
                "reason": reason,
                "revoked": True,
            }
            atomic_json(self.revocations / f"{assignment_id}.json", receipt)
            return receipt

    @staticmethod
    def _effective(spec: dict, context: dict) -> dict:
        if not isinstance(context, dict):
            fail("Need context must be an object", "input_validation_failed")
        settings = spec["settings"]
        if spec["target_layer"] == "L1":
            if (
                set(context) != {"field_path"}
                or context["field_path"] not in settings["field_paths"]
            ):
                fail(
                    "L1 needs must select an authorized evidence field; generation is not evidence",
                    "input_validation_failed",
                )
            return dict(context)
        return ContextQueue._l2_context(settings, context)

    @staticmethod
    def _role_context(settings: dict, effective: dict) -> dict:
        if "role" not in effective:
            if len(settings["roles"]) == 1:
                effective["role"] = settings["roles"][0]
            elif not (effective.get("name") or effective.get("canonical_id")):
                fail(
                    "Specify which authorized role is needed", "input_validation_failed"
                )
        if "role" in effective and effective["role"] not in settings["roles"]:
            fail("Role is outside the assignment scope", "input_validation_failed")
        if "observed_behavior" in effective:
            _strings(effective["observed_behavior"], "observed_behavior")
        return effective

    def submit(
        self, assignment_id: str, need_id: str, question: str, context: dict
    ) -> dict:
        identifier(need_id)
        self.world._validate_request(question, context, need_id, "create")
        with self.world.locked():
            record = self._assignment(assignment_id)
            effective = self._effective(record["spec"], context)
            job_id = (
                "need-"
                + semantic_sha256({"assignment": assignment_id, "need": need_id})[:24]
            )
            payload = {
                "assignment_id": assignment_id,
                "assignment_digest": record["digest"],
                "need_id": need_id,
                "question": question,
                "context": effective,
            }
            digest = semantic_sha256(payload)
            path = self.jobs / f"{job_id}.json"
            if path.exists():
                job = read_json(path)
                if job["input_digest"] != digest:
                    fail(
                        "Need ID already belongs to different input",
                        "transaction_conflict",
                    )
                return job
            used = sum(
                read_json(p)["input"]["assignment_id"] == assignment_id
                for p in self.jobs.glob("*.json")
            )
            if used >= record["spec"]["max_jobs"]:
                fail("Assignment job budget exhausted", "context_budget_exhausted")
            job = {
                "job_id": job_id,
                "input": payload,
                "input_digest": digest,
                "status": "queued",
                "needs_attention": False,
            }
            atomic_json(path, job)
            return job

    def inspect(self, job_id: str) -> dict:
        with self.world.locked():
            return read_json(self.jobs / f"{identifier(job_id)}.json")

    def status(self) -> dict:
        with self.world.locked():
            return {
                "world": self.world.verify(),
                "policy_id": POLICY_ID,
                "assignments": [
                    {**read_json(p), "revoked": (self.revocations / p.name).exists()}
                    for p in sorted(self.assignments.glob("*.json"))
                ],
                "jobs": [
                    {
                        k: read_json(p)[k]
                        for k in ("job_id", "status", "needs_attention")
                    }
                    for p in sorted(self.jobs.glob("*.json"))
                ],
            }

    def _execute(self, job: dict, record: dict) -> dict:
        spec = record["spec"]
        payload = job["input"]
        job_id = job["job_id"]
        options = {
            "invocation_mode": "autonomic",
            "caller_kind": "system",
            "caller_ref": f"context:{spec['assignment_id']}",
            "trigger_kind": "coherence_seam",
            "trigger_reason": payload["question"],
            "seam_ref": f"context-need:{job_id}",
            "trigger_policy_ref": POLICY_ID,
        }
        authority_ref = f"{POLICY_ID}:{spec['world_id']}:{record['digest']}:{job_id}"
        job["l3_receipt"] = self._l3_receipt(spec, record, authority_ref)
        # Save the decision before any native transaction. A crashed worker reuses this job ID.
        atomic_json(self.jobs / f"{job_id}.json", job)
        if spec["target_layer"] == "L2":
            effective = payload["context"]
            operation = "create" if effective.get("role") else "retrieve"
            fingerprint = semantic_sha256(
                {"context_job": payload, "authority_ref": authority_ref}
            )
            return self.world._character_locked(
                payload["question"],
                effective,
                job_id,
                operation,
                fingerprint,
                context_authority={
                    "authority_ref": authority_ref,
                    "invocation_options": options,
                    "l3_receipt": job["l3_receipt"],
                },
            )
        return self._execute_l1(job, spec, options)

    def work_once(self) -> dict | None:
        with self.world.locked():
            candidates = [read_json(p) for p in sorted(self.jobs.glob("*.json"))]
            job = next((j for j in candidates if j["status"] not in TERMINAL), None)
            if job is None:
                return None
            path = self.jobs / f"{identifier(job['job_id'])}.json"
            try:
                record = self._validate_job(job)
                self.world._recover()
                self.world.verify()
                job["status"] = "running"
                atomic_json(path, job)
                result = self._execute(job, record)
                status = result["status"]
                job.update(
                    result=result,
                    status="conflict"
                    if status == "TRUE_CONFLICT"
                    else "blocked"
                    if status == "EXECUTION_BLOCKED"
                    else "complete",
                )
                job["needs_attention"] = job["status"] != "complete"
            except (ACEError, ValueError, KeyError, OSError) as exc:
                job.update(status="blocked", needs_attention=True, error=str(exc))
            atomic_json(path, job)
            return job

    def _bind_l2_settings(self, spec: dict, settings: dict) -> None:
        if spec["target_layer"] == "L2":
            binding_path = self.base / "l2_settings.json"
            binding = {
                "world_id": spec["world_id"],
                "settings_digest": semantic_sha256(world_settings(settings)),
                "settings": world_settings(settings),
            }
            if binding_path.exists() and read_json(binding_path) != binding:
                fail(
                    "Different L2 settings require a separate world; existing facts keep their original context"
                )
            atomic_json(binding_path, binding)

    @staticmethod
    def _l2_context(settings: dict, context: dict) -> dict:
        allowed = {
            "role",
            "name",
            "canonical_id",
            "observed_behavior",
            "faction_id",
            "location_type",
        }
        if set(context) - allowed:
            fail(
                "Need attempts an unsupported setting or authority override",
                "input_validation_failed",
            )
        for key in ("faction_id", "location_type"):
            if key in context and context[key] != settings[key]:
                fail(
                    f"Need {key} disagrees with authorized settings",
                    "input_validation_failed",
                )
        effective = {
            **context,
            "faction_id": settings["faction_id"],
            "location_type": settings["location_type"],
        }
        return ContextQueue._role_context(settings, effective)

    def _execute_l1(self, job: dict, spec: dict, options: dict) -> dict:
        payload = job["input"]
        job_id = job["job_id"]
        settings = spec["settings"]
        invocation = compile_canon_invocation(
            payload["question"],
            {"evidence_refs": settings["evidence_refs"], "layers": ["L1"]},
            subject_ref=settings["subject_ref"],
            field_path=payload["context"]["field_path"],
            root=self.world.root,
            session_ref=job_id,
            **options,
        )
        output_name = "context-" + job_id
        packet = self.world.runtime / output_name
        sidecar = self.world.runtime / f"{output_name}.ace-invocation.json"
        if sidecar.exists():
            recorded = read_json(sidecar)
            determination = _validate_receipt(
                packet / "determination_receipt.json", root=self.world.root
            )
            if (
                recorded["invocation_id"] != job.get("l1_invocation_id")
                or recorded["determination_ref"] != determination["determination_id"]
            ):
                fail("Recorded L1 invocation does not match this need")
            invocation = recorded
        else:
            job["l1_invocation_id"] = invocation["invocation_id"]
            atomic_json(self.jobs / f"{job_id}.json", job)
            result = ace_resolve(invocation, output_name, root=self.world.root)
            determination = result["determination"]
        return {
            "world_id": spec["world_id"],
            "status": determination["status"],
            "invocation_id": invocation["invocation_id"],
            "determination_id": determination["determination_id"],
            "answer": determination["answer"],
            "notice": "Committed L1 evidence in this world; not independent verification of external reality.",
        }

    def _l3_receipt(self, spec: dict, record: dict, authority_ref: str) -> dict:
        return {
            "policy_id": POLICY_ID,
            "policy_digest": self.policy_digest,
            "assignment_id": spec["assignment_id"],
            "assignment_digest": record["digest"],
            "world_id": spec["world_id"],
            "target_layer": spec["target_layer"],
            "settings_digest": semantic_sha256(spec["settings"]),
            "authority_ref": authority_ref,
            "cross_layer_authority": False,
            "reality_verified": False,
            "truth_basis": "world_scoped_generative_canon"
            if spec["target_layer"] == "L2"
            else "committed_L1_evidence",
        }

    def _validate_job(self, job: dict) -> dict:
        if job["input_digest"] != semantic_sha256(job["input"]):
            fail("Queued need input changed")
        record = self._assignment(job["input"]["assignment_id"])
        if job["input"]["assignment_digest"] != record["digest"]:
            fail("Queued assignment authorization changed")
        self._effective(record["spec"], job["input"]["context"])
        return record

    def _validate_grant(self, purpose: str, authority_ref: str, max_jobs: int) -> None:
        if not all(
            isinstance(v, str) and v.strip() and len(v) < 4096
            for v in (purpose, authority_ref)
        ):
            fail(
                "A bounded purpose and explicit operator authority reference are required"
            )
        if (
            not isinstance(max_jobs, int)
            or isinstance(max_jobs, bool)
            or not 1 <= max_jobs <= self.policy["max_jobs_per_assignment"]
        ):
            fail("Assignment job budget is out of bounds")


def _validate_l1_settings(settings: dict) -> None:
    if set(settings) != {"subject_ref", "evidence_refs", "field_paths"}:
        fail(
            "L1 settings require subject_ref, evidence_refs, and field_paths",
            "input_validation_failed",
        )
    if (
        not isinstance(settings["subject_ref"], str)
        or not settings["subject_ref"].strip()
    ):
        fail("L1 subject_ref is required", "input_validation_failed")
    _strings(settings["field_paths"], "field_paths")
    for ref in _strings(settings["evidence_refs"], "evidence_refs"):
        path = Path(ref)
        if (
            path.parts[:2] != ("canon", "L1")
            or ".." in path.parts
            or path.suffix != ".json"
        ):
            fail(
                "L1 evidence must be explicit canon/L1 JSON records; L2 evidence cannot become L1 truth",
                "input_validation_failed",
            )
