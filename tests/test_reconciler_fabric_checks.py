"""FABRIC_INVARIANTS P1/P2/P4 enforcement in aurora-canon-reconciler.

Implements the reconciler half of the 2026-07-21 ruling batch
(canon/L2/mechanics/FABRIC_INVARIANTS__v0.1__2026-07-21.md verification table):

  P1  entity canonical_position_status must not exceed its map authority row
  P2  moving entities never hold fixed coordinates; placement_rule required
  P4  canon promotions citing movement/cross-region events must cite route/drive

tools/fabric_invariants_check.py enforces T/P/C statically over committed canon;
these checks run at validation time, before content becomes canon. The two must
agree — so the semantics here are pinned to the linter's, and these tests exist
to keep them from drifting apart.

Field finding 2026-08-09: a first draft of P4 matched bare "deploy"/"ftl"/"jump"
and fired on capability text ("rapid sentinel deployment"), a court "deployed"
aboard a ship, and a region described as an "FTL-disruption anomaly" — 11 findings,
9 of them false. A promotion gate that cries wolf is a gate someone switches off,
so P4 now requires event context AND an event-shaped phrase. The false-positive
tests below are the guard.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "aurora-canon-reconciler" / "scripts"))

from validate_entity import (  # noqa: E402
    ValidationReport,
    check_fabric_invariants,
    load_map_authority_rows,
)


def _run(data: dict, ek: str, context: dict | None = None) -> ValidationReport:
    report = ValidationReport(data.get("name", "test"), "L2", ek)
    check_fabric_invariants(data, ek, report, context)
    return report


def _codes(report: ValidationReport) -> set[str]:
    return {f["code"] for f in report.findings}


def _blocks(report: ValidationReport) -> set[str]:
    return {f["code"] for f in report.blocks}


# ── P2: moving entities ───────────────────────────────────────────────────

def test_p2_mobile_asset_with_fixed_placement_blocks():
    r = _run({"name": "Umbra Stalker", "region_id": "loc_zone_core"}, "mobile_asset")
    assert "FABRIC_P2_MOVING_ENTITY_FIXED_PLACEMENT" in _blocks(r)


def test_p2_covers_every_fixed_placement_field():
    for field in ("region_id", "coordinates", "position", "fixed_position"):
        r = _run({"name": "V", field: "somewhere"}, "mobile_asset")
        assert "FABRIC_P2_MOVING_ENTITY_FIXED_PLACEMENT" in _blocks(r), field


def test_p2_mobile_asset_kind_is_covered():
    """Regression: 'mobile_asset' is the kind CanonRec actually uses.

    It was absent from MOVING_ENTITY_KINDS, so P2 was silently unenforced for
    all 23 real moving entities in canon.
    """
    r = _run({"name": "V", "coordinates": [1, 2]}, "mobile_asset")
    assert r.blocks, "mobile_asset must be treated as a moving entity"


def test_p2_missing_placement_rule_warns_but_does_not_block():
    r = _run({"name": "V"}, "mobile_asset")
    assert "FABRIC_P2_NO_PLACEMENT_RULE" in _codes(r)
    assert not r.blocks


def test_p2_compliant_mobile_asset_is_clean():
    r = _run({"name": "V", "placement_rule": "patrols the Kharis corridor"}, "mobile_asset")
    assert not r.findings


def test_p2_does_not_apply_to_static_kinds():
    r = _run({"name": "A World", "region_id": "loc_zone_core"}, "location")
    assert "FABRIC_P2_MOVING_ENTITY_FIXED_PLACEMENT" not in _codes(r)


# ── P1: map primacy ───────────────────────────────────────────────────────

_ROWS = {
    "khalrix-3": {"name": "Khalrix-3", "status": "STAGING", "notes": "Toxic wasteland"},
    "vel-surak": {"name": "Vel-Surak", "status": "CANON", "notes": "Placed"},
    "kaelor's rift": {"name": "Kaelor's Rift", "status": "CANON", "notes": "placement TBD"},
}


def _ctx_rows(monkeypatched_rows):
    """check_fabric_invariants loads rows via context; emulate a loaded table."""
    import validate_entity as ve
    ve.load_map_authority_rows = lambda ctx: monkeypatched_rows  # type: ignore
    return {"context_root": "/nonexistent"}


def test_p1_canon_position_against_staging_map_row_blocks():
    import validate_entity as ve
    original = ve.load_map_authority_rows
    try:
        ctx = _ctx_rows(_ROWS)
        r = _run({"name": "Khalrix-3", "canonical_position_status": "canon"}, "location", ctx)
        assert "FABRIC_P1_POSITION_EXCEEDS_MAP" in _blocks(r)
    finally:
        ve.load_map_authority_rows = original


def test_p1_canon_position_against_canon_map_row_is_clean():
    import validate_entity as ve
    original = ve.load_map_authority_rows
    try:
        ctx = _ctx_rows(_ROWS)
        r = _run({"name": "Vel-Surak", "canonical_position_status": "canon"}, "location", ctx)
        assert "FABRIC_P1_POSITION_EXCEEDS_MAP" not in _codes(r)
    finally:
        ve.load_map_authority_rows = original


def test_p1_tbd_note_counts_as_unresolved():
    import validate_entity as ve
    original = ve.load_map_authority_rows
    try:
        ctx = _ctx_rows(_ROWS)
        r = _run({"name": "Kaelor's Rift", "canonical_position_status": "canon"}, "location", ctx)
        assert "FABRIC_P1_POSITION_EXCEEDS_MAP" in _blocks(r)
    finally:
        ve.load_map_authority_rows = original


def test_p1_unplaced_entity_never_blocks():
    import validate_entity as ve
    original = ve.load_map_authority_rows
    try:
        ctx = _ctx_rows(_ROWS)
        r = _run({"name": "Khalrix-3", "canonical_position_status": "unplaced"}, "location", ctx)
        assert not r.blocks
    finally:
        ve.load_map_authority_rows = original


def test_p1_superseded_records_carry_no_placement_obligation():
    """Linter parity: alias-forward records are skipped."""
    import validate_entity as ve
    original = ve.load_map_authority_rows
    try:
        ctx = _ctx_rows(_ROWS)
        r = _run({"name": "Khalrix-3", "certainty": "SUPERSEDED",
                  "canonical_position_status": "canon"}, "location", ctx)
        assert not r.blocks
    finally:
        ve.load_map_authority_rows = original


def test_p1_degrades_to_info_when_table_missing():
    """The skill must stay usable outside a CanonRec checkout — fail open, loudly."""
    r = _run({"name": "Somewhere", "canonical_position_status": "canon"}, "location", None)
    assert "FABRIC_P1_MAP_UNVERIFIED" in _codes(r)
    assert not r.blocks


# ── P4: movement promotions must cite a route ─────────────────────────────

def _with_route_registry(exists: bool):
    """P4 severity depends on whether canon has anything citable."""
    import validate_entity as ve
    ve.route_registry_exists = lambda ctx: exists  # type: ignore


def test_p4_event_movement_without_route_blocks_when_registry_exists():
    import validate_entity as ve
    original = ve.route_registry_exists
    try:
        _with_route_registry(True)
        r = _run({
            "name": "Dark Star Incident",
            "certainty": "CANON",
            "canonical_sequence": ["The Shadow Fleet withdrew from the Lethan system."],
        }, "event")
        assert "FABRIC_P4_MOVEMENT_WITHOUT_ROUTE" in _blocks(r)
    finally:
        ve.route_registry_exists = original


def test_p4_warns_instead_of_blocking_when_no_route_registry_exists():
    """An exit condition nobody can meet is a defect, not a gate.

    Canon contains no route/corridor/drive entity as of 2026-08-09, so a hard
    BLOCK would make every movement event permanently unpromotable with no
    compliant action available. P4 self-activates instead.
    """
    import validate_entity as ve
    original = ve.route_registry_exists
    try:
        _with_route_registry(False)
        r = _run({
            "name": "Dark Star Incident",
            "certainty": "CANON",
            "canonical_sequence": ["The Shadow Fleet withdrew from the Lethan system."],
        }, "event")
        assert "FABRIC_P4_NO_ROUTE_REGISTRY" in _codes(r)
        assert not r.blocks, "must not block on an unsatisfiable requirement"
    finally:
        ve.route_registry_exists = original


def test_p4_is_now_enforceable_against_real_canon():
    """P4 went live on 2026-08-09.

    The Hollow Expanse is typed "region / lawless corridor" — a genuine corridor
    referent that the original subtype-only detector missed. Once location_type is
    considered, a registry exists and P4 escalates from WARN to BLOCK.
    """
    from validate_entity import route_registry_exists
    canon_dir = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
    if not canon_dir.exists():
        return
    assert route_registry_exists({"context_root": str(canon_dir)}) is True


def test_corridor_typed_location_counts_as_a_route_registry(tmp_path=None):
    """A corridor expressed via location_type must register."""
    import json as _json
    import tempfile
    from pathlib import Path as _Path
    from validate_entity import route_registry_exists

    tmp = _Path(tempfile.mkdtemp())
    (tmp / "loc.json").write_text(_json.dumps({
        "entity_id": "loc_x", "location_type": "region / lawless corridor",
    }))
    assert route_registry_exists({"context_root": str(tmp)}) is True


def test_p4_satisfied_by_an_explicit_route_exemption():
    """Answering the route question honestly satisfies P4; inventing is not required.

    Canon attests transits between named places without ever naming the corridor
    between them. Demanding a route name there would force invention — the exact
    failure canon reconciliation exists to prevent.
    """
    import validate_entity as ve
    original = ve.route_registry_exists
    try:
        _with_route_registry(True)
        r = _run({
            "name": "Dark Star Incident",
            "certainty": "CANON",
            "canonical_sequence": ["The Shadow Fleet withdrew from the Lethan system."],
            "route_exemption": {
                "status": "no_canonical_route_established",
                "endpoints": ["place_kharis_sector", "place_lethan_system"],
            },
        }, "event")
        assert not r.blocks
    finally:
        ve.route_registry_exists = original


def test_p4_exemption_must_be_present_not_empty():
    import validate_entity as ve
    original = ve.route_registry_exists
    try:
        _with_route_registry(True)
        r = _run({
            "name": "Dark Star Incident",
            "certainty": "CANON",
            "canonical_sequence": ["The Shadow Fleet withdrew from the Lethan system."],
            "route_exemption": {},
        }, "event")
        assert "FABRIC_P4_MOVEMENT_WITHOUT_ROUTE" in _blocks(r)
    finally:
        ve.route_registry_exists = original


def test_p4_satisfied_by_a_route_citation():
    r = _run({
        "name": "Dark Star Incident",
        "certainty": "CANON",
        "canonical_sequence": ["The Shadow Fleet withdrew from the Lethan system."],
        "route_ref": "route_kharis_corridor",
    }, "event")
    assert not r.blocks


def test_p4_only_gates_at_promotion():
    r = _run({
        "name": "Draft Event",
        "certainty": "STAGING",
        "canonical_sequence": ["The fleet withdrew from the system."],
    }, "event")
    assert not r.blocks, "P4 is a promotion gate; drafts must pass"


def test_p4_ignores_capability_text_on_a_ship_class():
    """Regression: 'rapid sentinel deployment' is a capability, not an event."""
    r = _run({
        "name": "Sentinel Class",
        "certainty": "CANON",
        "role": "covert operations, rapid sentinel deployment, counterinsurgency",
    }, "ship_class")
    assert "FABRIC_P4_MOVEMENT_WITHOUT_ROUTE" not in _codes(r)


def test_p4_ignores_property_text_on_a_location():
    """Regression: an 'FTL-disruption anomaly' is a property, not a transit."""
    r = _run({
        "name": "Kaelor's Rift",
        "certainty": "CANON",
        "description": "FTL-disruption anomaly region and the site of a canonical battle.",
    }, "location")
    assert "FABRIC_P4_MOVEMENT_WITHOUT_ROUTE" not in _codes(r)


def test_p4_requires_event_context_not_just_a_phrase():
    """A movement phrase with no event context is description, not a claim."""
    r = _run({
        "name": "Some Org",
        "certainty": "CANON",
        "description": "Its members relocated often in the old days.",
    }, "organization")
    assert "FABRIC_P4_MOVEMENT_WITHOUT_ROUTE" not in _codes(r)


# ── linter parity ─────────────────────────────────────────────────────────

def test_every_committed_canon_record_validates_clean():
    """The validator must not report well-formed canon as BLOCKED.

    Field finding 2026-08-09: it reported 100% of canon blocked. REQUIRED_FIELDS
    demanded 'canonical_id' and 'canonical_name' — fields present in 0 of 166
    records — plus 'subtype' on locations (which use location_type) and species
    (which have none), 'faction' on characters (which use faction_bindings), and
    'government_type' (which never appears). SUPERSEDED was missing from the
    certainty vocabulary, so every alias-forward record failed too.

    A validator that rejects valid canon gets bypassed, and then it protects
    nothing. This test is the guard.
    """
    import json
    from validate_entity import validate_entity

    canon_dir = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
    if not canon_dir.exists():
        return

    kind_to_type = {
        "polity": "polity", "species": "species", "character": "character",
        "location": "location", "organization": "organization",
        "mobile_asset": "mobile_asset", "ship_class": "ship_class",
        "event": "event", "conflict": "conflict", "equipment": "equipment",
        "place": "place", "anomaly": "anomaly", "report": "report",
    }
    context = {"context_root": str(canon_dir)}
    blocked = []
    for path in canon_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or "entity_id" not in data:
            continue
        entity_type = kind_to_type.get(data.get("entity_kind"), "character")
        report = validate_entity(data, "L2", entity_type, context)
        if report.blocks:
            blocked.append((data["entity_id"], [b["code"] for b in report.blocks]))

    assert not blocked, f"committed canon must validate clean; blocked: {blocked[:8]}"


def test_certainty_vocabulary_matches_canonrec():
    """CERTAINTY_TAGS.md is the authoritative vocabulary; stay in sync with it."""
    import re
    from validate_entity import VALID_CERTAINTY_TAGS

    tags_file = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "CERTAINTY_TAGS.md"
    if not tags_file.exists():
        return
    known = set(re.findall(
        r"\b(CANON_PROMOTE|CANON|STAGING|UNCONFIRMED|LEGEND_CONTESTED|"
        r"SUPERSEDED|LOCKED_POSITION|PLACED|APPROX)\b",
        tags_file.read_text(encoding="utf-8"),
    ))
    missing = sorted(known - VALID_CERTAINTY_TAGS)
    assert not missing, f"certainty tags in CERTAINTY_TAGS.md but not accepted: {missing}"


def test_empty_list_counts_as_an_explicit_answer():
    """`faction_bindings: []` states 'unaffiliated' — it is not an omission."""
    from validate_entity import _field_satisfied
    assert _field_satisfied({"faction_bindings": []}, "faction_bindings") is True
    assert _field_satisfied({}, "faction_bindings") is False
    assert _field_satisfied({"faction_bindings": None}, "faction_bindings") is False
    assert _field_satisfied({"name": "   "}, "name") is False


def test_precursor_polities_are_not_required_to_have_a_government():
    """A vanished civilization has no known government; demanding one invites invention."""
    from validate_entity import validate_entity
    data = {
        "entity_id": "polity_test_precursor", "name": "Test Precursors",
        "aliases": [], "entity_kind": "polity", "certainty": "CANON",
        "doc_sources": ["codex"], "subtype": "precursor_civilization",
    }
    report = validate_entity(data, "L2", "polity", None)
    codes = [b["code"] for b in report.blocks]
    assert "MISSING_REQUIRED" not in codes, report.blocks


def test_entity_kind_vocabulary_covers_committed_canon():
    """The validator must accept every entity_kind canon actually uses.

    Field finding 2026-08-09: VALID_ENTITY_KINDS never grew with canon, so 77 of
    189 committed records were rejected on entity_kind alone — including every
    mobile_asset, the kind P2 exists to police. A gate that rejects valid canon
    gets bypassed, which defeats the point of adding gates.
    """
    import json
    from validate_entity import VALID_ENTITY_KINDS

    canon_dir = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
    if not canon_dir.exists():
        return  # CanonRec not checked out

    used = set()
    for path in canon_dir.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("entity_kind"):
            used.add(data["entity_kind"])

    missing = sorted(used - VALID_ENTITY_KINDS)
    assert not missing, f"entity kinds in canon but rejected by the validator: {missing}"


def test_authority_table_parses_from_real_canon_when_present():
    lat_dir = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
    if not lat_dir.exists():
        return  # CanonRec not checked out; nothing to assert
    rows = load_map_authority_rows({"context_root": str(lat_dir)})
    assert rows, "Location Authority Table should parse from CanonRec"
    assert any("vel" in k for k in rows), "expected Velar rows in the table"
