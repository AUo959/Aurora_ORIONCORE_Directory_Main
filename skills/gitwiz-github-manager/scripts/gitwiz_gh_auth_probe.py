#!/usr/bin/env python3
"""Probe GitHub CLI auth without exposing tokens.

The probe intentionally reports failures as "current execution context"
failures. In Codex, sandboxed commands can fail to access the same keyring or
network context that the real desktop session uses, so a failed probe is not a
token diagnosis until it has been rerun outside the sandbox.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow_display() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed gh probe commands with optional repo arg.
        args,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )


def completed_payload(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def probe_gh_auth(repo: str | None = None, cwd: Path | None = None) -> dict[str, Any]:
    gh_path = shutil.which("gh")
    payload: dict[str, Any] = {
        "generated_at_utc": utcnow_display(),
        "gh_path": gh_path or "",
        "status": "gh_missing",
        "login": "",
        "repo": repo or "",
        "commands": {},
        "next_step": "",
    }

    if not gh_path:
        payload["next_step"] = "Install GitHub CLI or use SSH Git plus the GitHub connector."
        return payload

    auth_status = run_command(["gh", "auth", "status"], cwd=cwd)
    payload["commands"]["auth_status"] = completed_payload(auth_status)

    if auth_status.returncode != 0:
        payload["status"] = "auth_failed_in_current_context"
        payload["next_step"] = (
            "Codex: rerun this probe or `gh auth status` with escalated/unsandboxed execution "
            "before changing tokens. A sandbox failure is not proof that the keyring token is broken."
        )
        return payload

    api_user = run_command(["gh", "api", "user", "--jq", ".login"], cwd=cwd)
    payload["commands"]["api_user"] = completed_payload(api_user)
    if api_user.returncode != 0:
        payload["status"] = "api_failed_in_current_context"
        payload["next_step"] = (
            "Auth status passed, but API access failed in this execution context. "
            "Rerun unsandboxed/escalated before rotating credentials."
        )
        return payload

    payload["login"] = api_user.stdout.strip()

    if repo:
        repo_probe = run_command(
            ["gh", "pr", "list", "--repo", repo, "--limit", "1", "--json", "number"],
            cwd=cwd,
        )
        payload["commands"]["repo_pr_list"] = completed_payload(repo_probe)
        if repo_probe.returncode != 0:
            payload["status"] = "repo_probe_failed_in_current_context"
            payload["next_step"] = (
                "GitHub CLI auth works, but this repo probe failed in the current context. "
                "Check repo access or rerun unsandboxed/escalated before falling back."
            )
            return payload

    payload["status"] = "usable"
    payload["next_step"] = "Use gh for PR and issue operations in this execution context."
    return payload


def human_summary(payload: dict[str, Any]) -> str:
    lines = [
        "GITWIZ GitHub CLI Auth Probe",
        f"- Status: {payload['status']}",
        f"- gh: {payload['gh_path'] or 'not_found'}",
    ]
    if payload.get("login"):
        lines.append(f"- Login: {payload['login']}")
    if payload.get("repo"):
        lines.append(f"- Repo probe: {payload['repo']}")
    lines.append(f"- Next step: {payload['next_step']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Optional owner/repo probe with gh pr list.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a short human summary.")
    parser.add_argument("--cwd", help="Optional working directory for gh commands.")
    args = parser.parse_args()

    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else None
    payload = probe_gh_auth(repo=args.repo, cwd=cwd)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(human_summary(payload), end="")
    return 0 if payload["status"] == "usable" else 3


if __name__ == "__main__":
    raise SystemExit(main())
