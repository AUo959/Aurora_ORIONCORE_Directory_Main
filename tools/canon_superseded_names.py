#!/usr/bin/env python3
"""Flag canon records that still use a name canon has ruled superseded.

Why this exists
---------------
Conflict scans compare a candidate against existing ENTITY RECORDS. They do not
read the rulings that declare a name superseded, so a *rename* passes cleanly
while a duplicate string is caught.

That gap produced a live inconsistency. On 2026-07-20 canon ruled
``"Galactic Security Bureau" -> canonical Union Intelligence Bureau``. On
2026-07-21 ``char_sarina_vael`` was promoted as "Director of the Galactic
Security Bureau (GSB)" with a conflict scan recording *"zero name/office
collisions"*. Both statements were true as written: no other record used that
string. The scan simply never read the ruling issued the day before — which is
why that record's own notes say "No GSB org record exists yet". There is no GSB
record because GSB is not a canonical agency.

What counts as a use
--------------------
The distinction that makes this checker useful rather than noisy: a superseded
name appearing in an IDENTITY field (``name``, ``role``, ``title``) is a finding,
because the record is asserting it. The same string in an alias, a documented
conflict block, or a history note is *correct* — that is canon recording its own
drift, and flagging it would punish the records that did the right thing.

This mirrors the ``conflict_flags`` lesson from tools/canon_reference_integrity.py:
a field that legitimately carries curator annotation cannot be a hard check.

Usage
-----
    python3 tools/canon_superseded_names.py
    python3 tools/canon_superseded_names.py --rulings   # show the index only
    python3 tools/canon_superseded_names.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANON_L2 = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L2"

#: ``early surname "X" -> canonical **Y**`` and its siblings.
#:
#: Applied to whitespace-normalised text, NOT line by line: canon markdown wraps
#: these declarations mid-sentence, so the Zylox and GSB rulings each straddle a
#: line break. A line-oriented grep finds neither.
RENAME = re.compile(
    r'(early (?:[a-z]+ )?(?:name|surname|title)|earlier title)\s*'
    r'"([^"]+)"\s*(?:→|->)\s*canonical\s*\*\*([^*]+)\*\*',
    re.IGNORECASE,
)

#: Fields where a name is ASSERTED as this record's identity.
IDENTITY_FIELDS = ("name", "role", "title")

#: Fields where a superseded name is legitimately recorded rather than claimed:
#: aliases preserve searchability, and conflict/history blocks are canon
#: documenting its own drift. Substring, so `agency_name_conflict`,
#: `alignment_conflict`, `career_arc` and `*_note` are all covered.
ANNOTATION_MARKERS = (
    "alias", "conflict", "note", "history", "prev_", "superseded",
    "supersedes", "disambiguation", "lineage", "career", "variant",
)


def load_rulings(canon: Path = CANON_L2) -> list[dict]:
    """Index every superseded-name ruling declared in canon markdown."""
    rulings: list[dict] = []
    if not canon.is_dir():
        return rulings
    for path in sorted(canon.rglob("*.md")):
        try:
            body = " ".join(path.read_text(encoding="utf-8", errors="ignore").split())
        except Exception:
            continue
        for match in RENAME.finditer(body):
            rulings.append({
                "kind": match.group(1).strip().lower(),
                "superseded": match.group(2).strip(),
                "canonical": match.group(3).strip(),
                "authority": str(path.relative_to(canon)),
            })
    return rulings


def _records(canon: Path):
    for path in sorted(canon.rglob("*.json")):
        if "/capsule/" in path.as_posix():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("entity_kind"):
            yield path, data


def find_violations(canon: Path = CANON_L2, rulings: list[dict] | None = None) -> list[dict]:
    """Records asserting a superseded name in an identity field."""
    rulings = load_rulings(canon) if rulings is None else rulings
    if not rulings:
        return []
    out = []
    for path, data in _records(canon):
        for ruling in rulings:
            needle = ruling["superseded"].lower()
            for field in IDENTITY_FIELDS:
                value = data.get(field)
                if isinstance(value, str) and needle in value.lower():
                    out.append({
                        "entity_id": data.get("entity_id") or data.get("canonical_id"),
                        "field": field,
                        "value": value,
                        "superseded": ruling["superseded"],
                        "canonical": ruling["canonical"],
                        "authority": ruling["authority"],
                        "file": str(path.relative_to(canon)),
                    })
    return out


def find_annotations(canon: Path = CANON_L2, rulings: list[dict] | None = None) -> list[dict]:
    """Records that MENTION a superseded name outside identity fields.

    Reported separately and never as a violation: this is canon recording its
    own drift, which is the behaviour we want.
    """
    rulings = load_rulings(canon) if rulings is None else rulings
    out = []
    for path, data in _records(canon):
        blob = json.dumps(data, ensure_ascii=False).lower()
        for ruling in rulings:
            needle = ruling["superseded"].lower()
            if needle not in blob:
                continue
            if any(
                isinstance(data.get(f), str) and needle in data[f].lower()
                for f in IDENTITY_FIELDS
            ):
                continue  # counted as a violation instead
            out.append({
                "entity_id": data.get("entity_id") or data.get("canonical_id"),
                "superseded": ruling["superseded"],
                "canonical": ruling["canonical"],
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rulings", action="store_true", help="Print the ruling index and exit")
    ap.add_argument("--json", dest="as_json", action="store_true")
    args = ap.parse_args()

    rulings = load_rulings()
    if not rulings:
        print("canon-superseded-names: no rename rulings found — is CanonRec checked out?",
              file=sys.stderr)
        return 1

    if args.rulings:
        for r in rulings:
            print(f"  {r['superseded']!r} -> {r['canonical']!r}   [{r['kind']}]  {r['authority']}")
        return 0

    violations = find_violations(rulings=rulings)
    annotations = find_annotations(rulings=rulings)

    if args.as_json:
        print(json.dumps({"rulings": rulings, "violations": violations,
                          "annotations": annotations}, indent=2))
        return 1 if violations else 0

    print(f"canon-superseded-names: {len(rulings)} rename ruling(s) indexed")
    print(f"  identity-field violations : {len(violations)}")
    print(f"  documented mentions       : {len(annotations)} (not violations)")

    if violations:
        print("\nRECORDS ASSERTING A SUPERSEDED NAME:")
        for v in violations:
            print(f"  {v['entity_id']}.{v['field']}")
            print(f"    {v['value']!r}")
            print(f"    {v['superseded']!r} was superseded by {v['canonical']!r}")
            print(f"    ruling: {v['authority']}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
