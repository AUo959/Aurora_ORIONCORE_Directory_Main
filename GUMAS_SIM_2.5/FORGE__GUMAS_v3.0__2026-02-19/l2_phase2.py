#!/usr/bin/env python3
"""Additive phase-2 L2 runtime layers for ships, logistics, and location pressure."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _normalize_key(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def _read_lines(path: Path) -> List[tuple[int, str]]:
    return list(enumerate(path.read_text(encoding="utf-8").splitlines(), start=1))


def _source_ref(source_id: str, rel_path: str, line_start: int, line_end: int) -> Dict[str, Any]:
    return {
        "source_id": source_id,
        "path": rel_path,
        "line_start": line_start,
        "line_end": line_end,
    }


def _copy_source_refs(source_refs: Iterable[Any]) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for ref in source_refs:
        if hasattr(ref, "to_dict"):
            refs.append(ref.to_dict())
        elif isinstance(ref, dict):
            refs.append(dict(ref))
    return refs


def _asset_aliases(name: str, aliases: Iterable[str]) -> List[str]:
    values = {alias.strip() for alias in aliases if str(alias).strip()}
    stripped = re.sub(r"^[A-Z](?:\.[A-Z])+\.\s*", "", name).strip()
    if stripped and _normalize_key(stripped) != _normalize_key(name):
        values.add(stripped)
    if name.startswith("G.U.S. "):
        values.add(name.replace("G.U.S. ", "", 1))
    return sorted(values)


def _allegiance_to_factions(allegiance: str) -> List[str]:
    mapping = {
        "galactic_union": ["galactic_union"],
        "ai_warlord_collective": ["ai_warlord"],
        "separatist_confederation": ["separatist_confed"],
        "velar_imperium": ["velar_imperium"],
        "outer_colonies": ["outer_colonies"],
        "pmc_syndicate": ["pmc_syndicate"],
        "neutral": [],
        "contested": [],
    }
    return list(mapping.get(allegiance, []))


def _extract_json_block(text: str, heading: str) -> list[dict[str, Any]]:
    marker = f"### {heading}"
    if marker not in text:
        return []
    segment = text.split(marker, 1)[1]
    if "```json" not in segment:
        return []
    block = segment.split("```json", 1)[1].split("```", 1)[0].strip()
    if not block:
        return []
    payload = json.loads(block)
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def _location_lookup(bundle: Any) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for location_id, entity in sorted(getattr(bundle, "locations", {}).items()):
        names = [getattr(entity, "name", "")] + list(getattr(entity, "aliases", []))
        for name in names:
            key = _normalize_key(str(name))
            if key:
                lookup[key] = location_id
    return lookup


def _entity_name_map(section: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for entity_id, entity in sorted(section.items()):
        result[entity_id] = str(getattr(entity, "name", ""))
    return result


def _merge_scalar_conflict(record: Dict[str, Any], field_name: str, incoming: Any, source_ref: Dict[str, Any]) -> None:
    if incoming in (None, "", []):
        return
    existing = record.get(field_name)
    if existing in (None, "", []):
        record[field_name] = incoming
        return
    if existing != incoming:
        record.setdefault("conflict_flags", []).append(
            {
                "type": "field_conflict",
                "field": field_name,
                "existing": existing,
                "incoming": incoming,
                "source_ref": source_ref,
            }
        )


def _dedupe_source_refs(refs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[tuple[str, str, int, int], Dict[str, Any]] = {}
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        key = (
            str(ref.get('source_id') or ''),
            str(ref.get('path') or ''),
            int(ref.get('line_start') or 0),
            int(ref.get('line_end') or 0),
        )
        deduped[key] = dict(ref)
    return [deduped[key] for key in sorted(deduped)]


def _merge_string_lists(*values: Iterable[str]) -> List[str]:
    merged: set[str] = set()
    for group in values:
        for item in group:
            text = str(item).strip()
            if text:
                merged.add(text)
    return sorted(merged)


def _merge_mobile_asset(assets: Dict[str, Dict[str, Any]], incoming: Dict[str, Any]) -> None:
    asset_id = str(incoming["asset_id"])
    if asset_id not in assets:
        assets[asset_id] = incoming
        return
    current = assets[asset_id]
    for list_field in ("aliases", "faction_bindings", "tags", "doc_sources"):
        current[list_field] = _merge_string_lists(current.get(list_field, []), incoming.get(list_field, []))
    current['source_refs'] = _dedupe_source_refs([*current.get('source_refs', []), *incoming.get('source_refs', [])])
    for field_name in ("name", "certainty", "status", "class_id", "allegiance", "commanding_officer", "home_port", "movement_policy", "notes"):
        _merge_scalar_conflict(current, field_name, incoming.get(field_name), incoming["source_refs"][0])


def _line_for_needle(lines: List[tuple[int, str]], needle: str) -> int:
    for line_no, line in lines:
        if needle in line:
            return line_no
    return 1


def _record_asset(
    *,
    assets: Dict[str, Dict[str, Any]],
    source_id: str,
    rel_path: str,
    certainty: str,
    row: Dict[str, Any],
    line_no: int,
) -> None:
    asset_id = str(row.get("vessel_id") or f"asset_{_slugify(str(row.get('vessel_name') or 'unknown'))}")
    name = str(row.get("vessel_name") or row.get("name") or asset_id)
    aliases = _asset_aliases(name, row.get("aliases") or [])
    allegiance = str(row.get("allegiance") or "")
    movement_policy = "moving_location" if str(row.get("location_type") or "moving") == "moving" else "fixed_position"
    asset = {
        "asset_id": asset_id,
        "name": name,
        "aliases": aliases,
        "entity_kind": "mobile_asset",
        "certainty": str(row.get("certainty") or certainty),
        "source_refs": [_source_ref(source_id, rel_path, line_no, line_no)],
        "status": str(row.get("status") or "active"),
        "faction_bindings": _allegiance_to_factions(allegiance),
        "tags": sorted(
            {
                str(row.get("narrative_significance") or "").strip(),
                str(row.get("class_id") or "").strip(),
                movement_policy,
            }
            - {""}
        ),
        "class_id": row.get("class_id"),
        "allegiance": allegiance or None,
        "commanding_officer": row.get("commanding_officer"),
        "home_port": row.get("home_port"),
        "movement_policy": movement_policy,
        "notes": row.get("notes"),
        "doc_sources": sorted(str(item) for item in row.get("doc_sources") or []),
        "conflict_flags": [],
    }
    _merge_mobile_asset(assets, asset)


def _parse_runtime_assets(*, source_id: str, rel_path: str, source_path: Path, certainty: str, assets: Dict[str, Dict[str, Any]]) -> None:
    text = source_path.read_text(encoding="utf-8")
    lines = _read_lines(source_path)
    for heading in ("3.1 Galactic Union Vessels", "3.2 Non-Union Vessels"):
        for row in _extract_json_block(text, heading):
            name = str(row.get("vessel_name") or row.get("name") or "")
            line_no = _line_for_needle(lines, name) if name else _line_for_needle(lines, heading)
            _record_asset(
                assets=assets,
                source_id=source_id,
                rel_path=rel_path,
                certainty=certainty,
                row=row,
                line_no=line_no,
            )


def _make_logistics_node(*, location_id: str, name: str, source_ref: Dict[str, Any], certainty: str, logistics_role: str, chokepoint_level: str, throughput_score: float, route_signals: Iterable[str], linked_faction_ids: Iterable[str], tags: Iterable[str]) -> Dict[str, Any]:
    return {
        "node_id": f"logistics_{_slugify(name)}_{_slugify(logistics_role)}",
        "location_id": location_id,
        "name": name,
        "certainty": certainty,
        "logistics_role": logistics_role,
        "chokepoint_level": chokepoint_level,
        "throughput_score": round(float(throughput_score), 3),
        "route_signals": sorted(set(str(item) for item in route_signals if str(item))),
        "linked_faction_ids": sorted(set(str(item) for item in linked_faction_ids if str(item))),
        "source_refs": [source_ref],
        "tags": sorted(set(str(item) for item in tags if str(item))),
        "conflict_flags": [],
    }


def _merge_logistics_node(nodes: Dict[str, Dict[str, Any]], incoming: Dict[str, Any]) -> None:
    node_id = incoming["node_id"]
    if node_id not in nodes:
        nodes[node_id] = incoming
        return
    current = nodes[node_id]
    current["source_refs"] = _dedupe_source_refs([*current.get("source_refs", []), *incoming.get("source_refs", [])])
    for list_field in ("route_signals", "linked_faction_ids", "tags"):
        current[list_field] = _merge_string_lists(current.get(list_field, []), incoming.get(list_field, []))
    current["throughput_score"] = round(max(float(current.get("throughput_score") or 0.0), float(incoming.get("throughput_score") or 0.0)), 3)
    if incoming.get("chokepoint_level") == "high":
        current["chokepoint_level"] = "high"
    elif current.get("chokepoint_level") != "high" and incoming.get("chokepoint_level") == "medium":
        current["chokepoint_level"] = "medium"


def _make_location_pressure(*, location_id: str, name: str, source_ref: Dict[str, Any], certainty: str, severity: float, pressure_signals: Iterable[str], driving_faction_ids: Iterable[str], tags: Iterable[str]) -> Dict[str, Any]:
    return {
        "pressure_id": f"pressure_{_slugify(name)}",
        "location_id": location_id,
        "name": name,
        "certainty": certainty,
        "severity": round(float(severity), 3),
        "pressure_signals": sorted(set(str(item) for item in pressure_signals if str(item))),
        "driving_faction_ids": sorted(set(str(item) for item in driving_faction_ids if str(item))),
        "source_refs": [source_ref],
        "tags": sorted(set(str(item) for item in tags if str(item))),
        "conflict_flags": [],
    }


def _merge_location_pressure(pressures: Dict[str, Dict[str, Any]], incoming: Dict[str, Any]) -> None:
    pressure_id = incoming["pressure_id"]
    if pressure_id not in pressures:
        pressures[pressure_id] = incoming
        return
    current = pressures[pressure_id]
    current["source_refs"] = _dedupe_source_refs([*current.get("source_refs", []), *incoming.get("source_refs", [])])
    for list_field in ("pressure_signals", "driving_faction_ids", "tags"):
        current[list_field] = _merge_string_lists(current.get(list_field, []), incoming.get(list_field, []))
    current["severity"] = round(max(float(current.get("severity") or 0.0), float(incoming.get("severity") or 0.0)), 3)


def _parse_origin_dossier_logistics(*, source_id: str, rel_path: str, source_path: Path, certainty: str, location_lookup: Dict[str, str], location_names: Dict[str, str], logistics_nodes: Dict[str, Dict[str, Any]], location_pressures: Dict[str, Dict[str, Any]]) -> None:
    lines = _read_lines(source_path)
    for line_no, line in lines:
        if 'Logistics terrain:' in line:
            for name, role, score in (("Vel-Surak", "trade_hub", 0.92), ("Rethos IV", "trade_hub", 0.86)):
                location_id = location_lookup.get(_normalize_key(name))
                if not location_id:
                    continue
                _merge_logistics_node(
                    logistics_nodes,
                    _make_logistics_node(
                        location_id=location_id,
                        name=location_names.get(location_id, name),
                        source_ref=_source_ref(source_id, rel_path, line_no, line_no),
                        certainty=certainty,
                        logistics_role=role,
                        chokepoint_level='high',
                        throughput_score=score,
                        route_signals=['hyperlane_backbone', 'gate_chokepoint'],
                        linked_faction_ids=[],
                        tags=['origin_dossier', 'high_leverage_hub'],
                    ),
                )
        if 'Black-zone hubs:' in line:
            for name, severity in (("Hollow Expanse", 0.82), ("Draskor-9", 0.79), ("Rethos IV", 0.88)):
                location_id = location_lookup.get(_normalize_key(name))
                if not location_id:
                    continue
                _merge_location_pressure(
                    location_pressures,
                    _make_location_pressure(
                        location_id=location_id,
                        name=location_names.get(location_id, name),
                        source_ref=_source_ref(source_id, rel_path, line_no, line_no),
                        certainty=certainty,
                        severity=severity,
                        pressure_signals=['criminal_pressure', 'black_zone'],
                        driving_faction_ids=[],
                        tags=['origin_dossier', 'law_crime'],
                    ),
                )
        if 'FTL/anomalies:' in line:
            for name, severity in (("Hollow Expanse", 0.76), ("Xyphos Prime ruins", 0.81), ("Kaelor's Rift", 0.74), ("Veil Nebula", 0.72)):
                location_id = location_lookup.get(_normalize_key(name))
                if not location_id:
                    continue
                _merge_location_pressure(
                    location_pressures,
                    _make_location_pressure(
                        location_id=location_id,
                        name=location_names.get(location_id, name),
                        source_ref=_source_ref(source_id, rel_path, line_no, line_no),
                        certainty=certainty,
                        severity=severity,
                        pressure_signals=['anomaly_hazard', 'ftl_instability'],
                        driving_faction_ids=[],
                        tags=['origin_dossier', 'science_packet'],
                    ),
                )


def _synthesize_from_locations(bundle: Any, logistics_nodes: Dict[str, Dict[str, Any]], location_pressures: Dict[str, Dict[str, Any]]) -> None:
    for location_id, entity in sorted(getattr(bundle, 'locations', {}).items()):
        name = str(getattr(entity, 'name', location_id))
        tags = [str(tag) for tag in getattr(entity, 'tags', [])]
        source_refs = _copy_source_refs(getattr(entity, 'source_refs', []))
        source_ref = source_refs[0] if source_refs else {
            'source_id': 'derived_location_layer',
            'path': str(getattr(bundle, 'source_manifest_path', 'unknown')),
            'line_start': 1,
            'line_end': 1,
        }
        certainty = str(getattr(entity, 'certainty', 'STAGING'))
        text = ' '.join([name] + list(getattr(entity, 'aliases', [])) + tags)
        key = _normalize_key(text)
        route_signals: list[str] = []
        pressure_signals: list[str] = []
        throughput_score = 0.0
        severity = 0.0
        logistics_role = 'regional_node'
        chokepoint_level = 'low'

        if any(token in key for token in ('trade', 'hub', 'logistics', 'corridor')):
            route_signals.append('trade_hub')
            throughput_score += 0.35
            logistics_role = 'trade_hub'
        if any(token in key for token in ('hyperlane', 'gate', 'frontier', 'command')):
            route_signals.append('strategic_chokepoint')
            throughput_score += 0.4
            chokepoint_level = 'high' if 'gate' in key or 'hyperlane' in key else 'medium'
        if route_signals:
            _merge_logistics_node(
                logistics_nodes,
                _make_logistics_node(
                    location_id=location_id,
                    name=name,
                    source_ref=source_ref,
                    certainty=certainty,
                    logistics_role=logistics_role,
                    chokepoint_level=chokepoint_level,
                    throughput_score=min(0.95, throughput_score),
                    route_signals=route_signals,
                    linked_faction_ids=list(getattr(entity, 'faction_bindings', [])),
                    tags=['derived_phase2'],
                ),
            )

        if any(token in key for token in ('lawless', 'black district', 'underbelly', 'criminal', 'shadow logistics')):
            pressure_signals.append('criminal_pressure')
            severity += 0.45
        if any(token in key for token in ('restricted', 'precursor', 'anomaly', 'interfere with ship systems')):
            pressure_signals.append('anomaly_hazard')
            severity += 0.35
        if any(token in key for token in ('frontier', 'counter insurgency', 'safe zone / lawless', 'semi unregulated')):
            pressure_signals.append('governance_fragility')
            severity += 0.25
        if pressure_signals:
            _merge_location_pressure(
                location_pressures,
                _make_location_pressure(
                    location_id=location_id,
                    name=name,
                    source_ref=source_ref,
                    certainty=certainty,
                    severity=min(0.95, severity),
                    pressure_signals=pressure_signals,
                    driving_faction_ids=list(getattr(entity, 'faction_bindings', [])),
                    tags=['derived_phase2'],
                ),
            )


def _resolve_asset_home_ports(location_lookup: Dict[str, str], mobile_assets: Dict[str, Dict[str, Any]]) -> None:
    for asset in mobile_assets.values():
        home_port = str(asset.get('home_port') or '').strip()
        if not home_port:
            continue
        location_id = location_lookup.get(_normalize_key(home_port))
        if location_id:
            asset['home_port_location_id'] = location_id


def _ensure_bucket_keys(bundle: Any) -> None:
    for bucket in getattr(bundle, 'indexes', {}).get('by_faction_id', {}).values():
        bucket.setdefault('mobile_assets', [])
        bucket.setdefault('logistics_nodes', [])
        bucket.setdefault('pressure_locations', [])
        bucket.setdefault('warnings', [])
    for bucket in getattr(bundle, 'indexes', {}).get('by_location_id', {}).values():
        bucket.setdefault('mobile_assets', [])
        bucket.setdefault('logistics_nodes', [])
        bucket.setdefault('pressure_ids', [])
        bucket.setdefault('warnings', [])
        bucket.setdefault('faction_ids', [])


def _asset_alias_index(mobile_assets: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for asset_id, asset in sorted(mobile_assets.items()):
        for alias in [asset.get('name', '')] + list(asset.get('aliases', [])):
            key = _normalize_key(str(alias))
            if key:
                index.setdefault(key, []).append(asset_id)
    return {key: sorted(set(ids)) for key, ids in sorted(index.items())}


def _build_named_list(id_list: Iterable[str], records: Dict[str, Dict[str, Any]], id_key: str, score_key: str | None = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for record_id in id_list:
        record = records.get(record_id)
        if not record:
            continue
        row = {id_key: record_id, 'name': record.get('name')}
        if score_key is not None:
            row[score_key] = record.get(score_key)
        rows.append(row)
    return rows


def _build_operational_views(bundle: Any) -> Dict[str, Any]:
    characters = {entity_id: {'name': entity.name} for entity_id, entity in getattr(bundle, 'characters', {}).items()}
    organizations = {entity_id: {'name': entity.name} for entity_id, entity in getattr(bundle, 'organizations', {}).items()}
    locations = {entity_id: {'name': entity.name} for entity_id, entity in getattr(bundle, 'locations', {}).items()}
    mobile_assets = getattr(bundle, 'mobile_assets', {})
    logistics_nodes = getattr(bundle, 'logistics_nodes', {})
    location_pressures = getattr(bundle, 'location_pressures', {})

    faction_views: Dict[str, Any] = {}
    by_faction = getattr(bundle, 'indexes', {}).get('by_faction_id', {})
    for faction_id, bucket in sorted(by_faction.items()):
        faction_views[faction_id] = {
            'characters': _build_named_list(bucket.get('characters', []), characters, 'entity_id'),
            'organizations': _build_named_list(bucket.get('organizations', []), organizations, 'entity_id'),
            'locations': _build_named_list(bucket.get('locations', []), locations, 'entity_id'),
            'mobile_assets': _build_named_list(bucket.get('mobile_assets', []), mobile_assets, 'asset_id'),
            'logistics_nodes': _build_named_list(bucket.get('logistics_nodes', []), logistics_nodes, 'node_id', 'throughput_score'),
            'pressure_locations': _build_named_list(bucket.get('pressure_locations', []), location_pressures, 'pressure_id', 'severity'),
            'warnings': list(bucket.get('warnings', [])),
        }

    hotspots = {
        'logistics': [
            {'node_id': node_id, 'name': node.get('name'), 'throughput_score': node.get('throughput_score'), 'logistics_role': node.get('logistics_role')}
            for node_id, node in sorted(logistics_nodes.items(), key=lambda item: (float(item[1].get('throughput_score') or 0.0), item[0]), reverse=True)[:5]
        ],
        'location_pressures': [
            {'pressure_id': pressure_id, 'name': pressure.get('name'), 'severity': pressure.get('severity'), 'pressure_signals': list(pressure.get('pressure_signals', []))}
            for pressure_id, pressure in sorted(location_pressures.items(), key=lambda item: (float(item[1].get('severity') or 0.0), item[0]), reverse=True)[:5]
        ],
    }
    return {
        'by_faction_id': faction_views,
        'hotspots': hotspots,
    }


def augment_l2_state_bundle(*, bundle: Any, workspace_root: Path) -> Any:
    manifest = json.loads(Path(getattr(bundle, 'source_manifest_path')).read_text(encoding='utf-8'))
    sources = manifest.get('sources', [])
    location_lookup = _location_lookup(bundle)
    location_names = _entity_name_map(getattr(bundle, 'locations', {}))
    mobile_assets: Dict[str, Dict[str, Any]] = {}
    logistics_nodes: Dict[str, Dict[str, Any]] = {}
    location_pressures: Dict[str, Dict[str, Any]] = {}

    for entry in sources:
        source_id = str(entry.get('source_id') or '')
        rel_path = str(entry.get('path') or '')
        parser = str(entry.get('parser') or '')
        certainty = str(entry.get('default_certainty') or 'STAGING')
        source_path = workspace_root / rel_path
        if not source_path.exists():
            continue
        if parser in {'runtime_reference_packet', 'ship_registry'}:
            _parse_runtime_assets(
                source_id=source_id,
                rel_path=rel_path,
                source_path=source_path,
                certainty=certainty,
                assets=mobile_assets,
            )
        elif parser == 'origin_dossier_logistics':
            _parse_origin_dossier_logistics(
                source_id=source_id,
                rel_path=rel_path,
                source_path=source_path,
                certainty=certainty,
                location_lookup=location_lookup,
                location_names=location_names,
                logistics_nodes=logistics_nodes,
                location_pressures=location_pressures,
            )

    _synthesize_from_locations(bundle, logistics_nodes, location_pressures)
    _resolve_asset_home_ports(location_lookup, mobile_assets)

    bundle.mobile_assets = {asset_id: mobile_assets[asset_id] for asset_id in sorted(mobile_assets)}
    bundle.logistics_nodes = {node_id: logistics_nodes[node_id] for node_id in sorted(logistics_nodes)}
    bundle.location_pressures = {pressure_id: location_pressures[pressure_id] for pressure_id in sorted(location_pressures)}

    _ensure_bucket_keys(bundle)
    bundle.indexes['by_asset_alias'] = _asset_alias_index(bundle.mobile_assets)

    for asset_id, asset in bundle.mobile_assets.items():
        for faction_id in asset.get('faction_bindings', []):
            bucket = bundle.indexes['by_faction_id'].setdefault(
                faction_id,
                {
                    'characters': [],
                    'organizations': [],
                    'locations': [],
                    'mobile_assets': [],
                    'logistics_nodes': [],
                    'pressure_locations': [],
                    'warnings': [],
                },
            )
            bucket['mobile_assets'].append(asset_id)
        home_port_location_id = asset.get('home_port_location_id')
        if home_port_location_id:
            location_bucket = bundle.indexes['by_location_id'].setdefault(
                home_port_location_id,
                {
                    'characters': [],
                    'organizations': [],
                    'locations': [],
                    'mobile_assets': [],
                    'logistics_nodes': [],
                    'pressure_ids': [],
                    'faction_ids': [],
                    'warnings': [],
                },
            )
            location_bucket['mobile_assets'].append(asset_id)
            for faction_id in asset.get('faction_bindings', []):
                if faction_id not in location_bucket['faction_ids']:
                    location_bucket['faction_ids'].append(faction_id)

    for node_id, node in bundle.logistics_nodes.items():
        location_bucket = bundle.indexes['by_location_id'].setdefault(
            node['location_id'],
            {
                'characters': [],
                'organizations': [],
                'locations': [],
                'mobile_assets': [],
                'logistics_nodes': [],
                'pressure_ids': [],
                'faction_ids': [],
                'warnings': [],
            },
        )
        location_bucket['logistics_nodes'].append(node_id)
        for faction_id in node.get('linked_faction_ids', []):
            faction_bucket = bundle.indexes['by_faction_id'].setdefault(
                faction_id,
                {
                    'characters': [],
                    'organizations': [],
                    'locations': [],
                    'mobile_assets': [],
                    'logistics_nodes': [],
                    'pressure_locations': [],
                    'warnings': [],
                },
            )
            faction_bucket['logistics_nodes'].append(node_id)
            if faction_id not in location_bucket['faction_ids']:
                location_bucket['faction_ids'].append(faction_id)

    for pressure_id, pressure in bundle.location_pressures.items():
        location_bucket = bundle.indexes['by_location_id'].setdefault(
            pressure['location_id'],
            {
                'characters': [],
                'organizations': [],
                'locations': [],
                'mobile_assets': [],
                'logistics_nodes': [],
                'pressure_ids': [],
                'faction_ids': [],
                'warnings': [],
            },
        )
        location_bucket['pressure_ids'].append(pressure_id)
        for faction_id in pressure.get('driving_faction_ids', []):
            faction_bucket = bundle.indexes['by_faction_id'].setdefault(
                faction_id,
                {
                    'characters': [],
                    'organizations': [],
                    'locations': [],
                    'mobile_assets': [],
                    'logistics_nodes': [],
                    'pressure_locations': [],
                    'warnings': [],
                },
            )
            faction_bucket['pressure_locations'].append(pressure_id)
            if faction_id not in location_bucket['faction_ids']:
                location_bucket['faction_ids'].append(faction_id)

    for bucket in bundle.indexes['by_faction_id'].values():
        for key in ('mobile_assets', 'logistics_nodes', 'pressure_locations'):
            bucket[key] = sorted(set(bucket.get(key, [])))
    for bucket in bundle.indexes['by_location_id'].values():
        for key in ('mobile_assets', 'logistics_nodes', 'pressure_ids', 'faction_ids'):
            bucket[key] = sorted(set(bucket.get(key, [])))

    bundle.operational_views = _build_operational_views(bundle)
    return bundle
