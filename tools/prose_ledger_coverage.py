#!/usr/bin/env python3
"""Report which prose-ledger entities have actually been reconciled into canon.

Why this exists
---------------
`prose_claim_ledger__2026-08-09.json` holds 1,044 claims across 108 entities and
records **no reconciliation status**. Progress lived in session notes and in the
canon records themselves, so "what is left" was answered from memory — and
memory drifted. The session queue described `org_prime_construct_polity`
(152 claims) as the largest open seam long after it had been fully reconciled on
2026-08-09, with `legal_status`, `seat_and_territory`, `political_evolution` and
a recorded `open_doctrinal_question` all citing the ledger by name.

Re-litigating 152 settled claims is the cheap failure. The expensive one is the
opposite: treating the whole ledger as done because part of it obviously is.
So this derives coverage from the canon records, which is the only place the
answer is actually written down.

How coverage is detected
------------------------
A record counts as reconciled when its own content cites the ledger — the
reconciliation passes stamp `source` / `pass` / `basis` fields naming
`prose_claim_ledger` or "Prose-Claim Ledger Reconciliation". That is a
deliberate, load-bearing convention rather than an inference: the passes wrote
provenance into the records precisely so this question could be answered later.

Alias forwarding matters. The ledger keys claims by whatever surface form the
extractor matched, so 152 Prime Construct claims are filed under the SUPERSEDED
`org_prime_construct_polity` while the reconciliation landed on
`polity_prime_construct`. Following `superseded_by` is therefore required; without
it every renamed entity reads as untouched.

Usage
-----
    python3 tools/prose_ledger_coverage.py
    python3 tools/prose_ledger_coverage.py --open-only
    python3 tools/prose_ledger_coverage.py --json coverage.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "reports" / "recovery" / "data" / "prose_claim_ledger__2026-08-09.json"
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

#: Markers a reconciliation pass leaves in the record it wrote.
LEDGER_MARKERS = (
    "prose_claim_ledger",
    "prose-claim ledger reconciliation",
    "prose claim ledger",
)


#: Sidecar artifacts that carry a canonical_id but are not the entity record.
#: They live beside capsules rather than inside them, so a `/capsule/` skip
#: does not catch them.
NON_ENTITY_FILENAMES = {
    "bundle.manifest.json",
    "manifest.json",
    "BUILD_RECEIPT.json",
}


def load_records() -> dict[str, dict]:
    """entity_id -> record, preferring the real entity record on collision.

    Several ids are claimed by more than one file. `entities/char_roake/` holds
    a bundle manifest and a build receipt carrying `canonical_id: char_roake`,
    outside the capsule directory — so a naive last-write-wins scan replaced the
    actual entity record with a sidecar that has no `entity_id` and none of the
    record's content. char_roake then reported as unreconciled with 12 open
    claims immediately after being reconciled, because the tool was reading the
    wrong file.

    Two guards: skip known sidecar filenames, and let a record that declares
    `entity_id` win over one that only declares `canonical_id`.
    """
    records: dict[str, dict] = {}
    if not CANON_L2.is_dir():
        return records
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix() or path.name in NON_ENTITY_FILENAMES:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        declared = data.get("entity_id")
        eid = declared or data.get("canonical_id")
        if not eid:
            continue
        eid = str(eid)
        incumbent = records.get(eid)
        if incumbent is not None and not declared and incumbent.get("entity_id"):
            continue  # keep the real entity record
        records[eid] = data
    return records


def resolve(eid: str, records: dict[str, dict], _seen: set | None = None) -> tuple[str, dict | None]:
    """Follow superseded_by so alias-keyed ledger entries land on the live record."""
    seen = _seen or set()
    record = records.get(eid)
    if record is None or eid in seen:
        return eid, record
    seen.add(eid)
    forward = record.get("superseded_by")
    if isinstance(forward, str) and forward and forward in records:
        return resolve(forward, records, seen)
    return eid, record


def cites_ledger(record: dict) -> bool:
    blob = json.dumps(record, ensure_ascii=False).lower()
    return any(marker in blob for marker in LEDGER_MARKERS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--open-only", action="store_true")
    ap.add_argument("--json", dest="as_json")
    args = ap.parse_args()

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    records = load_records()

    rows = []
    for eid, claims in ledger.items():
        target, record = resolve(eid, records)
        rows.append({
            "ledger_key": eid,
            "resolves_to": target,
            "claims": len(claims),
            "record_exists": record is not None,
            "reconciled": bool(record and cites_ledger(record)),
            "certainty": (record or {}).get("certainty"),
        })

    done = [r for r in rows if r["reconciled"]]
    missing = [r for r in rows if not r["record_exists"]]
    open_rows = [r for r in rows if r["record_exists"] and not r["reconciled"]]

    print(f"ledger entities      : {len(rows)}  ({sum(r['claims'] for r in rows)} claims)")
    print(f"reconciled           : {len(done)}  ({sum(r['claims'] for r in done)} claims)")
    print(f"open, record exists  : {len(open_rows)}  ({sum(r['claims'] for r in open_rows)} claims)")
    print(f"no canon record      : {len(missing)}  ({sum(r['claims'] for r in missing)} claims)")
    print()

    if not args.open_only and done:
        print("Already reconciled (largest first):")
        for r in sorted(done, key=lambda r: -r["claims"])[:10]:
            arrow = "" if r["ledger_key"] == r["resolves_to"] else f" -> {r['resolves_to']}"
            print(f"  {r['claims']:5d}  {r['ledger_key']}{arrow}")
        print()

    print("OPEN — record exists, no ledger provenance (largest first):")
    for r in sorted(open_rows, key=lambda r: -r["claims"])[:20]:
        arrow = "" if r["ledger_key"] == r["resolves_to"] else f" -> {r['resolves_to']}"
        print(f"  {r['claims']:5d}  {r['ledger_key']}{arrow}  [{r['certainty']}]")

    if missing:
        print("\nOPEN — no canon record at all (largest first):")
        for r in sorted(missing, key=lambda r: -r["claims"])[:15]:
            print(f"  {r['claims']:5d}  {r['ledger_key']}")

    if args.as_json:
        Path(args.as_json).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"\nwrote {args.as_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
