#!/usr/bin/env python3
"""Fabric-invariants static checker (FABRIC_INVARIANTS spec v0.1).

Statically verifies the T (temporal), P (physical), and C (corporeal)
invariant sets from CanonRec canon/L2/mechanics/FABRIC_INVARIANTS__v0.1
against canon records. First test case: the Velar Imperium domain pass.

Deterministic, stdlib-only. Exit codes: 0 = no violations (gaps/info may
exist), 1 = violations found, 2 = execution error.

Usage:
    python3 tools/fabric_invariants_check.py [--domain velar] [--json PATH]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

CANONREC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "GUMAS_SIM_2.5",
    "CanonRec",
)

STATUS_VOCAB = {
    "active", "deceased", "destroyed", "retired", "unknown", "inactive",
    "alias_forward_only",  # SUPERSEDED alias-forward records (CERTAINTY_TAGS.md)
}

DOMAIN_FACTIONS = {"velar": {"velar_imperium"}, "union": {"galactic_union"}}


def add(findings, code, severity, subject, detail):
    findings.append(
        {"invariant": code, "severity": severity, "subject": subject, "detail": detail}
    )


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_years_ago(timeframe):
    """Parse a canonical '~N years ago/before present' style timeframe.

    Returns (max_years_ago, min_years_ago) or None if not parseable
    (Present, Unknown, geological ranges are handled explicitly).
    """
    if not timeframe:
        return None
    tf = timeframe.strip().lower().replace("–", "-").replace("—", "-")
    if tf.startswith("present"):
        return (0.0, 0.0)
    if tf in {"unknown"}:
        return None
    mult = 1_000_000 if "million" in tf else 1.0
    nums = [float(n.replace(",", "")) for n in re.findall(r"[\d,]+(?:\.\d+)?", tf)]
    if not nums:
        return None
    vals = [n * mult for n in nums]
    return (max(vals), min(vals))


def domain_entities(domain_factions):
    """Collect (path, record) pairs for entity JSONs bound to the domain."""
    out = []
    ent_root = os.path.join(CANONREC, "canon", "L2", "entities")
    for path in sorted(glob.glob(os.path.join(ent_root, "**", "*.json"), recursive=True)):
        base = os.path.basename(path)
        if base.startswith(("CANON_LOCK", "DISAMBIGUATION")):
            continue
        try:
            rec = load_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(rec, dict):
            continue
        bindings = set(rec.get("faction_bindings") or [])
        if rec.get("faction_id"):
            bindings.add(rec["faction_id"])
        if rec.get("allegiance"):
            bindings.add(rec["allegiance"])
        if bindings & domain_factions:
            out.append((path, rec))
    return out


def all_entity_ids():
    ids = set()
    ent_root = os.path.join(CANONREC, "canon", "L2", "entities")
    for path in glob.glob(os.path.join(ent_root, "**", "*.json"), recursive=True):
        try:
            rec = load_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(rec, dict):
            for key in ("entity_id", "canonical_id"):
                if rec.get(key):
                    ids.add(rec[key])
    for cap in glob.glob(os.path.join(ent_root, "*", "capsule", "identity.json")):
        ids.add(os.path.basename(os.path.dirname(os.path.dirname(cap))))
    return ids


# ---------------------------------------------------------------- T checks
def check_temporal(findings, domain_terms):
    tl_dir = os.path.join(CANONREC, "canon", "L2", "timeline")
    files = sorted(glob.glob(os.path.join(tl_dir, "*.json")))
    per_file_events = {}
    for path in files:
        name = os.path.basename(path)
        data = load_json(path)
        eras = data.get("Galactic_Timeline", [])
        prev_oldest = None
        events = {}
        for era in eras:
            era_name = era.get("era") or era.get("era_id") or "?"
            oldest_in_era = None
            for ev in era.get("events", []):
                tf = ev.get("timeframe") or ev.get("date")
                parsed = parse_years_ago(tf)
                key = ev.get("event_id") or ev.get("name")
                if key:
                    events[key] = (tf, parsed, era_name)
                if parsed is None:
                    continue
                oldest_in_era = max(oldest_in_era or 0, parsed[0])
            # T1: eras must run oldest -> newest.
            if oldest_in_era is not None and prev_oldest is not None:
                if oldest_in_era > prev_oldest:
                    add(
                        findings,
                        "T1",
                        "VIOLATION",
                        f"{name}:{era_name}",
                        f"Era ordering non-monotonic: era oldest event "
                        f"{oldest_in_era} ya follows an era at {prev_oldest} ya.",
                    )
            if oldest_in_era is not None:
                prev_oldest = oldest_in_era
        per_file_events[name] = events

    # T1 cross-file: same event_id must carry the same timeframe everywhere.
    names = list(per_file_events)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            shared = set(per_file_events[a]) & set(per_file_events[b])
            for key in sorted(shared):
                tf_a = per_file_events[a][key][0]
                tf_b = per_file_events[b][key][0]
                if (tf_a or "").strip() != (tf_b or "").strip():
                    add(
                        findings,
                        "T1",
                        "VIOLATION",
                        key,
                        f"Timeframe drift between {a} ({tf_a!r}) and {b} ({tf_b!r}).",
                    )

    # T2: any stated cycle:year ratio must be 1:1.
    corpus = glob.glob(os.path.join(CANONREC, "canon", "**", "*.md"), recursive=True)
    ratio_re = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:standard\s+)?years?\s*(?:=|per)\s*(?:1\s*)?"
        r"galactic\s+cycle|galactic\s+cycle\s*=\s*(\d+(?:\.\d+)?)\s*(?:standard\s+)?years?",
        re.IGNORECASE,
    )
    for path in sorted(corpus):
        try:
            text = open(path, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        for m in ratio_re.finditer(text):
            val = m.group(1) or m.group(2)
            if val and float(val) != 1.0:
                add(
                    findings,
                    "T2",
                    "VIOLATION",
                    os.path.relpath(path, CANONREC),
                    f"Cycle ratio {val}:1 conflicts with canonical 1 cycle = 1 year.",
                )

    # T3: explicit ages inside recent_actions must be within ~2 cycles.
    for path, rec in domain_terms["entities"]:
        texts = []
        cap_dir = os.path.dirname(path)
        kfile = os.path.join(cap_dir, "knowledge.jsonl")
        if os.path.basename(path) == "identity.json" and os.path.exists(kfile):
            for line in open(kfile, encoding="utf-8"):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("type") == "recent_actions":
                    texts.append(row.get("text", ""))
        for text in texts:
            for m in re.finditer(r"~?(\d+)\s*(?:years?|cycles?)\s*ago", text):
                if int(m.group(1)) > 2:
                    add(
                        findings,
                        "T3",
                        "VIOLATION",
                        os.path.relpath(path, CANONREC),
                        f"recent_actions cites {m.group(0)!r} (> ~2 cycles).",
                    )
            if not re.search(r"\d", text):
                add(
                    findings,
                    "T3",
                    "INFO",
                    os.path.relpath(path, CANONREC),
                    "recent_actions undated; snapshot-window compliance "
                    "unverifiable statically (assumed Present-window).",
                )


# ---------------------------------------------------------------- P checks
def load_authority_table():
    path = os.path.join(
        CANONREC,
        "canon",
        "L2",
        "map",
        "L2_MAP__LOCATION_AUTHORITY_TABLE__v0.1__2026-02-08__BAY02_0809.md",
    )
    rows = {}
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        if not line.strip().startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0] not in {"Name", ""}:
            rows[cells[0].replace("‑", "-").replace("‐", "-")] = {
                "status": cells[3],
                "notes": cells[5],
            }
    return rows


def check_physical(findings, domain_terms):
    table = load_authority_table()
    known_ids = domain_terms["all_ids"]

    def table_row(name):
        norm = name.replace("‑", "-").lower()
        for key, row in table.items():
            if key.lower().startswith(norm[: max(len(norm) // 2, 8)]) or norm in key.lower():
                return key, row
        return None, None

    for path, rec in domain_terms["entities"]:
        rel = os.path.relpath(path, CANONREC)
        kind = rec.get("entity_kind")
        if kind == "location":
            if rec.get("certainty") == "SUPERSEDED":
                continue  # alias-forward records carry no placement obligations
            # P1: map/table is source of truth for placement.
            key, row = table_row(rec.get("name", ""))
            ent_status = rec.get("canonical_position_status")
            if row:
                tbd = "TBD" in (row["notes"] or "") or "TBD" in (row["status"] or "")
                staging = (row["status"] or "").upper() == "STAGING"
                if ent_status == "canon" and (tbd or staging):
                    add(
                        findings,
                        "P1",
                        "VIOLATION",
                        rec.get("entity_id", rel),
                        f"Entity claims canonical placement but map authority row "
                        f"{key!r} is {row['status']} with notes {row['notes']!r} — "
                        "map is source of truth; placement is unresolved.",
                    )
            else:
                add(
                    findings,
                    "P1",
                    "GAP",
                    rec.get("entity_id", rel),
                    "No row found in map authority table for this location.",
                )
            # P3: region references must resolve; no ghost edges.
            region = rec.get("region_id")
            if region is None:
                add(
                    findings,
                    "P3",
                    "GAP",
                    rec.get("entity_id", rel),
                    "region_id is null — location has no adjacency anchor.",
                )
            elif region not in known_ids:
                add(
                    findings,
                    "P3",
                    "VIOLATION",
                    rec.get("entity_id", rel),
                    f"region_id {region!r} does not resolve to a canonical entity.",
                )
            note = rec.get("promotion_note") or ""
            if (
                "collapse into" in note
                and not rec.get("parent_org_id")
                and not rec.get("forwarded_to")
            ):
                add(
                    findings,
                    "P3",
                    "GAP",
                    rec.get("entity_id", rel),
                    f"Promotion note says {note!r} but no structural parent link "
                    "field exists on the record.",
                )
        if kind == "mobile_asset":
            # P2: moving entities never hold fixed coordinates.
            for field in ("region_id", "coordinates", "position", "fixed_position"):
                if rec.get(field):
                    add(
                        findings,
                        "P2",
                        "VIOLATION",
                        rec.get("canonical_id", rel),
                        f"Mobile asset holds fixed placement field {field!r}.",
                    )
            if "placement_rule" not in rec:
                add(
                    findings,
                    "P2",
                    "GAP",
                    rec.get("canonical_id", rel),
                    "No placement_rule field; P2 is only enforced at reconciler "
                    "validation, not in the record schema.",
                )


# ---------------------------------------------------------------- C checks
def check_corporeal(findings, domain_terms):
    offices = {}
    for path, rec in domain_terms["entities"]:
        rel = os.path.relpath(path, CANONREC)
        subject = rec.get("canonical_id") or rec.get("entity_id") or rel
        status = rec.get("status")
        # C2: exactly one living-status value from the vocabulary.
        if status is not None:
            if isinstance(status, list):
                add(findings, "C2", "VIOLATION", subject, f"Multiple statuses: {status}.")
            elif status not in STATUS_VOCAB:
                add(
                    findings,
                    "C2",
                    "VIOLATION",
                    subject,
                    f"Status {status!r} outside vocabulary {sorted(STATUS_VOCAB)}.",
                )
        # C1: characters need a single location binding to be checkable.
        if os.path.basename(path) == "identity.json":
            binding = rec.get("location_binding")
            if binding is None:
                loc_fields = [
                    k for k in rec if "location" in k.lower() or "vessel" in k.lower()
                ]
                if not loc_fields:
                    add(
                        findings,
                        "C1",
                        "GAP",
                        subject,
                        "Character capsule has no location_binding field; "
                        "one-body-one-place is unenforceable statically or in-engine.",
                    )
            elif isinstance(binding, list):
                add(
                    findings,
                    "C1",
                    "VIOLATION",
                    subject,
                    f"Multiple simultaneous location bindings: {binding}.",
                )
            elif not isinstance(binding, dict) or not binding.get("target_id"):
                add(
                    findings,
                    "C1",
                    "VIOLATION",
                    subject,
                    "location_binding present but malformed (needs type/target_id/basis).",
                )
            elif binding["target_id"] not in domain_terms["all_ids"]:
                add(
                    findings,
                    "C1",
                    "VIOLATION",
                    subject,
                    f"location_binding target {binding['target_id']!r} does not resolve "
                    "to a canonical entity.",
                )
            # C3: collect office claims (title prefix of name + role).
            name = rec.get("name") or rec.get("character_name") or ""
            m = re.match(r"((?:Lord|Chief|Grand)\s+Marshal)\b", name)
            role = rec.get("role") or rec.get("character_role") or ""
            faction = rec.get("faction_id") or "?"
            if m and status == "active":
                offices.setdefault((m.group(1), faction), []).append(subject)
            if "Supreme Military Commander" in role and status == "active":
                offices.setdefault(("Supreme Military Commander", faction), []).append(subject)
    # C2 cross-check: deceased characters must not sit on active crew rosters.
    deceased = set()
    for path, rec in domain_terms["entities"]:
        if rec.get("status") == "deceased":
            deceased.add(rec.get("canonical_id") or rec.get("entity_id") or "")
    if deceased:
        for path, rec in domain_terms["entities"]:
            if rec.get("entity_kind") != "mobile_asset" and not rec.get("crew_ids"):
                continue
            roster = set(rec.get("crew_ids") or [])
            if rec.get("commanding_officer_id"):
                roster.add(rec["commanding_officer_id"])
            overlap = sorted(roster & deceased)
            if overlap and rec.get("status") == "active":
                add(
                    findings,
                    "C2",
                    "VIOLATION",
                    rec.get("canonical_id") or rec.get("entity_id") or path,
                    f"Active asset lists deceased personnel on its roster: {overlap}.",
                )

    # C3: at most one living incumbent per office per faction.
    for (office, faction), holders in sorted(offices.items()):
        if len(holders) > 1:
            add(
                findings,
                "C3",
                "VIOLATION",
                f"{office} ({faction})",
                f"Multiple living incumbents: {holders}.",
            )
    # C4: named actors referenced in domain knowledge must resolve.
    known_names = domain_terms["all_ids"]
    alias_index = domain_terms["alias_index"]
    for path, rec in domain_terms["entities"]:
        if os.path.basename(path) != "identity.json":
            continue
        cap_dir = os.path.dirname(path)
        kfile = os.path.join(cap_dir, "knowledge.jsonl")
        if not os.path.exists(kfile):
            continue
        text = open(kfile, encoding="utf-8").read()
        for m in re.finditer(
            r"(?:Chancellor|Marshal|Commander|General|Chief|Lord)\s+([A-Z][a-z']+)", text
        ):
            person = m.group(1)
            # Title-compound stopwords: "Chief Science Officer", "Lord Commander" etc.
            # are role strings, not personal names.
            if person.lower() in {
                "council", "academy", "class", "science", "medical", "engineering",
                "security", "operations", "command", "staff", "officer", "marshal",
                "commander", "general", "chief", "high", "standard", "of", "the",
                "charter", "corps", "service", "bureau", "directorate", "assembly",
                "council's", "charter's", "academy's", "prime", "supreme",
            }:
                continue
            # Trailing possessive ("Chief Marshal's reports") leaves a stray token.
            person = person.rstrip("'’s")
            if not person or person.lower() in {"marshal", "chief", "high"}:
                continue
            resolved = any(
                person.lower() in n.lower() for n in known_names
            ) or person.lower() in alias_index
            if not resolved:
                add(
                    findings,
                    "C4",
                    "VIOLATION",
                    os.path.relpath(kfile, CANONREC),
                    f"Named actor {m.group(0)!r} does not resolve to any canonical "
                    "entity or registered alias.",
                )


def build_alias_index():
    idx = set()
    ent_root = os.path.join(CANONREC, "canon", "L2", "entities")
    for path in glob.glob(os.path.join(ent_root, "**", "*.json"), recursive=True):
        try:
            rec = load_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(rec, dict):
            for alias in rec.get("aliases") or []:
                for tok in re.split(r"[\s'\-]", alias):
                    if tok:
                        idx.add(tok.lower())
            for field in ("name", "character_name"):
                for tok in re.split(r"[\s'\-]", rec.get(field) or ""):
                    if tok:
                        idx.add(tok.lower())
    return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", default="velar", choices=sorted(DOMAIN_FACTIONS))
    ap.add_argument("--json", help="write findings JSON to this path")
    args = ap.parse_args()

    factions = DOMAIN_FACTIONS[args.domain]
    findings = []
    entities = domain_entities(factions)
    if not entities:
        print("ERROR: no domain entities found — check CanonRec path", file=sys.stderr)
        return 2
    terms = {
        "entities": entities,
        "all_ids": all_entity_ids(),
        "alias_index": build_alias_index(),
    }
    check_temporal(findings, terms)
    check_physical(findings, terms)
    check_corporeal(findings, terms)

    order = {"VIOLATION": 0, "GAP": 1, "INFO": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["invariant"], f["subject"]))
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in order}
    print(
        f"fabric-invariants [{args.domain}] — entities scanned: {len(entities)} | "
        f"violations: {counts['VIOLATION']} gaps: {counts['GAP']} info: {counts['INFO']}"
    )
    for f in findings:
        print(f"  [{f['severity']:9s}] {f['invariant']}  {f['subject']}: {f['detail']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(
                {"domain": args.domain, "spec": "FABRIC_INVARIANTS__v0.1",
                 "counts": counts, "findings": findings},
                fh,
                indent=2,
                sort_keys=True,
            )
            fh.write("\n")
    return 1 if counts["VIOLATION"] else 0


if __name__ == "__main__":
    sys.exit(main())
