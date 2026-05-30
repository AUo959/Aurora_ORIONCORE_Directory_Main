#!/usr/bin/env python3
"""
Aurora Canon Reconciler — Entity Validation Script

Validates draft Aurora OS entities against the canonical schema requirements.
Produces a structured validation report with BLOCK/WARN/INFO severity levels.

Usage:
    python validate_entity.py --input <draft_file> --layer <L1|L2|L3> --type <entity_type>
    python validate_entity.py --input <draft_file> --auto-detect
    python validate_entity.py --json '{"name": "Test", ...}' --layer L1 --type character

Output: JSON validation report to stdout, human-readable summary to stderr.
"""

import argparse
import json
import os
import re
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

VALID_CERTAINTY_TAGS = {
    "CANON", "CANON_PROMOTE", "LOCKED_POSITION", "PLACED",
    "STAGING", "UNCONFIRMED", "LEGEND_CONTESTED", "APPROX"
}

VALID_ENTITY_KINDS = {
    "location", "ship", "fleet", "anomaly", "megafauna", "facility",
    "domain", "polity", "species", "character"
}

VALID_L2_LOCATION_SUBTYPES = {
    "system", "planet", "moon", "region", "route", "facility",
    "anomaly", "station", "unknown", "system_id"
}

VALID_L2_POLITY_SUBTYPES = {
    "nation_state", "federation", "compact", "collective",
    "pmc", "pact", "confederation",
    # v1.1: Added for entities that blur the polity/domain boundary
    "remnant_network", "precursor_remnant",
}

VALID_L2_SPECIES_SUBTYPES = {
    "biological", "synthetic", "hybrid", "energy", "unknown"
}

VALID_L1_VESSEL_STATUSES = {
    "ACTIVE", "DOCKED", "DEPLOYED", "MAINTENANCE", "DECOMMISSIONED"
}

VALID_L1_SYSTEM_STATUSES = {
    "NOMINAL", "DEGRADED", "OFFLINE", "MAINTENANCE"
}

MOVING_ENTITY_KINDS = {"ship", "fleet", "megafauna"}

L1_CHARACTER_ID_PREFIXES = {
    "CMD_", "ENG_", "SCI_", "MED_", "OPS_", "SEC_", "AI_"
}

# v1.1: Known valid L1 clearance levels (from canonical crew profiles)
VALID_L1_CLEARANCE_LEVELS = {
    "L1_GENERAL", "L2_OPERATIONAL", "L3_TECHNICAL", "L3_RESEARCH",
    "L4_COMMAND", "L5_EXECUTIVE",
}
# Note: L4_COMMAND *is* accepted (Thorne/Shepard level) but was previously
# undocumented. We now track it explicitly so we can flag truly unknown levels
# rather than silently accept anything.

# v1.1: Known L2 polity/faction names for cross-layer contamination detection.
# If an L1 entity references these terms in its content fields, that's a signal
# it may actually be an L2 entity incorrectly submitted as L1.
L2_KNOWN_FACTION_NAMES = {
    "galactic union", "velar imperium", "outer colonies confederation",
    "zyphari compact", "elari ascendancy", "vorran clans",
    "kaelar monastic orders", "tharaxian nomads", "prime construct polity",
    "ai-warlord collective", "separatist confederation", "pmc syndicate",
    "crimson pact",
}

# L2 system ID prefixes that shouldn't appear in L1 entity content
L2_SYSTEM_ID_PATTERNS = re.compile(
    r'\b(?:GU-CORE|GU-FRONT|VEL-PRI|VEL-BORDER|VEL-EDGE|ZY-TRADE|ZYP-TRADE|'
    r'AI-CORE|AI-FRINGE|SEP-|OUTER-|PMC-|CP-|ANOM-|ROUTE-|PREC-|SHIP-GU)-\d+\b',
    re.IGNORECASE
)

# L2 simulation-origin patterns in file references
L2_SIMULATION_ORIGIN_PATTERNS = re.compile(
    r'(?:gumas|simulation|sim_run|scenario_run|l2_export)',
    re.IGNORECASE
)

# v1.1: Valid L2 domain subtypes (includes precursor support)
VALID_L2_DOMAIN_SUBTYPES = {
    "precursor_site", "anomalous_region", "contested_zone",
    "trade_corridor", "unknown"
}

# Required fields per layer+type
REQUIRED_FIELDS = {
    "L1": {
        "character": [
            "name", "rank_position", "division", "clearance_level",
            "responsibilities", "background_summary", "links", "origin_file"
        ],
        "vessel": [
            "designation", "type", "status", "crew_capacity", "current_location"
        ],
        "system": ["name", "type", "status", "responsible_personnel"],
        "department": ["name", "type", "status", "responsible_personnel"],
        "timeline_event": [
            "event_id", "timestamp", "description", "participants", "outcome"
        ],
    },
    "L2": {
        "_base": [
            "canonical_id", "canonical_name", "aliases",
            "entity_kind", "certainty", "doc_sources", "notes"
        ],
        "location": ["subtype"],
        "polity": ["subtype", "government_type"],
        "species": ["subtype"],
        "character": ["role", "faction", "sources"],
        "ship": ["type"],
        "mechanic": ["mechanic_id", "category", "description"],
        "anomaly": ["subtype"],
        "facility": [],
        "domain": ["subtype"],  # v1.1: domain now requires subtype (precursor_site, etc.)
        "fleet": [],
        "megafauna": [],
    },
    "L3": {
        "protocol_update": [
            "protocol_name", "version", "change_description",
            "affected_layers", "backward_compatible", "anchor_impact"
        ],
        "schema_definition": ["schema_name", "version", "fields"],
        "anchor_rule": ["anchor_id", "rule_description", "affected_layers"],
    }
}


# ---------------------------------------------------------------------------
# Context-aware canonical scan defaults
# ---------------------------------------------------------------------------

CONTEXT_MARKER_FILE = "SYSTEM_MAP.md"
CONTEXT_PREFERRED_SUBDIRS = (
    "PROJECT_KNOWLEDGE",
    "SIM_ENGINE_OUTPUTS",
    "FORGE__GUMAS_v3.0__2026-02-19",
    "AGENT_CAPSULE_PROTO__v0.1.0__2026-02-16__STRUCTURED 2",
    "DuelSim",
    "CanonRec",
)
CONTEXT_EXCLUDED_SUBPATHS = (
    "__pycache__",
    "CanonRec/canonrec_test/out",
    "CanonRec/canonrec_test/input",
)
CONTEXT_SCAN_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".html", ".jsonl"}
CONTEXT_EXCLUDED_SUFFIXES = {
    ".zip", ".pyc", ".pdf", ".docx", ".png", ".jpg", ".jpeg", ".bin", ".skill",
}
CONTEXT_WARN_THRESHOLD = 20
CONTEXT_MAX_IDENTITY_TERMS = 3
CONTEXT_MAX_FILES_SCANNED = 5000


def discover_context_root(start: Optional[Path]) -> Optional[Path]:
    """Find the nearest parent containing SYSTEM_MAP.md."""
    cursor = (start or Path.cwd()).resolve()
    if cursor.is_file():
        cursor = cursor.parent
    for candidate in (cursor, *cursor.parents):
        if (candidate / CONTEXT_MARKER_FILE).exists():
            return candidate
    return None


def resolve_context_search_roots(context_root: Path) -> list[Path]:
    """Resolve preferred canonical roots under the discovered context root."""
    roots: list[Path] = []
    for rel in CONTEXT_PREFERRED_SUBDIRS:
        p = (context_root / rel).resolve()
        if p.exists() and p.is_dir():
            roots.append(p)
    if not roots:
        roots.append(context_root)
    return roots


def _subpath_is_excluded(path: Path, context_root: Path, excluded_subpaths: tuple[str, ...]) -> bool:
    try:
        rel = path.resolve().relative_to(context_root).as_posix()
    except ValueError:
        return False
    for excluded in excluded_subpaths:
        if rel == excluded or rel.startswith(f"{excluded}/"):
            return True
    return False


def _compile_identity_pattern(term: str) -> re.Pattern:
    if re.fullmatch(r"[A-Za-z0-9_-]+", term):
        return re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(term)}(?![A-Za-z0-9_-])")
    return re.compile(re.escape(term))


def _extract_identity_terms(data: dict, max_terms: int) -> list[tuple[str, str]]:
    """Pick high-signal identity fields for context collision scan."""
    priority_fields = (
        "protocol_name",
        "anchor_id",
        "schema_name",
        "canonical_id",
        "canonical_name",
        "name",
        "designation",
    )
    terms: list[tuple[str, str]] = []
    seen: set[str] = set()
    for field in priority_fields:
        value = data.get(field)
        if not isinstance(value, str):
            continue
        term = value.strip()
        if not term or term.lower() in {"unknown", "tbd", "none", "<unnamed>"}:
            continue
        dedupe_key = term.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        terms.append((field, term))
        if len(terms) >= max_terms:
            break
    return terms


def _count_term_matches(term: str, context: dict[str, Any]) -> dict[str, int]:
    """Count term matches across preferred canonical roots with exclusions."""
    cache = context.setdefault("term_cache", {})
    if term in cache:
        return cache[term]

    context_root: Path = context["context_root"]
    source_file: Optional[Path] = context.get("source_file")
    excluded_subpaths = tuple(context["excluded_subpaths"])
    scan_suffixes = set(context["scan_suffixes"])
    excluded_suffixes = set(context["excluded_suffixes"])
    max_files = int(context["max_files_scanned"])
    pattern = _compile_identity_pattern(term)

    files_scanned = 0
    files_with_matches = 0
    matches = 0
    stop_scan = False

    for root in context["search_roots"]:
        if stop_scan:
            break
        for dirpath, dirnames, filenames in os.walk(root):
            current_dir = Path(dirpath).resolve()
            dirnames[:] = [
                d
                for d in dirnames
                if not _subpath_is_excluded(current_dir / d, context_root, excluded_subpaths)
            ]
            if _subpath_is_excluded(current_dir, context_root, excluded_subpaths):
                continue

            for filename in filenames:
                file_path = (current_dir / filename).resolve()
                suffix = file_path.suffix.lower()
                if suffix in excluded_suffixes or suffix not in scan_suffixes:
                    continue
                if source_file and file_path == source_file:
                    continue
                if _subpath_is_excluded(file_path, context_root, excluded_subpaths):
                    continue

                files_scanned += 1
                if files_scanned > max_files:
                    stop_scan = True
                    break

                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                file_matches = len(pattern.findall(text))
                if file_matches > 0:
                    files_with_matches += 1
                    matches += file_matches

            if stop_scan:
                break

    result = {
        "matches": matches,
        "files_with_matches": files_with_matches,
        "files_scanned": min(files_scanned, max_files),
    }
    cache[term] = result
    return result


def build_validation_context(args: argparse.Namespace) -> dict[str, Any]:
    """Build optional context scan configuration from workspace conventions."""
    if args.no_context_scan:
        return {"enabled": False, "reason": "disabled-by-flag"}

    if args.context_root:
        root = Path(args.context_root).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            print(
                f"Warning: --context-root '{root}' is invalid; context scan disabled.",
                file=sys.stderr,
            )
            return {"enabled": False, "reason": "invalid-context-root"}
        context_root = root
    else:
        if args.input_file:
            start = Path(args.input_file).expanduser().resolve().parent
        else:
            start = Path.cwd().resolve()
        context_root = discover_context_root(start)
        if context_root is None:
            return {"enabled": False, "reason": "no-system-map-found"}

    search_roots = resolve_context_search_roots(context_root)
    source_file = Path(args.input_file).expanduser().resolve() if args.input_file else None
    return {
        "enabled": True,
        "context_root": context_root,
        "context_label": context_root.name,
        "search_roots": search_roots,
        "source_file": source_file,
        "excluded_subpaths": CONTEXT_EXCLUDED_SUBPATHS,
        "scan_suffixes": CONTEXT_SCAN_SUFFIXES,
        "excluded_suffixes": CONTEXT_EXCLUDED_SUFFIXES,
        "warn_threshold": int(args.context_warn_threshold),
        "max_identity_terms": CONTEXT_MAX_IDENTITY_TERMS,
        "max_files_scanned": CONTEXT_MAX_FILES_SCANNED,
        "term_cache": {},
    }


def apply_context_identity_scan(data: dict, report: "ValidationReport", context: dict[str, Any]):
    """Add collision/reference findings using workspace-aware canonical scan."""
    if not context.get("enabled"):
        return

    terms = _extract_identity_terms(data, int(context["max_identity_terms"]))
    if not terms:
        return

    report.add(
        "INFO",
        "CONTEXT_SCAN_APPLIED",
        (
            f"Context scan enabled for '{context['context_label']}' "
            f"across {len(context['search_roots'])} preferred canonical roots."
        ),
    )

    for field, term in terms:
        stats = _count_term_matches(term, context)
        matches = stats["matches"]
        files_with_matches = stats["files_with_matches"]
        if matches >= int(context["warn_threshold"]):
            report.add(
                "WARN",
                "IDENTITY_COLLISION_PRESSURE",
                (
                    f"Identity '{term}' appears {matches} time(s) across "
                    f"{files_with_matches} file(s) in preferred canon roots. "
                    "Review merge/update strategy before promotion."
                ),
                field,
            )
        elif matches > 0:
            report.add(
                "INFO",
                "CANON_REFERENCE_MATCHES",
                (
                    f"Identity '{term}' appears {matches} time(s) across "
                    f"{files_with_matches} file(s) in preferred canon roots."
                ),
                field,
            )


# ---------------------------------------------------------------------------
# Validation engine
# ---------------------------------------------------------------------------

class ValidationReport:
    """Collects validation findings at BLOCK/WARN/INFO severity."""

    def __init__(self, entity_name: str, layer: str, entity_type: str):
        self.entity_name = entity_name
        self.layer = layer
        self.entity_type = entity_type
        self.findings: list[dict] = []
        self.required_fields_total: int | None = None
        self.required_fields: list[str] | None = None
        # Timestamp discipline: default is wall-clock UTC unless overridden upstream.
        self.timestamp_source = "WALL_CLOCK_UTC"
        self.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

    def add(self, severity: str, code: str, message: str, field: str = None):
        finding = {
            "severity": severity,
            "code": code,
            "message": message,
        }
        if field:
            finding["field"] = field
        self.findings.append(finding)

    @property
    def blocks(self):
        return [f for f in self.findings if f["severity"] == "BLOCK"]

    @property
    def warnings(self):
        return [f for f in self.findings if f["severity"] == "WARN"]

    @property
    def infos(self):
        return [f for f in self.findings if f["severity"] == "INFO"]

    @property
    def passed(self):
        return len(self.blocks) == 0

    def to_dict(self):
        return {
            "entity_name": self.entity_name,
            "layer": self.layer,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp,
            "timestamp_source": getattr(self, 'timestamp_source', None),
            "required_fields_total": self.required_fields_total,
            "required_fields": self.required_fields,
            "passed": self.passed,
            "summary": {
                "blocks": len(self.blocks),
                "warnings": len(self.warnings),
                "infos": len(self.infos),
            },
            "findings": self.findings,
        }

    def to_markdown(self) -> str:
        status = "PASS" if self.passed else "BLOCKED"
        lines = [
            f"### {self.entity_name} — {status}",
            f"**Layer:** {self.layer} | **Type:** {self.entity_type}",
            f"**Blocks:** {len(self.blocks)} | **Warnings:** {len(self.warnings)} | **Info:** {len(self.infos)}",
            "",
        ]
        for f in self.findings:
            icon = {"BLOCK": "🛑", "WARN": "⚠️", "INFO": "ℹ️"}.get(f["severity"], "?")
            field_str = f" (`{f['field']}`)" if f.get("field") else ""
            lines.append(f"- {icon} **{f['severity']}** [{f['code']}]{field_str}: {f['message']}")
        return "\n".join(lines)


def validate_entity(
    data: dict,
    layer: str,
    entity_type: str,
    context: Optional[dict[str, Any]] = None,
) -> ValidationReport:
    """Run all validation checks on a single entity."""

    name = (
        data.get("name")
        or data.get("canonical_name")
        or data.get("designation")
        or data.get("protocol_name")
        or data.get("anchor_id")
        or data.get("schema_name")
        or "<unnamed>"
    )
    report = ValidationReport(name, layer, entity_type)

    # --- Required field checks ---
    required = list(REQUIRED_FIELDS.get(layer, {}).get(entity_type, []))
    if layer == "L2":
        required = REQUIRED_FIELDS["L2"]["_base"] + required

    report.required_fields_total = len(required)
    report.required_fields = required

    # Fields where empty values are valid (empty string or empty list is OK)
    ALLOW_EMPTY = {"notes", "aliases"}

    for field in required:
        val = data.get(field)
        if val is None:
            report.add("BLOCK", "MISSING_REQUIRED", f"Required field '{field}' is missing.", field)
        elif field not in ALLOW_EMPTY and isinstance(val, str) and val.strip() == "":
            report.add("BLOCK", "MISSING_REQUIRED", f"Required field '{field}' is empty.", field)
        elif isinstance(val, list) and entity_type != "character":
            pass  # Empty lists are valid for aliases, doc_sources etc.

    # --- EG-lite provenance pointer check ---
    # Warn (not block) if no clear provenance pointer exists. Promotion policy may escalate.
    if not data.get("doc_sources") and not data.get("origin_file"):
        report.add(
            "WARN",
            "MISSING_PROVENANCE_POINTER",
            "No provenance pointer found (expected 'doc_sources' or 'origin_file').",
        )

    # --- Certainty tag validation ---
    certainty = data.get("certainty")
    if certainty is not None:
        if certainty not in VALID_CERTAINTY_TAGS:
            report.add("BLOCK", "INVALID_CERTAINTY",
                        f"Certainty tag '{certainty}' is not in the approved set: {sorted(VALID_CERTAINTY_TAGS)}",
                        "certainty")
        if certainty == "CANON":
            report.add("WARN", "CANON_TAG_ON_DRAFT",
                        "Certainty 'CANON' should only exist on Git-committed content. "
                        "Use 'CANON_PROMOTE' if this is ready for commit.", "certainty")

    # --- Entity kind validation (L2) ---
    if layer == "L2":
        ek = data.get("entity_kind")
        if ek and ek not in VALID_ENTITY_KINDS:
            report.add("BLOCK", "INVALID_ENTITY_KIND",
                        f"entity_kind '{ek}' is not valid. Must be one of: {sorted(VALID_ENTITY_KINDS)}",
                        "entity_kind")

        # Subtype validation for locations
        if entity_type == "location":
            st = data.get("subtype")
            if st and st not in VALID_L2_LOCATION_SUBTYPES:
                report.add("WARN", "INVALID_LOCATION_SUBTYPE",
                            f"Location subtype '{st}' is not standard. Expected: {sorted(VALID_L2_LOCATION_SUBTYPES)}",
                            "subtype")

        # Subtype validation for polities
        if entity_type == "polity":
            st = data.get("subtype")
            if st and st not in VALID_L2_POLITY_SUBTYPES:
                report.add("WARN", "INVALID_POLITY_SUBTYPE",
                            f"Polity subtype '{st}' is not standard. Expected: {sorted(VALID_L2_POLITY_SUBTYPES)}",
                            "subtype")

        # Moving entity coordinate check
        if ek in MOVING_ENTITY_KINDS:
            if data.get("coordinates") is not None:
                report.add("BLOCK", "MOVING_ENTITY_FIXED_COORDS",
                            f"Entity kind '{ek}' is a moving entity and must NOT have fixed coordinates. "
                            "Use 'placement_rule' for movement patterns instead.",
                            "coordinates")
            if not data.get("placement_rule"):
                report.add("WARN", "MOVING_ENTITY_NO_RULE",
                            f"Moving entity '{ek}' should have a 'placement_rule' describing movement patterns.",
                            "placement_rule")

        # Canonical ID format check
        cid = data.get("canonical_id")
        if cid and cid != "TBD":
            # Check for known Zyphari prefix inconsistency
            if cid.startswith("ZYP-") or cid.startswith("ZY-"):
                report.add("WARN", "ZYPHARI_ID_PREFIX",
                            f"Zyphari ID '{cid}' detected. There is a known normalization issue "
                            "(ZY- vs ZYP-). Confirm which prefix is canonical.", "canonical_id")

    # --- L1-specific checks ---
    if layer == "L1":
        if entity_type == "character":
            cid = data.get("character_id")
            if cid:
                valid_prefix = any(cid.startswith(p) for p in L1_CHARACTER_ID_PREFIXES)
                if not valid_prefix:
                    report.add("WARN", "NONSTANDARD_CHARACTER_ID",
                                f"Character ID '{cid}' doesn't use a standard prefix. "
                                f"Expected one of: {sorted(L1_CHARACTER_ID_PREFIXES)}",
                                "character_id")

        if entity_type == "vessel":
            status = data.get("status")
            if status and status not in VALID_L1_VESSEL_STATUSES:
                report.add("WARN", "INVALID_VESSEL_STATUS",
                            f"Vessel status '{status}' is not standard. Expected: {sorted(VALID_L1_VESSEL_STATUSES)}",
                            "status")

    # --- Cross-reference orphan hints ---
    # (These are heuristic — the full cross-reference happens in the reconciliation step,
    # but we can flag obvious issues here.)
    if layer == "L1" and entity_type == "character":
        links = data.get("links", [])
        if isinstance(links, list) and len(links) == 0:
            report.add("WARN", "NO_SYSTEM_LINKS",
                        "Character has no links to missions, ships, or systems. "
                        "Canon Protocol §4.2 requires at least one.", "links")

    # --- Schema drift checks ---
    # Check for deprecated field names
    deprecated_fields = {
        "type": "subtype" if layer == "L2" and entity_type == "location" else None,
    }
    for old_field, new_field in deprecated_fields.items():
        if new_field and old_field in data and new_field not in data:
            report.add("WARN", "DEPRECATED_FIELD",
                        f"Field '{old_field}' appears to be the deprecated name for '{new_field}'. "
                        f"Consider renaming.", old_field)

    # ===================================================================
    # v1.1 IMPROVEMENTS
    # ===================================================================

    # --- Improvement 1: Cross-layer contamination heuristic ---
    # Scan L1 entities for L2-specific content that suggests the entity
    # actually belongs in L2. This catches cases like an L2 character
    # (e.g., Torr-Kai) submitted in L1 crew manifest format.
    if layer == "L1":
        l2_signals = []

        # Collect all string values from the entity for scanning
        text_fields_to_scan = {
            "responsibilities": data.get("responsibilities", []),
            "background_summary": [data.get("background_summary", "")],
            "links": data.get("links", []),
            "origin_file": [data.get("origin_file", "")],
            "rank_position": [data.get("rank_position", "")],
            "division": [data.get("division", "")],
            "name": [data.get("name", "")],
        }

        all_text = ""
        for field_name, values in text_fields_to_scan.items():
            if isinstance(values, str):
                values = [values]
            if isinstance(values, list):
                for v in values:
                    if isinstance(v, str):
                        all_text += " " + v

        all_text_lower = all_text.lower()

        # Check for known L2 faction names in content
        for faction in L2_KNOWN_FACTION_NAMES:
            if faction in all_text_lower:
                l2_signals.append(f"References L2 faction '{faction}'")

        # Check for L2 system ID patterns in links and text
        l2_id_matches = L2_SYSTEM_ID_PATTERNS.findall(all_text)
        for match in l2_id_matches:
            l2_signals.append(f"References L2 system ID '{match}'")

        # Check for simulation-origin patterns in origin_file
        origin = data.get("origin_file", "")
        if isinstance(origin, str) and L2_SIMULATION_ORIGIN_PATTERNS.search(origin):
            l2_signals.append(f"Origin file '{origin}' appears to be a simulation/GUMAS export")

        # Report findings
        if len(l2_signals) >= 2:
            # Multiple L2 signals — high confidence this is a cross-layer issue
            report.add("WARN", "CROSS_LAYER_CONTAMINATION",
                        f"This L1 entity shows multiple L2/GUMAS signals, suggesting it may "
                        f"actually be an L2 entity incorrectly submitted as L1. "
                        f"Signals: {'; '.join(l2_signals)}. "
                        f"Verify layer assignment. If cross-layer bridge is intentional, "
                        f"document it explicitly.")
        elif len(l2_signals) == 1:
            # Single signal — worth noting but not conclusive
            report.add("INFO", "POSSIBLE_L2_REFERENCE",
                        f"This L1 entity contains a possible L2 reference: {l2_signals[0]}. "
                        f"This may be intentional (e.g., cross-system documentation) or may "
                        f"indicate a layer assignment error.")

    # --- Improvement 4: Clearance level validation (L1 characters) ---
    if layer == "L1" and entity_type == "character":
        clearance = data.get("clearance_level")
        if clearance and clearance not in VALID_L1_CLEARANCE_LEVELS:
            report.add("WARN", "UNKNOWN_CLEARANCE_LEVEL",
                        f"Clearance level '{clearance}' is not in the known set: "
                        f"{sorted(VALID_L1_CLEARANCE_LEVELS)}. If this is a new clearance "
                        f"tier, add it to the schema. Otherwise, correct to a known level.",
                        "clearance_level")

    # --- Improvement 3: Domain subtype validation (L2 domains) ---
    if layer == "L2" and entity_type == "domain":
        st = data.get("subtype")
        if st and st not in VALID_L2_DOMAIN_SUBTYPES:
            report.add("WARN", "INVALID_DOMAIN_SUBTYPE",
                        f"Domain subtype '{st}' is not standard. Expected: "
                        f"{sorted(VALID_L2_DOMAIN_SUBTYPES)}",
                        "subtype")

    # ===================================================================
    # END v1.1 IMPROVEMENTS
    # ===================================================================

    # Context-aware canonical identity scan (non-blocking).
    if context:
        apply_context_identity_scan(data, report, context)

    # --- Info-level observations ---
    if not report.blocks and not report.warnings:
        report.add("INFO", "CLEAN_ENTITY", "Entity passes all validation checks.")

    return report


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def extract_json_blocks(text: str) -> list[dict]:
    """Extract JSON objects and arrays from markdown text."""
    results = []
    # Match ```json ... ``` blocks
    json_blocks = re.findall(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
    for block in json_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, list):
                results.extend(parsed)
            elif isinstance(parsed, dict):
                results.append(parsed)
        except json.JSONDecodeError:
            pass
    return results


def extract_yaml_frontmatter(text: str) -> dict:
    """Extract YAML-style frontmatter from markdown (basic key: value parsing)."""
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}
    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            frontmatter[key] = value
    return frontmatter


def detect_layer_and_type(data: dict) -> tuple[str, str]:
    """Heuristic detection of layer and entity type from field signatures."""
    # L2 signatures
    if "canonical_id" in data or "entity_kind" in data:
        ek = data.get("entity_kind", "")
        if ek in ("polity",):
            return "L2", "polity"
        if ek in ("species",):
            return "L2", "species"
        if ek in ("ship",):
            return "L2", "ship"
        if ek in ("location",):
            return "L2", "location"
        if ek in ("facility",):
            return "L2", "facility"
        if ek in ("domain",):
            return "L2", "domain"
        if ek in ("anomaly",):
            return "L2", "anomaly"
        if ek == "character" or "faction" in data:
            return "L2", "character"
        if "mechanic_id" in data:
            return "L2", "mechanic"
        return "L2", "location"  # default L2

    # L1 signatures
    if "rank_position" in data or "clearance_level" in data:
        return "L1", "character"
    if "designation" in data and "crew_capacity" in data:
        return "L1", "vessel"
    if "event_id" in data and "participants" in data:
        return "L1", "timeline_event"
    if "responsible_personnel" in data:
        return "L1", "system"

    # L3 signatures
    if "protocol_name" in data:
        return "L3", "protocol_update"
    if "anchor_id" in data:
        return "L3", "anchor_rule"
    if "schema_name" in data and "fields" in data:
        return "L3", "schema_definition"

    return "UNKNOWN", "UNKNOWN"


def load_input(args) -> list[tuple[dict, str, str]]:
    """Load entities from the specified input source. Returns [(data, layer, type), ...]"""
    entities = []

    if args.json_input:
        try:
            data = json.loads(args.json_input)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON input: {e}", file=sys.stderr)
            sys.exit(1)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if args.auto_detect:
                layer, etype = detect_layer_and_type(item)
            else:
                layer, etype = args.layer, args.type
            entities.append((item, layer, etype))
        return entities

    if args.input_file:
        path = Path(args.input_file)
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)

        text = path.read_text(encoding="utf-8")

        # Try JSON file
        if path.suffix == ".json":
            try:
                data = json.loads(text)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if args.auto_detect:
                        layer, etype = detect_layer_and_type(item)
                    else:
                        layer, etype = args.layer, args.type
                    entities.append((item, layer, etype))
                return entities
            except json.JSONDecodeError:
                pass

        # Try markdown with embedded JSON
        json_entities = extract_json_blocks(text)
        if json_entities:
            for item in json_entities:
                if args.auto_detect:
                    layer, etype = detect_layer_and_type(item)
                else:
                    layer, etype = args.layer, args.type
                entities.append((item, layer, etype))
            return entities

        # Try YAML frontmatter
        fm = extract_yaml_frontmatter(text)
        if fm:
            if args.auto_detect:
                layer, etype = detect_layer_and_type(fm)
            else:
                layer, etype = args.layer, args.type
            entities.append((fm, layer, etype))
            return entities

        print("Warning: Could not parse structured data from input file. "
              "The file may contain unstructured content that needs manual entity extraction.",
              file=sys.stderr)
        return []

    print("Error: No input specified. Use --input <file> or --json '<data>'", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------

def generate_fill_template(entity_type: str, layer: str, existing: dict) -> str:
    """Generate a template showing missing fields that need to be filled."""
    required = list(REQUIRED_FIELDS.get(layer, {}).get(entity_type, []))
    if layer == "L2":
        required = REQUIRED_FIELDS["L2"]["_base"] + required

    lines = [f"# Fill Template — {layer} {entity_type}", ""]
    lines.append("Fill in the missing fields marked with `# TODO`:\n")
    lines.append("```yaml")
    for field in required:
        val = existing.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            lines.append(f"{field}: # TODO — required")
        else:
            if isinstance(val, list):
                lines.append(f"{field}: {json.dumps(val)}")
            else:
                lines.append(f"{field}: {val}")
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# v1.1: Batch duplicate detection
# ---------------------------------------------------------------------------

def detect_batch_duplicates(entities: list[tuple[dict, str, str]]) -> list[dict]:
    """Detect name and ID collisions within a batch of entities.

    Returns a list of collision records, each containing:
      - type: 'name' or 'id'
      - field: which field collided
      - description: human-readable explanation
      - entities: list of entity names involved
    """
    collisions = []

    # Track names and IDs we've seen
    seen_names: dict[str, list[str]] = {}  # normalized_name -> [entity_display_names]
    seen_ids: dict[str, list[str]] = {}    # id_value -> [entity_display_names]

    for data, layer, etype in entities:
        # Get display name
        display_name = (
            data.get("name")
            or data.get("canonical_name")
            or data.get("designation")
            or data.get("protocol_name")
            or data.get("anchor_id")
            or data.get("schema_name")
            or "<unnamed>"
        )

        # Check canonical_name / name collisions
        for name_field in ("name", "canonical_name", "designation"):
            name_val = data.get(name_field)
            if name_val and isinstance(name_val, str):
                norm = name_val.strip().lower()
                if norm in seen_names:
                    seen_names[norm].append(display_name)
                else:
                    seen_names[norm] = [display_name]

        # Check aliases for cross-collisions with other entities' names
        aliases = data.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str):
                    norm = alias.strip().lower()
                    if norm in seen_names:
                        seen_names[norm].append(f"{display_name} (via alias '{alias}')")
                    else:
                        seen_names[norm] = [f"{display_name} (via alias '{alias}')"]

        # Check ID collisions
        for id_field in ("canonical_id", "character_id", "event_id", "mechanic_id"):
            id_val = data.get(id_field)
            if id_val and isinstance(id_val, str) and id_val != "TBD":
                if id_val in seen_ids:
                    seen_ids[id_val].append(display_name)
                else:
                    seen_ids[id_val] = [display_name]

    # Report collisions (only where 2+ entities share the same value)
    for norm_name, entity_list in seen_names.items():
        if len(entity_list) > 1:
            # Deduplicate (same entity might appear via name + alias)
            unique = list(dict.fromkeys(entity_list))
            if len(unique) > 1:
                collisions.append({
                    "type": "name",
                    "field": "name/canonical_name",
                    "description": f"Multiple entities share name '{norm_name}': {', '.join(unique)}",
                    "entities": unique,
                })

    for id_val, entity_list in seen_ids.items():
        if len(entity_list) > 1:
            collisions.append({
                "type": "id",
                "field": "canonical_id/character_id",
                "description": f"Multiple entities share ID '{id_val}': {', '.join(entity_list)}",
                "entities": entity_list,
            })

    return collisions


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Run receipt hashing (proto-receipt)
# ---------------------------------------------------------------------------

def _severity_rank(severity: str) -> int:
    """Stable ordering for findings (lower = more severe)."""
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    return order.get(severity, 99)


def _canonicalize_report_dict(report_dict: dict) -> dict:
    """Return a canonicalized copy of a report dict for stable hashing.

    Notes:
      - This does NOT mutate the original report dict.
      - Canonicalization is used for hashing only; presentation order may differ.
    """
    d = dict(report_dict)

    # Canonicalize required fields (order-insensitive).
    rf = d.get("required_fields")
    if isinstance(rf, list):
        d["required_fields"] = sorted(str(x) for x in rf)

    # Canonicalize findings ordering for stable hashing.
    findings = d.get("findings")
    if isinstance(findings, list):
        def key(f: dict):
            return (
                _severity_rank(str(f.get("severity", ""))),
                str(f.get("code", "")),
                str(f.get("field", "")),
                str(f.get("message", "")),
            )
        d["findings"] = sorted((dict(f) for f in findings), key=key)

    return d


def compute_validation_run_output_hash(reports: list["ValidationReport"]) -> str:
    """Compute a SHA-256 hash over canonically ordered per-entity report dicts.

    This produces a run-level proto-receipt suitable for later referencing in
    canon promotion receipts and audit logs.

    Canonicalization rules:
      - Reports sorted by (layer, entity_type, entity_name).
      - Dict keys are JSON-serialized with sort_keys=True and stable separators.
      - Findings and required_fields are treated as order-insensitive for hashing.
    """
    canonical_reports = [_canonicalize_report_dict(r.to_dict()) for r in reports]
    canonical_reports.sort(key=lambda d: (
        str(d.get("layer", "")),
        str(d.get("entity_type", "")),
        str(d.get("entity_name", "")),
    ))

    payload = json.dumps(
        canonical_reports,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


# Hash canonicalization contract metadata (versioned semantics for hash meaning).
HASH_CANON_VERSION = "CANONREC_HASH_CANON_V1"
HASH_CANON_RULES_REF = "validate_entity.py::_canonicalize_for_hash"

# Fields that should be excluded for semantic replay-equivalence signatures.
# Keep this list explicit and versioned; add to it only with a scope change.
_CONTENT_HASH_EXCLUDED_FIELDS = ("timestamp", "timestamp_source")


def _strip_nonsemantic_fields(report_dict: dict, excluded_fields: tuple[str, ...]) -> dict:
    """Return a shallow copy of report_dict excluding non-semantic fields.

    Notes:
      - This is intentionally shallow: current report dicts are flat aside from
        'summary' and 'findings' which are retained for semantic hashing.
      - If nested non-semantic fields are introduced later, update this helper
        (and bump content_hash_scope accordingly).
    """
    d = dict(report_dict)
    for k in excluded_fields:
        d.pop(k, None)
    return d


def compute_validation_run_content_hash(reports: list["ValidationReport"]) -> str:
    """Compute a SHA-256 semantic hash over per-entity report dicts.

    This signature is intended for replay comparison: it excludes run-unique
    timestamp fields so that semantically identical validation results can be
    detected across replays.

    Canonicalization rules:
      - Same as output_hash (ordering, stable JSON serialization, and
        order-insensitive normalization for findings/required_fields).
      - Excludes non-semantic fields: {excluded}.
    """.format(excluded=",".join(_CONTENT_HASH_EXCLUDED_FIELDS))
    canonical_reports = [
        _canonicalize_report_dict(
            _strip_nonsemantic_fields(r.to_dict(), _CONTENT_HASH_EXCLUDED_FIELDS)
        )
        for r in reports
    ]
    canonical_reports.sort(key=lambda d: (
        str(d.get("layer", "")),
        str(d.get("entity_type", "")),
        str(d.get("entity_name", "")),
    ))

    payload = json.dumps(
        canonical_reports,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Validate Aurora OS entities against canonical schemas."
    )
    parser.add_argument("--input", dest="input_file", help="Path to draft file (JSON or Markdown)")
    parser.add_argument("--json", dest="json_input", help="Inline JSON entity data")
    parser.add_argument("--layer", choices=["L1", "L2", "L3"], help="Entity layer")
    parser.add_argument("--type", dest="type", help="Entity type (character, vessel, location, etc.)")
    parser.add_argument("--auto-detect", action="store_true", help="Auto-detect layer and type from data")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both",
                        help="Output format (default: both)")
    parser.add_argument("--fill-template", action="store_true",
                        help="Generate fill templates for entities with missing fields")
    parser.add_argument(
        "--no-context-scan",
        action="store_true",
        help="Disable automatic context-aware canonical identity scan.",
    )
    parser.add_argument(
        "--context-root",
        help="Optional path override for context root discovery (defaults to nearest SYSTEM_MAP.md).",
    )
    parser.add_argument(
        "--context-warn-threshold",
        type=int,
        default=CONTEXT_WARN_THRESHOLD,
        help=f"Warn when identity matches reach this count (default: {CONTEXT_WARN_THRESHOLD}).",
    )

    args = parser.parse_args()

    if not args.input_file and not args.json_input:
        parser.print_help()
        sys.exit(1)

    if not args.auto_detect and (not args.layer or not args.type):
        print("Error: Specify --layer and --type, or use --auto-detect", file=sys.stderr)
        sys.exit(1)

    context = build_validation_context(args)

    entities = load_input(args)

    if not entities:
        print("No entities found in input.", file=sys.stderr)
        sys.exit(1)

    all_reports = []
    for data, layer, etype in entities:
        report = validate_entity(data, layer, etype, context=context)
        all_reports.append(report)

        if args.fill_template and not report.passed:
            template = generate_fill_template(etype, layer, data)
            print(template, file=sys.stderr)

    # --- v1.1 Improvement 2: Batch duplicate detection ---
    # When multiple entities are processed in one run, check for intra-batch
    # name and ID collisions. This catches cases where a simulation export
    # produces two entities with the same name or where copy-paste errors
    # create duplicate IDs.
    if len(entities) > 1:
        batch_duplicates = detect_batch_duplicates(entities)
        for dup in batch_duplicates:
            # Find the reports for the affected entities and add warnings
            for report in all_reports:
                if report.entity_name in dup["entities"]:
                    report.add("WARN", "BATCH_DUPLICATE",
                               f"Intra-batch {dup['type']} collision: {dup['description']}",
                               dup.get("field"))

    output_hash = compute_validation_run_output_hash(all_reports)
    content_hash = compute_validation_run_content_hash(all_reports)


    # Output
    if args.format in ("json", "both"):
        output = {
            "validation_run": {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
                "timestamp_source": "WALL_CLOCK_UTC",
                "hash_canon_version": HASH_CANON_VERSION,
                "hash_canon_rules_ref": HASH_CANON_RULES_REF,
                "output_hash_alg": "SHA256",
                "output_hash_scope": "RUN_ARTIFACT_INCLUDING_TIMESTAMPS",
                "output_hash": output_hash,
                "content_hash_alg": "SHA256",
                "content_hash_scope": "SEMANTIC_OUTPUT_EXCLUDING_TIMESTAMPS",
                "content_hash_excluded_fields": list(_CONTENT_HASH_EXCLUDED_FIELDS),
                "content_hash": content_hash,
                "receipt_id_policy": "receipt_id = content_hash",
                "receipt_id": content_hash,
                "entities_checked": len(all_reports),
                "passed": sum(1 for r in all_reports if r.passed),
                "blocked": sum(1 for r in all_reports if not r.passed),
            },
            "reports": [r.to_dict() for r in all_reports],
        }
        print(json.dumps(output, indent=2))

    if args.format in ("markdown", "both"):
        lines = [
            "# Entity Validation Report",
            f"**Timestamp:** {datetime.now(timezone.utc).isoformat().replace('+00:00','Z')}",
            f"**Timestamp source:** WALL_CLOCK_UTC",
            f"**Hash canon version:** {HASH_CANON_VERSION}",
            f"**Hash canon rules ref:** {HASH_CANON_RULES_REF}",
            f"**Output hash:** {output_hash}",
            f"**Output hash scope:** RUN_ARTIFACT_INCLUDING_TIMESTAMPS",
            f"**Content hash:** {content_hash}",
            f"**Content hash scope:** SEMANTIC_OUTPUT_EXCLUDING_TIMESTAMPS",
            f"**Content hash excluded fields:** {', '.join(_CONTENT_HASH_EXCLUDED_FIELDS)}",
            f"**Receipt id policy:** receipt_id = content_hash",
            f"**Receipt id:** {content_hash}",
            f"**Entities checked:** {len(all_reports)}",
            f"**Passed:** {sum(1 for r in all_reports if r.passed)} | "
            f"**Blocked:** {sum(1 for r in all_reports if not r.passed)}",
            "",
        ]
        for r in all_reports:
            lines.append(r.to_markdown())
            lines.append("")
        print("\n".join(lines), file=sys.stderr)

    # Exit code
    if any(not r.passed for r in all_reports):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
