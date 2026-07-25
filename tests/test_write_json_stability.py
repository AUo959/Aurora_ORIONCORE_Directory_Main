"""Generated reports must not go dirty when only their timestamps move.

Field finding 2026-07-25: every `*_latest.json` under reports/analysis/ was
permanently dirty in git. Two runs of the same tool seconds apart produced a
diff consisting solely of `generated_at`. A file that is always dirty is a file
everyone learns to ignore, so real changes hid among the churn and governance
drift accumulated until someone went digging.

These tests pin the fix: write_json compares meaning, not timestamps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import _workspace_common as wc  # noqa: E402


def test_unchanged_content_does_not_rewrite(tmp_path: Path) -> None:
    target = tmp_path / "report.json"

    assert wc.write_json(target, {"generated_at": "2026-01-01T00:00:00Z", "findings": []}) is True
    first = target.read_text(encoding="utf-8")

    # Same findings, later clock — the only thing a re-run usually changes.
    assert wc.write_json(target, {"generated_at": "2026-06-30T12:00:00Z", "findings": []}) is False
    assert target.read_text(encoding="utf-8") == first


def test_changed_content_does_rewrite(tmp_path: Path) -> None:
    target = tmp_path / "report.json"
    wc.write_json(target, {"generated_at": "2026-01-01T00:00:00Z", "findings": []})

    assert wc.write_json(
        target, {"generated_at": "2026-01-01T00:00:00Z", "findings": ["blocking"]}
    ) is True
    assert json.loads(target.read_text(encoding="utf-8"))["findings"] == ["blocking"]


def test_volatile_keys_are_stripped_at_any_depth(tmp_path: Path) -> None:
    target = tmp_path / "report.json"
    wc.write_json(target, {"runs": [{"timestamp": "t1", "status": "ok"}]})

    assert wc.write_json(target, {"runs": [{"timestamp": "t2", "status": "ok"}]}) is False
    assert wc.write_json(target, {"runs": [{"timestamp": "t2", "status": "warn"}]}) is True


def test_always_write_forces_the_write(tmp_path: Path) -> None:
    """Escape hatch for artifacts whose timestamp is the payload."""
    target = tmp_path / "heartbeat.json"
    wc.write_json(target, {"generated_at": "t1", "beat": 1})

    assert wc.write_json(target, {"generated_at": "t2", "beat": 1}, always_write=True) is True
    assert json.loads(target.read_text(encoding="utf-8"))["generated_at"] == "t2"


def test_liveness_marker_records_verification_without_dirtying(tmp_path: Path) -> None:
    """A skipped write still records that the tool ran — in a git-ignored place."""
    target = tmp_path / "report.json"
    wc.write_json(target, {"generated_at": "t1", "findings": []})
    body = target.read_text(encoding="utf-8")

    wc.write_json(target, {"generated_at": "t2", "findings": []})

    marker = tmp_path / wc.LASTRUN_DIR_NAME / "report.json.lastrun"
    assert marker.exists(), "verification time must survive a skipped write"
    assert marker.read_text(encoding="utf-8").strip().endswith("Z")
    assert target.read_text(encoding="utf-8") == body


def test_unreadable_existing_file_is_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "report.json"
    target.write_text("{ not json", encoding="utf-8")

    assert wc.write_json(target, {"findings": []}) is True
    assert json.loads(target.read_text(encoding="utf-8")) == {"findings": []}


def test_first_write_creates_the_file(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deep" / "report.json"
    assert wc.write_json(target, {"findings": []}) is True
    assert target.exists()
