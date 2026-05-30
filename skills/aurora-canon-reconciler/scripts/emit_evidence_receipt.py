#!/usr/bin/env python3
"""
CanonRec — Emit Evidence Receipt (EG-lite proto-receipt)

This script transforms a CanonRec validation-run JSON output into a structured
`evidence_receipt.json` artifact. It is intentionally non-interpretive:

- It does not infer new facts.
- It does not treat missing fields as claims.
- It only records provenance pointers to existing validation outputs and
  any explicitly provided canon target references.

The goal is to make CanonRec runs referencable downstream (Promotion Pipeline /
MutationRequest.gate_receipts) without re-parsing or folklore.

Usage:
  python emit_evidence_receipt.py \
    --validation-run out/validation_run.json \
    --out out/evidence_receipt.json \
    [--canon-targets out/canon_targets.json]

Canon targets file format:
  - JSON list of strings: ["ref1", "ref2", ...]
  - OR an object with {"canon_targets": ["ref1", ...]}

Output:
  Writes evidence_receipt.json to --out
  Prints a brief summary to stderr
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# -----------------------------------------------------------------------------
# Receipt / hashing metadata (versioned semantics)
# -----------------------------------------------------------------------------

EVIDENCE_HASH_CANON_VERSION = "CANONREC_EVIDENCE_HASH_CANON_V1"
EVIDENCE_HASH_CANON_RULES_REF = "emit_evidence_receipt.py::_canonicalize_for_hash"

# For semantic equivalence signatures, exclude volatile metadata.
_CONTENT_HASH_EXCLUDED_FIELDS = (
    "timestamp",
    "timestamp_source",
    # Paths are environment-variant; store them for provenance, but exclude for semantic hash.
    "inputs.validation_run_file",
    "inputs.canon_targets_file",
    # Hash fields should not participate in hashing (avoid self-reference).
    "output_hash",
    "content_hash",
)

# Claim status vocabulary (contract-aligned, avoids "absence implies refutation").
VALID_CLAIM_STATUSES = {"SUPPORTED", "ASSUMPTION", "UNKNOWN"}

# Evidence verdict rules (boring by design):
# - FAIL if any SUPPORTED claim lacks provenance pointers.
# - WARN if any UNKNOWN or ASSUMPTION claims exist (properly labeled).
# - PASS otherwise.
VALID_VERDICTS = {"PASS", "WARN", "FAIL"}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _utc_now_z() -> str:
    """Timezone-aware UTC timestamp with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to read JSON from {path}: {e}") from e


def _load_canon_targets(path: Path) -> list[str]:
    obj = _load_json(path)
    if isinstance(obj, list):
        if not all(isinstance(x, str) for x in obj):
            raise ValueError("canon targets list must contain only strings")
        return obj
    if isinstance(obj, dict):
        targets = obj.get("canon_targets", [])
        if targets is None:
            return []
        if not isinstance(targets, list) or not all(isinstance(x, str) for x in targets):
            raise ValueError('canon targets dict must have key "canon_targets": [str, ...]')
        return targets
    raise ValueError("canon targets must be a JSON list[str] or object with canon_targets list")


def _get_nested(d: dict[str, Any], dotted_path: str) -> Any:
    cur: Any = d
    for part in dotted_path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _set_nested(d: dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    cur: dict[str, Any] = d
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def _strip_fields_by_dotted_path(obj: dict[str, Any], dotted_paths: Iterable[str]) -> dict[str, Any]:
    """Return a deep-ish copy of obj with dotted-path keys removed.

    Only supports removal from dicts (not lists). If a dotted-path is absent,
    it is ignored.
    """
    # Deep copy via JSON roundtrip keeps things simple and deterministic.
    clone = json.loads(json.dumps(obj, ensure_ascii=False))
    for path in dotted_paths:
        parts = path.split(".")
        cur = clone
        for part in parts[:-1]:
            if not isinstance(cur, dict) or part not in cur:
                cur = None
                break
            cur = cur[part]
        if isinstance(cur, dict):
            cur.pop(parts[-1], None)
    return clone


def _canonicalize_for_hash(obj: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize receipt dict for hashing.

    - Sort order-insensitive lists where appropriate (claims, provenance, excluded fields).
    - Ensure stable dict shapes.
    """
    d = json.loads(json.dumps(obj, ensure_ascii=False))

    # Canonicalize excluded fields ordering.
    excluded = d.get("content_hash_excluded_fields")
    if isinstance(excluded, list):
        d["content_hash_excluded_fields"] = sorted(str(x) for x in excluded)

    # Canonicalize claims ordering and their provenance ordering.
    claims = d.get("claims")
    if isinstance(claims, list):
        for c in claims:
            if isinstance(c, dict):
                prov = c.get("provenance")
                if isinstance(prov, list):
                    prov_sorted = sorted(
                        (dict(p) for p in prov if isinstance(p, dict)),
                        key=lambda p: (str(p.get("ref_type", "")), str(p.get("ref", ""))),
                    )
                    c["provenance"] = prov_sorted

        d["claims"] = sorted(
            (dict(c) for c in claims if isinstance(c, dict)),
            key=lambda c: (
                str(c.get("layer", "")),
                str(c.get("entity_type", "")),
                str(c.get("entity_name", "")),
                str(c.get("claim_id", "")),
            ),
        )

    # Canonicalize canon targets ordering.
    canon_targets = _get_nested(d, "inputs.canon_targets")
    if isinstance(canon_targets, list):
        _set_nested(d, "inputs.canon_targets", sorted(str(x) for x in canon_targets))

    return d


def _compute_hash(obj: dict[str, Any]) -> str:
    payload = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_hex(payload)


def _make_claim_id(layer: str, entity_type: str, entity_name: str, claim_kind: str) -> str:
    raw = f"{layer}|{entity_type}|{entity_name}|{claim_kind}".encode("utf-8")
    return "CLM-" + _sha256_hex(raw)[:12]


def _per_report_content_fingerprint(report: dict[str, Any]) -> str:
    """A stable fingerprint for referencing a specific report entry.

    Excludes volatile timestamp fields.
    """
    stripped = _strip_fields_by_dotted_path(report, ("timestamp", "timestamp_source"))
    canonical = json.loads(json.dumps(stripped, ensure_ascii=False))
    payload = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_hex(payload)


# -----------------------------------------------------------------------------
# Core transform
# -----------------------------------------------------------------------------

def build_evidence_receipt(
    validation_run_obj: dict[str, Any],
    validation_run_file: Path,
    canon_targets: list[str] | None = None,
    canon_targets_file: Path | None = None,
) -> dict[str, Any]:
    """Transform a CanonRec validation-run JSON into an EG-lite proto receipt.

    The receipt records only what exists in the validation output:
      - One claim per report: that the validation run observed an entity with the
        given layer/type/name and pass/fail result.

    Provenance pointers:
      - Always includes the validation run receipt_id if present.
      - Includes a stable per-report fingerprint for pinpointing a report entry.
    """
    if "validation_run" not in validation_run_obj or "reports" not in validation_run_obj:
        raise ValueError("validation run JSON must contain keys: validation_run, reports")

    vr = validation_run_obj.get("validation_run", {})
    reports = validation_run_obj.get("reports", [])
    if not isinstance(vr, dict) or not isinstance(reports, list):
        raise ValueError("validation_run must be object and reports must be list")

    run_receipt_id = vr.get("receipt_id") or vr.get("content_hash") or None
    run_output_hash = vr.get("output_hash") or None
    run_content_hash = vr.get("content_hash") or None

    # Build claims mechanically.
    claims: list[dict[str, Any]] = []
    for r in reports:
        if not isinstance(r, dict):
            continue

        layer = str(r.get("layer", ""))
        entity_type = str(r.get("entity_type", ""))
        entity_name = str(r.get("entity_name", ""))

        # If key identity fields are missing, skip claim generation (no inference).
        if not layer or not entity_type or not entity_name:
            continue

        passed = bool(r.get("passed", False))
        claim_kind = "ENTITY_VALIDATION_OBSERVED"
        claim_id = _make_claim_id(layer, entity_type, entity_name, claim_kind)

        provenance: list[dict[str, str]] = []

        if run_receipt_id:
            provenance.append({"ref_type": "validation_run_receipt_id", "ref": str(run_receipt_id)})
        elif run_content_hash:
            provenance.append({"ref_type": "validation_run_content_hash", "ref": str(run_content_hash)})
        elif run_output_hash:
            provenance.append({"ref_type": "validation_run_output_hash", "ref": str(run_output_hash)})


        # Include explicit provenance pointers if present in the report payload.
        # (Validator may choose to surface these fields in future versions.)
        origin_file = r.get("origin_file")
        if isinstance(origin_file, str) and origin_file.strip():
            provenance.append({"ref_type": "origin_file", "ref": origin_file.strip()})

        doc_sources = r.get("doc_sources")
        if isinstance(doc_sources, list):
            for s in doc_sources:
                if isinstance(s, str) and s.strip():
                    provenance.append({"ref_type": "doc_source", "ref": s.strip()})

        artifact_hash = r.get("artifact_hash")
        if isinstance(artifact_hash, str) and artifact_hash.strip():
            provenance.append({"ref_type": "artifact_hash", "ref": artifact_hash.strip()})

# Pinpoint this specific report entry deterministically.
        provenance.append({"ref_type": "entity_report_fingerprint", "ref": _per_report_content_fingerprint(r)})

        status = "SUPPORTED" if len(provenance) > 0 else "UNKNOWN"

        claim = {
            "claim_id": claim_id,
            "claim_kind": claim_kind,
            "entity_name": entity_name,
            "layer": layer,
            "entity_type": entity_type,
            "claim_text": f"Validation observed entity '{entity_name}' as {layer}/{entity_type} with passed={passed}.",
            "provenance": provenance,
            "status": status,
        }
        claims.append(claim)

    # Deterministic ordering.
    claims.sort(key=lambda c: (c["layer"], c["entity_type"], c["entity_name"], c["claim_id"]))

    # Verdict rules.
    any_unsupported_supported = any(c["status"] == "SUPPORTED" and not c.get("provenance") for c in claims)
    any_warn = any(c["status"] in ("UNKNOWN", "ASSUMPTION") for c in claims)

    if any_unsupported_supported:
        verdict = "FAIL"
    elif any_warn:
        verdict = "WARN"
    else:
        verdict = "PASS"

    # Summary.
    summary = {
        "total_claims": len(claims),
        "supported": sum(1 for c in claims if c["status"] == "SUPPORTED"),
        "assumptions": sum(1 for c in claims if c["status"] == "ASSUMPTION"),
        "unknown": sum(1 for c in claims if c["status"] == "UNKNOWN"),
    }

    receipt: dict[str, Any] = {
        "gate": "EVIDENCE",
        "kind": "EG_LITE_PROTO_RECEIPT",
        "verdict": verdict,
        "timestamp": _utc_now_z(),
        "timestamp_source": "WALL_CLOCK_UTC",
        "hash_canon_version": EVIDENCE_HASH_CANON_VERSION,
        "hash_canon_rules_ref": EVIDENCE_HASH_CANON_RULES_REF,
        "source_validation_run": {
            "receipt_id": run_receipt_id,
            "output_hash": run_output_hash,
            "content_hash": run_content_hash,
            "hash_canon_version": vr.get("hash_canon_version"),
            "hash_canon_rules_ref": vr.get("hash_canon_rules_ref"),
        },
        "inputs": {
            "validation_run_file": str(validation_run_file),
            "canon_targets_file": str(canon_targets_file) if canon_targets_file else None,
            "canon_targets": canon_targets or [],
        },
        "claims": claims,
        "summary": summary,
    }

    # Add evidence receipt hashes (artifact + semantic).
    canonical_artifact = _canonicalize_for_hash(receipt)
    receipt["output_hash_alg"] = "SHA256"
    receipt["output_hash_scope"] = "EVIDENCE_RECEIPT_RUN_ARTIFACT_INCLUDING_TIMESTAMPS"
    receipt["output_hash"] = _compute_hash(canonical_artifact)

    stripped = _strip_fields_by_dotted_path(receipt, _CONTENT_HASH_EXCLUDED_FIELDS)
    canonical_semantic = _canonicalize_for_hash(stripped)
    receipt["content_hash_alg"] = "SHA256"
    receipt["content_hash_scope"] = "EVIDENCE_RECEIPT_SEMANTIC_OUTPUT_EXCLUDING_VOLATILE_FIELDS"
    receipt["content_hash_excluded_fields"] = list(_CONTENT_HASH_EXCLUDED_FIELDS)
    receipt["content_hash"] = _compute_hash(canonical_semantic)

    # Default citeable pointer.
    receipt["receipt_id_policy"] = "receipt_id = content_hash"
    receipt["receipt_id"] = receipt["content_hash"]

    return receipt


def main() -> None:
    p = argparse.ArgumentParser(description="Emit EG-lite evidence receipt from a CanonRec validation run JSON.")
    p.add_argument("--validation-run", required=True, help="Path to validation_run.json produced by validate_entity.py")
    p.add_argument("--out", required=True, help="Output path for evidence_receipt.json")
    p.add_argument("--canon-targets", required=False, help="Optional JSON file containing canon target references")
    args = p.parse_args()

    vr_path = Path(args.validation_run)
    out_path = Path(args.out)
    canon_path = Path(args.canon_targets) if args.canon_targets else None

    vr_obj = _load_json(vr_path)
    canon_targets = _load_canon_targets(canon_path) if canon_path else None

    receipt = build_evidence_receipt(
        validation_run_obj=vr_obj if isinstance(vr_obj, dict) else {},
        validation_run_file=vr_path,
        canon_targets=canon_targets,
        canon_targets_file=canon_path,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"[CanonRec] Wrote evidence receipt: {out_path} | verdict={receipt['verdict']} | receipt_id={receipt['receipt_id']}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
