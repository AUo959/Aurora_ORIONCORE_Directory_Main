#!/usr/bin/env python3
"""Advance the integrated GUMAS sim by one turn and write a retrospective."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


LOCAL_TIMEZONE = ZoneInfo("America/New_York")
RISK_HIGH_THRESHOLD = 0.54
STABILITY_LOW_THRESHOLD = 0.48
RISK_DELTA_ALERT_THRESHOLD = 0.005
STABILITY_DELTA_ALERT_THRESHOLD = -0.005
EVENT_SURGE_THRESHOLD = 35
TREND_RISK_SLOPE_3_ALERT_THRESHOLD = 0.0025
TREND_STABILITY_SLOPE_3_ALERT_THRESHOLD = -0.0025
TREND_RISK_VOLATILITY_6_ALERT_THRESHOLD = 0.0100
TREND_STABILITY_VOLATILITY_6_ALERT_THRESHOLD = 0.0100
DEFAULT_ARCHIVE_AFTER_DAYS = 30
HISTORY_SCAN_LIMIT = 120

SUMMARY_PATTERN = re.compile(r"Turn\s+(\d+):\s+stability=([0-9.]+),\s+risk=([0-9.]+),\s+v3_events=(\d+)")
REPORT_FILENAME_PATTERN = re.compile(r"^retrospective_(\d{8}T\d{6}Z)_turn_(\d{4})\.md$")
MAX_EVIDENCE_EVENT_IDS = 5
MAX_EVENT_SPOTLIGHTS = 5
MAX_DETERMINISTIC_SAMPLES = 3


@dataclass
class SnapshotMetrics:
    turn: int
    stability_index: float | None
    risk_index: float | None
    summary: str | None
    event_ledger_path: str | None = None
    event_ledger_record_count: int | None = None
    ledger_checkpoint_hash: str | None = None
    civil_war_factions: list[dict[str, Any]] = field(default_factory=list)
    anchor_hash: str | None = None
    system_components: dict[str, Any] = field(default_factory=dict)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_previous_metrics(snapshot_path: Path) -> SnapshotMetrics | None:
    if not snapshot_path.exists():
        return None

    payload = _load_json(snapshot_path)
    latest = payload.get("latest_metrics") or {}
    return SnapshotMetrics(
        turn=int(payload.get("turn") or 0),
        stability_index=_coerce_float(latest.get("stability_index")),
        risk_index=_coerce_float(latest.get("risk_index")),
        summary=latest.get("summary"),
    )


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.6f}"


def _format_delta(current: float | None, previous: float | None) -> str:
    if current is None or previous is None:
        return "n/a"
    delta = current - previous
    return f"{delta:+.6f}"


def _parse_lock_age_seconds(path: Path) -> float:
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except FileNotFoundError:
        return 0.0


def _acquire_lock(lock_path: Path, stale_seconds: int) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        age = _parse_lock_age_seconds(lock_path)
        if age > stale_seconds:
            lock_path.unlink(missing_ok=True)
        else:
            raise RuntimeError(
                f"Lock is active at {lock_path} (age={age:.1f}s <= stale_seconds={stale_seconds})."
            )

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(lock_path), flags, 0o644)
    try:
        lock_payload = {
            "pid": os.getpid(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        os.write(fd, json.dumps(lock_payload, indent=2).encode("utf-8"))
    finally:
        os.close(fd)


def _release_lock(lock_path: Path) -> None:
    lock_path.unlink(missing_ok=True)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _stable_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _extract_civil_war_factions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    v3_state = payload.get("v3_state")
    if not isinstance(v3_state, dict):
        return []

    insurgencies = v3_state.get("insurgencies")
    if not isinstance(insurgencies, list):
        return []

    civil_wars: list[dict[str, Any]] = []
    for row in insurgencies:
        if not isinstance(row, dict) or row.get("phase") != "civil_war":
            continue
        civil_wars.append(
            {
                "insurgency_id": row.get("insurgency_id"),
                "host_faction_id": row.get("host_faction_id"),
                "phase": row.get("phase"),
                "insurgent_strength": _coerce_float(row.get("insurgent_strength")),
                "territory_controlled": _coerce_float(row.get("territory_controlled")),
                "popular_support": _coerce_float(row.get("popular_support")),
            }
        )

    civil_wars.sort(key=lambda row: str(row.get("host_faction_id") or ""))
    return civil_wars


def _load_turn_event_atoms(ledger_path: str | None, turn: int) -> list[dict[str, Any]]:
    if not ledger_path:
        return []

    path = Path(ledger_path)
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("type") != "event_atom":
                continue
            if int(record.get("turn") or -1) != turn:
                continue
            events.append(record)
    return events


def _ranked_counter(counter: Counter[str], limit: int | None = None) -> list[dict[str, Any]]:
    rows = [{"name": name, "count": count} for name, count in counter.most_common(limit)]
    return rows


def _resolve_named_records(section: dict[str, Any], ids: list[str], *, id_key: str, score_key: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item_id in ids:
        record = section.get(item_id)
        if not isinstance(record, dict):
            continue
        row = {id_key: item_id, "name": record.get("name")}
        if score_key is not None and score_key in record:
            row[score_key] = record.get(score_key)
        rows.append(row)
    return rows


def _build_named_operational_context(*, snapshot_payload: dict[str, Any], top_faction_ids: list[str]) -> dict[str, Any]:
    l2_state = snapshot_payload.get("l2_state")
    if not isinstance(l2_state, dict):
        return {}

    indexes = l2_state.get("indexes")
    if not isinstance(indexes, dict):
        return {}

    by_faction = indexes.get("by_faction_id")
    if not isinstance(by_faction, dict):
        return {}

    character_counter: Counter[str] = Counter()
    organization_counter: Counter[str] = Counter()
    location_counter: Counter[str] = Counter()
    mobile_asset_counter: Counter[str] = Counter()
    logistics_counter: Counter[str] = Counter()
    pressure_counter: Counter[str] = Counter()

    weighted_factions = [faction_id for faction_id in top_faction_ids if faction_id in by_faction]
    for rank, faction_id in enumerate(weighted_factions):
        bucket = by_faction.get(faction_id)
        if not isinstance(bucket, dict):
            continue
        weight = max(1, len(weighted_factions) - rank)
        for entity_id in bucket.get("characters") or []:
            character_counter[str(entity_id)] += weight
        for entity_id in bucket.get("organizations") or []:
            organization_counter[str(entity_id)] += weight
        for entity_id in bucket.get("locations") or []:
            location_counter[str(entity_id)] += weight
        for asset_id in bucket.get("mobile_assets") or []:
            mobile_asset_counter[str(asset_id)] += weight
        for node_id in bucket.get("logistics_nodes") or []:
            logistics_counter[str(node_id)] += weight
        for pressure_id in bucket.get("pressure_locations") or []:
            pressure_counter[str(pressure_id)] += weight

    operational_views = l2_state.get("operational_views")
    hotspots = operational_views.get("hotspots") if isinstance(operational_views, dict) else {}

    named_context = {
        "top_named_characters": [
            {"entity_id": entity_id, "name": l2_state.get("characters", {}).get(entity_id, {}).get("name"), "weight": count}
            for entity_id, count in character_counter.most_common(5)
            if l2_state.get("characters", {}).get(entity_id)
        ],
        "top_named_organizations": [
            {"entity_id": entity_id, "name": l2_state.get("organizations", {}).get(entity_id, {}).get("name"), "weight": count}
            for entity_id, count in organization_counter.most_common(5)
            if l2_state.get("organizations", {}).get(entity_id)
        ],
        "top_named_locations": [
            {"entity_id": entity_id, "name": l2_state.get("locations", {}).get(entity_id, {}).get("name"), "weight": count}
            for entity_id, count in location_counter.most_common(5)
            if l2_state.get("locations", {}).get(entity_id)
        ],
        "top_mobile_assets": [
            {"asset_id": asset_id, "name": l2_state.get("mobile_assets", {}).get(asset_id, {}).get("name"), "weight": count}
            for asset_id, count in mobile_asset_counter.most_common(5)
            if l2_state.get("mobile_assets", {}).get(asset_id)
        ],
        "logistics_hotspots": [
            {
                "node_id": node_id,
                "name": l2_state.get("logistics_nodes", {}).get(node_id, {}).get("name"),
                "throughput_score": l2_state.get("logistics_nodes", {}).get(node_id, {}).get("throughput_score"),
            }
            for node_id, count in logistics_counter.most_common(5)
            if l2_state.get("logistics_nodes", {}).get(node_id)
        ],
        "pressure_hotspots": [
            {
                "pressure_id": pressure_id,
                "name": l2_state.get("location_pressures", {}).get(pressure_id, {}).get("name"),
                "severity": l2_state.get("location_pressures", {}).get(pressure_id, {}).get("severity"),
            }
            for pressure_id, count in pressure_counter.most_common(5)
            if l2_state.get("location_pressures", {}).get(pressure_id)
        ],
    }

    if not named_context["logistics_hotspots"] and isinstance(hotspots, dict):
        named_context["logistics_hotspots"] = list(hotspots.get("logistics") or [])
    if not named_context["pressure_hotspots"] and isinstance(hotspots, dict):
        named_context["pressure_hotspots"] = list(hotspots.get("location_pressures") or [])
    return named_context


def _render_named_operational_context(named_context: Any) -> list[str]:
    if not isinstance(named_context, dict):
        return ["- `none`"]

    sections = [
        ("Named actors", named_context.get("top_named_characters") or []),
        ("Named organizations", named_context.get("top_named_organizations") or []),
        ("Named locations", named_context.get("top_named_locations") or []),
        ("Mobile assets", named_context.get("top_mobile_assets") or []),
        ("Logistics hotspots", named_context.get("logistics_hotspots") or []),
        ("Pressure hotspots", named_context.get("pressure_hotspots") or []),
    ]
    lines: list[str] = []
    for label, items in sections:
        if not isinstance(items, list) or not items:
            lines.append(f"- {label}: `none`")
            continue
        rendered = ", ".join(str(item.get("name") or "n/a") for item in items[:5] if isinstance(item, dict))
        lines.append(f"- {label}: `{rendered or 'none'}`")
    return lines


def _format_metric_value(value: float | None, *, places: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{places}f}"


def _event_numeric_score(event: dict[str, Any]) -> float:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    event_type = str(event.get("event_type") or "")
    if event_type == "REFUGEE_CRISIS":
        return max(
            _coerce_float(payload.get("demographic_stress")) or 0.0,
            _coerce_float(payload.get("refugee_population")) or 0.0,
        )
    if event_type == "POPULATION_MIGRATION":
        return (_coerce_float(payload.get("magnitude")) or 0.0) * 10.0
    if event_type == "INTELLIGENCE_COMPROMISE":
        return max(0.0, 1.0 - (_coerce_float(payload.get("ci_strength")) or 0.0))
    if event_type == "SURVEILLANCE_EXPANSION":
        return abs(_coerce_float(payload.get("legitimacy_penalty")) or 0.0) * 10.0
    if event_type == "CIVIL_WAR_ONSET":
        return max(
            _coerce_float(payload.get("insurgent_strength")) or 0.0,
            _coerce_float(payload.get("territory_controlled")) or 0.0,
        )
    if event_type == "STATE_FRAGMENTATION":
        return max(
            _coerce_float(payload.get("fragmentation_risk")) or 0.0,
            _coerce_float(payload.get("territory_split")) or 0.0,
        )
    if event_type == "MASS_CONSCRIPTION":
        return min(1.0, ((_coerce_float(payload.get("active_insurgencies")) or 0.0) * 0.75))
    if event_type == "TECH_NODE_UNLOCKED":
        return 0.6
    if event_type == "TECH_DIFFUSION":
        return (_coerce_float(payload.get("amount")) or 0.0) * 10.0

    for value in payload.values():
        if isinstance(value, (float, int)):
            return float(abs(value))
    return 0.0


def _render_event_summary(event: dict[str, Any]) -> str:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    event_type = str(event.get("event_type") or "UNKNOWN")
    if event_type == "POPULATION_MIGRATION":
        return (
            f"{payload.get('origin', 'unknown')} -> {payload.get('destination', 'unknown')} "
            f"migration magnitude={_format_metric_value(_coerce_float(payload.get('magnitude')), places=4)}"
        )
    if event_type == "REFUGEE_CRISIS":
        return (
            f"{payload.get('faction_id', 'unknown')} refugee stress="
            f"{_format_metric_value(_coerce_float(payload.get('demographic_stress')))} "
            f"refugee_population={_format_metric_value(_coerce_float(payload.get('refugee_population')))}"
        )
    if event_type == "INTELLIGENCE_COMPROMISE":
        return (
            f"{payload.get('defending_faction', 'unknown')} compromised by "
            f"{payload.get('adversary_faction', 'unknown')} ci_strength="
            f"{_format_metric_value(_coerce_float(payload.get('ci_strength')))}"
        )
    if event_type == "SURVEILLANCE_EXPANSION":
        return (
            f"{payload.get('faction_id', 'unknown')} surveillance={payload.get('level', 'unknown')} "
            f"legitimacy_penalty={_format_metric_value(_coerce_float(payload.get('legitimacy_penalty')))}"
        )
    if event_type == "CIVIL_WAR_ONSET":
        return (
            f"{payload.get('faction_id', 'unknown')} civil war onset insurgent_strength="
            f"{_format_metric_value(_coerce_float(payload.get('insurgent_strength')))} "
            f"territory={_format_metric_value(_coerce_float(payload.get('territory_controlled')))}"
        )
    if event_type == "STATE_FRAGMENTATION":
        return (
            f"{payload.get('faction_id', 'unknown')} fragmentation_risk="
            f"{_format_metric_value(_coerce_float(payload.get('fragmentation_risk')))} "
            f"territory_split={_format_metric_value(_coerce_float(payload.get('territory_split')))}"
        )
    if event_type == "MASS_CONSCRIPTION":
        return (
            f"{payload.get('faction_id', 'unknown')} mass conscription trigger={payload.get('trigger', 'unknown')} "
            f"active_insurgencies={payload.get('active_insurgencies', 'n/a')}"
        )
    if event_type == "TECH_NODE_UNLOCKED":
        return (
            f"{payload.get('faction_id', 'unknown')} unlocked {payload.get('node_name', 'unknown_node')} "
            f"({payload.get('node_id', 'unknown')}, category={payload.get('category', 'unknown')})"
        )
    if event_type == "TECH_DIFFUSION":
        return (
            f"{payload.get('source_faction', 'unknown')} -> {payload.get('destination_faction', 'unknown')} "
            f"{payload.get('category', 'unknown')} amount={_format_metric_value(_coerce_float(payload.get('amount')), places=4)}"
        )
    return event_type


def _top_event_refs(events: list[dict[str, Any]], limit: int = MAX_EVIDENCE_EVENT_IDS) -> list[str]:
    ordered = sorted(
        events,
        key=lambda event: (_event_numeric_score(event), str(event.get("event_id") or "")),
        reverse=True,
    )
    refs: list[str] = []
    for event in ordered[:limit]:
        event_id = str(event.get("event_id") or "unknown")
        payload_hash = str(event.get("payload_hash") or "n/a")
        refs.append(f"{event_id} ({payload_hash})")
    return refs


def _deterministic_event_samples(events: list[dict[str, Any]], seed: int, turn: int) -> list[dict[str, Any]]:
    ranked = sorted(
        events,
        key=lambda event: hashlib.sha256(
            f"{seed}:{turn}:{event.get('event_id', '')}".encode("utf-8")
        ).hexdigest(),
    )
    samples: list[dict[str, Any]] = []
    for event in ranked[:MAX_DETERMINISTIC_SAMPLES]:
        samples.append(
            {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "phase": event.get("phase"),
                "payload_hash": event.get("payload_hash"),
                "summary": _render_event_summary(event),
            }
        )
    return samples


def _build_evidence_brief(
    *,
    seed: int,
    generated_at_utc: datetime,
    current_metrics: SnapshotMetrics,
    snapshot_path: Path,
) -> dict[str, Any]:
    snapshot_payload = _load_json(snapshot_path)
    turn_events = _load_turn_event_atoms(current_metrics.event_ledger_path, current_metrics.turn)

    phase_counts: Counter[str] = Counter()
    event_type_counts: Counter[str] = Counter()
    faction_counts: Counter[str] = Counter()
    defending_factions: set[str] = set()

    for event in turn_events:
        phase = str(event.get("phase") or "unknown")
        event_type = str(event.get("event_type") or "unknown")
        phase_counts[phase] += 1
        event_type_counts[event_type] += 1

        for faction_id in event.get("faction_ids") or []:
            faction_counts[str(faction_id)] += 1

        payload = event.get("payload")
        if isinstance(payload, dict):
            defending_faction = payload.get("defending_faction")
            if defending_faction:
                defending_factions.add(str(defending_faction))

    population_events = [event for event in turn_events if event.get("phase") == "population"]
    intelligence_events = [event for event in turn_events if event.get("phase") == "intelligence"]
    rebellion_events = [event for event in turn_events if event.get("phase") == "rebellion"]
    technology_events = [event for event in turn_events if event.get("phase") == "technology"]

    migration_events = [event for event in turn_events if event.get("event_type") == "POPULATION_MIGRATION"]
    refugee_events = [event for event in turn_events if event.get("event_type") == "REFUGEE_CRISIS"]
    intelligence_compromises = [
        event for event in turn_events if event.get("event_type") == "INTELLIGENCE_COMPROMISE"
    ]
    surveillance_expansions = [
        event for event in turn_events if event.get("event_type") == "SURVEILLANCE_EXPANSION"
    ]
    civil_war_onsets = [event for event in turn_events if event.get("event_type") == "CIVIL_WAR_ONSET"]
    state_fragmentations = [event for event in turn_events if event.get("event_type") == "STATE_FRAGMENTATION"]
    tech_diffusions = [event for event in turn_events if event.get("event_type") == "TECH_DIFFUSION"]

    civil_war_factions = list(current_metrics.civil_war_factions)
    conflict_pressure = _coerce_float(current_metrics.system_components.get("conflict_pressure"))
    insurgency_pressure = _coerce_float(current_metrics.system_components.get("insurgency_pressure"))
    active_insurgency_count = current_metrics.system_components.get("active_insurgency_count")

    claims: list[dict[str, Any]] = []
    if turn_events:
        claims.append(
            {
                "claim_id": "population_pressure_dominates",
                "statement": (
                    f"Civilian stress and displacement remained a major pressure vector in turn {current_metrics.turn}: "
                    f"population accounted for {len(population_events)}/{len(turn_events)} event atoms, "
                    f"while conflict_pressure remained {_format_metric_value(conflict_pressure)} and "
                    f"insurgency_pressure remained {_format_metric_value(insurgency_pressure)}."
                ),
                "evidence": [
                    f"phase_counts population={phase_counts.get('population', 0)} intelligence={phase_counts.get('intelligence', 0)} "
                    f"rebellion={phase_counts.get('rebellion', 0)} technology={phase_counts.get('technology', 0)}",
                    f"event_type_counts POPULATION_MIGRATION={len(migration_events)} REFUGEE_CRISIS={len(refugee_events)}",
                ],
                "event_refs": _top_event_refs(population_events),
                "falsifier": (
                    f"This claim is false if recomputing turn {current_metrics.turn} from ledger checkpoint "
                    f"{current_metrics.ledger_checkpoint_hash or 'n/a'} yields no population events, or if conflict_pressure "
                    f"is not {_format_metric_value(conflict_pressure)} in the exported snapshot."
                ),
            }
        )

        if civil_war_factions:
            civil_war_labels = ", ".join(
                str(row.get("host_faction_id") or "unknown") for row in civil_war_factions
            )
            claims.append(
                {
                    "claim_id": "civil_war_regime_persists",
                    "statement": (
                        f"Civil-war conditions persisted in {len(civil_war_factions)} factions: {civil_war_labels}."
                    ),
                    "evidence": [
                        f"active_insurgency_count={active_insurgency_count}",
                        "civil_war_factions="
                        + ", ".join(
                            (
                                f"{row.get('host_faction_id')} territory={_format_metric_value(_coerce_float(row.get('territory_controlled')))} "
                                f"support={_format_metric_value(_coerce_float(row.get('popular_support')))}"
                            )
                            for row in civil_war_factions
                        ),
                        f"event_type_counts CIVIL_WAR_ONSET={len(civil_war_onsets)} STATE_FRAGMENTATION={len(state_fragmentations)}",
                    ],
                    "event_refs": _top_event_refs(civil_war_onsets + state_fragmentations),
                    "falsifier": (
                        "This claim is false if the exported `v3_state.insurgencies` list does not contain these factions "
                        "with `phase=civil_war`, or if the rebellion events referenced above are absent from the same ledger checkpoint."
                    ),
                }
            )

        if intelligence_compromises or surveillance_expansions:
            claims.append(
                {
                    "claim_id": "intelligence_pressure_broad",
                    "statement": (
                        f"Intelligence pressure remained broad, with {len(intelligence_compromises)} compromise events "
                        f"touching {len(defending_factions)} defending factions and {len(surveillance_expansions)} surveillance expansions."
                    ),
                    "evidence": [
                        f"phase_count intelligence={phase_counts.get('intelligence', 0)}",
                        "defending_factions=" + ", ".join(sorted(defending_factions)) if defending_factions else "defending_factions=none",
                        f"event_type_counts INTELLIGENCE_COMPROMISE={len(intelligence_compromises)} "
                        f"SURVEILLANCE_EXPANSION={len(surveillance_expansions)}",
                    ],
                    "event_refs": _top_event_refs(intelligence_compromises + surveillance_expansions),
                    "falsifier": (
                        "This claim is false if replaying the same turn yields fewer intelligence events or a different defending-faction set "
                        "from the same event IDs."
                    ),
                }
            )

        if tech_diffusions:
            claims.append(
                {
                    "claim_id": "technology_diffusion_background_channel",
                    "statement": (
                        f"Technology diffusion remained a background channel rather than the dominant driver, "
                        f"with {len(tech_diffusions)} diffusion events against {len(turn_events) - len(technology_events)} non-technology events."
                    ),
                    "evidence": [
                        f"phase_count technology={phase_counts.get('technology', 0)}",
                        f"event_type_count TECH_DIFFUSION={len(tech_diffusions)}",
                    ],
                    "event_refs": _top_event_refs(tech_diffusions),
                    "falsifier": (
                        "This claim is false if technology becomes the dominant phase count for the same turn or if the listed diffusion events "
                        "cannot be found in the ledger checkpoint."
                    ),
                }
            )

    dominant_phase = phase_counts.most_common(1)[0][0] if phase_counts else "none"
    narrative_parts: list[str] = []
    if dominant_phase != "none":
        narrative_parts.append(
            f"The observable turn was dominated by {dominant_phase} activity ({phase_counts.get(dominant_phase, 0)} of {len(turn_events)} event atoms)."
        )
    if civil_war_factions:
        narrative_parts.append(
            f"Civil-war state persisted across {len(civil_war_factions)} factions, so L2 instability is still being carried by insurgency rather than interstate conflict."
        )
    if intelligence_compromises or surveillance_expansions:
        narrative_parts.append(
            f"Intelligence compromise remained systemic, with compromise/surveillance activity concentrated in the same turn as civilian stress."
        )
    if tech_diffusions:
        narrative_parts.append(
            "Technology transfer continued, but only as a secondary background signal."
        )
    narrative_summary = " ".join(narrative_parts) if narrative_parts else "No turn-local event atoms were available."

    spotlight_events = sorted(
        turn_events,
        key=lambda event: (_event_numeric_score(event), str(event.get("event_id") or "")),
        reverse=True,
    )[:MAX_EVENT_SPOTLIGHTS]

    top_faction_rows = _ranked_counter(faction_counts, limit=MAX_EVIDENCE_EVENT_IDS)
    named_operational_context = _build_named_operational_context(
        snapshot_payload=snapshot_payload,
        top_faction_ids=[str(row.get("name") or "") for row in top_faction_rows if row.get("name")],
    )

    return {
        "schema_version": "hourly-l2-evidence-v1",
        "generated_at_utc": generated_at_utc.isoformat(),
        "seed": seed,
        "turn": current_metrics.turn,
        "anchor_hash": current_metrics.anchor_hash or _stable_json_hash(snapshot_payload.get("anchor") or {}),
        "ledger_checkpoint_hash": current_metrics.ledger_checkpoint_hash,
        "event_ledger_path": current_metrics.event_ledger_path,
        "turn_event_atom_count": len(turn_events),
        "phase_counts": dict(phase_counts),
        "event_type_counts": dict(event_type_counts),
        "top_factions": top_faction_rows,
        "civil_war_factions": civil_war_factions,
        "supporting_metrics": {
            "conflict_pressure": conflict_pressure,
            "insurgency_pressure": insurgency_pressure,
            "active_insurgency_count": active_insurgency_count,
        },
        "narrative_summary": narrative_summary,
        "named_operational_context": named_operational_context,
        "claims": claims,
        "spotlight_events": [
            {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "phase": event.get("phase"),
                "payload_hash": event.get("payload_hash"),
                "score": _event_numeric_score(event),
                "summary": _render_event_summary(event),
            }
            for event in spotlight_events
        ],
        "deterministic_samples": _deterministic_event_samples(turn_events, seed=seed, turn=current_metrics.turn),
    }


def _extract_event_count(summary: str | None) -> int | None:
    if not summary:
        return None
    match = re.search(r"v3_events=(\d+)", summary)
    if not match:
        return None
    return int(match.group(1))


def _extract_summary_metrics(summary: str | None) -> tuple[int | None, float | None, float | None, int | None]:
    if not summary:
        return None, None, None, None
    match = SUMMARY_PATTERN.search(summary)
    if not match:
        return None, None, None, None
    return int(match.group(1)), float(match.group(2)), float(match.group(3)), int(match.group(4))


def _history_from_report(path: Path) -> dict[str, Any] | None:
    fname_match = REPORT_FILENAME_PATTERN.match(path.name)
    if not fname_match:
        return None
    turn_from_name = int(fname_match.group(2))
    text = path.read_text(encoding="utf-8")
    summary_match = re.search(r"- Summary: `([^`]+)`", text)
    if not summary_match:
        return None
    turn, stability, risk, events = _extract_summary_metrics(summary_match.group(1))
    if turn is None or stability is None or risk is None:
        return None
    if turn != turn_from_name:
        return None
    return {
        "turn": turn,
        "stability": stability,
        "risk": risk,
        "events": events,
        "source": str(path),
    }


def _collect_history_points(report_dir: Path, limit: int = HISTORY_SCAN_LIMIT) -> list[dict[str, Any]]:
    if not report_dir.exists():
        return []
    points: list[dict[str, Any]] = []
    for path in sorted(report_dir.glob("retrospective_*_turn_*.md"))[-limit:]:
        point = _history_from_report(path)
        if point:
            points.append(point)
    return points


def _stddev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _slope(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return (values[-1] - values[0]) / float(len(values) - 1)


def _compute_trends(
    *,
    history_points: list[dict[str, Any]],
    current_metrics: SnapshotMetrics,
    current_event_count: int | None,
) -> dict[str, Any]:
    by_turn: dict[int, dict[str, Any]] = {}
    for point in history_points:
        turn = point.get("turn")
        if isinstance(turn, int):
            by_turn[turn] = point

    if (
        current_metrics.turn is not None
        and current_metrics.stability_index is not None
        and current_metrics.risk_index is not None
    ):
        by_turn[current_metrics.turn] = {
            "turn": current_metrics.turn,
            "stability": current_metrics.stability_index,
            "risk": current_metrics.risk_index,
            "events": current_event_count,
            "source": "current_run",
        }

    ordered = [by_turn[t] for t in sorted(by_turn.keys())]

    stability_values = [float(p["stability"]) for p in ordered if isinstance(p.get("stability"), (float, int))]
    risk_values = [float(p["risk"]) for p in ordered if isinstance(p.get("risk"), (float, int))]
    event_values = [int(p["events"]) for p in ordered if isinstance(p.get("events"), int)]

    stability_last_3 = stability_values[-3:]
    risk_last_3 = risk_values[-3:]
    stability_last_6 = stability_values[-6:]
    risk_last_6 = risk_values[-6:]

    return {
        "history_points_considered": len(ordered),
        "stability_slope_3": _slope(stability_last_3),
        "risk_slope_3": _slope(risk_last_3),
        "stability_volatility_6": _stddev(stability_last_6),
        "risk_volatility_6": _stddev(risk_last_6),
        "event_mean_6": (sum(event_values[-6:]) / len(event_values[-6:])) if event_values[-6:] else None,
    }


def _archive_old_reports(
    *,
    report_dir: Path,
    archive_dir: Path,
    archive_after_days: int,
) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc).timestamp() - max(0, archive_after_days) * 86400
    archived_count = 0
    archived_evidence_count = 0

    for path in sorted(report_dir.glob("retrospective_*_turn_*.md")):
        match = REPORT_FILENAME_PATTERN.match(path.name)
        if not match:
            continue
        stamp = match.group(1)
        try:
            run_dt = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if run_dt.timestamp() > cutoff:
            continue

        bucket = run_dt.strftime("%Y-%m")
        destination_dir = archive_dir / bucket
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / path.name
        os.replace(str(path), str(destination))
        archived_count += 1

        evidence_path = path.with_suffix(".evidence.json")
        if evidence_path.exists():
            os.replace(str(evidence_path), str(destination_dir / evidence_path.name))
            archived_evidence_count += 1

    return {
        "archive_dir": str(archive_dir),
        "archive_after_days": archive_after_days,
        "archived_report_count": archived_count,
        "archived_evidence_count": archived_evidence_count,
    }


def _import_engine(engine_dir: Path):
    sys.path.insert(0, str(engine_dir))
    from engine import GUMASEngine  # type: ignore

    return GUMASEngine


def _run_simulation(engine_dir: Path, seed: int, turns: int, snapshot_path: Path) -> SnapshotMetrics:
    GUMASEngine = _import_engine(engine_dir)
    engine = GUMASEngine(seed=seed)
    engine.init_scenario()
    results = engine.run(max(0, turns))

    if hasattr(engine, "export_advanced_state"):
        engine.export_advanced_state(
            str(snapshot_path),
            include_base_history=False,
            include_advanced_history=False,
        )
    else:
        engine.export_state(str(snapshot_path), include_history=False)

    latest_summary = None
    latest_stability = None
    latest_risk = None
    latest_turn = turns
    if results:
        latest = results[-1]
        latest_turn = int(getattr(latest, "turn", latest_turn))
        latest_summary = getattr(latest, "summary", None)
        if callable(latest_summary):
            latest_summary = latest_summary()
        latest_stability = _coerce_float(getattr(latest, "stability_index", None))
        latest_risk = _coerce_float(getattr(latest, "risk_index", None))

    payload = _load_json(snapshot_path)
    ledger_info = payload.get("event_ledger") or {}
    latest_payload = payload.get("latest_metrics") or {}
    ledger_path = ledger_info.get("path")
    ledger_count = ledger_info.get("record_count")
    ledger_checkpoint_hash = None
    components = latest_payload.get("system_components")
    if not isinstance(ledger_path, str):
        ledger_path = None
    elif Path(ledger_path).exists():
        ledger_checkpoint_hash = _sha256_file(Path(ledger_path))
    if not isinstance(ledger_count, int):
        ledger_count = None
    if not isinstance(components, dict):
        components = {}

    if latest_stability is None or latest_risk is None or latest_summary is None:
        latest_turn = int(payload.get("turn") or latest_turn)
        latest_stability = latest_stability if latest_stability is not None else _coerce_float(latest_payload.get("stability_index"))
        latest_risk = latest_risk if latest_risk is not None else _coerce_float(latest_payload.get("risk_index"))
        latest_summary = latest_summary or latest_payload.get("summary")

    return SnapshotMetrics(
        turn=latest_turn,
        stability_index=latest_stability,
        risk_index=latest_risk,
        summary=latest_summary,
        event_ledger_path=ledger_path,
        event_ledger_record_count=ledger_count,
        ledger_checkpoint_hash=ledger_checkpoint_hash,
        civil_war_factions=_extract_civil_war_factions(payload),
        anchor_hash=_stable_json_hash(payload.get("anchor") or {}),
        system_components=dict(components),
    )


def _build_alerts(
    *,
    current_metrics: SnapshotMetrics,
    previous_metrics: SnapshotMetrics | None,
    v3_event_count: int | None,
    trends: dict[str, Any],
) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []

    if current_metrics.risk_index is not None and current_metrics.risk_index >= RISK_HIGH_THRESHOLD:
        alerts.append(
            {
                "code": "RISK_HIGH",
                "severity": "high",
                "message": (
                    f"Risk index {current_metrics.risk_index:.3f} is above threshold {RISK_HIGH_THRESHOLD:.3f}."
                ),
            }
        )

    if current_metrics.stability_index is not None and current_metrics.stability_index <= STABILITY_LOW_THRESHOLD:
        alerts.append(
            {
                "code": "STABILITY_LOW",
                "severity": "high",
                "message": (
                    f"Stability index {current_metrics.stability_index:.3f} is below threshold {STABILITY_LOW_THRESHOLD:.3f}."
                ),
            }
        )

    if previous_metrics is not None:
        risk_delta = None
        stability_delta = None
        if current_metrics.risk_index is not None and previous_metrics.risk_index is not None:
            risk_delta = current_metrics.risk_index - previous_metrics.risk_index
        if current_metrics.stability_index is not None and previous_metrics.stability_index is not None:
            stability_delta = current_metrics.stability_index - previous_metrics.stability_index

        if risk_delta is not None and risk_delta >= RISK_DELTA_ALERT_THRESHOLD:
            alerts.append(
                {
                    "code": "RISK_ACCELERATING",
                    "severity": "medium",
                    "message": (
                        f"Risk increased by {risk_delta:+.3f} (threshold {RISK_DELTA_ALERT_THRESHOLD:+.3f})."
                    ),
                }
            )

        if stability_delta is not None and stability_delta <= STABILITY_DELTA_ALERT_THRESHOLD:
            alerts.append(
                {
                    "code": "STABILITY_DROPPING",
                    "severity": "medium",
                    "message": (
                        f"Stability changed by {stability_delta:+.3f} (threshold {STABILITY_DELTA_ALERT_THRESHOLD:+.3f})."
                    ),
                }
            )

    if v3_event_count is not None and v3_event_count >= EVENT_SURGE_THRESHOLD:
        alerts.append(
            {
                "code": "EVENT_SURGE",
                "severity": "medium",
                "message": f"V3 event count {v3_event_count} is above threshold {EVENT_SURGE_THRESHOLD}.",
            }
        )

    conflict_pressure = _coerce_float(current_metrics.system_components.get("conflict_pressure"))
    insurgency_pressure = _coerce_float(current_metrics.system_components.get("insurgency_pressure"))
    if conflict_pressure is not None and conflict_pressure >= 0.50:
        alerts.append(
            {
                "code": "CONFLICT_PRESSURE_HIGH",
                "severity": "medium",
                "message": f"Conflict pressure {conflict_pressure:.3f} exceeds 0.500.",
            }
        )
    if insurgency_pressure is not None and insurgency_pressure >= 0.50:
        alerts.append(
            {
                "code": "INSURGENCY_PRESSURE_HIGH",
                "severity": "medium",
                "message": f"Insurgency pressure {insurgency_pressure:.3f} exceeds 0.500.",
            }
        )

    risk_slope_3 = _coerce_float(trends.get("risk_slope_3"))
    if risk_slope_3 is not None and risk_slope_3 >= TREND_RISK_SLOPE_3_ALERT_THRESHOLD:
        alerts.append(
            {
                "code": "RISK_UPTREND_3",
                "severity": "medium",
                "message": (
                    f"3-turn risk slope {risk_slope_3:+.4f} exceeds {TREND_RISK_SLOPE_3_ALERT_THRESHOLD:+.4f}."
                ),
            }
        )

    stability_slope_3 = _coerce_float(trends.get("stability_slope_3"))
    if stability_slope_3 is not None and stability_slope_3 <= TREND_STABILITY_SLOPE_3_ALERT_THRESHOLD:
        alerts.append(
            {
                "code": "STABILITY_DOWNTREND_3",
                "severity": "medium",
                "message": (
                    "3-turn stability slope "
                    f"{stability_slope_3:+.4f} is below {TREND_STABILITY_SLOPE_3_ALERT_THRESHOLD:+.4f}."
                ),
            }
        )

    risk_volatility_6 = _coerce_float(trends.get("risk_volatility_6"))
    if risk_volatility_6 is not None and risk_volatility_6 >= TREND_RISK_VOLATILITY_6_ALERT_THRESHOLD:
        alerts.append(
            {
                "code": "RISK_VOLATILE_6",
                "severity": "medium",
                "message": (
                    f"6-turn risk volatility {risk_volatility_6:.4f} exceeds "
                    f"{TREND_RISK_VOLATILITY_6_ALERT_THRESHOLD:.4f}."
                ),
            }
        )

    stability_volatility_6 = _coerce_float(trends.get("stability_volatility_6"))
    if (
        stability_volatility_6 is not None
        and stability_volatility_6 >= TREND_STABILITY_VOLATILITY_6_ALERT_THRESHOLD
    ):
        alerts.append(
            {
                "code": "STABILITY_VOLATILE_6",
                "severity": "medium",
                "message": (
                    f"6-turn stability volatility {stability_volatility_6:.4f} exceeds "
                    f"{TREND_STABILITY_VOLATILITY_6_ALERT_THRESHOLD:.4f}."
                ),
            }
        )

    return alerts


def _build_report(
    *,
    generated_at_utc: datetime,
    seed: int,
    previous_metrics: SnapshotMetrics | None,
    current_metrics: SnapshotMetrics,
    snapshot_path: Path,
    trends: dict[str, Any],
    alerts: list[dict[str, str]],
    evidence_brief: dict[str, Any],
    evidence_path: Path | None,
    latest_evidence_path: Path | None,
) -> str:
    generated_at_local = generated_at_utc.astimezone(LOCAL_TIMEZONE)
    current_event_count = _extract_event_count(current_metrics.summary)
    turn_event_atom_count = evidence_brief.get("turn_event_atom_count")

    lines = [
        "# Hourly Sim Retrospective",
        "",
        "## Run Context",
        f"- Generated at (ET): `{generated_at_local.isoformat()}`",
        f"- Generated at (UTC): `{generated_at_utc.isoformat()}`",
        f"- Seed: `{seed}`",
        f"- Previous turn: `{previous_metrics.turn if previous_metrics else 0}`",
        f"- Current turn: `{current_metrics.turn}`",
        f"- Snapshot path: `{snapshot_path}`",
        f"- Event ledger path: `{current_metrics.event_ledger_path or 'n/a'}`",
        f"- Event ledger records: `{current_metrics.event_ledger_record_count if current_metrics.event_ledger_record_count is not None else 'n/a'}`",
        f"- Ledger checkpoint hash: `{current_metrics.ledger_checkpoint_hash or 'n/a'}`",
        f"- Run anchor hash: `{current_metrics.anchor_hash or 'n/a'}`",
        f"- Evidence JSON path: `{evidence_path if evidence_path is not None else 'n/a'}`",
        f"- Latest evidence JSON path: `{latest_evidence_path if latest_evidence_path is not None else 'n/a'}`",
        "",
        "## Current Snapshot",
        f"- Summary: `{current_metrics.summary or 'n/a'}`",
        f"- Stability index: `{_format_float(current_metrics.stability_index)}`",
        f"- Risk index: `{_format_float(current_metrics.risk_index)}`",
        f"- V3 event count: `{current_event_count if current_event_count is not None else 'n/a'}`",
        f"- Turn event atoms: `{turn_event_atom_count if isinstance(turn_event_atom_count, int) else 'n/a'}`",
        "",
        "## Component Metrics",
        f"- Avg population stability: `{_format_float(_coerce_float(current_metrics.system_components.get('avg_population_stability')))}`",
        f"- Avg leader legitimacy: `{_format_float(_coerce_float(current_metrics.system_components.get('avg_leader_legitimacy')))}`",
        f"- Avg trust: `{_format_float(_coerce_float(current_metrics.system_components.get('avg_trust')))}`",
        f"- Conflict pressure: `{_format_float(_coerce_float(current_metrics.system_components.get('conflict_pressure')))}`",
        f"- Insurgency pressure: `{_format_float(_coerce_float(current_metrics.system_components.get('insurgency_pressure')))}`",
        "",
        "## Trend Metrics",
        f"- 3-turn stability slope: `{_format_float(_coerce_float(trends.get('stability_slope_3')))}`",
        f"- 3-turn risk slope: `{_format_float(_coerce_float(trends.get('risk_slope_3')))}`",
        f"- 6-turn stability volatility: `{_format_float(_coerce_float(trends.get('stability_volatility_6')))}`",
        f"- 6-turn risk volatility: `{_format_float(_coerce_float(trends.get('risk_volatility_6')))}`",
        f"- 6-turn mean event count: `{_format_float(_coerce_float(trends.get('event_mean_6')))}`",
        "",
        "## Alerts",
    ]

    if alerts:
        for alert in alerts:
            lines.append(f"- [{alert['severity']}] {alert['code']}: `{alert['message']}`")
    else:
        lines.append("- `none`")

    lines.extend(
        [
            "",
            "## L2 Narrative",
            evidence_brief.get("narrative_summary") or "No deterministic L2 narrative was generated.",
            "",
            "## Named Operational Context",
        ]
    )
    lines.extend(_render_named_operational_context(evidence_brief.get("named_operational_context")))
    lines.extend(["", "## Falsifiable L2 Claims"])

    claims = evidence_brief.get("claims")
    if isinstance(claims, list) and claims:
        for index, claim in enumerate(claims, start=1):
            if not isinstance(claim, dict):
                continue
            lines.extend(
                [
                    f"### Claim {index}",
                    f"- Claim: `{claim.get('statement', 'n/a')}`",
                    f"- Evidence: `{' | '.join(str(item) for item in claim.get('evidence') or ['n/a'])}`",
                    f"- Event refs: `{' | '.join(str(item) for item in claim.get('event_refs') or ['n/a'])}`",
                    f"- Falsifier: `{claim.get('falsifier', 'n/a')}`",
                ]
            )
    else:
        lines.append("- `none`")

    lines.extend(["", "## Event Spotlights"])
    spotlight_events = evidence_brief.get("spotlight_events")
    if isinstance(spotlight_events, list) and spotlight_events:
        for event in spotlight_events:
            if not isinstance(event, dict):
                continue
            lines.append(
                "- "
                f"`{event.get('event_id', 'n/a')}` {event.get('summary', 'n/a')} "
                f"(type={event.get('event_type', 'n/a')}, payload={event.get('payload_hash', 'n/a')})"
            )
    else:
        lines.append("- `none`")

    lines.extend(["", "## Deterministic Samples"])
    deterministic_samples = evidence_brief.get("deterministic_samples")
    if isinstance(deterministic_samples, list) and deterministic_samples:
        for sample in deterministic_samples:
            if not isinstance(sample, dict):
                continue
            lines.append(
                "- "
                f"`{sample.get('event_id', 'n/a')}` {sample.get('summary', 'n/a')} "
                f"(type={sample.get('event_type', 'n/a')}, payload={sample.get('payload_hash', 'n/a')})"
            )
    else:
        lines.append("- `none`")

    lines.extend(["", "## Drift From Prior Run"])

    if previous_metrics is None:
        lines.extend(
            [
                "- Baseline run: `true`",
                "- Drift note: `No prior snapshot was available; this report establishes the baseline.`",
            ]
        )
    else:
        lines.extend(
            [
                f"- Stability delta: `{_format_delta(current_metrics.stability_index, previous_metrics.stability_index)}`",
                f"- Risk delta: `{_format_delta(current_metrics.risk_index, previous_metrics.risk_index)}`",
                f"- Prior summary: `{previous_metrics.summary or 'n/a'}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Next Step",
            f"- Next automation run should resume from turn `{current_metrics.turn}` and advance one additional turn.",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one incremental GUMAS hour and write a retrospective report.")
    parser.add_argument("--workspace", default=".", help="Workspace root path")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed")
    parser.add_argument("--turn-step", type=int, default=1, help="How many turns to advance from the previous snapshot")
    parser.add_argument("--dry-run", action="store_true", help="Compute one run without writing snapshot/report artifacts.")
    parser.add_argument("--no-lock", action="store_true", help="Disable lock file protection for this run.")
    parser.add_argument("--no-archive", action="store_true", help="Disable automatic archival of older retrospective reports.")
    parser.add_argument("--archive-dir", default=None, help="Archive directory for old report files.")
    parser.add_argument(
        "--archive-after-days",
        type=int,
        default=DEFAULT_ARCHIVE_AFTER_DAYS,
        help=f"Archive report files older than this many days (default: {DEFAULT_ARCHIVE_AFTER_DAYS}).",
    )
    parser.add_argument("--lock-path", default=None, help="Optional lock file path.")
    parser.add_argument(
        "--lock-stale-seconds",
        type=int,
        default=7200,
        help="Age threshold for considering an existing lock stale.",
    )
    parser.add_argument(
        "--snapshot",
        default=None,
        help="Optional snapshot JSON path (default: workspace/GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/advanced_skill_output.json)",
    )
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Optional report directory (default: workspace/GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/hourly_retrospectives)",
    )
    parser.add_argument(
        "--latest-report",
        default=None,
        help="Optional path for a stable copy of the latest report (default: workspace/GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/hourly_retrospective_latest.md)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    engine_dir = workspace / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
    if not engine_dir.is_dir():
        raise FileNotFoundError(f"Engine directory not found: {engine_dir}")

    snapshot_path = (
        Path(args.snapshot).resolve()
        if args.snapshot
        else engine_dir / "advanced_skill_output.json"
    )
    report_dir = (
        Path(args.report_dir).resolve()
        if args.report_dir
        else engine_dir / "hourly_retrospectives"
    )
    latest_report_path = (
        Path(args.latest_report).resolve()
        if args.latest_report
        else engine_dir / "hourly_retrospective_latest.md"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    lock_path = (
        Path(args.lock_path).resolve()
        if args.lock_path
        else engine_dir / "hourly_retrospective.lock"
    )

    if not args.no_lock:
        _acquire_lock(lock_path, max(1, args.lock_stale_seconds))
    dry_run_tmp_dir: Path | None = None
    try:
        previous_metrics = _read_previous_metrics(snapshot_path)
        previous_turn = previous_metrics.turn if previous_metrics else 0
        requested_turn = max(0, previous_turn + max(1, args.turn_step))

        simulation_snapshot_path = snapshot_path
        if args.dry_run:
            dry_run_tmp_dir = Path(tempfile.mkdtemp(prefix="gumas_hourly_dryrun_", dir="/tmp"))
            simulation_snapshot_path = dry_run_tmp_dir / "advanced_skill_output.json"

        current_metrics = _run_simulation(
            engine_dir=engine_dir,
            seed=args.seed,
            turns=requested_turn,
            snapshot_path=simulation_snapshot_path,
        )

        current_event_count = _extract_event_count(current_metrics.summary)
        history_points = _collect_history_points(report_dir)
        trends = _compute_trends(
            history_points=history_points,
            current_metrics=current_metrics,
            current_event_count=current_event_count,
        )
        alerts = _build_alerts(
            current_metrics=current_metrics,
            previous_metrics=previous_metrics,
            v3_event_count=current_event_count,
            trends=trends,
        )

        generated_at_utc = datetime.now(timezone.utc)
        stamp = generated_at_utc.strftime("%Y%m%dT%H%M%SZ")
        report_path: Path | None = report_dir / f"retrospective_{stamp}_turn_{current_metrics.turn:04d}.md"
        latest_output_path: Path | None = latest_report_path
        evidence_path: Path | None = report_path.with_suffix(".evidence.json")
        latest_evidence_output_path: Path | None = latest_report_path.with_name(
            f"{latest_report_path.stem}_evidence.json"
        )
        evidence_brief = _build_evidence_brief(
            seed=args.seed,
            generated_at_utc=generated_at_utc,
            current_metrics=current_metrics,
            snapshot_path=simulation_snapshot_path,
        )
        report_text = _build_report(
            generated_at_utc=generated_at_utc,
            seed=args.seed,
            previous_metrics=previous_metrics,
            current_metrics=current_metrics,
            snapshot_path=simulation_snapshot_path,
            trends=trends,
            alerts=alerts,
            evidence_brief=evidence_brief,
            evidence_path=evidence_path,
            latest_evidence_path=latest_evidence_output_path,
        )
        evidence_text = json.dumps(evidence_brief, indent=2, sort_keys=True) + "\n"

        archive_dir = Path(args.archive_dir).resolve() if args.archive_dir else report_dir / "archive"
        archive_stats: dict[str, Any] = {
            "archive_dir": str(archive_dir),
            "archive_after_days": int(args.archive_after_days),
            "archived_report_count": 0,
            "archived_evidence_count": 0,
        }
        if not args.dry_run:
            _atomic_write_text(report_path, report_text)
            _atomic_write_text(latest_report_path, report_text)
            _atomic_write_text(evidence_path, evidence_text)
            _atomic_write_text(latest_evidence_output_path, evidence_text)
            if not args.no_archive:
                archive_stats = _archive_old_reports(
                    report_dir=report_dir,
                    archive_dir=archive_dir,
                    archive_after_days=max(0, int(args.archive_after_days)),
                )
        else:
            report_path = None
            latest_output_path = None
            evidence_path = None
            latest_evidence_output_path = None

        payload = {
            "workspace": str(workspace),
            "engine_dir": str(engine_dir),
            "seed": args.seed,
            "dry_run": args.dry_run,
            "lock_path": str(lock_path),
            "previous_turn": previous_turn,
            "current_turn": current_metrics.turn,
            "snapshot_path": str(snapshot_path),
            "simulation_snapshot_path": str(simulation_snapshot_path),
            "report_path": str(report_path) if report_path is not None else None,
            "latest_report_path": str(latest_output_path) if latest_output_path is not None else None,
            "evidence_report_path": str(evidence_path) if evidence_path is not None else None,
            "latest_evidence_report_path": (
                str(latest_evidence_output_path) if latest_evidence_output_path is not None else None
            ),
            "stability_index": current_metrics.stability_index,
            "risk_index": current_metrics.risk_index,
            "stability_delta": (
                None
                if previous_metrics is None or current_metrics.stability_index is None or previous_metrics.stability_index is None
                else current_metrics.stability_index - previous_metrics.stability_index
            ),
            "risk_delta": (
                None
                if previous_metrics is None or current_metrics.risk_index is None or previous_metrics.risk_index is None
                else current_metrics.risk_index - previous_metrics.risk_index
            ),
            "summary": current_metrics.summary,
            "v3_event_count": current_event_count,
            "event_ledger_path": current_metrics.event_ledger_path,
            "event_ledger_record_count": current_metrics.event_ledger_record_count,
            "ledger_checkpoint_hash": current_metrics.ledger_checkpoint_hash,
            "anchor_hash": current_metrics.anchor_hash,
            "system_components": dict(current_metrics.system_components),
            "trend_metrics": trends,
            "alerts": alerts,
            "evidence_brief": evidence_brief,
            "archive": archive_stats,
            "generated_at_utc": generated_at_utc.isoformat(),
        }
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        if dry_run_tmp_dir is not None:
            shutil.rmtree(dry_run_tmp_dir, ignore_errors=True)
        if not args.no_lock:
            _release_lock(lock_path)


if __name__ == "__main__":
    raise SystemExit(main())
