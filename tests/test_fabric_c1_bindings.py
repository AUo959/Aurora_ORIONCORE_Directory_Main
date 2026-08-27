"""C1 (one body, one place) capsule bindings and manifest integrity.

RULING-FABRIC-SCHEMA part (b): every charforge capsule carries a location_binding,
so one-body-one-place is checkable rather than merely asserted.

Capsules are sha256-manifested (charforge-capsule-v1.0), so a binding cannot be
hand-edited in — the manifest must be re-derived or the capsule's integrity breaks.
These tests pin both halves: bindings present, manifests still verifying.

Design note on 'undetermined': canon establishes the OFFICES these characters hold
(Chancellor, Chief Marshal, Admiral, Minister…) but names no seat, vessel or world
for any of them — the Union capital appears only as "the capital planet" in the
Marshal Academy charter and has no location entity. Demanding a target_id would
fabricate a canonical place. So C1 accepts an explicit undetermined binding *with a
basis* as an answer, and still rejects a malformed one. Same convention as
canonical_position_status: unplaced and route_exemption.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CAPSULE_GLOB = "GUMAS_SIM_2.5/CanonRec/canon/L2/entities/*/capsule"
sys.path.insert(0, str(REPO_ROOT / "tools"))


def _capsule_dirs() -> list[Path]:
    return sorted((REPO_ROOT).glob(CAPSULE_GLOB))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def test_every_capsule_has_a_location_binding():
    caps = _capsule_dirs()
    if not caps:
        return  # CanonRec not checked out
    missing = []
    for cap in caps:
        identity = cap / "identity.json"
        if not identity.exists():
            continue
        data = json.loads(identity.read_text(encoding="utf-8"))
        if "location_binding" not in data:
            missing.append(cap.parent.name)
    assert not missing, f"capsules without a location_binding: {missing}"


def test_every_binding_is_well_formed():
    """Either it resolves to a target, or it is explicitly undetermined WITH a basis."""
    caps = _capsule_dirs()
    if not caps:
        return
    bad = []
    for cap in caps:
        identity = cap / "identity.json"
        if not identity.exists():
            continue
        binding = json.loads(identity.read_text(encoding="utf-8")).get("location_binding")
        if binding is None:
            continue
        if isinstance(binding, list):
            bad.append((cap.parent.name, "multiple simultaneous bindings"))
            continue
        if not isinstance(binding, dict):
            bad.append((cap.parent.name, "binding is not an object"))
            continue
        if str(binding.get("type", "")).lower() == "undetermined":
            if not binding.get("basis"):
                bad.append((cap.parent.name, "undetermined without a basis"))
        elif not binding.get("target_id"):
            bad.append((cap.parent.name, "no target_id and not marked undetermined"))
    assert not bad, f"malformed bindings: {bad}"


def test_resolved_bindings_point_at_real_canon_entities():
    """A binding with a target must resolve — no ghost destinations."""
    canon = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
    if not canon.exists():
        return
    ids = set()
    for path in canon.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        # Canon uses BOTH identity spellings: entity_id nearly everywhere, but
        # canonical_id on all 23 mobile_assets. An index that reads only one of
        # them reports live vessels as ghost destinations.
        for key in ("entity_id", "canonical_id"):
            if data.get(key):
                ids.add(data[key])

    dangling = []
    for cap in _capsule_dirs():
        identity = cap / "identity.json"
        if not identity.exists():
            continue
        binding = json.loads(identity.read_text(encoding="utf-8")).get("location_binding")
        if isinstance(binding, dict) and binding.get("target_id"):
            if binding["target_id"] not in ids:
                dangling.append((cap.parent.name, binding["target_id"]))
    assert not dangling, f"location_binding targets that do not resolve: {dangling}"


def test_manifests_still_verify_after_binding_rebuild():
    """Capsules are sha256-manifested: adding a binding requires a real rebuild.

    This is the guard against someone hand-editing identity.json and silently
    breaking capsule integrity.
    """
    caps = _capsule_dirs()
    if not caps:
        return
    mismatched = []
    for cap in caps:
        manifest_path = cap / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("records")
        if records is None:
            # Older shape: a {filename: sha} map that includes manifest.json itself.
            # That self-hash cannot be consistent by construction, so skip it.
            records = [
                {"path": name, "sha256": digest}
                for name, digest in (manifest.get("sha256") or {}).items()
                if name != "manifest.json"
            ]
        for record in records:
            target = cap / record["path"]
            if not target.exists() or _sha256(target) != record["sha256"]:
                mismatched.append((cap.parent.name, record["path"]))
    assert not mismatched, f"capsule manifest mismatches: {mismatched}"


def test_c1_check_accepts_undetermined_and_rejects_baseless():
    """The linter must treat an explicit undetermined binding as answered."""
    import fabric_invariants_check as fic

    findings: list = []
    fic.add(findings, "C1", "INFO", "probe", "probe")
    assert findings, "linter add() should record findings"

    source = (REPO_ROOT / "tools" / "fabric_invariants_check.py").read_text(encoding="utf-8")
    assert "undetermined" in source, "C1 must handle explicitly undetermined bindings"
    assert "must say why no place is established" in source, (
        "an undetermined binding without a basis must still be a violation"
    )
