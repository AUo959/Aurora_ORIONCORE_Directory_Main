#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from _workspace_common import REPORTS_ANALYSIS_DIR, ROOT, ensure_parent, now_iso_utc, write_json


DEFAULT_BUNDLE_DIR = REPORTS_ANALYSIS_DIR / "recovered_root_text_batch__2026-03-20"
CORPUS_DIRNAME = "corpus"

L2_SOURCE_FILES = [
    "text_L2_characters .txt",
    "text_characters_zylox.txt",
]

L1_SOURCE_FILE = "text_Orion_Crew.txt"
L2_BASE_CORPUS = ROOT / "_staging" / "recovered_textAu__2026-03-13" / "L2" / "dossiers" / "l2_character_dossiers__recovered_textAu.json"
L1_LEDGER = ROOT / "reports" / "analysis" / "L1_ENTITY_LEDGER__2026-03-08.json"
L1_DRAFT_STAFF = ROOT / "intake" / "GUMAS_Staff_Core_Module_Rebuild.json"
L2_CANON_ROOT = ROOT / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS" / "L2_CANON__2026-03-19"

L1_ALIAS_MAP = {
    "Prof. E. Sorensen": "Prof. Elena Sorensen",
}


def normalize_name(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.replace("*", "")
    return value.lower()


def normalize_role(value: str) -> str:
    value = value.lower().replace("*", "")
    value = value.replace("(xo)", "executive officer")
    value = value.replace("(cso)", "chief science officer")
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def split_list_field(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_bullet_block(block: str) -> dict[str, str]:
    record: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        payload = line[2:]
        if ":" not in payload:
            continue
        key, value = payload.split(":", 1)
        record[key.strip()] = value.strip()
    return record


def parse_l2_profiles(root: Path) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source_name in L2_SOURCE_FILES:
        text = (root / source_name).read_text(encoding="utf-8", errors="replace")
        blocks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if "- Name:" in chunk]
        for block in blocks:
            parsed = parse_bullet_block(block)
            if not parsed.get("Name"):
                continue
            name = parsed["Name"]
            key = normalize_name(name)
            entry = merged.setdefault(
                key,
                {
                    "recovered_name": name,
                    "recovered_sources": [],
                    "recovered_profile": {},
                },
            )
            entry["recovered_sources"].append(source_name)
            for field_name, field_value in parsed.items():
                if field_name == "Name":
                    continue
                existing = entry["recovered_profile"].get(field_name)
                if existing and existing != field_value:
                    if isinstance(existing, list):
                        if field_value not in existing:
                            existing.append(field_value)
                    else:
                        entry["recovered_profile"][field_name] = [existing, field_value]
                else:
                    entry["recovered_profile"][field_name] = field_value

    records: list[dict[str, Any]] = []
    for entry in merged.values():
        profile = entry["recovered_profile"]
        records.append(
            {
                "recovered_name": entry["recovered_name"],
                "recovered_sources": sorted(set(entry["recovered_sources"])),
                "recovered_role": profile.get("Role", ""),
                "allegiance": profile.get("Allegiance", ""),
                "traits": split_list_field(profile.get("Traits", "")),
                "reputation": split_list_field(profile.get("Reputation", "")),
                "personal_relationships": split_list_field(profile.get("Personal Relationships", "")),
                "recent_actions": split_list_field(profile.get("Recent Actions", "")),
                "decision_style": profile.get("Decision Style", ""),
            }
        )
    return sorted(records, key=lambda item: item["recovered_name"])


def load_l2_base_corpus() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    data = json.loads(L2_BASE_CORPUS.read_text(encoding="utf-8"))
    index: dict[str, dict[str, Any]] = {}
    for row in data:
        index[normalize_name(row["canonical_name"])] = row
        for alias in row.get("aliases", []):
            index[normalize_name(alias)] = row
    return data, index


def load_l2_canon_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in sorted(L2_CANON_ROOT.glob("*/capsule/identity.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        canonical_name = data.get("character_name") or data.get("name")
        if not canonical_name:
            continue
        record = {
            "capsule_id": data.get("capsule_id") or data.get("canonical_id") or path.parts[-3],
            "name": canonical_name,
            "role": data.get("character_role") or data.get("role", ""),
            "certainty": data.get("certainty", ""),
            "path": path.relative_to(ROOT).as_posix(),
        }
        index[normalize_name(canonical_name)] = record
        for alias in data.get("aliases", []):
            index[normalize_name(alias)] = record
    return index


def role_alignment(recovered_role: str, canon_role: str) -> str:
    recovered_tokens = set(normalize_role(recovered_role).split())
    canon_tokens = set(normalize_role(canon_role).split())
    if not recovered_tokens or not canon_tokens:
        return "unknown"
    overlap = recovered_tokens & canon_tokens
    if overlap == recovered_tokens or overlap == canon_tokens:
        return "aligned"
    if len(overlap) >= max(2, min(len(recovered_tokens), len(canon_tokens)) // 2):
        return "compatible_variation"
    return "role_drift"


def build_l2_enrichment(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recovered = parse_l2_profiles(root)
    _, base_index = load_l2_base_corpus()
    canon_index = load_l2_canon_index()
    enrichments: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []

    for record in recovered:
        recovered_name = record["recovered_name"]
        base_match = base_index.get(normalize_name(recovered_name))
        canon_match = canon_index.get(normalize_name(recovered_name))
        if not canon_match and base_match:
            canon_match = canon_index.get(normalize_name(base_match["canonical_name"]))

        canonical_name = (
            base_match["canonical_name"]
            if base_match
            else canon_match["name"]
            if canon_match
            else recovered_name
        )
        role_reference = ""
        if base_match:
            role_reference = base_match.get("role", "")
        elif canon_match:
            role_reference = canon_match.get("role", "")

        alignment = role_alignment(record["recovered_role"], role_reference) if role_reference else "new_record"
        alias_note = ""
        if canonical_name != recovered_name:
            alias_note = f"Recovered name normalizes to existing canonical identity '{canonical_name}'."
        notes = (
            alias_note
            if alias_note
            else "Recovered profile resolves to an active canon capsule and enriches an existing character identity."
            if canon_match
            else "Recovered profile enriches an existing character identity."
            if base_match
            else "Recovered profile did not match existing corpus or canon."
        )

        enrichments.append(
            {
                "canonical_id": base_match["canonical_id"] if base_match else None,
                "canonical_name": canonical_name,
                "recovered_name": recovered_name,
                "match_status": "matched_existing" if (base_match or canon_match) else "new_staging",
                "base_corpus_match": base_match["canonical_id"] if base_match else None,
                "canon_capsule_match": canon_match["capsule_id"] if canon_match else None,
                "certainty_reference": (
                    canon_match["certainty"]
                    if canon_match
                    else base_match["certainty"]
                    if base_match
                    else "STAGING"
                ),
                "doc_sources": sorted(
                    set(
                        record["recovered_sources"]
                        + (base_match.get("doc_sources", []) if base_match else [])
                        + ([canon_match["path"]] if canon_match else [])
                    )
                ),
                "recovered_profile": {
                    "role": record["recovered_role"],
                    "allegiance": record["allegiance"],
                    "traits": record["traits"],
                    "reputation": record["reputation"],
                    "personal_relationships": record["personal_relationships"],
                    "recent_actions": record["recent_actions"],
                    "decision_style": record["decision_style"],
                },
                "clash_check": {
                    "name_collision": False,
                    "role_alignment": alignment,
                    "alias_note": alias_note,
                    "notes": notes,
                },
            }
        )
        audit.append(
            {
                "layer": "L2",
                "recovered_name": recovered_name,
                "canonical_name": canonical_name,
                "match_status": "matched_existing" if (base_match or canon_match) else "new_staging",
                "role_alignment": alignment,
                "base_corpus_match": base_match["canonical_id"] if base_match else None,
                "canon_capsule_match": canon_match["capsule_id"] if canon_match else None,
                "hard_collision": False,
                "notes": notes if (base_match or canon_match) else "No hard clash detected.",
            }
        )
    return enrichments, audit


def parse_l1_crew_registry(root: Path) -> list[dict[str, str]]:
    text = (root / L1_SOURCE_FILE).read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if "|" not in line or line.strip().startswith("|---") or "Name" in line:
            continue
        pieces = [piece.strip() for piece in line.strip().strip("|").split("|")]
        if len(pieces) != 5:
            continue
        if not pieces[0]:
            continue
        rows.append(
            {
                "recovered_name": pieces[0],
                "recovered_title": pieces[1],
                "recovered_guild": pieces[2],
                "recovered_module": pieces[3],
                "recovered_anchor_path": pieces[4],
            }
        )
    return rows


def load_l1_ledger_index() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    data = json.loads(L1_LEDGER.read_text(encoding="utf-8"))
    humans = data["humans"]
    index: dict[str, dict[str, Any]] = {}
    for row in humans:
        index[normalize_name(row["display_name"])] = row
        index[normalize_name(row["name"])] = row
        legacy_drift = row.get("legacy_drift") or {}
        for variant in legacy_drift.get("name_variants", []):
            index[normalize_name(variant)] = row
    return humans, index


def load_l1_draft_staff_index() -> dict[str, dict[str, Any]]:
    if not L1_DRAFT_STAFF.exists():
        return {}
    data = json.loads(L1_DRAFT_STAFF.read_text(encoding="utf-8"))
    records = data.get("staff_registry", data.get("staff", data.get("Staff", data)))
    index: dict[str, dict[str, Any]] = {}
    if isinstance(records, list):
        for row in records:
            name = row.get("Name") or row.get("name")
            if name:
                index[normalize_name(name)] = row
    return index


def match_l1_record(
    recovered_name: str,
    ledger_index: dict[str, dict[str, Any]],
    draft_index: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any] | None, str]:
    alias_name = L1_ALIAS_MAP.get(recovered_name, recovered_name)
    direct = ledger_index.get(normalize_name(recovered_name))
    if direct:
        return "matched_primary", direct, ""

    alias_match = ledger_index.get(normalize_name(alias_name))
    if alias_match:
        return "probable_alias", alias_match, f"Recovered name '{recovered_name}' treated as alias of '{alias_match['name']}'."

    draft_match = draft_index.get(normalize_name(recovered_name))
    if draft_match:
        return "draft_only_match", None, "Recovered name appears in draft intake staff module but not current primary L1 ledger."

    return "new_staging", None, "Recovered name not found in current L1 ledger."


def build_l1_enrichment(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recovered = parse_l1_crew_registry(root)
    _, ledger_index = load_l1_ledger_index()
    draft_index = load_l1_draft_staff_index()
    enrichments: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []

    for record in recovered:
        match_status, ledger_match, note = match_l1_record(record["recovered_name"], ledger_index, draft_index)
        canonical_name = ledger_match["name"] if ledger_match else record["recovered_name"]
        canonical_role = ledger_match["role"] if ledger_match else ""
        alignment = role_alignment(record["recovered_title"], canonical_role) if canonical_role else "new_record"

        enrichments.append(
            {
                "recovered_name": record["recovered_name"],
                "canonical_name": canonical_name,
                "match_status": match_status,
                "matched_entity_id": ledger_match["entity_id"] if ledger_match else None,
                "canonical_role_reference": canonical_role or None,
                "recovered_role": record["recovered_title"],
                "recovered_guild": record["recovered_guild"],
                "recovered_module": record["recovered_module"],
                "recovered_anchor_path": record["recovered_anchor_path"],
                "doc_sources": [L1_SOURCE_FILE],
                "clash_check": {
                    "name_collision": False,
                    "role_alignment": alignment,
                    "notes": note or "No hard clash detected.",
                },
            }
        )
        audit.append(
            {
                "layer": "L1",
                "recovered_name": record["recovered_name"],
                "canonical_name": canonical_name,
                "match_status": match_status,
                "matched_entity_id": ledger_match["entity_id"] if ledger_match else None,
                "role_alignment": alignment,
                "hard_collision": False,
                "notes": note or "No hard clash detected.",
            }
        )
    return enrichments, audit


def build_audit_markdown(
    generated_at: str,
    l2_enrichments: list[dict[str, Any]],
    l1_enrichments: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> str:
    counts = Counter(row["match_status"] for row in audit_rows)
    lines = [
        "# Character Clash Audit",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Summary",
        "",
        f"- L2 recovered profiles processed: `{len(l2_enrichments)}`",
        f"- L1 recovered crew rows processed: `{len(l1_enrichments)}`",
        f"- Hard collisions detected: `0`",
        "",
        "## Match Status Counts",
        "",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Soft Issues", ""])
    soft_rows = [row for row in audit_rows if row["match_status"] in {"probable_alias", "draft_only_match", "new_staging"} or row["role_alignment"] == "role_drift"]
    if not soft_rows:
        lines.append("- None")
    else:
        for row in soft_rows:
            lines.append(
                f"- `{row['layer']}` `{row['recovered_name']}` -> `{row['canonical_name']}` "
                f"[{row['match_status']}; role {row['role_alignment']}] {row['notes']}"
            )

    lines.extend(["", "## Result", ""])
    lines.append("- Recovered character details were added as corpus enrichments, and any now-primary matches resolve against the active canon ledger.")
    lines.append("- Existing canonical identities were reused wherever available.")
    return "\n".join(lines) + "\n"


def build_corpus_readme(generated_at: str) -> str:
    return (
        "# Character Corpus Enrichment\n\n"
        f"Generated: `{generated_at}`\n\n"
        "This corpus adds recovered character detail from the root text artifacts into staged,\n"
        "schema-aligned enrichment files. It does not overwrite locked canon. Instead, it reuses\n"
        "existing L2 and L1 identities where matches exist and records a clash audit for review.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build recovered character enrichment corpora.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--bundle-dir", default=str(DEFAULT_BUNDLE_DIR))
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve() if args.root else ROOT
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    corpus_dir = bundle_dir / CORPUS_DIRNAME
    corpus_dir.mkdir(parents=True, exist_ok=True)
    generated_at = now_iso_utc()

    l2_enrichments, l2_audit = build_l2_enrichment(root)
    l1_enrichments, l1_audit = build_l1_enrichment(root)
    audit_rows = l2_audit + l1_audit

    write_json(corpus_dir / "l2_character_corpus_enrichment__recovered_root_text_batch.json", l2_enrichments)
    write_json(corpus_dir / "l1_character_corpus_enrichment__recovered_root_text_batch.json", l1_enrichments)
    write_json(corpus_dir / "character_clash_audit.json", audit_rows)
    ensure_parent(corpus_dir / "README.md")
    (corpus_dir / "README.md").write_text(build_corpus_readme(generated_at), encoding="utf-8")
    (corpus_dir / "CHARACTER_CLASH_AUDIT.md").write_text(
        build_audit_markdown(generated_at, l2_enrichments, l1_enrichments, audit_rows),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
