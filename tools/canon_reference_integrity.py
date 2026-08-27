#!/usr/bin/env python3
"""Check that every cross-reference in the L2 canon corpus resolves.

Why this exists
---------------
Canon records point at each other constantly — crew_ids, participant_refs,
organization_ids, commanding_officer_id. Nothing checked that the targets exist.
A salvage pass that mints fifteen records and cross-links them into six parents
can leave a dangling pointer in either direction and no test would notice.

The three namespaces
--------------------
The corpus deliberately uses more than one identifier namespace, and a checker
that does not know this reports dozens of false dangles:

  1. **entity** — ``char_alric_tann``, ``polity_velar_imperium``. The record
     identity, carried in ``entity_id``.
  2. **capsule** — ``alric_tann``. The charforge capsule directory name, used in
     relational fields like ``crew_ids`` and ``commanding_officer_id``. A capsule
     is a real artifact under ``canon/L2/entities/<capsule_id>/capsule/``, so
     these are not typos; they are a second, legitimate namespace.
  3. **local keys** — ``doctrine_id``, ``roster_id``, ``office_id``,
     ``engine_conflict_id``. Identifiers within their own scheme that are NOT
     pointers to entity records. ``office_id`` is the instructive one: it appears
     inside a self-describing object that already carries the office title and an
     ``incumbent_entity_id``, so the office is described in place, not referenced
     elsewhere.

The finding this encodes
-----------------------
The entity and capsule namespaces are bridged only by string manipulation —
strip a ``char_`` prefix and hope. No record states that ``alric_tann`` and
``char_alric_tann`` are the same person. That is the same defect class as the
``entity_id`` / ``canonical_id`` split fixed on 2026-08-09: not that two
namespaces exist, but that the bridge between them is implicit. ``--strict``
reports unbridged capsule references so the gap stays visible.

Usage
-----
    python3 tools/canon_reference_integrity.py            # dangles + summary
    python3 tools/canon_reference_integrity.py --strict   # also unbridged bridges
    python3 tools/canon_reference_integrity.py --orphans  # records nothing points at
    python3 tools/canon_reference_integrity.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

#: Fields whose values point at other entity records.
REF_FIELD = re.compile(r"(_id|_ids|_refs)$")

#: Fields ending in _id that are NOT entity pointers — they are keys in their own
#: namespace. Listed explicitly: a checker that guesses produces noise, and noise
#: is what teaches people to ignore checkers.
LOCAL_KEY_FIELDS = {
    # the record's own identity
    "entity_id", "canonical_id",
    # provenance
    "source_id", "doc_id", "record_id", "report_id",
    # in-scheme identifiers, not entity references
    "doctrine_id", "roster_id", "architecture_id", "office_id", "presiding_office_id",
    "mechanic_id", "anchor_id", "schema_id", "protocol_id", "ruling_id",
    "capsule_id", "identity_id", "run_id",
    # designations that look like ids but are hull/registry numbers
    "vessel_id", "class_id", "system_id", "event_id", "artifact_id",
    # engine-side identifiers, deliberately not entity ids
    "engine_faction_id", "engine_conflict_id", "engine_character_id",
}

#: Fields that carry entity references but do NOT end in _id/_ids/_refs.
#:
#: Found by inverting the check — scanning for values that ARE known entity ids in
#: fields the suffix pattern skipped. Without these the orphan count is badly
#: overstated: all three ``conflict`` records looked orphaned at 100% purely
#: because polities cite them in ``conflict_flags``.
ADDITIONAL_REF_FIELDS = {
    "member_polities", "vessel_binding", "peer_organizations",
    "endpoints", "parties", "linked_records", "supersedes", "bears_on",
    "internal_factions", "forwarded_to", "known_subplaces", "attributed_actors",
    "substructures", "related_records", "successor_ids", "predecessor_ids",
}

#: ``conflict_flags`` is MIXED: it holds conflict entity ids
#: (``conflict_union_imperium_border``) alongside free-form markers written by
#: salvage passes (``name_collision_sovereign_nexus``). A field that legitimately
#: carries non-references cannot be a dangling check, so it counts as a soft link
#: only — otherwise the checker reports a curator's own annotation as corruption.
MIXED_FIELDS = {"conflict_flags"}

#: Faction-namespace fields. These name a FACTION (``velar_imperium``), not an
#: entity record, and a faction id often coincides with a polity's unprefixed
#: name. They are counted as soft links when deciding whether a record is an
#: orphan — a polity every character binds to is plainly not disconnected — but
#: they are never reported as dangling, because a faction with no polity record
#: is a legitimate state.
SOFT_LINK_FIELDS = {"faction_bindings", "allegiance", "engine_faction_id",
                    "jurisdiction", "origin_polity_id"} | MIXED_FIELDS

#: Never treated as references: free-text or classification values.
NON_REF_FIELDS = {"tags", "aliases", "forwarding_aliases", "status", "subtype"}

VALUE_SHAPE = re.compile(r"^[a-z][a-z0-9_]{2,}$")
ENTITY_PREFIXES = ("char_", "polity_", "org_", "loc_", "vessel_", "cls_", "eq_",
                   "event_", "conflict_", "species_", "artifact_", "place_",
                   "anomaly_", "office_")


def load_corpus():
    """Return (entity_ids, capsule_ids, records)."""
    entity_ids, records = set(), {}
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or not data.get("entity_kind"):
            continue
        eid = data.get("entity_id") or data.get("canonical_id")
        if eid:
            entity_ids.add(eid)
            records[eid] = (path, data)
    capsule_ids = {
        p.parent.name for p in CANON_L2.glob("entities/*/capsule") if p.is_dir()
    }
    return entity_ids, capsule_ids, records


def _is_ref_field(key: str) -> bool:
    if not key or key in NON_REF_FIELDS or key in LOCAL_KEY_FIELDS:
        return False
    return bool(REF_FIELD.search(key)) or key in ADDITIONAL_REF_FIELDS


def iter_refs(data, include_soft: bool = False):
    """Yield (field, value) for every entity-pointer-shaped value.

    ``include_soft`` adds the faction-namespace fields. They are wanted when
    deciding what is an orphan and unwanted when deciding what is dangling, so
    the caller chooses rather than the function guessing.
    """
    found: list = []

    def walk(node, key):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, key)
        elif isinstance(node, str) and VALUE_SHAPE.match(node):
            if _is_ref_field(key) or (include_soft and key in SOFT_LINK_FIELDS):
                found.append((key, node))

    walk(data, "")
    return found


def alias_collisions(records, entity_ids):
    """Aliases equal to a DIFFERENT record's entity_id.

    Not a reference — a collision. Two records claiming the same handle is how a
    lookup silently returns the wrong entity, which is the failure mode the
    Sovereign Nexus split was created to avoid.
    """
    out = []
    for eid, (_path, data) in records.items():
        for alias in data.get("aliases") or []:
            if isinstance(alias, str) and alias in entity_ids and alias != eid:
                out.append({"record": eid, "alias": alias})
    return out


def faction_index(records):
    """Map faction id -> entity id, read from records' own ``faction_bindings``.

    The faction namespace is NOT derivable from the entity namespace by string
    surgery. ``separatist_confed`` belongs to ``polity_separatist_confederation``
    and ``ai_warlord`` to ``polity_ai_warlord_collective`` — no prefix rule gets
    from one to the other. Canon already states the mapping in each polity's
    ``faction_bindings``, so it is read rather than guessed.

    Only polities claim a faction here. Characters and organizations also carry
    ``faction_bindings``, but as membership, not identity — indexing those would
    make the last-scanned member of a faction its canonical record.
    """
    index = {}
    for eid, (_path, data) in records.items():
        if data.get("entity_kind") != "polity":
            continue
        for faction in data.get("faction_bindings") or []:
            if isinstance(faction, str):
                index.setdefault(faction, eid)
    return index


def bridge(value, entity_ids, factions=None):
    """Resolve a capsule-namespace value to its entity record, if one exists."""
    for prefix in ENTITY_PREFIXES:
        if prefix + value in entity_ids:
            return prefix + value
    if factions:
        return factions.get(value)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true",
                    help="Also report capsule-namespace refs whose bridge is implicit")
    ap.add_argument("--orphans", action="store_true",
                    help="Report entity records that nothing points at")
    ap.add_argument("--json", dest="as_json", action="store_true")
    args = ap.parse_args()

    entity_ids, capsule_ids, records = load_corpus()
    factions = faction_index(records)
    if not entity_ids:
        print("canon-reference-integrity: no L2 entity records found — is CanonRec "
              "checked out?", file=sys.stderr)
        return 1

    dangling, cross_ns = [], []
    pointed_at = set()
    by_field = Counter()

    for eid, (path, data) in records.items():
        for field, value in iter_refs(data, include_soft=True):
            if value == eid:
                continue
            if field in SOFT_LINK_FIELDS:
                # counts toward "is anything connected to this record", never
                # toward dangling: a faction id with no polity record is fine.
                target = value if value in entity_ids else bridge(value, entity_ids, factions)
                if target:
                    pointed_at.add(target)
                continue
            if value in entity_ids:
                pointed_at.add(value)
                continue
            bridged = bridge(value, entity_ids, factions)
            if bridged:
                pointed_at.add(bridged)
                cross_ns.append({"from": eid, "field": field, "value": value,
                                 "resolves_to": bridged,
                                 "capsule_backed": value in capsule_ids})
                by_field[field] += 1
            else:
                dangling.append({"from": eid, "field": field, "value": value,
                                 "file": str(path.relative_to(REPO_ROOT))})

    orphans = sorted(entity_ids - pointed_at)
    collisions = alias_collisions(records, entity_ids)

    if args.as_json:
        print(json.dumps({"entities": len(entity_ids), "capsules": len(capsule_ids),
                          "dangling": dangling, "cross_namespace": cross_ns,
                          "orphans": orphans, "alias_collisions": collisions},
                         indent=2))
        return 1 if dangling else 0

    print(f"canon-reference-integrity: {len(entity_ids)} entity records | "
          f"{len(capsule_ids)} capsules")
    print(f"  dangling references : {len(dangling)}")
    print(f"  cross-namespace refs: {len(cross_ns)} "
          f"(capsule -> entity, all resolvable)")
    print(f"  orphan records      : {len(orphans)} (nothing points at them)")
    print(f"  alias collisions    : {len(collisions)}")

    if collisions:
        print("\nALIAS COLLISIONS — an alias equal to another record's entity_id:")
        for c in collisions:
            print(f"  {c['record']:<38} alias -> {c['alias']}")

    if dangling:
        print("\nDANGLING — the target does not exist in either namespace:")
        for d in dangling:
            print(f"  {d['from']:<38} {d['field']:<26} -> {d['value']}")

    if args.strict and cross_ns:
        print("\nCROSS-NAMESPACE (--strict) — resolvable only by prefix guessing:")
        for field, n in by_field.most_common():
            print(f"  {field:<30} {n}")
        unbacked = [c for c in cross_ns if not c["capsule_backed"]]
        if unbacked:
            print(f"\n  {len(unbacked)} use the capsule form with NO capsule directory:")
            for c in unbacked[:20]:
                print(f"    {c['from']:<36} {c['field']:<24} -> {c['value']}")

    if args.orphans and orphans:
        print(f"\nORPHANS — no other record references these {len(orphans)}:")
        for o in orphans:
            print(f"  {o}")

    return 1 if dangling else 0


if __name__ == "__main__":
    raise SystemExit(main())
