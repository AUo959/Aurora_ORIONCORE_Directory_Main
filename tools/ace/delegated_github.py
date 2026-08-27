"""Fixed-endpoint GitHub draft-PR client for ACE delegated publication."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from .core import ACEError

_GITHUB_PULL_URL = "https://api.github.com/repos/AUo959/CanonRec/pulls"
_GITHUB_PULL_WEB_PREFIX = "https://github.com/AUo959/CanonRec/pull/"
_GITHUB_TOKEN_ENVS = ("ACE_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
_MAX_RESPONSE_BYTES = 1_048_576


class PublicationStateUncertain(ACEError):
    """A remote PR may exist, so automatic branch deletion is unsafe."""


def _httpx_module() -> Any:
    """Load the optional remote transport only when publication is invoked."""
    try:
        import httpx
    except ImportError as exc:
        raise ACEError(
            "delegated publication requires the httpx runtime dependency",
            code="tool_unavailable",
        ) from exc
    return httpx


def _github_token() -> str:
    for name in _GITHUB_TOKEN_ENVS:
        token = os.environ.get(name, "").strip()
        if token:
            return token
    raise ACEError(
        "delegated publication requires ACE_GITHUB_TOKEN, GH_TOKEN, or GITHUB_TOKEN",
        code="tool_unavailable",
    )


def _display_subject(determination: Mapping[str, Any]) -> str:
    subjects = determination.get("subject_refs", [])
    raw = str(subjects[0]) if isinstance(subjects, list) and subjects else "ACE proposal"
    normalized = " ".join(raw.split()).strip()
    return normalized[:120] or "ACE proposal"


def _pull_request_text(
    packet_kind: str,
    determination: Mapping[str, Any],
    authority_ref: str,
    principal_id: str,
    policy: Mapping[str, Any],
) -> tuple[str, str]:
    subject = _display_subject(determination)
    title = f"feat(canon): ACE delegated {packet_kind} {subject}"[:240]
    body = "\n".join(
        [
            "## ACE delegated canon proposal",
            "",
            f"- Authority: `{authority_ref}`",
            f"- Authenticated publisher: `{principal_id}`",
            f"- ACE policy: `{policy['policy_id']}`",
            "- Promotion remains review-gated; repository CI is authoritative before merge.",
            f"- Source determination: `{determination.get('determination_id')}`",
            "- Mainline canon changed by this action: **no**",
            "- Auto-merge: **disabled**",
        ]
    )
    return title, body


def _request_payload(
    branch: str,
    packet_kind: str,
    determination: Mapping[str, Any],
    authority_ref: str,
    principal_id: str,
    policy: Mapping[str, Any],
) -> bytes:
    title, body = _pull_request_text(packet_kind, determination, authority_ref, principal_id, policy)
    payload = {
        "title": title,
        "head": branch,
        "base": policy["base_branch"],
        "body": body,
        "draft": True,
    }
    return json.dumps(payload).encode("utf-8")


def _github_create_pr(body: bytes) -> dict[str, Any]:
    httpx = _httpx_module()
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_github_token()}",
        "Content-Type": "application/json",
        "User-Agent": "aurora-ace-v0.12",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = httpx.post(
            _GITHUB_PULL_URL,
            content=body,
            headers=headers,
            timeout=20.0,
            follow_redirects=False,
        )
    except httpx.TransportError as exc:
        raise PublicationStateUncertain(
            "GitHub PR request lost transport certainty after transmission",
            code="runtime_failure",
        ) from exc
    raw = response.content
    if response.status_code != 201:
        detail = raw[:4096].decode("utf-8", errors="replace")
        raise ACEError(
            f"GitHub pull request creation failed ({response.status_code}): {detail}",
            code="runtime_failure",
        )
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise PublicationStateUncertain("GitHub created a PR but returned an oversized response", code="runtime_failure")
    try:
        parsed = response.json()
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PublicationStateUncertain("GitHub created a PR but returned an unreadable response", code="runtime_failure") from exc
    if not isinstance(parsed, Mapping):
        raise PublicationStateUncertain("GitHub created a PR but returned an invalid response", code="runtime_failure")
    return dict(parsed)


def _parse_pull_request(response: Mapping[str, Any]) -> tuple[int, str]:
    number = response.get("number")
    expected_url = f"{_GITHUB_PULL_WEB_PREFIX}{number}"
    if not isinstance(number, int) or number <= 0:
        raise PublicationStateUncertain("GitHub created a PR without a valid number", code="runtime_failure")
    if response.get("html_url") != expected_url:
        raise PublicationStateUncertain("GitHub created a PR with an unexpected URL", code="runtime_failure")
    if response.get("draft") is not True or response.get("state") != "open":
        raise PublicationStateUncertain("GitHub created a PR with unexpected review state", code="runtime_failure")
    return number, expected_url


def open_pull_request(
    branch: str,
    packet_kind: str,
    determination: Mapping[str, Any],
    authority_ref: str,
    principal_id: str,
    policy: Mapping[str, Any],
) -> tuple[int, str]:
    """Open one draft PR against the fixed CanonRec GitHub endpoint."""
    body = _request_payload(branch, packet_kind, determination, authority_ref, principal_id, policy)
    return _parse_pull_request(_github_create_pr(body))
