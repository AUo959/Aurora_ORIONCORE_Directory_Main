from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import aurora_ace_acceptance as acceptance  # noqa: E402


MATRIX_PATH = REPO_ROOT / acceptance.DEFAULT_MATRIX
SCHEMA_PATH = REPO_ROOT / "catalog/schemas/aurora_ace_v1_acceptance_matrix.schema.json"


def test_committed_matrix_is_repository_grounded() -> None:
    matrix = acceptance.load_matrix(MATRIX_PATH)
    rows = acceptance.validate_matrix(matrix, root=REPO_ROOT)

    assert len(rows) == 13
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["static_status"] == "ready" for row in rows)
    assert {row["execution_class"] for row in rows} == {"local_safe", "isolated_ci"}
    assert all(len(row["boundaries"]) >= 2 for row in rows)


def test_committed_matrix_conforms_to_json_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    matrix = acceptance.load_matrix(MATRIX_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    jsonschema.Draft202012Validator(schema).validate(matrix)


def test_unexecuted_report_is_attention_not_failure() -> None:
    matrix = acceptance.load_matrix(MATRIX_PATH)
    report = acceptance.build_report(
        matrix,
        matrix_path=MATRIX_PATH,
        root=REPO_ROOT,
        run_practical=False,
        generated_at="2026-08-15T00:00:00Z",
    )

    assert report["status"] == "attention"
    assert report["seal_eligible"] is False
    assert report["canonical_nested_repositories_mutated"] is False
    assert report["summary"]["blocked"] == 0
    assert all(row["practical"]["status"] == "not_run" for row in report["rows"])


@pytest.mark.parametrize(
    ("returncode", "counts", "expected"),
    [
        (0, {"tests": 2, "passed": 2, "failed": 0, "errors": 0, "skipped": 0}, "ready"),
        (
            0,
            {"tests": 2, "passed": 1, "failed": 0, "errors": 0, "skipped": 1},
            "attention",
        ),
        (
            1,
            {"tests": 1, "passed": 0, "failed": 1, "errors": 0, "skipped": 0},
            "blocked",
        ),
    ],
)
def test_practical_status_distinguishes_failure_from_unverified(
    returncode: int,
    counts: dict[str, int],
    expected: str,
) -> None:
    assert acceptance._practical_status(returncode, counts) == expected


def test_official_mcp_client_enumerates_registered_surface() -> None:
    pytest.importorskip("mcp")
    from mcp import Client

    from ace.mcp_adapter import MCP_TOOL_NAMES
    from aurora_ace_mcp import mcp

    async def inspect() -> tuple[str, ...]:
        async with Client(mcp) as client:
            response = await client.list_tools()
            return tuple(tool.name for tool in response.tools)

    names = asyncio.run(inspect())
    assert len(names) == 6
    assert set(names) == set(MCP_TOOL_NAMES)
    assert {"ace_materialize_preview", "ace_materialize_commit"}.issubset(names)
