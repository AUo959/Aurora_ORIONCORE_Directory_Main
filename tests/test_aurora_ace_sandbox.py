"""Persistent-world tests use independent clones and real stdio MCP processes."""

# ruff: noqa: S603, S607
# Subprocesses run fixed Git/Python test commands against isolated fixtures.
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ace.core import ACEError  # noqa: E402
from ace.sandbox import World, REQUEST_ID  # noqa: E402
from aurora_ace_sandbox import provision  # noqa: E402


def test_non_world_and_canonical_target_are_refused(tmp_path):
    with pytest.raises(ACEError):
        World(ROOT)
    with pytest.raises(ACEError, match="separate"):
        provision(ROOT / "bad-sandbox", ROOT, ROOT, Path(sys.executable))
    tmp_path.joinpath("existing").mkdir()
    with pytest.raises(ACEError, match="already exists"):
        provision(tmp_path / "existing", ROOT, ROOT, Path(sys.executable))


@pytest.mark.parametrize(
    "value", ["../outside", "/outside/escape", "a/b", "a\\b", "", ".", "x" * 97]
)
def test_request_ids_are_identifiers(value):
    assert not REQUEST_ID.fullmatch(value)


def test_acceptance_ci_requires_ready_and_tracks_registry():
    text = (ROOT / ".github/workflows/ace-v1-acceptance.yml").read_text()
    assert "--require-ready" in text
    assert text.count('"catalog/repo_registry.yaml"') >= 2


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    if os.environ.get("ACE_SANDBOX_E2E") != "1":
        pytest.skip(
            "requires committed implementation and registered local source repositories"
        )
    pytest.importorskip("mcp")
    destination = tmp_path_factory.mktemp("ace-world-parent") / "world"
    source = Path(os.environ.get("ACE_SANDBOX_SOURCE", str(ROOT)))
    owners = Path(os.environ.get("ACE_SANDBOX_REPOSITORIES_ROOT", str(ROOT)))
    provision(destination, source, owners, Path(sys.executable))
    return destination


def rpc(world, tool, arguments=None, *, error=False):
    from mcp import Client, StdioServerParameters

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=[
                str(world / "workspace/tools/aurora_ace_sandbox_mcp.py"),
                "--world",
                str(world),
            ],
            cwd=str(world / "workspace"),
        )
        async with Client(params, read_timeout_seconds=180) as client:
            if tool == "list":
                return sorted(item.name for item in (await client.list_tools()).tools)
            result = await client.call_tool(tool, arguments or {})
            if error:
                assert result.is_error, result
                return str(result)
            assert not result.is_error, result
            return result.structured_content or json.loads(result.content[0].text)

    return asyncio.run(run())


def character(
    world, request_id, operation, context, question="Who is this character?", **kwargs
):
    return rpc(
        world,
        "aurora_character",
        dict(
            question=question,
            context=context,
            request_id=request_id,
            operation=operation,
        ),
        **kwargs,
    )


def context(role="continuity_expedition_archivist"):
    return dict(
        role=role,
        faction_id="galactic_union",
        location_type="continuity_archive_outpost",
        observed_behavior=["Carefully cross-checks conflicting expedition logs."],
    )


def head(world):
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(world / "workspace/GUMAS_SIM_2.5/CanonRec"),
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()


def test_real_mcp_create_restart_retrieve_and_second_creation(world):
    assert rpc(world, "list") == [
        "aurora_character",
        "aurora_inspect",
        "aurora_world_status",
    ]
    before = head(world)
    # Discover a committed character through the native index, never generate fixture canon.
    script = "from ace.character_retrieval import build_character_index; import json; print(json.dumps(build_character_index()))"
    result = subprocess.check_output(
        [sys.executable, "-c", script], cwd=world / "workspace/tools", text=True
    )
    index = json.loads(result)
    identities = index["records"]
    existing = character(
        world, "existing", "retrieve", {"canonical_id": identities[0]["canonical_id"]}
    )
    assert existing["status"] == "RETRIEVED_CANON"
    assert head(world) == before
    missing = character(
        world, "missing", "retrieve", {"name": "No Such Continuity Person"}
    )
    assert missing["status"] == "EXECUTION_BLOCKED"
    preview = character(world, "preview", "preview", context())
    assert preview["materialization"]["status"] == "commit_ready"
    assert head(world) == before
    created = character(world, "create-one", "create", context())
    assert created["status"] == "GENERATED_CANON"
    assert created["origin"] == "sandbox_created"
    assert created["entity_id"]
    after = head(world)
    assert after != before
    assert character(world, "create-one", "create", context()) == created
    assert head(world) == after
    # Every rpc starts a new OS process. Recall cannot use an in-process cache.
    recalled = character(
        world, "recall", "retrieve", {"canonical_id": created["entity_id"]}
    )
    assert recalled["status"] == "RETRIEVED_CANON"
    assert recalled["entity_id"] == created["entity_id"]
    assert recalled["origin"] == "sandbox_created"
    assert recalled["character"]["background"] == created["character"]["background"]
    by_name = character(
        world, "recall-name", "retrieve", {"name": created["character"]["name"]}
    )
    assert by_name["entity_id"] == created["entity_id"]
    inspected = rpc(
        world, "aurora_inspect", {"determination_id": created["determination_id"]}
    )
    assert inspected["found"] is True
    second = character(
        world, "create-two", "create", context("continuity_orbital_cartographer")
    )
    assert second["status"] == "GENERATED_CANON"
    assert second["entity_id"] != created["entity_id"]


def test_duplicate_input_path_escape_and_dirty_tree_refuse(world):
    before = head(world)
    character(world, "../escape", "create", context(), error=True)
    character(world, "create-one", "create", context("different"), error=True)
    tree = world / "workspace/GUMAS_SIM_2.5/CanonRec"
    dirty = tree / "unexpected.txt"
    dirty.write_text("external edit")
    try:
        character(world, "dirty", "create", context(), error=True)
    finally:
        dirty.unlink()
    assert head(world) == before


def test_journal_recovers_commit_before_baseline_update(world):
    # Simulate process death immediately before _finish. Only the sandbox process is patched.
    code = """
import json,sys
from ace.sandbox import World
from pathlib import Path
w=World(Path(sys.argv[1]))
def stop(*args): raise RuntimeError('simulated process interruption')
w._finish=stop
try: w.character('Create recovery character', json.loads(sys.argv[2]), 'recover', 'create')
except RuntimeError: pass
"""
    subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(world),
            json.dumps(context("continuity_recovery_historian")),
        ],
        cwd=world / "workspace/tools",
        check=True,
    )
    committed = head(world)
    assert rpc(world, "aurora_world_status")["status"] == "recovery_pending"
    result = character(
        world,
        "recover",
        "create",
        context("continuity_recovery_historian"),
        question="Create recovery character",
    )
    assert result["status"] == "GENERATED_CANON"
    assert head(world) == committed
    assert rpc(world, "aurora_world_status")["status"] == "ready"


def test_concurrent_duplicate_creation_is_one_commit(world):
    before = head(world)

    def create():
        return character(
            world, "concurrent", "create", context("continuity_signal_curator")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(pool.map(lambda _: create(), range(2)))
    assert a == b
    count = subprocess.check_output(
        [
            "git",
            "-C",
            str(world / "workspace/GUMAS_SIM_2.5/CanonRec"),
            "rev-list",
            "--count",
            f"{before}..HEAD",
        ],
        text=True,
    ).strip()
    assert count == "1"


def test_symlink_world_and_runtime_escape_refused(world, tmp_path):
    link = tmp_path / "world-link"
    link.symlink_to(world, target_is_directory=True)
    with pytest.raises(ACEError, match="symlinks"):
        World(link)
    escape = world / "workspace/reports/ace/mcp_runtime/escape"
    escape.symlink_to(tmp_path, target_is_directory=True)
    try:
        with pytest.raises(ACEError, match="symlink"):
            World(world)
    finally:
        escape.unlink()
