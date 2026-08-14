from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import delegated_github as github_client  # noqa: E402


def _expect(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_parse_pull_request_requires_expected_open_draft_state() -> None:
    number, url = github_client._parse_pull_request(
        {
            "number": 42,
            "html_url": "https://github.com/AUo959/CanonRec/pull/42",
            "draft": True,
            "state": "open",
        }
    )
    _expect(number == 42, "GitHub response must preserve PR number")
    _expect(url == "https://github.com/AUo959/CanonRec/pull/42", "GitHub response must preserve fixed CanonRec PR URL")

    with pytest.raises(github_client.PublicationStateUncertain):
        github_client._parse_pull_request(
            {
                "number": 42,
                "html_url": "https://github.com/AUo959/CanonRec/pull/42",
                "draft": False,
                "state": "open",
            }
        )


def test_github_transport_loss_after_post_is_state_uncertain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_post(*args: object, **kwargs: object) -> object:
        raise github_client.httpx.TransportError("synthetic transport loss")

    monkeypatch.setenv("ACE_GITHUB_TOKEN", "synthetic-test-token")
    monkeypatch.setattr(github_client.httpx, "post", broken_post)
    with pytest.raises(github_client.PublicationStateUncertain, match="lost transport certainty"):
        github_client._github_create_pr(b"{}")
