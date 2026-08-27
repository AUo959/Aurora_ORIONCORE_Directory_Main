"""Every controlled vocabulary in the validator must cover committed canon.

The defect class this guards
----------------------------
A vocabulary encoded in a checker drifts from the canon it checks, and fails in
one of two ways — both of which hide:

  * **loudly, which is the same as silently.** ``VALID_L2_POLITY_SUBTYPES``
    shared ZERO members with the subtypes canon actually used, so all 19 polity
    records raised INVALID_POLITY_SUBTYPE. A warning that fires on every record
    is not a signal; it teaches people to scroll past the checker.
  * **silently.** ``VALID_ENTITY_KINDS`` was missing eight kinds in active use,
    so 77 of 189 canonical records were rejected on ``entity_kind`` alone —
    including every ``mobile_asset``, which is the kind FABRIC P2 exists to
    police.

Three instances surfaced on 2026-08-09 alone (status vocabulary, entity kinds,
polity subtypes), which is what makes it a class rather than three bugs. The
governing principle, already written into ``VALID_ENTITY_KINDS``: **canon is the
source of truth for the vocabulary, not the other way round.**

These tests fail when canon starts using a value the validator does not know.
That is the intended direction — a new canonical subtype should force a
deliberate decision (widen the vocabulary, or reclassify the record), not
produce background noise nobody reads.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(
    0, str(REPO_ROOT / "skills" / "aurora-canon-reconciler" / "scripts")
)
sys.path.insert(0, str(REPO_ROOT / "tools"))

CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

pytestmark = pytest.mark.skipif(
    not CANON_L2.is_dir(), reason="CanonRec not checked out"
)


def _records():
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("entity_kind"):
            yield path, data


def _values_in_canon(field, kind=None):
    """Collect the distinct values canon uses for a field, with example records."""
    seen = defaultdict(list)
    for path, data in _records():
        if kind and data.get("entity_kind") != kind:
            continue
        value = data.get(field)
        if isinstance(value, str) and value:
            seen[value].append(data.get("entity_id") or path.name)
    return seen


def _assert_covered(field, vocabulary, vocab_name, kind=None):
    unknown = {
        value: refs[:3]
        for value, refs in _values_in_canon(field, kind).items()
        if value not in vocabulary
    }
    assert not unknown, (
        f"Committed canon uses {field} values that {vocab_name} does not know:\n"
        + "\n".join(f"  {v!r} — e.g. {', '.join(r)}" for v, r in sorted(unknown.items()))
        + f"\n\nCanon is the source of truth for the vocabulary. Either add these "
          f"to {vocab_name}, or reclassify the records — but the validator must "
          f"not warn on the canon it exists to validate."
    )


# --- validate_entity.py vocabularies -------------------------------------

def test_entity_kinds_cover_canon():
    """The regression that rejected 77 of 189 records, including every vessel."""
    from validate_entity import VALID_ENTITY_KINDS
    _assert_covered("entity_kind", VALID_ENTITY_KINDS, "VALID_ENTITY_KINDS")


def test_certainty_tags_cover_canon():
    from validate_entity import VALID_CERTAINTY_TAGS
    _assert_covered("certainty", VALID_CERTAINTY_TAGS, "VALID_CERTAINTY_TAGS")


def test_polity_subtypes_cover_canon():
    """The regression that fired on 19 of 19 polity records."""
    from validate_entity import VALID_L2_POLITY_SUBTYPES
    _assert_covered("subtype", VALID_L2_POLITY_SUBTYPES,
                    "VALID_L2_POLITY_SUBTYPES", kind="polity")


def test_species_subtypes_cover_canon():
    from validate_entity import VALID_L2_SPECIES_SUBTYPES
    _assert_covered("subtype", VALID_L2_SPECIES_SUBTYPES,
                    "VALID_L2_SPECIES_SUBTYPES", kind="species")


# --- fabric_invariants_check.py vocabularies ------------------------------

def test_status_vocabulary_covers_canon_per_kind():
    """C2 status vocabulary — the first instance of this defect class.

    A flat ``STATUS_VOCAB`` applied one kind's lifecycle words to every kind, so
    a species being ``extant`` looked like a violation. It is now keyed by kind;
    this checks each kind's vocabulary against the records of that kind.
    """
    from fabric_invariants_check import status_vocab_for

    unknown = defaultdict(set)
    for _path, data in _records():
        kind, status = data.get("entity_kind"), data.get("status")
        if isinstance(status, str) and status:
            if status not in status_vocab_for(kind):
                unknown[kind].add(status)
    assert not unknown, (
        "Canon uses status values outside STATUS_VOCAB_BY_KIND:\n"
        + "\n".join(f"  {k}: {sorted(v)}" for k, v in sorted(unknown.items()))
    )


# --- the guard on the guard ----------------------------------------------

def test_location_subtype_drift_is_reported_not_hidden():
    """Location subtypes are known to drift; the drift must stay visible.

    Unlike the vocabularies above, this one is NOT asserted clean. Canon uses
    descriptive location subtypes (``orbital_station``, ``ai_polity_interface_node``)
    while the validator lists structural ones, and a handful still warn. That is
    a real open question about how locations should be classified — recorded
    here so it is a known quantity with a number attached, rather than warning
    noise nobody counts.

    If this count grows, the classification decision is overdue.
    """
    from validate_entity import VALID_L2_LOCATION_SUBTYPES
    drifting = {
        v for v in _values_in_canon("subtype", kind="location")
        if v not in VALID_L2_LOCATION_SUBTYPES
    }
    assert len(drifting) <= 8, (
        f"Location subtype drift has grown to {len(drifting)} distinct values: "
        f"{sorted(drifting)}. Decide the classification scheme rather than "
        f"raising this ceiling again."
    )
