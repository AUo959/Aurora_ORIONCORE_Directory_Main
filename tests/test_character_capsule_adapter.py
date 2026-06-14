from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from character_capsule_adapter import (  # noqa: E402
    STATE_VECTOR_SLOTS,
    decision_profile,
    load_capsule,
    load_capsules,
    to_evidence_facts,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_capsule(root: Path, name: str = "drenn_korvath", *, bias: str = "zero_sum_thinking") -> Path:
    bundle = root / name
    capsule = bundle / "capsule"
    capsule.mkdir(parents=True)

    (capsule / "identity.json").write_text(
        json.dumps(
            {
                "capsule_id": name,
                "declared_layer": "L2",
                "ethics_protocol": "Picard_Delta_3",
                "anchor_seed": "EOS_SEED_ORION",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (capsule / "traits.json").write_text(
        json.dumps(
            {
                "canonical_id": name,
                "schema": "charforge-traits-v1.0",
                "dominant_bias": bias,
                "decision_style": "Zero-Sum Clan Calculus",
                "traits": ["Territorial Aggression"],
                "allegiance": "Vorran Clans",
                "relationships": "Distrustful of Zylox",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (capsule / "knowledge.jsonl").write_text(
        json.dumps({"type": "decision_style", "text": "Zero-Sum Clan Calculus"}) + "\n",
        encoding="utf-8",
    )
    (capsule / "cns.yaml").write_text(
        json.dumps(
            {
                "tool_policy": {"internet": False, "filesystem_write": "state.bin_only"},
                "self_checks": {"truthfulness": True, "layer_safety": True, "style_ctl": True},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    values = [0.5] * len(STATE_VECTOR_SLOTS)
    values[6] = 0.85
    values[10] = 0.4
    (capsule / "state.bin").write_bytes(struct.pack("<" + "e" * len(values), *values))
    (capsule / "runtime.py").write_text("# runtime stub\n", encoding="utf-8")

    records = [
        {"path": path.name, "sha256": _sha(path)}
        for path in sorted(capsule.iterdir())
        if path.name != "manifest.json"
    ]
    (capsule / "manifest.json").write_text(
        json.dumps({"records": records}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (bundle / "BUILD_RECEIPT.json").write_text(
        json.dumps({"leader_id": name, "charforge": "3.0.0"}, sort_keys=True),
        encoding="utf-8",
    )
    return bundle


def test_capsule_loads_verified_decision_profile(tmp_path: Path) -> None:
    bundle = _write_capsule(tmp_path)

    capsule = load_capsule(bundle, authority_tier="CANON")
    profile = decision_profile(capsule)

    assert capsule.verified
    assert profile.canonical_id == "drenn_korvath"
    assert profile.dominant_bias == "zero_sum_thinking"
    assert profile.settlement_lean < 0
    assert profile.escalation_lean > 0
    assert capsule.state_vector["oversight_resistance"] == pytest.approx(0.85, abs=0.01)


def test_evidence_facts_preserve_authority_boundaries(tmp_path: Path) -> None:
    bundle = _write_capsule(tmp_path)

    canon_facts = to_evidence_facts(load_capsule(bundle, authority_tier="CANON"))
    staging_facts = to_evidence_facts(load_capsule(bundle, authority_tier="STAGING"))

    assert {fact.status for fact in canon_facts} == {"established"}
    assert all(fact.promotable for fact in canon_facts)
    assert {fact.status for fact in staging_facts} == {"staging"}
    assert not any(fact.promotable for fact in staging_facts)
    assert {fact.claim_type for fact in staging_facts} >= {
        "character_identity",
        "character_decision_profile",
        "character_state_vector",
        "character_runtime_safety",
    }


def test_tampered_capsule_stays_unverified(tmp_path: Path) -> None:
    bundle = _write_capsule(tmp_path)
    traits = bundle / "capsule" / "traits.json"
    data = json.loads(traits.read_text(encoding="utf-8"))
    data["dominant_bias"] = "hyper_rationalism_bias"
    traits.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

    capsule = load_capsule(bundle, authority_tier="CANON")
    facts = to_evidence_facts(capsule)

    assert not capsule.verified
    assert capsule.verification.mismatched_files == ("traits.json",)
    assert {fact.status for fact in facts} == {"unverified"}
    assert not any(fact.promotable for fact in facts)


def test_discovers_multiple_capsules(tmp_path: Path) -> None:
    _write_capsule(tmp_path, "drenn_korvath", bias="zero_sum_thinking")
    _write_capsule(tmp_path, "varek_norr", bias="hyper_rationalism_bias")

    capsules = load_capsules(tmp_path, authority_tier="CANON")
    profiles = {capsule.canonical_id: decision_profile(capsule) for capsule in capsules}

    assert set(profiles) == {"drenn_korvath", "varek_norr"}
    assert profiles["drenn_korvath"].settlement_lean < 0
    assert profiles["varek_norr"].settlement_lean > 0
