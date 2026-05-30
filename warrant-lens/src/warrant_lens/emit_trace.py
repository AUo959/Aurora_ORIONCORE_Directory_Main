"""Stage [6b] EMIT JSONL provenance trace.

One ClaimRecord per line. Exportable, replayable, diffable. Filename follows
Aurora archival convention: WARRANTLENS__TRACE__[topic]__v1.0__YYYY-MM-DD.jsonl
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .model import ClaimRecord


def trace_filename(topic: str, when: date | None = None) -> str:
    when = when or date.today()
    safe_topic = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in topic).strip("-")
    if not safe_topic:
        safe_topic = "untopiced"
    return f"WARRANTLENS__TRACE__{safe_topic}__v1.0__{when.isoformat()}.jsonl"


def write_trace(
    records: Iterable[ClaimRecord], out_dir: Path, topic: str
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / trace_filename(topic)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(_to_jsonable(r), ensure_ascii=False) + "\n")
    return path


def records_to_jsonable(records: Iterable[ClaimRecord]) -> list[dict]:
    return [_to_jsonable(r) for r in records]


def _to_jsonable(obj):
    """Recursively convert dataclasses + tuples to JSON-safe types."""
    if is_dataclass(obj):
        return {k: _to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    return obj
