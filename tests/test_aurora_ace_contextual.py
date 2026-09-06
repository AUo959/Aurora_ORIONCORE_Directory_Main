"""Executable L1/L2 authority and persistent autonomic-worker acceptance."""

# ruff: noqa: E402
import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ace.contextual import ContextQueue, validate_settings
from ace.core import ACEError
from ace.sandbox import World, atomic_json, atomic_text, git
from aurora_ace_sandbox import provision

SETTINGS = {
    "roles": ["contextual_archive_coordinator"],
    "faction_id": "galactic_union",
    "location_type": "context_archive",
}


@pytest.mark.parametrize(
    "layer,settings",
    [
        ("L3", SETTINGS),
        ("L2", {**SETTINGS, "physics": "anything"}),
        (
            "L1",
            {
                "subject_ref": "test",
                "evidence_refs": ["canon/L2/entities/test.json"],
                "field_paths": ["value"],
            },
        ),
        (
            "L1",
            {
                "subject_ref": "test",
                "evidence_refs": ["canon/L1/../../escape.json"],
                "field_paths": ["value"],
            },
        ),
    ],
)
def test_settings_enforce_layer_boundaries(layer, settings):
    with pytest.raises(ACEError):
        validate_settings(layer, settings)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    if os.environ.get("ACE_CONTEXT_E2E") != "1":
        pytest.skip("Set ACE_CONTEXT_E2E=1 with registered local source repositories")
    destination = tmp_path_factory.mktemp("context-world") / "world"
    owners = Path(os.environ.get("ACE_SANDBOX_REPOSITORIES_ROOT", str(ROOT)))
    provision(destination, ROOT, owners, Path(sys.executable))
    # Explicit isolated fixture facts exercise the native L1 evidence resolver.
    fixture_world = World(destination)
    for name, value in (("one", 7), ("two", 8)):
        path = fixture_world.canon / f"canon/L1/context_test_{name}.json"
        atomic_json(path, {"certainty": "CANON", "fact": {"value": value}})
    git(
        fixture_world.canon,
        "add",
        "canon/L1/context_test_one.json",
        "canon/L1/context_test_two.json",
    )
    git(
        fixture_world.canon,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@aurora.local",
        "commit",
        "-m",
        "test: isolated L1 evidence fixtures",
    )
    head = git(fixture_world.canon, "rev-parse", "HEAD")
    fixture_world.metadata["canon_head"] = head
    atomic_json(destination / "world.json", fixture_world.metadata)
    atomic_text(
        fixture_world.root / "catalog/repo_registry.yaml",
        yaml.safe_dump(fixture_world._registry(head), sort_keys=False),
    )
    return destination


def grant(world, name, *, max_jobs=20, role=None):
    queue = ContextQueue(world)
    queue.authorize(
        name,
        "Supply the archive team needed by this bounded survey.",
        "L2",
        {**SETTINGS, "roles": [role]} if role else SETTINGS,
        "test:explicit-assignment",
        max_jobs,
    )
    return queue


def test_missing_authority_and_scope_overrides_refused(world):
    queue = ContextQueue(world)
    with pytest.raises(ACEError):
        queue.submit("ungranted", "one", "We need an archivist.", {})
    grant(world, "scope")
    for context in (
        {"role": "unapproved"},
        {"target_layer": "L1"},
        {"authority_ref": "pretend"},
        {"faction_id": "different"},
        {"existence_status": "new"},
        {"location_type": "elsewhere"},
    ):
        with pytest.raises(ACEError):
            queue.submit("scope", "bad", "Need a character.", context)
    with pytest.raises(ACEError, match="separate world"):
        queue.authorize(
            "other-settings",
            "Different experiment",
            "L2",
            {**SETTINGS, "location_type": "other"},
            "test",
        )


def test_assignment_budget_revocation_and_duplicate_need(world):
    queue = grant(world, "budget", max_jobs=1)
    job = queue.submit("budget", "one", "We need a coordinator.", {})
    assert queue.submit("budget", "one", "We need a coordinator.", {}) == job
    with pytest.raises(ACEError, match="different input"):
        queue.submit("budget", "one", "Different need", {})
    with pytest.raises(ACEError, match="budget"):
        queue.submit("budget", "two", "Another coordinator.", {})
    queue.revoke("budget", "Test canceled assignment")
    result = queue.work_once()
    assert result["status"] == "blocked"
    assert "revoked" in result["error"]


def test_background_stdio_need_without_explicit_create_and_restart(world):
    grant(world, "background")
    from mcp import Client, StdioServerParameters

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(ROOT / "tools/aurora_ace_context_mcp.py"), "--world", str(world)],
        )
        async with Client(params, read_timeout_seconds=180) as client:
            assert sorted(t.name for t in (await client.list_tools()).tools) == [
                "aurora_context_status",
                "aurora_need_inspect",
                "aurora_simulation_need",
            ]
            submitted = await client.call_tool(
                "aurora_simulation_need",
                {
                    "assignment_id": "background",
                    "need_id": "archive-duty",
                    "question": "The archive survey needs someone to coordinate the expedition logs.",
                    "context": {},
                },
            )
            assert not submitted.is_error, submitted
            job_id = submitted.structured_content["job_id"]
            for _ in range(160):
                inspected = await client.call_tool(
                    "aurora_need_inspect", {"job_id": job_id}
                )
                assert not inspected.is_error, inspected
                job = inspected.structured_content
                if job["status"] in {"complete", "blocked", "conflict"}:
                    break
                await asyncio.sleep(0.25)
            assert job["status"] == "complete", job
            assert job["result"]["status"] == "GENERATED_CANON"
            assert job["result"]["invocation_id"].startswith(
                "ace.invocation.autonomic."
            )
            assert not job["needs_attention"]
            assert job["l3_receipt"]["target_layer"] == "L2"
            assert not job["l3_receipt"]["cross_layer_authority"]
            assert (
                job["l3_receipt"]["authority_ref"]
                in job["result"]["materialization"]["gate_policy_ref"]
            )
        async with Client(params, read_timeout_seconds=180) as client:
            recalled = await client.call_tool("aurora_need_inspect", {"job_id": job_id})
            assert recalled.structured_content == job
        return job

    job = asyncio.run(run())
    recalled = World(world).character(
        "Who coordinates these logs?",
        {"canonical_id": job["result"]["entity_id"]},
        "context-recall",
        "retrieve",
    )
    for field in ("canonical_id", "name", "background"):
        assert recalled["character"][field] == job["result"]["character"][field]
    assert recalled["character"]["background_and_traits"]["knowledge"]


def test_native_commit_recovered_after_worker_interruption(world, monkeypatch):
    queue = grant(world, "recovery", role="contextual_recovery_cartographer")
    job = queue.submit("recovery", "one", "The archive survey needs a coordinator.", {})
    original = queue._execute

    def interrupt(*args):
        result = original(*args)
        assert result["status"] == "GENERATED_CANON", result
        raise SystemExit("Simulated worker exit after native outcome")

    monkeypatch.setattr(queue, "_execute", interrupt)
    with pytest.raises(SystemExit):
        queue.work_once()
    before = git(queue.world.canon, "rev-parse", "HEAD")
    recovered = ContextQueue(world).work_once()
    assert recovered["job_id"] == job["job_id"]
    assert recovered["status"] == "complete"
    assert git(queue.world.canon, "rev-parse", "HEAD") == before


def test_concurrent_workers_serialize(world):
    queue = grant(world, "concurrency", role="contextual_concurrency_liaison")
    job = queue.submit("concurrency", "one", "We need the archive coordinator.", {})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: ContextQueue(world).work_once(), range(2)))
    assert sum(r is not None for r in results) == 1
    assert queue.inspect(job["job_id"])["status"] == "complete"


def test_l1_evidence_resolution_and_conflict_never_generate(world):
    queue = ContextQueue(world)
    before = git(queue.world.canon, "rev-parse", "HEAD")
    for name, refs, expected in (
        ("l1-fact", ["one"], "complete"),
        ("l1-conflict", ["one", "two"], "conflict"),
    ):
        queue.authorize(
            name,
            "Read isolated L1 test evidence.",
            "L1",
            {
                "subject_ref": "test.fact",
                "evidence_refs": [f"canon/L1/context_test_{r}.json" for r in refs],
                "field_paths": ["fact.value"],
            },
            "test:L1-evidence",
        )
        queue.submit(
            name, "read", "What value is supported?", {"field_path": "fact.value"}
        )
        result = queue.work_once()
        assert result["status"] == expected, result
        assert result["l3_receipt"]["truth_basis"] == "committed_L1_evidence"
        assert not result["l3_receipt"]["reality_verified"]
    with pytest.raises(ACEError, match="generation is not evidence"):
        queue.submit(
            "l1-fact", "invent", "Supply a missing person", {"role": "engineer"}
        )
    assert git(queue.world.canon, "rev-parse", "HEAD") == before


def test_settings_tampering_invalidates_authority(world):
    queue = grant(world, "tamper")
    path = queue.assignments / "tamper.json"
    original = path.read_bytes()
    record = json.loads(original)
    record["spec"]["settings"]["faction_id"] = "different"
    atomic_json(path, record)
    try:
        with pytest.raises(ACEError, match="settings changed"):
            queue.submit("tamper", "one", "Need someone", {})
    finally:
        path.write_bytes(original)


def test_interrupted_baseline_transition_recovers_once(world, monkeypatch):
    queue = grant(world, "baseline-recovery", role="context_baseline_engineer")
    job = queue.submit(
        "baseline-recovery", "one", "The survey needs a baseline engineer.", {}
    )

    def interrupt(*args):
        raise SystemExit("Interrupted before world baseline update")

    monkeypatch.setattr(queue.world, "_finish", interrupt)
    with pytest.raises(SystemExit):
        queue.work_once()
    committed = git(queue.world.canon, "rev-parse", "HEAD")
    assert committed != queue.world.metadata["canon_head"]
    recovered = ContextQueue(world).work_once()
    assert recovered["job_id"] == job["job_id"]
    assert recovered["status"] == "complete", recovered
    assert recovered["result"]["materialization"]["commit_sha"] == committed
    assert World(world).status()["canon_head"] == committed


def test_unexpected_canon_edit_blocks_work(world):
    queue = grant(world, "dirty-world", role="context_dirty_probe")
    job = queue.submit("dirty-world", "one", "The survey needs a specialist.", {})
    before = git(queue.world.canon, "rev-parse", "HEAD")
    unexpected = queue.world.canon / "unexpected-context-edit.txt"
    unexpected.write_text("Test concurrent edit")
    try:
        result = queue.work_once()
        assert result["job_id"] == job["job_id"]
        assert result["status"] == "blocked"
        assert git(queue.world.canon, "rev-parse", "HEAD") == before
    finally:
        unexpected.unlink()


def test_ambiguous_existing_character_is_not_duplicated(world):
    queue = grant(world, "ambiguity")
    before = git(queue.world.canon, "rev-parse", "HEAD")
    queue.submit("ambiguity", "one", "We need a coordinator for the same archive.", {})
    result = queue.work_once()
    assert result["status"] == "blocked"
    assert result["result"]["blockers"]
    assert git(queue.world.canon, "rev-parse", "HEAD") == before


def test_queue_symlink_escape_refused(world, tmp_path):
    queue = grant(world, "symlink")
    link = queue.jobs / "escape.json"
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    link.symlink_to(outside)
    try:
        with pytest.raises(ACEError, match="symlink"):
            queue.submit("symlink", "one", "Need a person", {})
        assert outside.read_text() == "{}"
    finally:
        link.unlink()
