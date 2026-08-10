"""Every canon entity record must be findable by a single identity key.

Field finding 2026-08-09: 23 `mobile_asset` records keyed identity as `canonical_id`
while the other 166 canon records used `entity_id`, with zero overlap. Six of the seven
tools that walk the canon tree index on exactly one of those keys, so each silently
saw a partial corpus.

That is not hypothetical. It produced two wrong results in a single session:

  * a full-canon validation sweep reported 166 records when the real count is 189 —
    every vessel was skipped, and the run was reported as clean coverage;
  * capsule `location_binding` targets pointing at `vessel_gu_001` looked like ghost
    destinations, because the resolver's id index never contained any vessel.

Silent partial coverage is worse than a crash: the tool reports success. These tests
pin the invariant that makes it impossible.

Resolution was additive — vessels gained `entity_id` (same value) and kept
`canonical_id`, so entity_id-only readers are fixed and canonical_id-only readers
(tools/character_capsule_adapter.py) keep working.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"


def _entity_records() -> list[tuple[Path, dict]]:
    """Every canon *entity* record. Capsules are a different artifact and excluded."""
    out = []
    if not CANON_L2.exists():
        return out
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("entity_kind"):
            out.append((path, data))
    return out


def test_every_entity_record_has_entity_id():
    """One key finds everything — no tool should need to know about a second spelling."""
    records = _entity_records()
    if not records:
        return  # CanonRec not checked out
    missing = [p.name for p, d in records if not d.get("entity_id")]
    assert not missing, f"entity records without entity_id: {missing}"


def test_identity_keys_agree_where_both_are_present():
    """canonical_id is retained for back-compat; it must never disagree with entity_id."""
    mismatched = [
        (p.name, d.get("entity_id"), d.get("canonical_id"))
        for p, d in _entity_records()
        if d.get("canonical_id") and d.get("canonical_id") != d.get("entity_id")
    ]
    assert not mismatched, f"identity keys disagree: {mismatched}"


def test_entity_ids_are_unique():
    seen: dict[str, str] = {}
    duplicates = []
    for path, data in _entity_records():
        eid = data.get("entity_id")
        if not eid:
            continue
        if eid in seen:
            duplicates.append((eid, seen[eid], path.name))
        seen[eid] = path.name
    assert not duplicates, f"duplicate entity_ids: {duplicates}"


def test_an_entity_id_index_covers_the_whole_corpus():
    """The regression itself: indexing on entity_id alone must not lose records.

    Guards the exact failure that reported 166/189 as full coverage.
    """
    records = _entity_records()
    if not records:
        return
    index = {d["entity_id"] for _, d in records if d.get("entity_id")}
    assert len(index) == len(records), (
        f"entity_id index covers {len(index)} of {len(records)} records — "
        "a tool indexing on entity_id would silently skip the remainder"
    )


def test_vessels_are_reachable_by_entity_id():
    """Concrete case: capsule bindings target vessel_gu_001 by id."""
    records = _entity_records()
    if not records:
        return
    index = {d["entity_id"] for _, d in records if d.get("entity_id")}
    vessels = [d for _, d in records if d.get("entity_kind") == "mobile_asset"]
    if not vessels:
        return
    assert "vessel_gu_001" in index, "the Judicator Prime must be findable by entity_id"
    unreachable = [v.get("canonical_id") for v in vessels if v.get("entity_id") not in index]
    assert not unreachable, f"vessels unreachable by entity_id: {unreachable}"
