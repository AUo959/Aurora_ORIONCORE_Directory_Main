#!/usr/bin/env python3
"""Validate a private Google Drive metadata snapshot without accessing Drive.

This command neither retrieves source content nor writes to Aurora state.
Only aggregate counts go to stdout; keep source IDs and titles private.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


class SnapshotError(ValueError):
    """Invalid or unsafe external-source snapshot."""


def validate_snapshot(payload: object) -> list[dict]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise SnapshotError("expected a version-1 JSON object")
    if payload.get("provider") != "google_drive":
        raise SnapshotError("provider must be google_drive")
    if payload.get("access_class") != "private":
        raise SnapshotError("access_class must be private")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) > 10000:
        raise SnapshotError("records must be a list of at most 10000 entries")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise SnapshotError("record must be an object")
        required = ("source_id", "title", "mime_type", "source_url")
        if any(not isinstance(record.get(key), str) or not record[key].strip()
               for key in required):
            raise SnapshotError("record has missing required metadata")
        if record["source_id"] in seen:
            raise SnapshotError("duplicate source_id")
        seen.add(record["source_id"])
        if not (record["source_url"].startswith("https://drive.google.com/")
                or record["source_url"].startswith("https://docs.google.com/")):
            raise SnapshotError("unrecognized source URL host")
        if record.get("promotion_status") != "not_promoted":
            raise SnapshotError("external records must remain not_promoted")
        if record.get("review_status") != "pending_review":
            raise SnapshotError("external records must remain pending_review")
        if record.get("content_sha256") not in (None, ""):
            raise SnapshotError("content hash cannot be asserted from metadata")
        if any(key in record for key in ("content", "body", "raw_text", "credentials")):
            raise SnapshotError("snapshot must contain metadata only")
        matches = record.get("repository_matches", [])
        if not isinstance(matches, list):
            raise SnapshotError("repository_matches must be a list")
        for match in matches:
            if not isinstance(match, dict):
                raise SnapshotError("repository match must be an object")
            if match.get("relationship") not in (
                "keyword_reference", "verified_path", "candidate"
            ):
                raise SnapshotError("repository relationship must be qualified")
            if match.get("authority") != "none":
                raise SnapshotError("repository matches cannot grant authority")
    return records


def summary(payload: object) -> dict:
    records = validate_snapshot(payload)
    return {
        "schema_version": 1,
        "tool": "drive_recovery_snapshot",
        "mode": "read_only",
        "promotion_status": "not_promoted",
        "record_count": len(records),
        "mime_type_counts": dict(sorted(Counter(r["mime_type"] for r in records).items())),
        "matched_record_count": sum(bool(r.get("repository_matches")) for r in records),
        "content_hashes_verified": 0,
        "note": "Metadata-only discovery; no canonical or implementation equivalence asserted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Local PRIVATE snapshot JSON")
    args = parser.parse_args()
    try:
        payload = json.loads(args.snapshot.read_text(encoding="utf-8"))
        report = summary(payload)
    except (OSError, json.JSONDecodeError, SnapshotError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
