from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import session_claim  # noqa: E402


FIXED_NOW = datetime(2026, 5, 31, 0, 30, tzinfo=timezone.utc)


def test_create_claim_blocks_overlapping_mutation(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    code, payload = session_claim.create_claim(
        root=root,
        platform="codex",
        task_id="coordination",
        repo="root",
        paths=["tools"],
        mutation_posture="editing",
        ttl_minutes=60,
        now=FIXED_NOW,
    )

    assert code == 0
    assert payload["claim"]["paths"] == ["tools"]

    check = session_claim.check_claims(
        root=root,
        repo="root",
        paths=["tools/session_claim.py"],
        mutation_posture="editing",
        now=FIXED_NOW,
    )

    assert check["status"] == "conflict"
    assert check["conflicts"][0]["overlapping_paths"] == [
        {"requested": "tools/session_claim.py", "claimed": "tools"}
    ]


def test_read_only_claim_does_not_block_mutation(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    code, _payload = session_claim.create_claim(
        root=root,
        platform="claude-code",
        task_id="read-only-review",
        repo="root",
        paths=["docs"],
        mutation_posture="read_only",
        ttl_minutes=60,
        now=FIXED_NOW,
    )

    assert code == 0
    check = session_claim.check_claims(
        root=root,
        repo="root",
        paths=["docs/SESSION_CLAIMS_WORKFLOW_v1.md"],
        mutation_posture="editing",
        now=FIXED_NOW,
    )

    assert check["status"] == "clear"
    assert check["conflicts"] == []


def test_stale_claim_is_non_blocking(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    code, _payload = session_claim.create_claim(
        root=root,
        platform="codex",
        task_id="expired",
        repo="root",
        paths=["AGENTS.md"],
        mutation_posture="editing",
        ttl_minutes=1,
        now=FIXED_NOW,
    )

    assert code == 0
    check = session_claim.check_claims(
        root=root,
        repo="root",
        paths=["AGENTS.md"],
        mutation_posture="editing",
        now=FIXED_NOW + timedelta(minutes=2),
    )

    assert check["status"] == "clear"
    assert len(check["stale_claims"]) == 1


def test_release_claim_removes_conflict(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    code, payload = session_claim.create_claim(
        root=root,
        platform="codex",
        task_id="release-me",
        repo="root",
        paths=["README.md"],
        mutation_posture="editing",
        ttl_minutes=60,
        now=FIXED_NOW,
    )
    claim_id = payload["claim"]["claim_id"]

    assert code == 0
    release_code, release_payload = session_claim.release_claim(root, claim_id, now=FIXED_NOW)
    check = session_claim.check_claims(
        root=root,
        repo="root",
        paths=["README.md"],
        mutation_posture="editing",
        now=FIXED_NOW,
    )

    assert release_code == 0
    assert release_payload["claim"]["status"] == "released"
    assert check["status"] == "clear"


def test_normalize_path_rejects_paths_outside_workspace(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    with pytest.raises(ValueError, match="outside the workspace"):
        session_claim.normalize_path(str(tmp_path / "outside.md"), root)


def test_cli_accepts_json_after_subcommand(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    result = subprocess.run(  # noqa: S603 - intentional CLI regression test with fixed argv.
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "session_claim.py"),
            "--root",
            str(root),
            "check",
            "--repo",
            "root",
            "--paths",
            ".",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "clear"
