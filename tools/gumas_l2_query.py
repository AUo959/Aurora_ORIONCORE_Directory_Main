#!/usr/bin/env python3
"""Query additive L2 state from a live engine init or exported snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _normalize_key(value: str) -> str:
    import re

    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', value.lower()).split())


def _load_snapshot(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _build_live_bundle(workspace: Path, seed: int) -> Dict[str, Any]:
    engine_dir = workspace / 'GUMAS_SIM_2.5' / 'SIM_ENGINE_OUTPUTS'
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))
    from engine import GUMASEngine  # type: ignore

    engine = GUMASEngine(seed=seed)
    engine.init_scenario()
    v3_state = engine.get_v3_state() if hasattr(engine, 'get_v3_state') else None
    if v3_state is None or getattr(v3_state, 'l2_state', None) is None:
        raise RuntimeError('Live engine did not provide l2_state.')
    return v3_state.l2_state.to_dict()


def _named_rows(section: Dict[str, Any], ids: List[str], id_key: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item_id in ids:
        item = section.get(item_id)
        if item is None:
            continue
        rows.append({id_key: item_id, 'name': item.get('name')})
    return rows


def _query_bundle(bundle: Dict[str, Any], query: str) -> Dict[str, Any]:
    key = _normalize_key(query)
    alias_index = bundle.get('indexes', {}).get('by_alias', {})
    asset_alias_index = bundle.get('indexes', {}).get('by_asset_alias', {})
    entity_ids = alias_index.get(key, [])
    asset_ids = asset_alias_index.get(key, [])
    results = {
        'entity_matches': [],
        'mobile_asset_matches': [],
    }
    for section_name in ('characters', 'organizations', 'locations'):
        section = bundle.get(section_name, {})
        for entity_id in entity_ids:
            entity = section.get(entity_id)
            if entity is None:
                continue
            results['entity_matches'].append({
                'section': section_name,
                'entity_id': entity_id,
                'name': entity.get('name'),
                'aliases': entity.get('aliases', []),
                'faction_bindings': entity.get('faction_bindings', []),
            })
    assets = bundle.get('mobile_assets', {})
    for asset_id in asset_ids:
        asset = assets.get(asset_id)
        if asset is None:
            continue
        results['mobile_asset_matches'].append({
            'asset_id': asset_id,
            'name': asset.get('name'),
            'aliases': asset.get('aliases', []),
            'faction_bindings': asset.get('faction_bindings', []),
            'movement_policy': asset.get('movement_policy'),
        })
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Query the additive GUMAS L2 runtime bundle.')
    parser.add_argument('--workspace', default='.', help='Workspace root for live engine init or default snapshot lookup.')
    parser.add_argument('--snapshot', default=None, help='Optional path to an exported advanced snapshot JSON.')
    parser.add_argument('--seed', type=int, default=42, help='Seed for live engine init when no snapshot is provided.')
    parser.add_argument('--query', default=None, help='Name or alias to resolve across entities and mobile assets.')
    parser.add_argument('--faction-id', default=None, help='Optional faction id for named operational context.')
    parser.add_argument('--location-id', default=None, help='Optional location id for location bucket context.')
    parser.add_argument('--top-hotspots', action='store_true', help='Include current logistics and pressure hotspots.')
    parser.add_argument('--export-path', default=None, help='Optional JSON export path.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    if args.snapshot:
        snapshot = _load_snapshot(Path(args.snapshot).resolve())
        bundle = snapshot.get('l2_state') or {}
    else:
        bundle = _build_live_bundle(workspace, seed=args.seed)

    payload: Dict[str, Any] = {
        'workspace': str(workspace),
        'schema_version': bundle.get('schema_version'),
        'query': args.query,
        'results': _query_bundle(bundle, args.query) if args.query else {'entity_matches': [], 'mobile_asset_matches': []},
        'faction_context': bundle.get('operational_views', {}).get('by_faction_id', {}).get(args.faction_id) if args.faction_id else None,
        'location_context': bundle.get('indexes', {}).get('by_location_id', {}).get(args.location_id) if args.location_id else None,
        'hotspots': bundle.get('operational_views', {}).get('hotspots') if args.top_hotspots else None,
    }

    output = json.dumps(payload, indent=2)
    if args.export_path:
        export_path = Path(args.export_path).resolve()
        export_path.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
