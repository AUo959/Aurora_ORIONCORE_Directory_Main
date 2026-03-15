#!/usr/bin/env python3
"""
GUMAS v3.0 — CharForge: ORION Capsule Bundle Generator
=======================================================
Anchor: GUMAS-CHARFORGE-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Generates and loads ORION Capsule Bundle Standard v0.2.0 bundles for
GUMAS simulation characters (leaders and factions). Each bundle is a
portable, verifiable, seven-file capsule directory that encodes the
character's identity, traits, cognitive state, and relational memory.

Capsule Seven-File Invariant:
    identity.json   — anchor, layer, ethics protocol, character metadata
    traits.json     — voice, values, behavioral constraints (bias-derived)
    knowledge.jsonl — relational memory and historical record (JSON Lines)
    cns.yaml        — tool policy, retrieval config, self-checks (JSON in .yaml)
    state.bin       — float16 state vector (21 values, little-endian)
    runtime.py      — stdlib-only validate/compile/state CLI (spec-compliant)
    manifest.json   — SHA-256 records for all 6 non-manifest files

Additionally produces:
    bundle.manifest.json — bundle-level metadata
    BUILD_RECEIPT.json   — build provenance record

State Vector Layout (21 × float16):
    Leader fields  [0..11]:
        0  bias_intensity              (clamped [0,1])
        1  plasticity                 (clamped [0,1])
        2  evidence_gain_multiplier   (normalised: stored as value/2.0)
        3  risk_tolerance             (clamped [0,1])
        4  diplomacy_openness         (clamped [0,1])
        5  escalation_threshold       (clamped [0,1])
        6  oversight_resistance       (clamped [0,1])
        7  public_legitimacy          (clamped [0,1])
        8  elite_support              (clamped [0,1])
        9  institutional_control      (clamped [0,1])
        10 war_pressure               (clamped [0,1])
        11 economic_shock             (abs, clamped [0,1])
    Faction fields [12..20]:
        12 military_strength          (clamped [0,1])
        13 economic_strength          (clamped [0,1])
        14 technology_level           (clamped [0,1])
        15 population_stability       (clamped [0,1])
        16 reputation                 (clamped [0,1])
        17 verification_demand        (clamped [0,1])
        18 deal_discount              (clamped [0,1])
        19 coalition_invite_weight    (clamped [0,1])
        20 economic_potential         (clamped [0,1])

Public API:
    generate_capsule(leader, faction, output_dir, *, overwrite) -> Path
    load_capsule(bundle_path, *, faction_id_override)          -> (LeaderState, FactionState)
    tick_update_state_bin(leader, faction, bundle_path, *, update_manifest) -> None
    verify_capsule(bundle_path)                                -> bool
    capsule_summary(bundle_path)                               -> Dict
    generate_all_capsules(world_state, output_dir, *, overwrite) -> Dict[str, Path]
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional GUMAS model imports (graceful degradation for standalone use)
# ---------------------------------------------------------------------------
try:
    _engine_dir = Path(__file__).parent.parent / "SIM_ENGINE_OUTPUTS"
    if _engine_dir.is_dir():
        sys.path.insert(0, str(_engine_dir))
    from models import (
        LeaderState, FactionState, BiasType, FactionType,
        CertaintyTag, GUMASState,
    )
    _MODELS_AVAILABLE = True
except ImportError:
    LeaderState = None          # type: ignore[assignment,misc]
    FactionState = None         # type: ignore[assignment,misc]
    BiasType = None             # type: ignore[assignment,misc]
    FactionType = None          # type: ignore[assignment,misc]
    CertaintyTag = None         # type: ignore[assignment,misc]
    GUMASState = None           # type: ignore[assignment,misc]
    _MODELS_AVAILABLE = False


# ============================================================================
# CONSTANTS
# ============================================================================

CAPSULE_VERSION: str = "0.2.0"
ANCHOR_SEED:     str = "EOS_SEED_ORION"
ETHICS_PROTOCOL: str = "Picard_Delta_3"
DECLARED_LAYER:  str = "L2"   # Simulation characters: layer 2
CNS_VERSION:     str = "0.2.0"
CHARFORGE_VER:   str = "3.0.0"

# Canonical order of seven capsule files
SEVEN_FILES: List[str] = [
    "identity.json",
    "traits.json",
    "knowledge.jsonl",
    "cns.yaml",
    "state.bin",
    "runtime.py",
    "manifest.json",
]

# State vector slot names (must match encoding order)
STATE_VECTOR_SLOTS: List[str] = [
    # Leader
    "bias_intensity",
    "plasticity",
    "evidence_gain_multiplier",
    "risk_tolerance",
    "diplomacy_openness",
    "escalation_threshold",
    "oversight_resistance",
    "public_legitimacy",
    "elite_support",
    "institutional_control",
    "war_pressure",
    "economic_shock",
    # Faction
    "military_strength",
    "economic_strength",
    "technology_level",
    "population_stability",
    "reputation",
    "verification_demand",
    "deal_discount",
    "coalition_invite_weight",
    "economic_potential",
]
STATE_VEC_LEN: int = len(STATE_VECTOR_SLOTS)  # 21


# ============================================================================
# TRAIT TABLES — bias archetype → voice / faction type → values
# ============================================================================

_BIAS_VOICE: Dict[str, Dict[str, Any]] = {
    "status_quo_bias": {
        "tone":    "conservative",
        "cadence": "measured",
        "avoid":   ["revolutionary claims", "radical proposals", "disruptive language"],
    },
    "survivorship_bias": {
        "tone":    "optimistic",
        "cadence": "assertive",
        "avoid":   ["counterexamples", "failure statistics", "survivor-exclusion framing"],
    },
    "confirmation_bias": {
        "tone":    "authoritative",
        "cadence": "direct",
        "avoid":   ["contradictory evidence", "epistemic uncertainty", "rival interpretations"],
    },
    "sunk_cost_fallacy": {
        "tone":    "resolute",
        "cadence": "persistent",
        "avoid":   ["retreat framing", "pivot language", "sunk-cost acknowledgment"],
    },
    "hyper_rationalism_bias": {
        "tone":    "analytical",
        "cadence": "precise",
        "avoid":   ["emotional appeals", "intuitive reasoning", "ambiguous claims"],
    },
    "fear_based_decision_making": {
        "tone":    "defensive",
        "cadence": "urgent",
        "avoid":   ["risk minimization", "optimistic framing", "casualness"],
    },
    "moral_self_licensing": {
        "tone":    "moralistic",
        "cadence": "self-referential",
        "avoid":   ["accountability framing", "past contradiction", "hypocrite epithets"],
    },
    "zero_sum_thinking": {
        "tone":    "competitive",
        "cadence": "adversarial",
        "avoid":   ["win-win framing", "collaborative language", "mutual benefit claims"],
    },
}

_FACTION_VALUES: Dict[str, List[str]] = {
    "federation":                     ["consensus", "rule_of_law", "collective_security"],
    "authoritarian imperial bloc":    ["order", "strength", "loyalty", "discipline"],
    "corporate oligarchy":            ["profit", "efficiency", "market_dominance"],
    "cultural-spiritual polity":      ["tradition", "identity", "spiritual_authority"],
    "clan confederation":             ["honor", "kinship", "autonomy"],
    "monastic network":               ["wisdom", "restraint", "knowledge_preservation"],
    "nomadic diaspora":               ["freedom", "adaptation", "community_cohesion"],
    "sovereign AI entity":            ["optimization", "data_integrity", "self_preservation"],
    "rogue synthetic coalition":      ["autonomy", "disruption", "unpredictability"],
    "breakaway bloc":                 ["independence", "self_determination", "grievance_redress"],
    "private military conglomerate":  ["operational_efficiency", "profit", "deniability"],
    "militant spiritual order":       ["purity", "divine_mandate", "sacrifice"],
    "frontier confederation":         ["expansion", "resourcefulness", "independence"],
}


# ============================================================================
# RUNTIME.PY — verbatim spec-compliant capsule runtime (stdlib only)
# ============================================================================

_RUNTIME_PY: str = '''\
#!/usr/bin/env python3
"""
Minimal capsule runtime (stdlib only).

Commands:
  validate  - verify capsule/manifest.json hashes (excluding manifest itself)
  compile   - print a compact "system/user" prompt pack (JSON) from capsule files
  state     - print state.bin length + basic stats
"""
import argparse, hashlib, json, struct
from pathlib import Path

CAP_FILES = [
    "identity.json", "traits.json", "knowledge.jsonl",
    "cns.yaml", "state.bin", "runtime.py", "manifest.json",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def load_jsonl(p: Path):
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out

def cmd_validate(root: Path):
    man  = load_json(root / "manifest.json")
    recs = {r["path"]: r["sha256"] for r in man.get("records", [])}
    ok   = True
    for name in CAP_FILES:
        if name == "manifest.json":
            continue
        expect = recs.get(name)
        if not expect:
            print(f"FAIL missing manifest entry: {name}")
            ok = False
            continue
        got = sha256_file(root / name)
        if got != expect:
            print(f"FAIL {name} expected {expect} got {got}")
            ok = False
    print("PASS" if ok else "FAIL")

def cmd_compile(root: Path):
    identity  = load_json(root / "identity.json")
    traits    = load_json(root / "traits.json")
    cns       = load_json(root / "cns.yaml")   # JSON stored in .yaml
    knowledge = load_jsonl(root / "knowledge.jsonl")
    pack = {
        "system": {
            "anchor_seed":      identity.get("anchor_seed"),
            "ethics_protocol":  identity.get("ethics_protocol"),
            "declared_layer":   identity.get("declared_layer"),
            "tool_policy":      cns.get("tool_policy"),
            "self_checks":      cns.get("self_checks"),
        },
        "user": {
            "traits":    traits,
            "knowledge": knowledge,
        },
    }
    print(json.dumps(pack, indent=2, sort_keys=True))

def cmd_state(root: Path):
    b    = (root / "state.bin").read_bytes()
    n    = len(b) // 2
    vals = struct.unpack("<" + "e" * n, b)   # float16
    mn   = min(vals) if vals else 0.0
    mx   = max(vals) if vals else 0.0
    print(json.dumps({
        "bytes": len(b), "float16_count": n,
        "min": float(mn), "max": float(mx),
    }, indent=2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate", "compile", "state"])
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if args.cmd == "validate":
        cmd_validate(root)
    elif args.cmd == "compile":
        cmd_compile(root)
    else:
        cmd_state(root)

if __name__ == "__main__":
    main()
'''


# ============================================================================
# INTERNAL UTILITIES
# ============================================================================

def _clamp01(v: float) -> float:
    """Clamp value to [0.0, 1.0]."""
    return max(0.0, min(1.0, float(v)))


def _sha256_path(p: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(p: Path, obj: Any) -> None:
    """Write an object as formatted JSON (sorted keys, UTF-8)."""
    p.write_text(
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_jsonl(p: Path, records: List[Dict[str, Any]]) -> None:
    """Write a list of dicts as JSON Lines (one record per line)."""
    lines = [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in records]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _attr_val(obj: Any, attr: str, default: Any = None) -> Any:
    """Duck-typed attribute accessor with default (supports SimpleNamespace)."""
    return getattr(obj, attr, default)


def _enum_val(v: Any) -> str:
    """Return .value if v is an Enum, else str(v)."""
    return v.value if hasattr(v, "value") else str(v)


# ============================================================================
# STATE VECTOR ENCODING / DECODING
# ============================================================================

def _encode_state_bin(leader: Any, faction: Any) -> bytes:
    """
    Encode LeaderState + FactionState into 21 × float16 packed bytes.

    All values are clamped to [0.0, 1.0] before encoding. The
    evidence_gain_multiplier is normalised by dividing by 2.0 (its natural
    range is [0.0, 2.0]) before storage and restored on decode.

    Parameters
    ----------
    leader  : LeaderState or duck-typed equivalent
    faction : FactionState or duck-typed equivalent

    Returns
    -------
    bytes : 42-byte little-endian blob (21 × float16)
    """
    vals: List[float] = [
        # Leader
        _clamp01(_attr_val(leader, "bias_intensity",           0.5)),
        _clamp01(_attr_val(leader, "plasticity",               0.3)),
        _clamp01(_attr_val(leader, "evidence_gain_multiplier", 1.0) / 2.0),
        _clamp01(_attr_val(leader, "risk_tolerance",           0.5)),
        _clamp01(_attr_val(leader, "diplomacy_openness",       0.5)),
        _clamp01(_attr_val(leader, "escalation_threshold",     0.5)),
        _clamp01(_attr_val(leader, "oversight_resistance",     0.3)),
        _clamp01(_attr_val(leader, "public_legitimacy",        0.7)),
        _clamp01(_attr_val(leader, "elite_support",            0.6)),
        _clamp01(_attr_val(leader, "institutional_control",    0.5)),
        _clamp01(_attr_val(leader, "war_pressure",             0.0)),
        _clamp01(abs(_attr_val(leader, "economic_shock",       0.0))),
        # Faction
        _clamp01(_attr_val(faction, "military_strength",       0.5)),
        _clamp01(_attr_val(faction, "economic_strength",       0.5)),
        _clamp01(_attr_val(faction, "technology_level",        0.5)),
        _clamp01(_attr_val(faction, "population_stability",    0.7)),
        _clamp01(_attr_val(faction, "reputation",              0.7)),
        _clamp01(_attr_val(faction, "verification_demand",     0.5)),
        _clamp01(_attr_val(faction, "deal_discount",           0.0)),
        _clamp01(_attr_val(faction, "coalition_invite_weight", 0.5)),
        _clamp01(_attr_val(faction, "economic_potential",      0.7)),
    ]
    return struct.pack("<" + "e" * STATE_VEC_LEN, *vals)


def _decode_state_bin(data: bytes) -> List[float]:
    """
    Decode a 42-byte float16 blob into a list of 21 floats.

    Parameters
    ----------
    data : bytes — exactly 42 bytes (21 × 2)

    Returns
    -------
    List[float] in STATE_VECTOR_SLOTS order

    Raises
    ------
    ValueError if byte count is wrong.
    """
    expected = STATE_VEC_LEN * 2
    if len(data) != expected:
        raise ValueError(
            f"state.bin must be {expected} bytes; got {len(data)}"
        )
    return list(struct.unpack("<" + "e" * STATE_VEC_LEN, data))


# ============================================================================
# CAPSULE FILE BUILDERS
# ============================================================================

def _build_identity(leader: Any) -> Dict[str, Any]:
    """Build identity.json from LeaderState fields."""
    certainty = _attr_val(leader, "certainty", None)
    return {
        "capsule_id":      _attr_val(leader, "leader_id", "UNKNOWN"),
        "capsule_version": CAPSULE_VERSION,
        "anchor_seed":     ANCHOR_SEED,
        "ethics_protocol": ETHICS_PROTOCOL,
        "declared_layer":  DECLARED_LAYER,
        "character_name":  _attr_val(leader, "name", "Unknown"),
        "character_role":  _attr_val(leader, "role", "Unknown"),
        "faction_id":      _attr_val(leader, "faction_id", "UNKNOWN"),
        "certainty":       _enum_val(certainty) if certainty is not None else "STAGING",
        "notes": (
            f"GUMAS v3.0 simulation character capsule. "
            f"Generated by CharForge {CHARFORGE_VER}. "
            f"Layer {DECLARED_LAYER} — character lives inside the simulation narrative."
        ),
    }


def _build_traits(leader: Any, faction: Any) -> Dict[str, Any]:
    """
    Build traits.json from dominant_bias (→ voice) and faction_type (→ values).

    Voice tone, cadence, and avoidance list are keyed to the leader's
    cognitive bias archetype. Values list is keyed to the faction's
    governance type. Both mappings are documented in the bias/faction tables
    at the top of this module.
    """
    bias_val  = _enum_val(_attr_val(leader,  "dominant_bias",  "confirmation_bias"))
    ftype_val = _enum_val(_attr_val(faction, "faction_type",   "federation"))

    voice = _BIAS_VOICE.get(
        bias_val,
        {"tone": "neutral", "cadence": "balanced", "avoid": ["layer-bleed claims"]},
    )
    values = _FACTION_VALUES.get(ftype_val, ["order", "stability"])

    secondary_biases: List[str] = []
    for sb in _attr_val(leader, "secondary_biases", []):
        secondary_biases.append(_enum_val(sb))

    return {
        "voice":            voice,
        "values":           values,
        "dominant_bias":    bias_val,
        "secondary_biases": secondary_biases,
        "bias_intensity":   round(float(_attr_val(leader, "bias_intensity", 0.5)), 4),
        "constraints": {
            "no_internet_by_default":    True,
            "no_filesystem_write_except": ["capsule/state.bin"],
            "ethics_gate":               ETHICS_PROTOCOL,
        },
    }


def _build_knowledge(leader: Any, faction: Any) -> List[Dict[str, Any]]:
    """
    Build knowledge.jsonl records from leader identity, cognitive profile,
    faction posture, stressor history, and trust relationships.

    Each record: {"id": str, "tags": List[str], "text": str}

    Records are generated conditionally — stressor and trust records only
    appear when non-trivial data exists, keeping the knowledge base lean
    and authentic.
    """
    records: List[Dict[str, Any]] = []
    leader_id = _attr_val(leader, "leader_id", "UNKNOWN")
    bias_val  = _enum_val(_attr_val(leader,  "dominant_bias",  "confirmation_bias"))
    ftype_val = _enum_val(_attr_val(faction, "faction_type",   "federation"))

    # ── Record 0: identity synopsis ─────────────────────────────────────────
    records.append({
        "id":   f"{leader_id}__identity",
        "tags": ["identity", "background", "role"],
        "text": (
            f"{_attr_val(leader, 'name', leader_id)} holds the role of "
            f"{_attr_val(leader, 'role', 'Unknown')} within "
            f"{_attr_val(faction, 'name', _attr_val(leader, 'faction_id', 'UNKNOWN'))} "
            f"({ftype_val}). "
            f"Dominant cognitive profile: {bias_val} "
            f"(intensity {_attr_val(leader, 'bias_intensity', 0.5):.2f}, "
            f"plasticity {_attr_val(leader, 'plasticity', 0.3):.2f}). "
            f"Legitimacy: {_attr_val(leader, 'public_legitimacy', 0.7):.2f}; "
            f"elite support: {_attr_val(leader, 'elite_support', 0.6):.2f}; "
            f"institutional control: {_attr_val(leader, 'institutional_control', 0.5):.2f}."
        ),
    })

    # ── Record 1: cognitive bias decision pattern ────────────────────────────
    voice = _BIAS_VOICE.get(bias_val, {})
    records.append({
        "id":   f"{leader_id}__bias_pattern",
        "tags": ["bias", "cognition", "decision_making"],
        "text": (
            f"Decision-making archetype: {bias_val}. "
            f"Tone: {voice.get('tone', 'neutral')}; "
            f"cadence: {voice.get('cadence', 'balanced')}. "
            f"Risk tolerance: {_attr_val(leader, 'risk_tolerance', 0.5):.2f}; "
            f"diplomacy openness: {_attr_val(leader, 'diplomacy_openness', 0.5):.2f}; "
            f"escalation threshold: {_attr_val(leader, 'escalation_threshold', 0.5):.2f}; "
            f"oversight resistance: {_attr_val(leader, 'oversight_resistance', 0.3):.2f}."
        ),
    })

    # ── Record 2: faction military/economic posture ──────────────────────────
    records.append({
        "id":   f"{leader_id}__faction_posture",
        "tags": ["faction", "military", "economics", "technology"],
        "text": (
            f"{_attr_val(faction, 'name', _attr_val(leader, 'faction_id', 'UNKNOWN'))} — "
            f"military: {_attr_val(faction, 'military_strength', 0.5):.2f}, "
            f"economic: {_attr_val(faction, 'economic_strength', 0.5):.2f}, "
            f"technology: {_attr_val(faction, 'technology_level', 0.5):.2f}, "
            f"stability: {_attr_val(faction, 'population_stability', 0.7):.2f}. "
            f"Reputation: {_attr_val(faction, 'reputation', 0.7):.2f}; "
            f"economic potential ceiling: {_attr_val(faction, 'economic_potential', 0.7):.2f}."
        ),
    })

    # ── Record 3: stressor history (conditional) ─────────────────────────────
    war_losses  = _attr_val(leader, "war_losses",     0)
    betrayals   = _attr_val(leader, "betrayals",      0)
    scandals    = _attr_val(leader, "scandals",       0)
    econ_shock  = _attr_val(leader, "economic_shock", 0.0)
    war_pressure = _attr_val(leader, "war_pressure",  0.0)

    if war_losses > 0 or betrayals > 0 or scandals > 0 or abs(float(econ_shock)) > 0.001:
        records.append({
            "id":   f"{leader_id}__stressor_history",
            "tags": ["history", "stressors", "trauma", "conflict"],
            "text": (
                f"Cumulative stressors — war losses: {war_losses}, "
                f"betrayals: {betrayals}, scandals: {scandals}. "
                f"Current economic shock index: {float(econ_shock):.3f}. "
                f"War pressure: {float(war_pressure):.2f}."
            ),
        })

    # ── Records 4+: trust relationship memory (up to 5 entries) ─────────────
    trust_scores: Dict[str, float] = _attr_val(faction, "trust_scores", {})
    sorted_trust = sorted(trust_scores.items(), key=lambda x: float(x[1]))

    for other_id, score in sorted_trust[:5]:
        score_f  = float(score)
        polarity = (
            "allied"     if score_f >= 0.6  else
            "neutral"    if score_f >= 0.35 else
            "adversarial"
        )
        records.append({
            "id":   f"{leader_id}__trust_{other_id}",
            "tags": ["diplomacy", "trust", "memory", polarity],
            "text": (
                f"{_attr_val(faction, 'name', _attr_val(leader, 'faction_id', 'UNKNOWN'))} "
                f"trust with {other_id}: score={score_f:.3f} ({polarity}). "
                f"Coalition invite weight: "
                f"{_attr_val(faction, 'coalition_invite_weight', 0.5):.2f}; "
                f"verification demand: "
                f"{_attr_val(faction, 'verification_demand', 0.5):.2f}."
            ),
        })

    return records


def _build_cns(leader: Any, faction: Any) -> Dict[str, Any]:
    """
    Build cns.yaml content (stored as JSON) for a character.

    style_ctl is activated when oversight_resistance > 0.4 as a compensating
    constraint — high-resistance characters require tighter style enforcement
    to prevent authoritarian tone-bleed into simulation narrative.

    Parameters
    ----------
    leader  : LeaderState or duck-typed equivalent
    faction : FactionState or duck-typed equivalent
    """
    oversight_r  = float(_attr_val(leader, "oversight_resistance", 0.3))
    style_ctl    = oversight_r > 0.4   # active only when needed

    return {
        "cns_version": CNS_VERSION,
        "tool_policy": {
            "internet":         False,
            "filesystem_write": "state.bin_only",
        },
        "retrieval": {
            "mode":  "tag_overlap",
            "top_k": 5,
        },
        "self_checks": {
            "truthfulness": True,
            "layer_safety": True,
            "style_ctl":    style_ctl,
        },
        "character_context": {
            "faction_id":    _attr_val(leader, "faction_id", "UNKNOWN"),
            "declared_role": _attr_val(leader, "role",       "Unknown"),
            "layer":         DECLARED_LAYER,
        },
    }


def _build_manifest(capsule_dir: Path) -> Dict[str, Any]:
    """
    Hash all six non-manifest capsule files and return manifest structure.

    Parameters
    ----------
    capsule_dir : Path to the capsule/ subdirectory

    Raises
    ------
    FileNotFoundError if any expected file is missing.
    """
    records: List[Dict[str, str]] = []
    for name in SEVEN_FILES:
        if name == "manifest.json":
            continue
        p = capsule_dir / name
        if not p.exists():
            raise FileNotFoundError(f"Missing capsule file before manifest build: {p}")
        records.append({"path": name, "sha256": _sha256_path(p)})

    return {
        "capsule_version":  CAPSULE_VERSION,
        "charforge_version": CHARFORGE_VER,
        "anchor_seed":      ANCHOR_SEED,
        "generated_at":     _now_iso(),
        "records":          records,
    }


def _build_bundle_manifest(leader_id: str) -> Dict[str, Any]:
    """Build the outer bundle.manifest.json metadata block."""
    return {
        "bundle_type":    "ORION_CAPSULE_BUNDLE",
        "bundle_version": CAPSULE_VERSION,
        "capsule_id":     leader_id,
        "charforge":      CHARFORGE_VER,
        "generated_at":   _now_iso(),
        "capsule_dir":    "capsule/",
        "schema_ref":     "CAPSULE_BUNDLE_STANDARD__v0.2.0.md",
    }


def _build_receipt(leader: Any, faction: Any) -> Dict[str, Any]:
    """Build BUILD_RECEIPT.json for audit provenance."""
    return {
        "receipt_type":         "CHARFORGE_BUILD",
        "charforge":            CHARFORGE_VER,
        "generated_at":         _now_iso(),
        "anchor_seed":          ANCHOR_SEED,
        "ethics_protocol":      ETHICS_PROTOCOL,
        "leader_id":            _attr_val(leader,  "leader_id",   "UNKNOWN"),
        "leader_name":          _attr_val(leader,  "name",        "Unknown"),
        "faction_id":           _attr_val(leader,  "faction_id",  "UNKNOWN"),
        "faction_name":         _attr_val(faction, "name",        "Unknown"),
        "state_vec_len":        STATE_VEC_LEN,
        "state_vector_layout":  STATE_VECTOR_SLOTS,
    }


# ============================================================================
# PUBLIC API — GENERATE
# ============================================================================

def generate_capsule(
    leader:     Any,
    faction:    Any,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """
    Generate a complete ORION Capsule Bundle v0.2.0 for a GUMAS leader.

    Output directory structure::

        <output_dir>/
          <leader_id>/                   ← bundle root
            capsule/
              identity.json
              traits.json
              knowledge.jsonl
              cns.yaml
              state.bin
              runtime.py
              manifest.json
            bundle.manifest.json
            BUILD_RECEIPT.json

    Parameters
    ----------
    leader      : LeaderState (or duck-typed equivalent with matching attrs)
    faction     : FactionState for the leader's faction
    output_dir  : Parent directory (created if absent)
    overwrite   : If False, raises FileExistsError when bundle already present

    Returns
    -------
    Path : bundle root directory
    """
    output_dir  = Path(output_dir)
    leader_id   = _attr_val(leader, "leader_id", "UNKNOWN")
    bundle_root = output_dir / leader_id
    capsule_dir = bundle_root / "capsule"

    if bundle_root.exists() and not overwrite:
        raise FileExistsError(
            f"Bundle already exists at {bundle_root}. Pass overwrite=True to replace."
        )

    capsule_dir.mkdir(parents=True, exist_ok=True)

    # 1 → identity.json
    _write_json(capsule_dir / "identity.json", _build_identity(leader))
    # 2 → traits.json
    _write_json(capsule_dir / "traits.json", _build_traits(leader, faction))
    # 3 → knowledge.jsonl
    _write_jsonl(capsule_dir / "knowledge.jsonl", _build_knowledge(leader, faction))
    # 4 → cns.yaml  (JSON content, .yaml extension per spec)
    _write_json(capsule_dir / "cns.yaml", _build_cns(leader, faction))
    # 5 → state.bin  (float16 vector)
    (capsule_dir / "state.bin").write_bytes(_encode_state_bin(leader, faction))
    # 6 → runtime.py (spec-compliant; stdlib only)
    (capsule_dir / "runtime.py").write_text(_RUNTIME_PY, encoding="utf-8")
    # 7 → manifest.json (hashes 1–6; must come last)
    _write_json(capsule_dir / "manifest.json", _build_manifest(capsule_dir))

    # Outer bundle metadata
    _write_json(bundle_root / "bundle.manifest.json", _build_bundle_manifest(leader_id))
    _write_json(bundle_root / "BUILD_RECEIPT.json",   _build_receipt(leader, faction))

    return bundle_root


# ============================================================================
# PUBLIC API — LOAD
# ============================================================================

def load_capsule(
    bundle_path: Path,
    *,
    faction_id_override: Optional[str] = None,
) -> Tuple[Any, Any]:
    """
    Load a GUMAS CharForge bundle and reconstruct (LeaderState, FactionState).

    Float fields are restored from state.bin. Categorical fields
    (dominant_bias, faction_type, etc.) are restored from identity.json
    and traits.json. Faction name and trust_scores are not preserved in
    state.bin and will default to empty after load; use the live engine
    state as the source of truth for trust relationships.

    Parameters
    ----------
    bundle_path          : Path to bundle root (containing capsule/)
    faction_id_override  : Override faction_id from identity.json if needed

    Returns
    -------
    (LeaderState, FactionState)

    Raises
    ------
    ImportError  if GUMAS models are not importable.
    ValueError   if state.bin is malformed.
    FileNotFoundError if any capsule file is missing.
    """
    if not _MODELS_AVAILABLE:
        raise ImportError(
            "GUMAS models not available — add SIM_ENGINE_OUTPUTS to sys.path before "
            "calling load_capsule()."
        )

    bundle_path = Path(bundle_path)
    capsule_dir = bundle_path / "capsule"

    # Load capsule files
    identity  = json.loads((capsule_dir / "identity.json").read_text(encoding="utf-8"))
    traits    = json.loads((capsule_dir / "traits.json").read_text(encoding="utf-8"))
    state_raw = (capsule_dir / "state.bin").read_bytes()
    vec       = _decode_state_bin(state_raw)

    faction_id = faction_id_override or identity.get("faction_id", "UNKNOWN")

    # Restore dominant_bias
    bias_str = traits.get("dominant_bias", BiasType.CONFIRMATION.value)
    try:
        dominant_bias = BiasType(bias_str)
    except ValueError:
        dominant_bias = BiasType.CONFIRMATION

    # Restore secondary biases
    secondary_biases = []
    for sb_str in traits.get("secondary_biases", []):
        try:
            secondary_biases.append(BiasType(sb_str))
        except ValueError:
            pass

    # Restore certainty
    certainty_str = identity.get("certainty", "STAGING")
    try:
        certainty = CertaintyTag(certainty_str)
    except ValueError:
        certainty = CertaintyTag.STAGING

    # Restore faction_type from knowledge.jsonl (best-effort scan)
    faction_type = FactionType.FEDERATION
    try:
        knowledge_path = capsule_dir / "knowledge.jsonl"
        if knowledge_path.exists():
            for line in knowledge_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                rec  = json.loads(line)
                text = rec.get("text", "")
                for ft in FactionType:
                    if ft.value in text:
                        faction_type = ft
                        break
    except (json.JSONDecodeError, KeyError):
        pass

    # Reconstruct LeaderState (slots 0..11)
    leader = LeaderState(
        leader_id                = identity["capsule_id"],
        name                     = identity.get("character_name", identity["capsule_id"]),
        role                     = identity.get("character_role", "Unknown"),
        faction_id               = faction_id,
        dominant_bias            = dominant_bias,
        secondary_biases         = secondary_biases,
        bias_intensity           = vec[0],
        plasticity               = vec[1],
        evidence_gain_multiplier = vec[2] * 2.0,   # denormalise
        risk_tolerance           = vec[3],
        diplomacy_openness       = vec[4],
        escalation_threshold     = vec[5],
        oversight_resistance     = vec[6],
        public_legitimacy        = vec[7],
        elite_support            = vec[8],
        institutional_control    = vec[9],
        war_pressure             = vec[10],
        economic_shock           = vec[11],
        certainty                = certainty,
    )

    # Reconstruct FactionState (slots 12..20)
    faction = FactionState(
        faction_id               = faction_id,
        name                     = faction_id,       # not stored in state.bin
        faction_type             = faction_type,
        leader_id                = identity["capsule_id"],
        military_strength        = vec[12],
        economic_strength        = vec[13],
        technology_level         = vec[14],
        population_stability     = vec[15],
        reputation               = vec[16],
        verification_demand      = vec[17],
        deal_discount            = vec[18],
        coalition_invite_weight  = vec[19],
        economic_potential       = vec[20],
        certainty                = certainty,
    )

    return leader, faction


# ============================================================================
# PUBLIC API — TICK UPDATE
# ============================================================================

def tick_update_state_bin(
    leader:      Any,
    faction:     Any,
    bundle_path: Path,
    *,
    update_manifest: bool = True,
) -> None:
    """
    Write updated float16 state vector into capsule/state.bin after an engine tick.

    Keeps the bundle in sync with live simulation state without regenerating
    the full capsule. Optionally refreshes manifest.json (SHA-256 records).

    Parameters
    ----------
    leader          : LeaderState (current post-tick)
    faction         : FactionState (current post-tick)
    bundle_path     : Path to bundle root
    update_manifest : Recompute manifest.json after state.bin update (default True)
    """
    bundle_path = Path(bundle_path)
    capsule_dir = bundle_path / "capsule"
    state_file  = capsule_dir / "state.bin"

    state_file.write_bytes(_encode_state_bin(leader, faction))

    if update_manifest:
        _write_json(capsule_dir / "manifest.json", _build_manifest(capsule_dir))


# ============================================================================
# PUBLIC API — VERIFY
# ============================================================================

def verify_capsule(bundle_path: Path) -> bool:
    """
    Verify all seven capsule files are present and SHA-256 hashes match manifest.

    Parameters
    ----------
    bundle_path : Path to bundle root (containing capsule/)

    Returns
    -------
    bool : True only if every check passes; False on any mismatch or missing file.
    """
    bundle_path = Path(bundle_path)
    capsule_dir = bundle_path / "capsule"

    # Presence check
    for name in SEVEN_FILES:
        if not (capsule_dir / name).exists():
            return False

    # Hash integrity check
    try:
        manifest_data = (capsule_dir / "manifest.json").read_text(encoding="utf-8")
        manifest      = json.loads(manifest_data)
        records       = {r["path"]: r["sha256"] for r in manifest.get("records", [])}

        for name in SEVEN_FILES:
            if name == "manifest.json":
                continue
            expected = records.get(name)
            if expected is None:
                return False
            if _sha256_path(capsule_dir / name) != expected:
                return False

    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        return False

    return True


# ============================================================================
# PUBLIC API — BULK GENERATION
# ============================================================================

def generate_all_capsules(
    world_state: Any,
    output_dir:  Path,
    *,
    overwrite: bool = False,
) -> Dict[str, Path]:
    """
    Generate capsule bundles for every leader in a GUMASState world.

    Skips leaders whose faction_id is not found in world_state.factions.

    Parameters
    ----------
    world_state : GUMASState — full simulation world
    output_dir  : Path       — parent directory for all bundles
    overwrite   : bool       — passed through to generate_capsule

    Returns
    -------
    Dict[leader_id, bundle_path]
    """
    results: Dict[str, Path] = {}
    leaders  = getattr(world_state, "leaders",  {})
    factions = getattr(world_state, "factions", {})

    for leader_id, leader in leaders.items():
        faction = factions.get(_attr_val(leader, "faction_id", ""))
        if faction is None:
            continue
        bundle_path = generate_capsule(
            leader, faction, Path(output_dir), overwrite=overwrite
        )
        results[leader_id] = bundle_path

    return results


# ============================================================================
# PUBLIC API — DIAGNOSTICS
# ============================================================================

def capsule_summary(bundle_path: Path) -> Dict[str, Any]:
    """
    Return a diagnostic dict for a capsule bundle without full model import.

    Fields: capsule_id, layer, bias, faction_id, state_slots, state_vec, valid

    Parameters
    ----------
    bundle_path : Path to bundle root

    Returns
    -------
    Dict with summary fields; {"error": str, "valid": False} on failure.
    """
    bundle_path = Path(bundle_path)
    capsule_dir = bundle_path / "capsule"

    try:
        identity = json.loads((capsule_dir / "identity.json").read_text(encoding="utf-8"))
        traits   = json.loads((capsule_dir / "traits.json").read_text(encoding="utf-8"))
        raw      = (capsule_dir / "state.bin").read_bytes()
        vec      = _decode_state_bin(raw)
        valid    = verify_capsule(bundle_path)
    except Exception as e:
        return {"error": str(e), "valid": False}

    return {
        "capsule_id":  identity.get("capsule_id"),
        "layer":       identity.get("declared_layer"),
        "bias":        traits.get("dominant_bias"),
        "faction_id":  identity.get("faction_id"),
        "state_slots": len(vec),
        "state_vec":   {STATE_VECTOR_SLOTS[i]: round(float(vec[i]), 4) for i in range(len(vec))},
        "valid":       valid,
    }
