"""Keep session-claim test identity out of the developer's home directory."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import session_claim


@pytest.fixture(autouse=True)
def isolated_machine_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_claim, "MACHINE_ID_PATH", tmp_path / "machine-id")
