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


# ── YAML and Markdown surfaces ────────────────────────────────────────────
#
# Field finding 2026-08-09: the 2026-07-25 fix above covered reports/*.json but
# never reached the catalog YAML surfaces or docs/workspace-map.md, which
# workspace_scan.py wrote through dump_yaml_like / path.write_text. Those three
# files were therefore dirtied by every no-op scan. The consequence was exactly
# the one this module was written to prevent: two genuinely new intake files sat
# unregistered for over a week because their diff looked like the usual churn.


def test_yaml_timestamp_only_change_does_not_rewrite(tmp_path: Path) -> None:
    target = tmp_path / "manifest.yaml"

    assert wc.write_yaml(target, {"generated_at": "2026-01-01T00:00:00Z",
                                  "entries": [{"path": "a", "family": "docs"}]}) is True
    first = target.read_text(encoding="utf-8")

    assert wc.write_yaml(target, {"generated_at": "2026-08-09T12:00:00Z",
                                  "entries": [{"path": "a", "family": "docs"}]}) is False
    assert target.read_text(encoding="utf-8") == first


def test_yaml_real_change_is_written(tmp_path: Path) -> None:
    target = tmp_path / "manifest.yaml"
    wc.write_yaml(target, {"generated_at": "t1", "entries": [{"path": "a"}]})

    assert wc.write_yaml(target, {"generated_at": "t2",
                                  "entries": [{"path": "a"}, {"path": "b"}]}) is True
    assert "b" in target.read_text(encoding="utf-8")


def test_markdown_generated_line_only_does_not_rewrite(tmp_path: Path) -> None:
    target = tmp_path / "workspace-map.md"
    body = "# Workspace Map\n\n- Generated: `2026-01-01T00:00:00Z`\n\n## Tree\n- root\n"

    assert wc.write_text(target, body) is True
    assert wc.write_text(
        target, body.replace("2026-01-01T00:00:00Z", "2026-08-09T12:00:00Z")
    ) is False
    assert target.read_text(encoding="utf-8") == body


def test_markdown_real_change_is_written(tmp_path: Path) -> None:
    target = tmp_path / "workspace-map.md"
    wc.write_text(target, "# Map\n- Generated: `t1`\n\n- root\n")

    assert wc.write_text(target, "# Map\n- Generated: `t2`\n\n- root\n- intake\n") is True
    assert "intake" in target.read_text(encoding="utf-8")


def test_skipped_yaml_and_text_writes_still_record_liveness(tmp_path: Path) -> None:
    yaml_target = tmp_path / "manifest.yaml"
    wc.write_yaml(yaml_target, {"generated_at": "t1", "entries": []})
    wc.write_yaml(yaml_target, {"generated_at": "t2", "entries": []})
    assert (tmp_path / wc.LASTRUN_DIR_NAME / "manifest.yaml.lastrun").exists()

    text_target = tmp_path / "map.md"
    wc.write_text(text_target, "- Generated: `t1`\nbody\n")
    wc.write_text(text_target, "- Generated: `t2`\nbody\n")
    assert (tmp_path / wc.LASTRUN_DIR_NAME / "map.md.lastrun").exists()


def test_scan_writers_are_wired_to_the_idempotent_helpers() -> None:
    """Guard the wiring, not just the helpers.

    The helpers existed since 2026-07-25; the defect was that workspace_scan.py
    bypassed them. This fails if anyone reverts to a raw write.
    """
    source = (TOOLS_DIR / "workspace_scan.py").read_text(encoding="utf-8")
    assert "dump_yaml_like(manifest" not in source
    assert "dump_yaml_like(repo_registry" not in source
    assert "write_yaml(manifest_out" in source
    assert "write_yaml(repo_registry_out" in source
    assert 'path.write_text("\\n".join(lines)' not in source
