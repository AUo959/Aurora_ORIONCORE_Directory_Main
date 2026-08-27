"""Every cross-reference in the L2 canon corpus must resolve to a real record.

Nothing checked this before 2026-08-09. A salvage pass that mints records and
cross-links them into parents could leave a pointer to nowhere in either
direction and no test would notice — and by then several passes had run.

The sweep that introduced these tests found 0 genuine dangles, which is the
result worth locking in. What it did find was structural: the corpus uses three
identifier namespaces, and 30 references cross between two of them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

pytestmark = pytest.mark.skipif(
    not CANON_L2.is_dir(), reason="CanonRec not checked out"
)


@pytest.fixture(scope="module")
def corpus():
    import canon_reference_integrity as cri
    entity_ids, capsules, records = cri.load_corpus()
    return cri, entity_ids, capsules, records


@pytest.fixture(scope="module")
def factions(corpus):
    cri, _e, _c, records = corpus
    return cri.faction_index(records)


def test_no_dangling_references(corpus, factions):
    """The headline invariant: no reference points at a record that isn't there."""
    cri, entity_ids, _capsules, records = corpus
    dangling = []
    for eid, (path, data) in records.items():
        for field, value in cri.iter_refs(data):
            if value == eid or value in entity_ids:
                continue
            if field in cri.SOFT_LINK_FIELDS:
                continue
            if cri.bridge(value, entity_ids, factions) is None:
                dangling.append(f"{eid}.{field} -> {value}  ({path.name})")
    assert not dangling, (
        "References with no target in either namespace:\n  "
        + "\n  ".join(sorted(dangling))
    )


def test_every_capsule_has_an_entity_record(corpus):
    """A capsule with no entity record dangles off the entity graph.

    This was a real gap: 29 capsule-only characters were found with no entity
    record at all, and had to be built in a dedicated pass.
    """
    cri, entity_ids, capsules, _records = corpus
    unbacked = [
        c for c in sorted(capsules)
        if c not in entity_ids and cri.bridge(c, entity_ids) is None
    ]
    assert not unbacked, f"Capsules with no entity record: {unbacked}"


def test_capsule_bridge_is_explicit(corpus):
    """Relational fields refer to entities by CAPSULE id; records must say so.

    Canon points at people by capsule id (``crew_ids: [alric_tann]``) while the
    record identity is ``char_alric_tann``. Before ``capsule_id`` was added, the
    only way to connect them was to strip a prefix and hope. This test pins the
    bridge so it cannot silently regress to guessing.
    """
    cri, entity_ids, capsules, records = corpus
    missing = []
    for capsule in sorted(capsules):
        target = capsule if capsule in entity_ids else cri.bridge(capsule, entity_ids)
        if target is None:
            continue  # covered by test_every_capsule_has_an_entity_record
        _path, data = records[target]
        if data.get("capsule_id") != capsule:
            missing.append(f"{target} (capsule {capsule})")
    assert not missing, (
        "Entity records backing a capsule but not declaring capsule_id:\n  "
        + "\n  ".join(missing)
    )


def test_local_key_fields_are_not_treated_as_pointers(corpus):
    """`office_id` and friends are keys in their own scheme, not entity refs.

    Guarding the exclusion list directly: a checker that treats these as pointers
    reports confident nonsense. ``office_id`` is the instructive case — it sits
    inside an object that already carries the office title and an
    ``incumbent_entity_id``, so the office is described in place.
    """
    import canon_reference_integrity as cri
    for field in ("office_id", "doctrine_id", "roster_id", "engine_conflict_id",
                  "vessel_id", "class_id", "source_id"):
        assert field in cri.LOCAL_KEY_FIELDS, (
            f"{field} must stay excluded from pointer checking, or the sweep "
            f"reports false dangles."
        )


def test_species_origin_polity_resolves_to_a_polity_record(corpus):
    """`origin_polity_id` carries the faction form; the entity form must exist too.

    The four species records point at their origin polity by faction-binding
    string (``velar_imperium``), which is meaningful but is not an entity id.
    ``origin_polity_entity_id`` was added alongside rather than rewriting it —
    the same additive pattern as ``entity_id`` beside ``canonical_id``.
    """
    _cri, entity_ids, _capsules, records = corpus
    problems = []
    for eid, (_path, data) in records.items():
        if data.get("entity_kind") != "species" or not data.get("origin_polity_id"):
            continue
        resolved = data.get("origin_polity_entity_id")
        if resolved is None and data["origin_polity_id"] in entity_ids:
            continue
        if resolved not in entity_ids:
            problems.append(f"{eid}: origin_polity_id={data['origin_polity_id']!r} "
                            f"origin_polity_entity_id={resolved!r}")
    assert not problems, "Species origin polity does not resolve:\n  " + "\n  ".join(problems)


def test_faction_namespace_is_indexed_not_guessed(corpus, factions):
    """Faction ids do not reduce to entity ids by any prefix rule.

    ``separatist_confed`` belongs to ``polity_separatist_confederation`` and
    ``ai_warlord`` to ``polity_ai_warlord_collective``. String surgery cannot get
    from one to the other, so the mapping is read out of each polity's
    ``faction_bindings``. This test pins the two cases that proved it, and that
    only polities are indexed — characters and organizations carry
    ``faction_bindings`` as membership, so indexing them would let the
    last-scanned member masquerade as the faction's canonical record.
    """
    cri, entity_ids, _capsules, records = corpus
    for faction, expected in (("separatist_confed", "polity_separatist_confederation"),
                              ("ai_warlord", "polity_ai_warlord_collective")):
        if expected not in entity_ids:
            pytest.skip(f"{expected} not in corpus")
        assert factions.get(faction) == expected
        assert cri.bridge(faction, entity_ids) is None, (
            f"{faction!r} must NOT resolve by prefix — if it does, the index is "
            f"masking a rule and the test no longer proves anything."
        )
        assert cri.bridge(faction, entity_ids, factions) == expected

    for eid in factions.values():
        assert records[eid][1].get("entity_kind") == "polity"


def test_mixed_fields_are_not_dangling_checks(corpus):
    """`conflict_flags` holds curator annotations as well as entity ids.

    ``name_collision_sovereign_nexus`` is a marker written by a salvage pass, not
    a broken pointer. Treating the field as a hard reference check reports the
    curator's own annotation as corruption.
    """
    import canon_reference_integrity as cri
    assert "conflict_flags" in cri.MIXED_FIELDS
    assert "conflict_flags" in cri.SOFT_LINK_FIELDS
