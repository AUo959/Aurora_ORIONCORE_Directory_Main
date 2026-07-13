#!/usr/bin/env python3
"""Character capsule adapter for CharForge bundles.

This is the implementation bridge between CharForge capsule files and the
deterministic GUMAS/narrative surfaces. It reads capsule artifacts as evidence;
it does not promote canon or mutate CanonRec.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

STATE_VECTOR_SLOTS = [
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

CAPSULE_FILES = [
    "identity.json",
    "traits.json",
    "knowledge.jsonl",
    "cns.yaml",
    "state.bin",
    "runtime.py",
    "manifest.json",
]


@dataclass(frozen=True)
class CapsuleVerification:
    valid: bool
    checked_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    mismatched_files: tuple[str, ...]


@dataclass(frozen=True)
class CharacterCapsule:
    capsule_id: str
    canonical_id: str
    bundle_root: str
    capsule_dir: str
    authority_tier: str
    identity: Mapping[str, Any]
    traits: Mapping[str, Any]
    cns: Mapping[str, Any]
    knowledge: tuple[Mapping[str, Any], ...]
    state_vector: Mapping[str, float]
    manifest: Mapping[str, Any]
    build_receipt: Mapping[str, Any]
    verification: CapsuleVerification

    @property
    def verified(self) -> bool:
        return self.verification.valid

    @property
    def dominant_bias(self) -> Optional[str]:
        value = self.traits.get("dominant_bias")
        return str(value) if value is not None else None

    @property
    def decision_style(self) -> Optional[str]:
        value = self.traits.get("decision_style")
        if value is None:
            value = self._first_knowledge_text("decision_style")
        return str(value) if value is not None else None

    def _first_knowledge_text(self, tag_or_type: str) -> Optional[str]:
        for record in self.knowledge:
            if record.get("type") == tag_or_type:
                return str(record.get("text", ""))
            tags = record.get("tags", [])
            if isinstance(tags, list) and tag_or_type in tags:
                return str(record.get("text", ""))
        return None


@dataclass(frozen=True)
class CharacterDecisionProfile:
    capsule_id: str
    canonical_id: str
    authority_tier: str
    verified: bool
    dominant_bias: Optional[str]
    decision_style: Optional[str]
    settlement_lean: float
    escalation_lean: float
    source_path: str


@dataclass(frozen=True)
class CapsuleEvidenceFact:
    fact_id: str
    claim_type: str
    authority_tier: str
    status: str
    source_path: str
    confidence: float
    promotable: bool
    value: Mapping[str, Any]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> tuple[Mapping[str, Any], ...]:
    if not path.exists():
        return ()
    records: list[Mapping[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return tuple(records)


def _load_cns(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return _parse_flat_yaml(text)


def _parse_flat_yaml(text: str) -> dict[str, Any]:
    """Parse the small flat YAML subset used by legacy capsule CNS files."""
    out: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        lowered = value.lower()
        if lowered in {"true", "false"}:
            out[key.strip()] = lowered == "true"
        else:
            out[key.strip()] = value
    return out


def _decode_state_vector(path: Path) -> Mapping[str, float]:
    if not path.exists():
        return {}
    raw = path.read_bytes()
    expected = len(STATE_VECTOR_SLOTS) * 2
    if len(raw) != expected:
        return {"_malformed_byte_count": float(len(raw))}
    values = struct.unpack("<" + "e" * len(STATE_VECTOR_SLOTS), raw)
    return {
        STATE_VECTOR_SLOTS[index]: round(float(value), 6)
        for index, value in enumerate(values)
    }


def _manifest_records(manifest: Mapping[str, Any]) -> dict[str, str]:
    records: dict[str, str] = {}
    raw_records = manifest.get("records")
    if isinstance(raw_records, list):
        for item in raw_records:
            if isinstance(item, Mapping) and "path" in item and "sha256" in item:
                records[str(item["path"])] = str(item["sha256"])

    files = manifest.get("files")
    if isinstance(files, Mapping):
        for path, value in files.items():
            if isinstance(value, str):
                records[str(path)] = value
            elif isinstance(value, Mapping) and "sha256" in value:
                records[str(path)] = str(value["sha256"])

    hashes = manifest.get("hashes")
    if isinstance(hashes, Mapping):
        for path, value in hashes.items():
            records[str(path)] = str(value)

    return records


def verify_capsule(capsule_dir: Path) -> CapsuleVerification:
    manifest = _load_json(capsule_dir / "manifest.json", {})
    expected_hashes = _manifest_records(manifest)
    missing: list[str] = []
    mismatched: list[str] = []
    checked: list[str] = []

    for name in CAPSULE_FILES:
        path = capsule_dir / name
        if not path.exists():
            missing.append(name)
            continue
        if name == "manifest.json":
            continue
        expected = expected_hashes.get(name)
        if expected is None:
            missing.append(f"manifest:{name}")
            continue
        checked.append(name)
        if sha256_file(path) != expected:
            mismatched.append(name)

    valid = not missing and not mismatched and bool(expected_hashes)
    return CapsuleVerification(
        valid=valid,
        checked_files=tuple(checked),
        missing_files=tuple(missing),
        mismatched_files=tuple(mismatched),
    )


def resolve_capsule_dir(path: Path) -> tuple[Path, Path]:
    path = Path(path)
    if path.name == "capsule":
        return path.parent, path
    if (path / "capsule").is_dir():
        return path, path / "capsule"
    return path.parent, path


def load_capsule(path: Path, *, authority_tier: str = "STAGING") -> CharacterCapsule:
    bundle_root, capsule_dir = resolve_capsule_dir(Path(path))
    identity = _load_json(capsule_dir / "identity.json", {})
    traits = _load_json(capsule_dir / "traits.json", {})
    cns = _load_cns(capsule_dir / "cns.yaml")
    knowledge = _load_jsonl(capsule_dir / "knowledge.jsonl")
    manifest = _load_json(capsule_dir / "manifest.json", {})
    receipt = _load_json(bundle_root / "BUILD_RECEIPT.json", {})
    verification = verify_capsule(capsule_dir)

    capsule_id = str(
        identity.get("capsule_id")
        or traits.get("canonical_id")
        or receipt.get("leader_id")
        or bundle_root.name
    )
    canonical_id = str(traits.get("canonical_id") or capsule_id)

    return CharacterCapsule(
        capsule_id=capsule_id,
        canonical_id=canonical_id,
        bundle_root=str(bundle_root),
        capsule_dir=str(capsule_dir),
        authority_tier=authority_tier,
        identity=identity,
        traits=traits,
        cns=cns,
        knowledge=knowledge,
        state_vector=_decode_state_vector(capsule_dir / "state.bin"),
        manifest=manifest,
        build_receipt=receipt,
        verification=verification,
    )


def load_capsules(root: Path, *, authority_tier: str = "STAGING") -> list[CharacterCapsule]:
    root = Path(root)
    capsules: list[CharacterCapsule] = []
    for capsule_dir in sorted(root.glob("*/capsule")):
        if (capsule_dir / "identity.json").exists() or (capsule_dir / "traits.json").exists():
            capsules.append(load_capsule(capsule_dir, authority_tier=authority_tier))
    return capsules


def decision_profile(
    capsule: CharacterCapsule,
    culture_model: Any = None,
) -> CharacterDecisionProfile:
    if culture_model is None:
        from mech_gov_001 import CultureModel

        culture_model = CultureModel()
    return CharacterDecisionProfile(
        capsule_id=capsule.capsule_id,
        canonical_id=capsule.canonical_id,
        authority_tier=capsule.authority_tier,
        verified=capsule.verified,
        dominant_bias=capsule.dominant_bias,
        decision_style=capsule.decision_style,
        settlement_lean=float(culture_model.settlement_lean(capsule.dominant_bias)),
        escalation_lean=float(culture_model.escalation_lean(capsule.dominant_bias)),
        source_path=capsule.capsule_dir,
    )


def evidence_status(authority_tier: str, verified: bool) -> str:
    tier = authority_tier.upper()
    if not verified:
        return "unverified"
    if tier == "CANON":
        return "established"
    if tier == "OPERATIONAL":
        return "operational"
    if tier == "PROPOSED":
        return "proposed"
    return "staging"


def to_evidence_facts(capsule: CharacterCapsule) -> list[CapsuleEvidenceFact]:
    status = evidence_status(capsule.authority_tier, capsule.verified)
    promotable = capsule.authority_tier.upper() == "CANON" and capsule.verified
    confidence = 0.95 if capsule.verified else 0.45
    base = f"{capsule.canonical_id}__charforge"
    source_path = capsule.capsule_dir

    facts = [
        CapsuleEvidenceFact(
            fact_id=f"{base}__identity",
            claim_type="character_identity",
            authority_tier=capsule.authority_tier,
            status=status,
            source_path=source_path,
            confidence=confidence,
            promotable=promotable,
            value={
                "capsule_id": capsule.capsule_id,
                "canonical_id": capsule.canonical_id,
                "declared_layer": capsule.identity.get("declared_layer"),
                "ethics_protocol": capsule.identity.get("ethics_protocol"),
                "anchor_seed": capsule.identity.get("anchor_seed"),
            },
        ),
        CapsuleEvidenceFact(
            fact_id=f"{base}__decision_profile",
            claim_type="character_decision_profile",
            authority_tier=capsule.authority_tier,
            status=status,
            source_path=source_path,
            confidence=confidence,
            promotable=promotable,
            value={
                "dominant_bias": capsule.dominant_bias,
                "decision_style": capsule.decision_style,
                "traits": capsule.traits.get("traits", []),
                "allegiance": capsule.traits.get("allegiance"),
                "relationships": capsule.traits.get("relationships"),
            },
        ),
    ]

    if capsule.state_vector:
        facts.append(
            CapsuleEvidenceFact(
                fact_id=f"{base}__state_vector",
                claim_type="character_state_vector",
                authority_tier=capsule.authority_tier,
                status=status,
                source_path=source_path,
                confidence=confidence,
                promotable=promotable,
                value=capsule.state_vector,
            )
        )

    if capsule.cns:
        facts.append(
            CapsuleEvidenceFact(
                fact_id=f"{base}__runtime_safety",
                claim_type="character_runtime_safety",
                authority_tier=capsule.authority_tier,
                status=status,
                source_path=source_path,
                confidence=confidence,
                promotable=promotable,
                value={
                    "tool_policy": capsule.cns.get("tool_policy", {}),
                    "self_checks": capsule.cns.get("self_checks", {}),
                    "style_ctl": _style_ctl(capsule.cns),
                },
            )
        )

    return facts


def _style_ctl(cns: Mapping[str, Any]) -> Optional[bool]:
    self_checks = cns.get("self_checks")
    if isinstance(self_checks, Mapping) and "style_ctl" in self_checks:
        return bool(self_checks["style_ctl"])
    if "style_ctl" in cns:
        return bool(cns["style_ctl"])
    return None


def facts_as_dicts(facts: Iterable[CapsuleEvidenceFact]) -> list[dict[str, Any]]:
    return [asdict(fact) for fact in facts]


def _cmd_summarize(args: argparse.Namespace) -> int:
    capsules = load_capsules(Path(args.root), authority_tier=args.authority_tier)
    payload = {
        "root": str(Path(args.root)),
        "authority_tier": args.authority_tier,
        "capsule_count": len(capsules),
        "capsules": [
            {
                **asdict(decision_profile(capsule)),
                "verification": asdict(capsule.verification),
            }
            for capsule in capsules
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_facts(args: argparse.Namespace) -> int:
    capsule = load_capsule(Path(args.path), authority_tier=args.authority_tier)
    print(json.dumps(facts_as_dicts(to_evidence_facts(capsule)), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    summarize = sub.add_parser("summarize", help="Summarize capsules under an entities root.")
    summarize.add_argument("root")
    summarize.add_argument("--authority-tier", default="STAGING")
    summarize.set_defaults(func=_cmd_summarize)

    facts = sub.add_parser("facts", help="Emit evidence facts for one capsule or bundle.")
    facts.add_argument("path")
    facts.add_argument("--authority-tier", default="STAGING")
    facts.set_defaults(func=_cmd_facts)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
