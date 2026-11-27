#!/usr/bin/env python3
"""Collect every referent canon names but does not have a record for.

Why these matter more than they look
------------------------------------
The world bible is itself a reconstruction: 139 of 242 entity records carry a
`recovered_source` naming exemption, and the promotion passes are all recovery
verbs — salvage, capsule closure, narrative reconciliation, prose-claim ledger.
Canon is the destination, not the origin.

So a name that appears in the prose with no record behind it is not a novelty
awaiting approval. It is material the reconstruction dropped. That inverts the
question: not "should this be admitted?" but "was it lost, or was it let go?"

Three fates are possible and they need different evidence:

* **dropped** — attested, distinct, nothing in canon covers it. Recover it.
* **superseded** — canon deliberately renamed, merged or retired it. Record the
  ruling so it stops resurfacing.
* **duplicate** — it is an existing entity under another name. Alias it.

Minting is the risky move, because a wrong mint creates a second entity for one
thing and every later reference has to guess. That is why this tool reports
evidence and does not decide.

Usage
-----
    python3 tools/canon_referent_gaps.py
    python3 tools/canon_referent_gaps.py --json gaps.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"
LEDGER = REPO_ROOT / "reports" / "recovery" / "data" / "prose_claim_ledger__2026-08-09.json"

#: Keys under which passes record a name they declined to mint.
GAP_KEYS = ("open_referents",)

#: Flags that mark an identity question rather than a content conflict.
IDENTITY_FLAG_HINTS = ("referent", "identity", "name", "directorship", "nature")


def entity_records() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not CANON_L2.is_dir():
        return out
    for path in CANON_L2.rglob("*.json"):
        if "/capsule/" in path.as_posix():
            continue
        if path.name in {"bundle.manifest.json", "manifest.json", "BUILD_RECEIPT.json"}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("entity_id"):
            out[str(data["entity_id"])] = data
    return out


def collect_gaps(records: dict[str, dict]) -> list[dict]:
    gaps: list[dict] = []
    for eid, rec in records.items():
        for key in GAP_KEYS:
            for item in rec.get(key) or []:
                if isinstance(item, dict) and item.get("term"):
                    gaps.append({
                        "term": item["term"],
                        "flagged_on": eid,
                        "status": item.get("status", ""),
                        "why": item.get("why_not_minted") or item.get("why_unresolved") or "",
                    })
        for flag in rec.get("conflict_flags") or []:
            if isinstance(flag, dict):
                name = str(flag.get("flag", ""))
                if any(h in name.lower() for h in IDENTITY_FLAG_HINTS):
                    gaps.append({
                        "term": name,
                        "flagged_on": eid,
                        "status": flag.get("status", "conflict_flag"),
                        "why": str(flag.get("detail", ""))[:200],
                    })
    return gaps


def canon_mentions(term: str) -> int:
    """How many canon files mention the term at all (records or prose docs)."""
    if not CANON_L2.is_dir():
        return 0
    needle = term.lower()
    hits = 0
    for path in CANON_L2.rglob("*"):
        if not path.is_file() or "/capsule/" in path.as_posix():
            continue
        try:
            if needle in path.read_text(encoding="utf-8", errors="ignore").lower():
                hits += 1
        except Exception:
            continue
    return hits


def ledger_mentions(term: str) -> int:
    if not LEDGER.is_file():
        return 0
    needle = term.lower()
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    return sum(
        1
        for claims in data.values()
        for c in claims
        if needle in str(c.get("claim", "")).lower()
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="as_json")
    args = ap.parse_args()

    records = entity_records()
    gaps = collect_gaps(records)

    # Dedupe by term, keeping every record that flagged it.
    merged: dict[str, dict] = {}
    for g in gaps:
        key = g["term"].lower()
        row = merged.setdefault(key, {**g, "flagged_on": []})
        row["flagged_on"].append(g["flagged_on"])

    print(f"entity records scanned : {len(records)}")
    print(f"flagged referents      : {len(merged)}\n")

    rows = []
    for key, row in sorted(merged.items()):
        term = row["term"]
        # A bare flag name is not a searchable term; skip counting for those.
        searchable = " " in term or term[0].isupper()
        cm = canon_mentions(term) if searchable else 0
        lm = ledger_mentions(term) if searchable else 0
        has_record = any(
            term.lower() in str(r.get("name", "")).lower()
            or term.lower() in [str(a).lower() for a in (r.get("aliases") or [])]
            for r in records.values()
        )
        rows.append({**row, "canon_files": cm, "ledger_claims": lm,
                     "has_entity_record": has_record})

    print(f"{'term':<44} {'canon':>6} {'ledger':>7}  record  flagged on")
    for r in sorted(rows, key=lambda r: -r["ledger_claims"]):
        flags = ", ".join(sorted(set(r["flagged_on"])))[:34]
        print(f"{r['term'][:44]:<44} {r['canon_files']:>6} "
              f"{r['ledger_claims']:>7}  {'yes' if r['has_entity_record'] else ' no'}    {flags}")

    if args.as_json:
        Path(args.as_json).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"\nwrote {args.as_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
