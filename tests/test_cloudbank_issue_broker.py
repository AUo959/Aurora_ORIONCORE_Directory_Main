from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import cloudbank_issue_broker as broker  # noqa: E402
import session_claim  # noqa: E402


FIXED_NOW = datetime(2026, 6, 1, 19, 0, tzinfo=timezone.utc)
CLOUDBANK_PATH = "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_registry(root: Path) -> None:
    write_file(
        root / "catalog" / "repo_registry.yaml",
        "repos:\n"
        "- name: aurora-cloudbank-symbolic-main\n"
        f"  path: {CLOUDBANK_PATH}\n"
        "  branch: main\n"
        "  head_sha: abc123\n"
        "  remote_status: configured\n",
    )


def test_normalize_cloudbank_paths_prefixes_repo_path(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    paths = broker.normalize_cloudbank_paths(
        [".github/dependabot.yml", "src/middleware/fastapi_security.py"],
        root=root,
        repo_rel=CLOUDBANK_PATH,
    )

    assert paths == [
        f"{CLOUDBANK_PATH}/.github/dependabot.yml",
        f"{CLOUDBANK_PATH}/src/middleware/fastapi_security.py",
    ]


def test_normalize_cloudbank_path_rejects_parent_traversal(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    try:
        broker.normalize_cloudbank_path("../root.txt", root=root, repo_rel=CLOUDBANK_PATH)
    except ValueError as exc:
        assert "Unsafe CloudBank path" in str(exc)
    else:
        raise AssertionError("expected unsafe path rejection")


def test_plan_blocks_issue_with_active_claim(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    write_registry(root)

    code, _payload = session_claim.create_claim(
        root=root,
        platform="claude-code",
        task_id="cloudbank-issue-842",
        repo=broker.CLOUDBANK_REPO_NAME,
        paths=[f"{CLOUDBANK_PATH}/src/auth.py"],
        mutation_posture="editing",
        ttl_minutes=60,
        now=FIXED_NOW,
    )

    assert code == 0
    report = broker.build_report(root, issues=[842], generated_at=FIXED_NOW)

    assert report["status"] == "blocked"
    assert report["candidates"][0]["status"] == "blocked"
    assert report["candidates"][0]["blockers"][0]["kind"] == "active_claim"
    assert report["candidates"][0]["blockers"][0]["platform"] == "claude-code"


def test_claim_issue_creates_cloudbank_session_claim(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    write_registry(root)

    code, payload = broker.claim_issue(
        root=root,
        issue=842,
        platform="codex",
        paths=["src/middleware/fastapi_security.py", "tests/test_security_middleware.py"],
        label="auth",
        validation_command=".venv/bin/python -m pytest -q tests/test_security_middleware.py",
        now=FIXED_NOW,
    )

    assert code == 0
    claim = payload["claim"]
    assert claim["repo"] == broker.CLOUDBANK_REPO_NAME
    assert claim["task_id"] == "cloudbank-issue-842"
    assert claim["paths"] == [
        f"{CLOUDBANK_PATH}/src/middleware/fastapi_security.py",
        f"{CLOUDBANK_PATH}/tests/test_security_middleware.py",
    ]
    notes = json.loads(claim["notes"])
    assert notes["issue"] == 842
    assert notes["cloudbank_branch"] == "codex/cloudbank-issue-842-auth"
    assert "worktree add" in payload["broker"]["worktree_command"]


def test_claim_issue_blocks_duplicate_issue_claim_even_with_different_paths(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    write_registry(root)
    session_claim.create_claim(
        root=root,
        platform="claude-code",
        task_id="cloudbank-issue-842",
        repo=broker.CLOUDBANK_REPO_NAME,
        paths=[f"{CLOUDBANK_PATH}/src/auth.py"],
        mutation_posture="editing",
        ttl_minutes=60,
        now=FIXED_NOW,
    )

    code, payload = broker.claim_issue(
        root=root,
        issue=842,
        platform="codex",
        paths=["docs/README.md"],
        now=FIXED_NOW,
    )

    assert code == 2
    assert payload["status"] == "conflict"
    assert payload["issue_claim_conflicts"][0]["kind"] == "active_issue_claim"


def test_cli_plan_accepts_json_after_subcommand(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    write_registry(root)

    result = subprocess.run(  # noqa: S603 - intentional CLI regression test with fixed argv.
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "cloudbank_issue_broker.py"),
            "--root",
            str(root),
            "plan",
            "--issue",
            "842",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["requested_issues"] == [842]
    assert payload["candidates"][0]["status"] == "claim_ready"
