"""detect_layer_and_type must return the record's actual kind, not fall back to 'location'.

Regression cover for a defect found 2026-08-09 while promoting the Battle of
Kaelor's Rift. The detector enumerated nine entity kinds and ended in
`return "L2", "location"  # default L2`. Every other kind in canon — event,
organization, mobile_asset, ship_class, equipment, place, conflict, report —
was therefore validated *as a location*: location subtype vocabulary was applied
to them, and their own REQUIRED_FIELDS entries (which exist) were unreachable.

It surfaced as a nonsense warning: an event record was told its subtype
"fleet_engagement_with_sentinel_boarding_action" was not a valid *location*
subtype, expected one of [anomaly, facility, moon, planet, region, route,
station, system, unknown].

Same defect class as the flat STATUS_VOCAB (one kind's vocabulary applied to
all kinds). A concrete fallback is what made it silent, so these tests pin the
absence of one as much as the mapping itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent
        / "skills" / "aurora-canon-reconciler" / "scripts"),
)

from validate_entity import (  # noqa: E402
    VALID_ENTITY_KINDS,
    REQUIRED_FIELDS,
    detect_layer_and_type,
)


@pytest.mark.parametrize("kind", sorted(VALID_ENTITY_KINDS))
def test_every_canonical_kind_detects_as_itself(kind):
    """No canonical kind may be silently reported as some other kind."""
    layer, etype = detect_layer_and_type({"entity_id": "x", "entity_kind": kind})
    assert layer == "L2"
    assert etype == kind, (
        f"entity_kind {kind!r} detected as {etype!r}. A kind that reports as "
        f"another kind gets that kind's checks — the original bug."
    )


@pytest.mark.parametrize(
    "kind", ["event", "organization", "mobile_asset", "ship_class",
             "equipment", "place", "conflict", "report"],
)
def test_kinds_that_used_to_fall_through_are_not_locations(kind):
    """The eight kinds the old if-chain never named."""
    _, etype = detect_layer_and_type({"entity_id": "x", "entity_kind": kind})
    assert etype != "location"


def test_event_record_is_not_checked_as_a_location():
    """The record that exposed the bug."""
    _, etype = detect_layer_and_type({
        "entity_id": "event_battle_of_kaelors_rift",
        "entity_kind": "event",
        "subtype": "fleet_engagement_with_sentinel_boarding_action",
    })
    assert etype == "event"


def test_per_kind_required_fields_are_reachable():
    """REQUIRED_FIELDS entries are useless if the detector never returns the key."""
    unreachable = [
        kind for kind in REQUIRED_FIELDS["L2"]
        if kind != "_base"
        and kind in VALID_ENTITY_KINDS
        and detect_layer_and_type(
            {"entity_id": "x", "entity_kind": kind})[1] != kind
    ]
    assert not unreachable, f"REQUIRED_FIELDS entries never reached: {unreachable}"


def test_character_detection_survives_the_rewrite():
    """entity_kind wins; the legacy 'faction' signature still works without one."""
    assert detect_layer_and_type(
        {"entity_id": "x", "entity_kind": "character"})[1] == "character"
    assert detect_layer_and_type(
        {"canonical_id": "x", "faction": "galactic_union"})[1] == "character"


def test_mechanic_signature_survives_the_rewrite():
    assert detect_layer_and_type(
        {"canonical_id": "x", "mechanic_id": "M1"})[1] == "mechanic"


def test_unknown_kind_is_not_laundered_into_a_valid_one():
    """An unknown kind must reach INVALID_ENTITY_KIND, not be renamed to 'location'."""
    _, etype = detect_layer_and_type({"entity_id": "x", "entity_kind": "spaceship"})
    assert etype == "spaceship"
    assert etype not in VALID_ENTITY_KINDS


def test_canonical_id_without_entity_kind_still_defaults():
    """The one legitimate fallback: no kind to go on at all."""
    assert detect_layer_and_type({"canonical_id": "x"})[1] == "location"


def test_polity_subtype_vocabulary_covers_committed_canon():
    """A vocabulary that rejects every canonical record is noise, not a check.

    Canon's polity subtypes and the validator's list had zero overlap on
    2026-08-09: all 19 committed polity records raised INVALID_POLITY_SUBTYPE.
    Same principle as VALID_ENTITY_KINDS — canon is the source of truth.
    """
    import json

    from validate_entity import VALID_L2_POLITY_SUBTYPES

    entities = (Path(__file__).resolve().parent.parent
                / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2" / "entities")
    if not entities.is_dir():
        pytest.skip("CanonRec not checked out")

    # Scan by entity_kind across ALL entity directories, not just entities/polities.
    # A first pass scanned only that directory and reported the vocabulary clean
    # while four polity records — the precursor civilizations, which live under
    # entities/precursors/ — were still warning. The validator dispatches on KIND,
    # so a directory-scoped test cannot see what the validator sees.
    unknown = {}
    for path in entities.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or data.get("entity_kind") != "polity":
            continue
        subtype = data.get("subtype")
        if subtype and subtype not in VALID_L2_POLITY_SUBTYPES:
            unknown.setdefault(subtype, []).append(path.parent.name)

    assert not unknown, (
        f"Committed canon uses polity subtypes the validator rejects: "
        f"{ {k: sorted(set(v)) for k, v in unknown.items()} }. Add them, or "
        f"reclassify the records — but the validator must not warn on the canon "
        f"it exists to validate."
    )
