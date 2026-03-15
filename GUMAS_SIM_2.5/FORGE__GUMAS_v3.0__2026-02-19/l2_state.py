#!/usr/bin/env python3
"""
Deterministic L2 registry and additive export bundle.

Phase 1 goals:
- Normalize named L2 characters, organizations, and locations
- Preserve source certainty and provenance
- Bind named entities onto the existing 13-faction runtime
- Avoid any changes to simulation math
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


_THIS_DIR = Path(__file__).resolve().parent
_MANIFEST_PATH = _THIS_DIR / "l2_source_manifest.json"

_TITLE_PREFIXES = (
    "chancellor",
    "high chancellor",
    "general",
    "grand strategist",
    "chief marshal",
    "admiral",
    "director",
    "minister",
    "captain",
    "commander",
    "major",
    "dr.",
    "dr",
    "doctor",
    "chief engineer",
    "lieutenant",
    "marshal-captain",
    "pirate queen",
    "board sovereign",
    "luminary",
    "resonance chief",
    "elder inscriber",
    "driftcaller",
    "supreme commander",
    "executive commander",
    "supreme war-chaplain",
)
_NOISE_TOKENS = {
    "the",
    "of",
    "and",
    "for",
    "to",
    "in",
    "on",
    "a",
    "an",
    "with",
    "by",
    "from",
}
_ORG_CANONICAL_NAMES = {
    "galactic marshals": "Union Marshals",
    "union marshals": "Union Marshals",
    "union intelligence bureau": "Union Intelligence Bureau",
    "union intelligence bureau uib": "Union Intelligence Bureau",
    "uib": "Union Intelligence Bureau",
    "office of strategic diplomacy": "Office of Strategic Diplomacy",
    "osd": "Office of Strategic Diplomacy",
    "galactic union": "Galactic Union",
    "union senate": "Union Senate",
    "union naval forces": "Union Naval Forces",
    "diplomatic corps": "Diplomatic Corps",
    "marshal academy on the capital planet": "Marshal Academy",
    "marshal academy": "Marshal Academy",
}
_LOCATION_CANONICAL_NAMES = {
    "kaelor’s rift": "Kaelor's Rift",
    "kaelor's rift": "Kaelor's Rift",
    "kaelor rift": "Kaelor's Rift",
    "vel‑surak": "Vel-Surak",
    "vel-surak": "Vel-Surak",
    "vel surak": "Vel-Surak",
    "xyphos prime ruins": "Xyphos Prime ruins",
    "xyphos ruins": "Xyphos Prime ruins",
    "torix‑7": "Torix-7",
    "torix-7": "Torix-7",
    "xelvani‑3": "Xelvani-3",
    "xelvani-3": "Xelvani-3",
}
_CHARACTER_TO_FACTION = {
    "chancellor zylox": "galactic_union",
    "high chancellor renn valcor": "galactic_union",
    "general kael durn": "galactic_union",
    "grand strategist lirian vos": "galactic_union",
    "chief marshal vael saros": "galactic_union",
    "admiral selene arcturus": "galactic_union",
    "director callan deyrus": "galactic_union",
    "minister anaya ral-seyr": "galactic_union",
    "captain alric tann": "galactic_union",
    "commander lyra voss": "galactic_union",
    "major elias radek": "galactic_union",
    "dr. adrienne kovas": "galactic_union",
    "doctor nia veran": "galactic_union",
    "chief engineer rhen kailo": "galactic_union",
    "lieutenant arin tavos": "galactic_union",
    "marshal-captain elias drayen": "galactic_union",
    "director varek norr": "galactic_union",
    "cross": "galactic_union",
    "vorn": "galactic_union",
    "roake": "galactic_union",
    "kade": "galactic_union",
    "prime construct": "prime_construct",
    "omega-veil": "ai_warlord",
    "sovereign nexus": "ai_warlord",
}


def _normalize_text(value: str) -> str:
    return (
        value.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2212", "-")
    )


def _normalize_key(value: str) -> str:
    clean = _normalize_text(value).lower()
    clean = re.sub(r"[^a-z0-9]+", " ", clean)
    return " ".join(clean.split())


def _slugify(value: str) -> str:
    key = _normalize_key(value)
    if not key:
        return "unknown"
    return key.replace(" ", "_")


def _tokenize_name(value: str) -> List[str]:
    key = _normalize_key(value)
    return [token for token in key.split() if token and token not in _NOISE_TOKENS]


def _strip_title(name: str) -> str:
    key = _normalize_text(name).strip()
    lowered = key.lower()
    for prefix in sorted(_TITLE_PREFIXES, key=len, reverse=True):
        if lowered.startswith(prefix + " "):
            return key[len(prefix) + 1 :].strip()
    return key


def _derive_character_aliases(name: str) -> List[str]:
    aliases: List[str] = []
    bare = _strip_title(name)
    if bare and bare != name:
        aliases.append(bare)
    tokens = bare.split()
    if len(tokens) >= 2:
        aliases.append(tokens[-1])
        aliases.append(" ".join(tokens[-2:]))
    elif tokens:
        aliases.append(tokens[0])
    normalized_seen = set()
    result: List[str] = []
    for alias in aliases:
        key = _normalize_key(alias)
        if key and key not in normalized_seen and _normalize_key(alias) != _normalize_key(name):
            normalized_seen.add(key)
            result.append(alias)
    return sorted(result)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _read_lines(path: Path) -> List[Tuple[int, str]]:
    return list(enumerate(path.read_text(encoding="utf-8").splitlines(), start=1))


@dataclass
class L2SourceRef:
    source_id: str
    path: str
    line_start: int
    line_end: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


@dataclass
class L2Relation:
    relation_id: str
    relation_type: str
    source_entity_id: str
    target_entity_id: str
    certainty: str
    source_refs: List[L2SourceRef] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    conflict_flags: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "certainty": self.certainty,
            "source_refs": [ref.to_dict() for ref in self.source_refs],
            "tags": list(self.tags),
            "conflict_flags": list(self.conflict_flags),
        }


@dataclass
class L2Entity:
    entity_id: str
    entity_kind: str
    name: str
    aliases: List[str]
    certainty: str
    source_refs: List[L2SourceRef]
    status: str
    faction_bindings: List[str]
    tags: List[str]
    conflict_flags: List[Dict[str, Any]] = field(default_factory=list)
    role: Optional[str] = None
    organization_ids: List[str] = field(default_factory=list)
    org_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    parent_org_id: Optional[str] = None
    location_type: Optional[str] = None
    region_id: Optional[str] = None
    canonical_position_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_kind": self.entity_kind,
            "name": self.name,
            "aliases": list(self.aliases),
            "certainty": self.certainty,
            "source_refs": [ref.to_dict() for ref in self.source_refs],
            "status": self.status,
            "faction_bindings": list(self.faction_bindings),
            "tags": list(self.tags),
            "conflict_flags": list(self.conflict_flags),
            "role": self.role,
            "organization_ids": list(self.organization_ids),
            "org_type": self.org_type,
            "jurisdiction": self.jurisdiction,
            "parent_org_id": self.parent_org_id,
            "location_type": self.location_type,
            "region_id": self.region_id,
            "canonical_position_status": self.canonical_position_status,
        }


@dataclass
class L2StateBundle:
    schema_version: str
    manifest_version: str
    source_manifest_path: str
    source_manifest_hash: str
    source_bundle_hash: str
    characters: Dict[str, L2Entity]
    organizations: Dict[str, L2Entity]
    locations: Dict[str, L2Entity]
    relations: List[L2Relation]
    indexes: Dict[str, Any]
    warnings: List[str]
    unresolved_conflict_count: int
    deferred_layers: Dict[str, str]
    mobile_assets: Dict[str, Dict[str, Any]]
    logistics_nodes: Dict[str, Dict[str, Any]]
    location_pressures: Dict[str, Dict[str, Any]]
    operational_views: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_version": self.manifest_version,
            "source_manifest_path": self.source_manifest_path,
            "source_manifest_hash": self.source_manifest_hash,
            "source_bundle_hash": self.source_bundle_hash,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "organizations": {k: v.to_dict() for k, v in self.organizations.items()},
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "relations": [relation.to_dict() for relation in self.relations],
            "indexes": dict(self.indexes),
            "warnings": list(self.warnings),
            "unresolved_conflict_count": self.unresolved_conflict_count,
            "deferred_layers": dict(self.deferred_layers),
            "mobile_assets": dict(self.mobile_assets),
            "logistics_nodes": dict(self.logistics_nodes),
            "location_pressures": dict(self.location_pressures),
            "operational_views": dict(self.operational_views),
        }


@dataclass
class L2Registry:
    schema_version: str
    manifest_version: str
    source_manifest_path: str
    source_manifest_hash: str
    source_bundle_hash: str
    entities: Dict[str, L2Entity]
    relations: List[L2Relation]
    warnings: List[str]
    alias_index: Dict[str, List[str]]

    def find_entities(self, query: str, entity_kind: Optional[str] = None) -> List[L2Entity]:
        matched_ids = self.alias_index.get(_normalize_key(query), [])
        entities = [self.entities[entity_id] for entity_id in matched_ids]
        if entity_kind is not None:
            entities = [entity for entity in entities if entity.entity_kind == entity_kind]
        return entities

    def to_state_bundle(self, faction_ids: Iterable[str]) -> L2StateBundle:
        characters = {
            entity_id: entity
            for entity_id, entity in sorted(self.entities.items())
            if entity.entity_kind == "character"
        }
        organizations = {
            entity_id: entity
            for entity_id, entity in sorted(self.entities.items())
            if entity.entity_kind == "organization"
        }
        locations = {
            entity_id: entity
            for entity_id, entity in sorted(self.entities.items())
            if entity.entity_kind == "location"
        }

        by_faction_id: Dict[str, Dict[str, Any]] = {}
        for faction_id in sorted(faction_ids):
            by_faction_id[faction_id] = {
                "characters": [],
                "organizations": [],
                "locations": [],
                "mobile_assets": [],
                "logistics_nodes": [],
                "pressure_locations": [],
                "warnings": [],
            }

        by_location_id: Dict[str, Dict[str, Any]] = {
            location_id: {
                "characters": [],
                "organizations": [],
                "locations": [],
                "mobile_assets": [],
                "logistics_nodes": [],
                "pressure_ids": [],
                "faction_ids": [],
                "warnings": [],
            }
            for location_id in sorted(locations)
        }

        for entity_id, entity in sorted(self.entities.items()):
            for faction_id in entity.faction_bindings:
                if faction_id not in by_faction_id:
                    by_faction_id[faction_id] = {
                        "characters": [],
                        "organizations": [],
                        "locations": [],
                        "mobile_assets": [],
                        "logistics_nodes": [],
                        "pressure_locations": [],
                        "warnings": [],
                    }
                by_faction_id[faction_id][f"{entity.entity_kind}s"].append(entity_id)

        for relation in self.relations:
            source = self.entities.get(relation.source_entity_id)
            target = self.entities.get(relation.target_entity_id)
            if source is None or target is None:
                continue
            if relation.relation_type in {"operates_in", "based_in"}:
                location = target if target.entity_kind == "location" else None
                actor = source
            elif source.entity_kind == "location" and target.entity_kind in {"character", "organization"}:
                location = source
                actor = target
            else:
                location = None
                actor = None

            if location is None or actor is None:
                continue

            bucket = by_location_id.setdefault(
                location.entity_id,
                {
                    "characters": [],
                    "organizations": [],
                    "locations": [],
                    "mobile_assets": [],
                    "logistics_nodes": [],
                    "pressure_ids": [],
                    "faction_ids": [],
                    "warnings": [],
                },
            )
            bucket[f"{actor.entity_kind}s"].append(actor.entity_id)
            for faction_id in actor.faction_bindings:
                if faction_id not in bucket["faction_ids"]:
                    bucket["faction_ids"].append(faction_id)

        alias_index = {alias: list(ids) for alias, ids in sorted(self.alias_index.items())}
        for bucket in by_faction_id.values():
            for key in (
                "characters",
                "organizations",
                "locations",
                "mobile_assets",
                "logistics_nodes",
                "pressure_locations",
            ):
                bucket[key] = sorted(set(bucket[key]))
        for bucket in by_location_id.values():
            for key in (
                "characters",
                "organizations",
                "locations",
                "mobile_assets",
                "logistics_nodes",
                "pressure_ids",
                "faction_ids",
            ):
                bucket[key] = sorted(set(bucket[key]))

        unresolved_conflict_count = sum(
            len(entity.conflict_flags) for entity in self.entities.values()
        ) + sum(len(relation.conflict_flags) for relation in self.relations)

        return L2StateBundle(
            schema_version="l2-state-bundle-v1",
            manifest_version=self.manifest_version,
            source_manifest_path=self.source_manifest_path,
            source_manifest_hash=self.source_manifest_hash,
            source_bundle_hash=self.source_bundle_hash,
            characters=characters,
            organizations=organizations,
            locations=locations,
            relations=sorted(self.relations, key=lambda relation: relation.relation_id),
            indexes={
                "by_alias": alias_index,
                "by_faction_id": by_faction_id,
                "by_location_id": by_location_id,
            },
            warnings=list(self.warnings),
            unresolved_conflict_count=unresolved_conflict_count,
            deferred_layers={
                "crew_rosters": "phase_3_reserved",
                "route_capacity": "phase_3_reserved",
                "asset_attrition": "phase_3_reserved",
            },
            mobile_assets={},
            logistics_nodes={},
            location_pressures={},
            operational_views={},
        )


class _RegistryBuilder:
    def __init__(self, workspace_root: Path, manifest: Dict[str, Any]) -> None:
        self.workspace_root = workspace_root
        self.manifest = manifest
        self.entities: Dict[str, L2Entity] = {}
        self.relations: Dict[str, L2Relation] = {}
        self.pending_relations: List[Dict[str, Any]] = []
        self.warnings: List[str] = []

    def add_entity(
        self,
        *,
        entity_kind: str,
        name: str,
        source_ref: L2SourceRef,
        certainty: str,
        aliases: Optional[Iterable[str]] = None,
        status: str = "active",
        tags: Optional[Iterable[str]] = None,
        role: Optional[str] = None,
        org_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        parent_org_name: Optional[str] = None,
        location_type: Optional[str] = None,
        region_id: Optional[str] = None,
        canonical_position_status: Optional[str] = None,
    ) -> str:
        source_name = _normalize_text(name).strip()
        canonical_name = self._canonical_name(entity_kind, name)
        entity_id = self._entity_id(entity_kind, canonical_name)
        alias_values = set()
        if source_name and _normalize_key(source_name) != _normalize_key(canonical_name):
            alias_values.add(source_name)
        for alias in aliases or []:
            normalized = _normalize_text(alias).strip()
            if normalized and _normalize_key(normalized) != _normalize_key(canonical_name):
                alias_values.add(normalized)
        if entity_kind == "character":
            alias_values.update(_derive_character_aliases(canonical_name))

        if entity_id not in self.entities:
            self.entities[entity_id] = L2Entity(
                entity_id=entity_id,
                entity_kind=entity_kind,
                name=canonical_name,
                aliases=sorted(alias_values),
                certainty=certainty,
                source_refs=[source_ref],
                status=status,
                faction_bindings=[],
                tags=sorted(set(tags or [])),
                role=role,
                org_type=org_type,
                jurisdiction=jurisdiction,
                location_type=location_type,
                region_id=region_id,
                canonical_position_status=canonical_position_status,
            )
        else:
            entity = self.entities[entity_id]
            entity.aliases = sorted(set(entity.aliases) | alias_values)
            entity.tags = sorted(set(entity.tags) | set(tags or []))
            entity.source_refs.append(source_ref)
            entity.certainty = self._merge_certainty(entity.certainty, certainty)
            self._merge_scalar(entity, "role", role, source_ref)
            self._merge_scalar(entity, "org_type", org_type, source_ref)
            self._merge_scalar(entity, "jurisdiction", jurisdiction, source_ref)
            self._merge_scalar(entity, "location_type", location_type, source_ref)
            self._merge_scalar(entity, "region_id", region_id, source_ref)
            self._merge_scalar(entity, "canonical_position_status", canonical_position_status, source_ref)

        if entity_kind == "organization" and parent_org_name:
            parent_id = self.add_entity(
                entity_kind="organization",
                name=parent_org_name,
                source_ref=source_ref,
                certainty=certainty,
                status="active",
            )
            entity = self.entities[entity_id]
            if entity.parent_org_id and entity.parent_org_id != parent_id:
                entity.conflict_flags.append(
                    {
                        "type": "parent_org_conflict",
                        "existing": entity.parent_org_id,
                        "incoming": parent_id,
                        "source_ref": source_ref.to_dict(),
                    }
                )
            else:
                entity.parent_org_id = parent_id
            self.add_pending_relation(
                relation_type="member_of",
                source_entity_id=entity_id,
                target_query=parent_org_name,
                source_ref=source_ref,
                certainty=certainty,
                tags=["parent_org"],
            )

        return entity_id

    def add_pending_relation(
        self,
        *,
        relation_type: str,
        source_entity_id: str,
        target_query: str,
        source_ref: L2SourceRef,
        certainty: str,
        tags: Optional[Iterable[str]] = None,
    ) -> None:
        self.pending_relations.append(
            {
                "relation_type": relation_type,
                "source_entity_id": source_entity_id,
                "target_query": target_query,
                "source_ref": source_ref,
                "certainty": certainty,
                "tags": list(tags or []),
            }
        )

    def finalize(self, base_state: Any) -> L2Registry:
        alias_index = self._build_alias_index()
        self._resolve_pending_relations(alias_index)
        self._apply_runtime_bindings(base_state)
        self._flag_ambiguous_aliases(alias_index)
        return L2Registry(
            schema_version="l2-registry-v1",
            manifest_version=str(self.manifest.get("schema_version") or "unknown"),
            source_manifest_path=str(_MANIFEST_PATH),
            source_manifest_hash=_stable_hash(self.manifest),
            source_bundle_hash=self._source_bundle_hash(),
            entities={k: self.entities[k] for k in sorted(self.entities)},
            relations=[self.relations[key] for key in sorted(self.relations)],
            warnings=sorted(set(self.warnings)),
            alias_index=alias_index,
        )

    def _source_bundle_hash(self) -> str:
        payload: Dict[str, Any] = {
            "manifest": self.manifest,
            "sources": {},
        }
        for entry in self.manifest.get("sources", []):
            path = self.workspace_root / str(entry.get("path") or "")
            payload["sources"][str(entry.get("source_id") or "")] = (
                path.read_text(encoding="utf-8") if path.exists() else None
            )
        return _stable_hash(payload)

    def _merge_scalar(self, entity: L2Entity, field_name: str, incoming: Optional[str], source_ref: L2SourceRef) -> None:
        if incoming is None:
            return
        existing = getattr(entity, field_name)
        if existing in (None, ""):
            setattr(entity, field_name, incoming)
            return
        if existing != incoming:
            entity.conflict_flags.append(
                {
                    "type": "field_conflict",
                    "field": field_name,
                    "existing": existing,
                    "incoming": incoming,
                    "source_ref": source_ref.to_dict(),
                }
            )

    def _canonical_name(self, entity_kind: str, name: str) -> str:
        clean = _normalize_text(name).strip()
        key = _normalize_key(clean)
        if entity_kind == "organization":
            return _ORG_CANONICAL_NAMES.get(key, clean)
        if entity_kind == "location":
            return _LOCATION_CANONICAL_NAMES.get(key, clean)
        return clean

    def _entity_id(self, entity_kind: str, canonical_name: str) -> str:
        prefix = {"character": "char", "organization": "org", "location": "loc"}[entity_kind]
        return f"{prefix}_{_slugify(canonical_name)}"

    @staticmethod
    def _merge_certainty(existing: str, incoming: str) -> str:
        order = {
            "UNCONFIRMED": 0,
            "LEGEND_CONTESTED": 1,
            "APPROX": 2,
            "STAGING": 3,
            "CANON_PROMOTE": 4,
            "CANON": 5,
        }
        return incoming if order.get(incoming, -1) > order.get(existing, -1) else existing

    def _build_alias_index(self) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = {}
        for entity_id, entity in self.entities.items():
            candidates = [entity.name] + list(entity.aliases)
            for alias in candidates:
                key = _normalize_key(alias)
                if not key:
                    continue
                index.setdefault(key, []).append(entity_id)
        return {key: sorted(set(ids)) for key, ids in sorted(index.items())}

    def _resolve_pending_relations(self, alias_index: Dict[str, List[str]]) -> None:
        for pending in self.pending_relations:
            relation_type = str(pending["relation_type"])
            source_entity_id = str(pending["source_entity_id"])
            query = str(pending["target_query"])
            certainty = str(pending["certainty"])
            source_ref = pending["source_ref"]
            matches = alias_index.get(_normalize_key(query), [])
            if len(matches) == 1:
                target_entity_id = matches[0]
                relation_id = f"rel_{relation_type}_{source_entity_id}_{target_entity_id}"
                if relation_id not in self.relations:
                    self.relations[relation_id] = L2Relation(
                        relation_id=relation_id,
                        relation_type=relation_type,
                        source_entity_id=source_entity_id,
                        target_entity_id=target_entity_id,
                        certainty=certainty,
                        source_refs=[source_ref],
                        tags=sorted(set(pending["tags"])),
                    )
                else:
                    relation = self.relations[relation_id]
                    relation.source_refs.append(source_ref)
                    relation.tags = sorted(set(relation.tags) | set(pending["tags"]))
            elif len(matches) > 1:
                warning = f"Ambiguous relation target '{query}' for {source_entity_id}: {matches}"
                self.warnings.append(warning)
                source = self.entities.get(source_entity_id)
                if source is not None:
                    source.conflict_flags.append(
                        {
                            "type": "ambiguous_relation_target",
                            "target_query": query,
                            "matches": matches,
                            "source_ref": source_ref.to_dict(),
                        }
                    )
            else:
                self.warnings.append(f"Unresolved relation target '{query}' for {source_entity_id}")

        for relation in self.relations.values():
            source = self.entities.get(relation.source_entity_id)
            target = self.entities.get(relation.target_entity_id)
            if source is None or target is None:
                continue
            if source.entity_kind == "character" and relation.relation_type in {"leads", "member_of"}:
                if target.entity_id not in source.organization_ids:
                    source.organization_ids.append(target.entity_id)

    def _apply_runtime_bindings(self, base_state: Any) -> None:
        faction_ids = sorted(getattr(base_state, "factions", {}).keys())
        for entity in self.entities.values():
            bindings: set[str] = set(entity.faction_bindings)

            direct = self._infer_direct_faction_binding(entity)
            if direct:
                bindings.add(direct)

            if entity.entity_kind == "character":
                for leader in getattr(base_state, "leaders", {}).values():
                    if getattr(leader, "faction_id", None) and self._names_compatible(entity, str(leader.name)):
                        bindings.add(str(leader.faction_id))

            if entity.entity_kind in {"character", "organization"}:
                for org_id in entity.organization_ids:
                    org = self.entities.get(org_id)
                    if org is not None:
                        bindings.update(org.faction_bindings)
                if entity.parent_org_id:
                    org = self.entities.get(entity.parent_org_id)
                    if org is not None:
                        bindings.update(org.faction_bindings)

            entity.faction_bindings = sorted(binding for binding in bindings if binding in faction_ids)

    def _infer_direct_faction_binding(self, entity: L2Entity) -> Optional[str]:
        name_key = _normalize_key(entity.name)
        role_key = _normalize_key(entity.role or "")
        tags_key = " ".join(sorted(_normalize_key(tag) for tag in entity.tags))
        combined = " ".join(part for part in (name_key, role_key, tags_key) if part)

        if entity.entity_kind == "character":
            for key, faction_id in _CHARACTER_TO_FACTION.items():
                if name_key == key:
                    return faction_id

        keyword_map = [
            ("galactic union", "galactic_union"),
            ("union senate", "galactic_union"),
            ("union marshals", "galactic_union"),
            ("union naval forces", "galactic_union"),
            ("union intelligence bureau", "galactic_union"),
            ("office of strategic diplomacy", "galactic_union"),
            ("diplomatic corps", "galactic_union"),
            ("excision task force", "galactic_union"),
            ("prime construct", "prime_construct"),
            ("ai warlord", "ai_warlord"),
            ("omega veil", "ai_warlord"),
            ("sovereign nexus", "ai_warlord"),
            ("velar", "velar_imperium"),
            ("zyphari", "zyphari_compact"),
            ("outer colonies", "outer_colonies"),
            ("pmc", "pmc_syndicate"),
            ("crimson pact", "crimson_pact"),
            ("separatist", "separatist_confed"),
        ]
        for needle, faction_id in keyword_map:
            if needle in combined:
                return faction_id
        if entity.entity_kind == "location":
            if name_key.startswith("gu "):
                return "galactic_union"
            if name_key.startswith("vel "):
                return "velar_imperium"
            if name_key.startswith("zy "):
                return "zyphari_compact"
        return None

    def _flag_ambiguous_aliases(self, alias_index: Dict[str, List[str]]) -> None:
        for alias, entity_ids in alias_index.items():
            if len(entity_ids) <= 1:
                continue
            warning = f"Ambiguous alias '{alias}' resolves to {entity_ids}"
            self.warnings.append(warning)
            for entity_id in entity_ids:
                entity = self.entities.get(entity_id)
                if entity is None:
                    continue
                entity.conflict_flags.append(
                    {
                        "type": "ambiguous_alias",
                        "alias": alias,
                        "entity_ids": list(entity_ids),
                    }
                )

    def _names_compatible(self, entity: L2Entity, candidate_name: str) -> bool:
        candidate_tokens = set(_tokenize_name(candidate_name))
        entity_token_sets = [set(_tokenize_name(entity.name))] + [set(_tokenize_name(alias)) for alias in entity.aliases]
        for tokens in entity_token_sets:
            if not tokens or not candidate_tokens:
                continue
            if tokens.issubset(candidate_tokens) or candidate_tokens.issubset(tokens):
                return True
            if len(tokens & candidate_tokens) >= min(2, len(tokens), len(candidate_tokens)):
                return True
        return False


def _manifest_entries() -> Dict[str, Any]:
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def _ref(source_id: str, rel_path: str, start: int, end: int) -> L2SourceRef:
    return L2SourceRef(source_id=source_id, path=rel_path, line_start=start, line_end=end)


def _find_line(lines: List[Tuple[int, str]], needle: str) -> int:
    for line_no, line in lines:
        if needle in line:
            return line_no
    return 1


def _is_marshals_ledger_character_candidate(name: str, role: str) -> bool:
    name_key = _normalize_key(name)
    role_key = _normalize_key(role)
    if not name_key or not role_key:
        return False

    blocked_exact = {
        'marshal operative',
        'sentinel variants',
        'marshal starship classes',
    }
    blocked_name_fragments = (
        'power suit',
        'ship systems',
        'starship classes',
    )
    blocked_role_fragments = (
        'pasted into chat',
        'uploaded 2026 01 31',
        'csv tables',
        'deployment platform',
        'mobile command ship',
        'patrol ship',
        'mid sized warship',
        'insertion platform',
        'fleet wide coordination',
        'small agile pursuit ship',
    )

    if name_key.startswith('src '):
        return False
    if name_key in blocked_exact:
        return False
    if any(fragment in name_key for fragment in blocked_name_fragments):
        return False
    if ' class ' in f' {name_key} ':
        return False
    if any(fragment in role_key for fragment in blocked_role_fragments):
        return False
    return True


def _parse_world_bible(builder: _RegistryBuilder, source_id: str, rel_path: str, path: Path, default_certainty: str) -> None:
    lines = _read_lines(path)
    current_name: Optional[str] = None
    current_start: Optional[int] = None
    current_block: List[Tuple[int, str]] = []

    def flush_character() -> None:
        nonlocal current_name, current_start, current_block
        if not current_name or current_start is None:
            current_name = None
            current_start = None
            current_block = []
            return

        block_end = current_block[-1][0] if current_block else current_start
        role = None
        relationships = None
        for _, line in current_block:
            if line.startswith("- **Role:**"):
                role = line.split(":", 1)[1].strip()
            elif line.startswith("- **Relationships:**"):
                relationships = line.split(":", 1)[1].strip()

        entity_id = builder.add_entity(
            entity_kind="character",
            name=current_name,
            source_ref=_ref(source_id, rel_path, current_start, block_end),
            certainty=default_certainty,
            role=role,
            tags=["world_bible"],
        )

        if role:
            org_specs = [
                ("Galactic Union", "member_of", "polity"),
                ("Union Senate", "leads" if "speaker" in role.lower() else "member_of", "legislative"),
                ("Union Marshals", "leads" if "leader" in role.lower() else "member_of", "law_enforcement"),
                ("Union Naval Forces", "leads" if "commander" in role.lower() else "member_of", "military"),
                ("Union Intelligence Bureau", "leads" if "head" in role.lower() else "member_of", "intelligence"),
                ("Office of Strategic Diplomacy", "leads" if "director" in role.lower() else "member_of", "diplomatic"),
                ("Diplomatic Corps", "member_of", "diplomatic"),
            ]
            for org_name, relation_type, org_type in org_specs:
                if org_name.lower() in _normalize_key(role):
                    org_id = builder.add_entity(
                        entity_kind="organization",
                        name=org_name,
                        source_ref=_ref(source_id, rel_path, current_start, block_end),
                        certainty=default_certainty,
                        org_type=org_type,
                        tags=["world_bible"],
                    )
                    builder.add_pending_relation(
                        relation_type=relation_type,
                        source_entity_id=entity_id,
                        target_query=org_name,
                        source_ref=_ref(source_id, rel_path, current_start, block_end),
                        certainty=default_certainty,
                        tags=["world_bible_role"],
                    )
                    entity = builder.entities[entity_id]
                    if org_id not in entity.organization_ids:
                        entity.organization_ids.append(org_id)

        if relationships:
            for clause in [part.strip() for part in relationships.split(",") if part.strip()]:
                patterns = [
                    (r"(?:Trusted by|Close Political Ally of|Longtime Ally of|Strong Ally of|Mutual Respect for|Strategic Confidant of|Respected by|Strong Diplomatic Rapport with|Close Professional Bond with|Close Working Relationship with|Close Confidant of|Strategic Collaborator with|Tactical Coordinator with|Good Rapport with)\s+(.+)$", "allied_with"),
                    (r"(?:Wary of|Dislikes|Distrustful of|Professional Rival of|Intellectual Rival of|Philosophical Rivalry with|Skeptical of)\s+(.+)$", "opposes"),
                ]
                for pattern, relation_type in patterns:
                    match = re.search(pattern, clause, flags=re.IGNORECASE)
                    if match:
                        target_query = match.group(1).strip()
                        builder.add_pending_relation(
                            relation_type=relation_type,
                            source_entity_id=entity_id,
                            target_query=target_query,
                            source_ref=_ref(source_id, rel_path, current_start, block_end),
                            certainty=default_certainty,
                            tags=["world_bible_relationship"],
                        )
                        break

        current_name = None
        current_start = None
        current_block = []

    for line_no, line in lines:
        if line.startswith("### "):
            flush_character()
            current_name = line[4:].strip()
            current_start = line_no
            current_block = []
            continue
        if current_name and line.startswith("#"):
            flush_character()
            continue
        if current_name:
            current_block.append((line_no, line))
    flush_character()

    ai_line = _find_line(lines, "Prime_Construct_Recognized_Statehood")
    builder.add_entity(
        entity_kind="organization",
        name="Prime Construct Polity",
        aliases=["Prime Construct"],
        source_ref=_ref(source_id, rel_path, ai_line, ai_line),
        certainty=default_certainty,
        org_type="ai_polity",
        tags=["world_bible", "recognized_statehood"],
    )


def _parse_location_authority_table(
    builder: _RegistryBuilder, source_id: str, rel_path: str, path: Path, default_certainty: str
) -> None:
    for line_no, line in _read_lines(path):
        if not line.startswith("|") or "---" in line or "canonical_name" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        canonical_name, aliases, location_type, certainty_tag, _, notes = cells
        if not canonical_name:
            continue
        alias_values = [] if aliases in {"", "-", "—"} else [alias.strip() for alias in aliases.split("/") if alias.strip()]
        location_id = builder.add_entity(
            entity_kind="location",
            name=canonical_name,
            aliases=alias_values,
            source_ref=_ref(source_id, rel_path, line_no, line_no),
            certainty=certainty_tag or default_certainty,
            location_type=location_type,
            canonical_position_status="canonical" if (certainty_tag or default_certainty) == "CANON" else "staging",
            tags=[location_type, notes] if notes else [location_type],
        )
        # Derived based_in links for explicit sub-sites.
        if canonical_name in {"Vel-Surak megacity infrastructure (gravity/atmosphere districts)", "Xyphos Precursor Research Center"}:
            target = "Vel-Surak" if "Vel-Surak" in canonical_name else "Xyphos Prime ruins"
            builder.add_pending_relation(
                relation_type="based_in",
                source_entity_id=location_id,
                target_query=target,
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=certainty_tag or default_certainty,
                tags=["lat_derived"],
            )


def _parse_marshals_ledger(builder: _RegistryBuilder, source_id: str, rel_path: str, path: Path, default_certainty: str) -> None:
    lines = _read_lines(path)
    for line_no, line in lines:
        if "**Galactic Marshals**" in line:
            builder.add_entity(
                entity_kind="organization",
                name="Galactic Marshals",
                aliases=["Union Marshals"],
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                org_type="law_enforcement",
                tags=["marshals", "ledger"],
            )
        elif "**Marshal Academy on the capital planet**" in line:
            builder.add_entity(
                entity_kind="location",
                name="Marshal Academy",
                aliases=["Marshal Academy on the capital planet"],
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                location_type="academy",
                canonical_position_status="staging",
                tags=["institution", "marshals"],
            )
        elif "**Armada Nova Systems**" in line:
            builder.add_entity(
                entity_kind="organization",
                name="Armada Nova Systems",
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                org_type="industrial",
                tags=["sentinel_tech"],
            )
        elif line.startswith("1. **Marshal-Enforcer Units**"):
            builder.add_entity(
                entity_kind="organization",
                name="Marshal-Enforcer Units",
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                org_type="law_enforcement",
                parent_org_name="Union Marshals",
                tags=["marshal_subunit"],
            )
        elif line.startswith("2. **Tactical Enforcement Officers (TEOs)**"):
            builder.add_entity(
                entity_kind="organization",
                name="Tactical Enforcement Officers",
                aliases=["TEOs"],
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                org_type="law_enforcement",
                parent_org_name="Union Marshals",
                tags=["marshal_subunit"],
            )
        elif line.startswith("3. **Interceptor Squads**"):
            builder.add_entity(
                entity_kind="organization",
                name="Interceptor Squads",
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                org_type="law_enforcement",
                parent_org_name="Union Marshals",
                tags=["marshal_subunit"],
            )
        elif line.startswith("4. **Covert Division"):
            builder.add_entity(
                entity_kind="organization",
                name="The Black Hand",
                aliases=["Covert Division"],
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                org_type="intelligence",
                parent_org_name="Union Marshals",
                tags=["marshal_subunit", "covert"],
            )
        elif "**Blackreach Station**" in line:
            builder.add_entity(
                entity_kind="location",
                name="Blackreach Station",
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                location_type="space_station",
                canonical_position_status="staging",
                tags=["mission_site", "silent_dagger"],
            )
        elif line.strip().startswith("- **") and "Sentinel" in line and "—" in line:
            match = re.match(r"- \*\*(.+?)\*\* — (.+)", line.strip())
            if not match:
                continue
            name = match.group(1).strip()
            role = match.group(2).strip()
            if not _is_marshals_ledger_character_candidate(name, role):
                continue
            entity_id = builder.add_entity(
                entity_kind="character",
                name=name,
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                role=role,
                tags=["silent_dagger", "marshals"],
            )
            builder.add_pending_relation(
                relation_type="member_of",
                source_entity_id=entity_id,
                target_query="Union Marshals",
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                tags=["silent_dagger"],
            )
            builder.add_pending_relation(
                relation_type="operates_in",
                source_entity_id=entity_id,
                target_query="Blackreach Station",
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                tags=["silent_dagger"],
            )


def _parse_marshals_sim_capture(
    builder: _RegistryBuilder, source_id: str, rel_path: str, path: Path, default_certainty: str
) -> None:
    for line_no, line in _read_lines(path):
        if re.match(r"- \*\*.+\*\* — ", line.strip()):
            match = re.match(r"- \*\*(.+?)\*\* — (.+)", line.strip())
            if not match:
                continue
            name = match.group(1).strip()
            role = match.group(2).strip()
            entity_id = builder.add_entity(
                entity_kind="character",
                name=name,
                source_ref=_ref(source_id, rel_path, line_no, line_no),
                certainty=default_certainty,
                role=role,
                tags=["marshals_sim_capture"],
            )
            if "marshal" in role.lower() or "sentinel" in role.lower():
                builder.add_pending_relation(
                    relation_type="member_of",
                    source_entity_id=entity_id,
                    target_query="Union Marshals",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    tags=["marshals_sim_capture"],
                )


def _parse_mission_csv(builder: _RegistryBuilder, source_id: str, rel_path: str, path: Path, default_certainty: str) -> None:
    rows: List[Tuple[int, Dict[str, str]]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_index, row in enumerate(reader, start=2):
            rows.append((row_index, {str(k): str(v) for k, v in row.items() if k is not None and v is not None}))

    stem = path.stem
    if "Director_Varek_Norr" in stem:
        line_start = rows[0][0] if rows else 2
        line_end = rows[-1][0] if rows else line_start
        entity_id = builder.add_entity(
            entity_kind="character",
            name="Director Varek Norr",
            source_ref=_ref(source_id, rel_path, line_start, line_end),
            certainty=default_certainty,
            role="Director of the Office of Strategic Diplomacy",
            tags=["mission_log"],
        )
        builder.add_entity(
            entity_kind="organization",
            name="Office of Strategic Diplomacy",
            aliases=["OSD"],
            source_ref=_ref(source_id, rel_path, line_start, line_end),
            certainty=default_certainty,
            org_type="diplomatic",
            tags=["mission_log"],
        )
        builder.add_pending_relation(
            relation_type="leads",
            source_entity_id=entity_id,
            target_query="Office of Strategic Diplomacy",
            source_ref=_ref(source_id, rel_path, line_start, line_end),
            certainty=default_certainty,
            tags=["mission_log"],
        )
        builder.add_pending_relation(
            relation_type="member_of",
            source_entity_id=entity_id,
            target_query="Galactic Union",
            source_ref=_ref(source_id, rel_path, line_start, line_end),
            certainty=default_certainty,
            tags=["mission_log"],
        )
        return

    if "Operation_Obsidian_Dawn_-_Mission_Briefing" in stem:
        for line_no, row in rows:
            value = row.get("Operational Focus", "")
            if "Omega-Veil" in value:
                builder.add_entity(
                    entity_kind="character",
                    name="Omega-Veil",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    role="Rogue AI warlord intelligence",
                    tags=["mission_log", "ai_warlord"],
                )
            if "Prime Construct" in value:
                builder.add_entity(
                    entity_kind="character",
                    name="Prime Construct",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    role="AI sovereign intelligence actor",
                    tags=["mission_log", "prime_construct"],
                )
            if "Aegis Cybernetics" in value:
                builder.add_entity(
                    entity_kind="organization",
                    name="Aegis Cybernetics",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    org_type="industrial",
                    tags=["mission_log"],
                )
        return

    if "Operation_Obsidian_Dawn_-_Mission_Outcome" in stem:
        for line_no, row in rows:
            value = row.get("Mission Results", "")
            if "Sovereign Nexus" in value:
                entity_id = builder.add_entity(
                    entity_kind="character",
                    name="Sovereign Nexus",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    role="Shadow AI rebellion coordinator",
                    tags=["mission_log", "ai_warlord"],
                )
                builder.add_pending_relation(
                    relation_type="opposes",
                    source_entity_id=entity_id,
                    target_query="Galactic Union",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    tags=["mission_log"],
                )
        return

    if "Operation_Obsidian_Dawn_-_Mission_Execution" in stem:
        for line_no, row in rows:
            value = row.get("Tactical Action", "")
            if "Omega-Veil" in value:
                entity_id = builder.add_entity(
                    entity_kind="character",
                    name="Omega-Veil",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    role="Rogue AI warlord intelligence",
                    tags=["mission_log", "ai_warlord"],
                )
                builder.add_pending_relation(
                    relation_type="opposes",
                    source_entity_id=entity_id,
                    target_query="Prime Construct",
                    source_ref=_ref(source_id, rel_path, line_no, line_no),
                    certainty=default_certainty,
                    tags=["mission_log"],
                )


def _parse_runtime_reference_packet(builder: _RegistryBuilder, source_id: str, rel_path: str, source_path: Path, default_certainty: str) -> None:
    """Phase-2 source consumed by additive ship/logistics layer only."""
    return


def _parse_ship_registry(builder: _RegistryBuilder, source_id: str, rel_path: str, source_path: Path, default_certainty: str) -> None:
    """Phase-2 source consumed by additive ship/logistics layer only."""
    return


def _parse_origin_dossier_logistics(builder: _RegistryBuilder, source_id: str, rel_path: str, source_path: Path, default_certainty: str) -> None:
    """Phase-2 source consumed by additive ship/logistics layer only."""
    return


_PARSER_DISPATCH = {
    "world_bible": _parse_world_bible,
    "location_authority_table": _parse_location_authority_table,
    "marshals_ledger": _parse_marshals_ledger,
    "marshals_sim_capture": _parse_marshals_sim_capture,
    "mission_csv": _parse_mission_csv,
    "runtime_reference_packet": _parse_runtime_reference_packet,
    "ship_registry": _parse_ship_registry,
    "origin_dossier_logistics": _parse_origin_dossier_logistics,
}


def build_l2_registry(workspace_root: Path, base_state: Any) -> L2Registry:
    workspace_root = workspace_root.resolve()
    manifest = _manifest_entries()
    builder = _RegistryBuilder(workspace_root=workspace_root, manifest=manifest)

    for entry in manifest.get("sources", []):
        source_id = str(entry.get("source_id") or "")
        rel_path = str(entry.get("path") or "")
        parser_name = str(entry.get("parser") or "")
        default_certainty = str(entry.get("default_certainty") or "STAGING")
        source_path = workspace_root / rel_path
        if not source_path.exists():
            builder.warnings.append(f"Missing L2 source: {rel_path}")
            continue
        parser = _PARSER_DISPATCH.get(parser_name)
        if parser is None:
            builder.warnings.append(f"No parser registered for source {source_id} ({parser_name})")
            continue
        parser(builder, source_id, rel_path, source_path, default_certainty)

    return builder.finalize(base_state=base_state)


def build_l2_state_bundle(workspace_root: Path, base_state: Any) -> L2StateBundle:
    registry = build_l2_registry(workspace_root=workspace_root, base_state=base_state)
    faction_ids = sorted(getattr(base_state, "factions", {}).keys())
    bundle = registry.to_state_bundle(faction_ids)
    try:
        from l2_phase2 import augment_l2_state_bundle

        return augment_l2_state_bundle(bundle=bundle, workspace_root=workspace_root)
    except Exception as exc:
        bundle.warnings.append(f"Phase 2 additive augmentation failed: {exc}")
        return bundle


def build_empty_l2_state_bundle(*, workspace_root: Path, faction_ids: Iterable[str], warning: str) -> L2StateBundle:
    manifest = _manifest_entries() if _MANIFEST_PATH.exists() else {"schema_version": "missing-manifest", "sources": []}
    return L2StateBundle(
        schema_version="l2-state-bundle-v1",
        manifest_version=str(manifest.get("schema_version") or "unknown"),
        source_manifest_path=str(_MANIFEST_PATH),
        source_manifest_hash=_stable_hash(manifest),
        source_bundle_hash=_stable_hash({"manifest": manifest, "workspace_root": str(workspace_root)}),
        characters={},
        organizations={},
        locations={},
        relations=[],
        indexes={
            "by_alias": {},
            "by_asset_alias": {},
            "by_faction_id": {
                faction_id: {
                    "characters": [],
                    "organizations": [],
                    "locations": [],
                    "mobile_assets": [],
                    "logistics_nodes": [],
                    "pressure_locations": [],
                    "warnings": [],
                }
                for faction_id in sorted(faction_ids)
            },
            "by_location_id": {},
        },
        warnings=[warning],
        unresolved_conflict_count=0,
        deferred_layers={
            "crew_rosters": "phase_3_reserved",
            "route_capacity": "phase_3_reserved",
            "asset_attrition": "phase_3_reserved",
        },
        mobile_assets={},
        logistics_nodes={},
        location_pressures={},
        operational_views={},
    )
