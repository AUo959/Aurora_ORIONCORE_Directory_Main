from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import workspace_plan_moves  # noqa: E402


def test_merge_batch_does_not_preserve_applied_status_for_unapplied_operations() -> None:
    existing = {
        "batch_id": "wave4_root_intake_cleanup_initial",
        "status": "applied",
        "operations": [
            {
                "source": "QGIA_SPACE_NAVAGATION_GUIDE.md",
                "destination": "intake/QGIA_SPACE_NAVAGATION_GUIDE.md",
                "operation": "move",
                "approved": False,
                "applied_at": None,
            }
        ],
    }
    generated = {
        "batch_id": "wave4_root_intake_cleanup_initial",
        "status": "planned",
        "operations": [
            {
                "source": "QGIA_SPACE_NAVAGATION_GUIDE.md",
                "destination": "intake/QGIA_SPACE_NAVAGATION_GUIDE.md",
                "operation": "move",
                "approved": False,
                "applied_at": None,
            }
        ],
    }

    merged = workspace_plan_moves.merge_batch(existing, generated)

    assert merged["status"] == "planned"


def test_merge_batch_preserves_applied_status_for_applied_operations() -> None:
    existing = {
        "batch_id": "wave3_small_intake_files_initial",
        "status": "applied",
        "operations": [
            {
                "source": "PROJECT_SPACE_BANNER.md",
                "destination": "intake/PROJECT_SPACE_BANNER.md",
                "operation": "move",
                "approved": True,
                "applied_at": "2026-03-08T00:09:55Z",
            }
        ],
    }
    generated = {
        "batch_id": "wave3_small_intake_files_initial",
        "status": "planned",
        "operations": [
            {
                "source": "PROJECT_SPACE_BANNER.md",
                "destination": "intake/PROJECT_SPACE_BANNER.md",
                "operation": "move",
                "approved": False,
                "applied_at": None,
            }
        ],
    }

    merged = workspace_plan_moves.merge_batch(existing, generated)

    assert merged["status"] == "applied"
    assert merged["operations"][0]["approved"] is True
    assert merged["operations"][0]["applied_at"] == "2026-03-08T00:09:55Z"
