# Entity Schemas Reference — Aurora Canon Reconciler

This document defines the required and optional fields for every entity type the reconciler
handles, organized by layer. Use this as the validation source when checking draft content.

---

## Certainty Tags (All Layers)

These are the only valid certainty values. Anything else is a validation error.

| Tag | Meaning | Can be assigned by skill? |
|-----|---------|--------------------------|
| `CANON` | Confirmed and locked. Committed to Git. | No — only Git commit creates this. |
| `CANON_PROMOTE` | Approved for promotion. Next commit locks it. | Only with explicit user approval. |
| `LOCKED_POSITION` | Placement frozen; attributes may evolve. L2 map entities. | Yes, for map-critical entities. |
| `PLACED` | In current L2 map layout, revisable. | Yes. |
| `STAGING` | Usable but revisable. Default for validated new content. | Yes. |
| `UNCONFIRMED` | Mentioned/implied but not validated. | Yes. |
| `LEGEND_CONTESTED` | In-universe rumor, myth, propaganda. | Yes. |
| `APPROX` | Approximate quantity/date/extent. | Yes. |

---

## L1 — Orion Station Entities

### L1 Character (Personnel)

Canon Protocol §4.2 defines the required fields. The v2.5 L1 Canon Edition format
(reference implementation: Tobias Qin profile) adds structured simulation attributes.

**Required fields:**

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Full name | `Tobias Qin` |
| `rank_position` | Rank and/or job title | `Code/Narrative Systems Engineer` |
| `division` | Division or assignment | `Simulation & Cognitive Systems` |
| `clearance_level` | Security clearance | `L3_RESEARCH` |
| `responsibilities` | Primary duties (list) | Language-model integration, ethical semantics |
| `background_summary` | Brief biography | 2-4 sentences of professional background |
| `links` | Connected missions, ships, or systems | `nl_integration.py`, `Lexicon Integrity Framework` |
| `origin_file` | File where character was first introduced | `simulation/TOBIAS_QIN_CHARACTER_PROFILE.md` |

**Optional fields (recommended for simulation-ready characters):**

| Field | Description | Example |
|-------|-------------|---------|
| `character_id` | Roster ID following prefix convention | `ENG_010` |
| `contact` | Communication channel | `Station Relay / NLI Console` |
| `symbolic_tag` | Associated symbolic identifier | `≋ LEXICAL_BRIDGE` |
| `base_speed` | Simulation stat: task execution rate | `0.75` |
| `specialization_multiplier` | Simulation stat: domain bonus | `1.4` |
| `collaboration_bonus` | Simulation stat: teamwork modifier | `0.15` |
| `focus_areas` | Keywords for task matching (list) | `code, narrative, semantics, ethics` |
| `primary_systems` | Repository files this character "owns" (list) | `tools/command_chain/nl_integration.py` |
| `key_collaborators` | Canonical working relationships (list) | `Varya Lin, Dr. Amira Sato` |
| `philosophy` | Core beliefs (list, 3-5 items) | See Tobias Qin profile |
| `working_style` | Personality and communication notes | `"quietly relentless"` |

**ID prefix conventions for L1 characters:**

| Division | Prefix | Example |
|----------|--------|---------|
| Command | `CMD_` | `CMD_001` |
| Engineering | `ENG_` | `ENG_010` |
| Science/Research | `SCI_` | `SCI_003` |
| Medical | `MED_` | `MED_001` |
| Operations | `OPS_` | `OPS_005` |
| Security | `SEC_` | `SEC_002` |
| AI Systems | `AI_` | `AI_001` |

### L1 Vessel

| Field | Required | Description |
|-------|----------|-------------|
| `designation` | Yes | e.g., `ORS-03 Archimedes` |
| `type` | Yes | Vessel class: shuttle, transport, research, etc. |
| `status` | Yes | ACTIVE, DOCKED, DEPLOYED, MAINTENANCE, DECOMMISSIONED |
| `crew_capacity` | Yes | Maximum crew |
| `assigned_crew` | No | Current crew count or names |
| `current_location` | Yes | Grid reference or docking bay |
| `hull_status` | No | Percentage or descriptive |
| `mission_assignment` | No | Current mission if any |
| `systems` | No | Key onboard systems |

### L1 System/Department

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | System or department name |
| `type` | Yes | `system` or `department` |
| `status` | Yes | NOMINAL, DEGRADED, OFFLINE, MAINTENANCE |
| `responsible_personnel` | Yes | Who owns/operates this |
| `dependencies` | No | Other systems this depends on |
| `location` | No | Physical location on station |

### L1 Timeline Event

| Field | Required | Description |
|-------|----------|-------------|
| `event_id` | Yes | Unique identifier |
| `timestamp` | Yes | When it occurred (station time) |
| `description` | Yes | What happened |
| `participants` | Yes | Personnel and systems involved |
| `outcome` | Yes | Result or current status |
| `canon_impact` | No | What this changes in the canonical state |

---

## L2 — GUMAS Entities

All L2 entities share a common base schema from the staging dossier, then add type-specific
fields.

### L2 Common Base (all entity types)

| Field | Required | Description |
|-------|----------|-------------|
| `canonical_id` | Yes | Stable unique key. Never changes once assigned. Format: `PREFIX-IDENTIFIER-##` |
| `canonical_name` | Yes | Primary display name. May change (unlike ID). |
| `aliases` | Yes | Array of alternate names. Can be empty `[]`. |
| `entity_kind` | Yes | One of: `location`, `ship`, `fleet`, `anomaly`, `megafauna`, `facility`, `domain`, `polity`, `species`, `character` |
| `certainty` | Yes | Must be from the approved tag set. |
| `doc_sources` | Yes | Array of filenames where this entity is referenced. |
| `notes` | Yes | Contradictions, gaps, open questions. Can be empty string. |

### L2 Location (extends base)

| Field | Required | Description |
|-------|----------|-------------|
| `subtype` | Yes | `system`, `planet`, `moon`, `region`, `route`, `facility`, `anomaly`, `station`, `unknown` |
| `coord_frame` | Conditional | Required when PLACED: `galactic_polar`, `sector_grid`, `local_system`, `none` |
| `coordinates` | Conditional | Object or null. Only when certainty allows placement. |
| `adjacency` | No | Array of `{to_id, relation, weight, notes}` |
| `placement_rule` | Conditional | Required for anomalies, domains, and moving entities. Constraints for positioning. |

**Moving entity rule:** Ships, nomad fleets, and megafauna must have `entity_kind` set
appropriately (ship/fleet/megafauna) and must NEVER have fixed coordinates. Use
`placement_rule` to describe movement patterns instead.

### L2 Polity

| Field | Required | Description |
|-------|----------|-------------|
| `subtype` | Yes | `nation_state`, `federation`, `compact`, `collective`, `pmc`, `pact`, `confederation` |
| `government_type` | Yes | Form of governance |
| `territory` | No | Array of `canonical_id` references to controlled locations |
| `leadership` | No | Array of `canonical_id` references to leader characters |
| `diplomatic_status` | No | Current stance toward other polities |
| `military_assets` | No | Array of ship/fleet references |

### L2 Species

| Field | Required | Description |
|-------|----------|-------------|
| `subtype` | Yes | `biological`, `synthetic`, `hybrid`, `energy`, `unknown` |
| `homeworld` | No | `canonical_id` of origin location |
| `affiliated_polities` | No | Array of polity `canonical_id` references |
| `biological_traits` | No | Key physical/cognitive characteristics |
| `cultural_notes` | No | Brief cultural summary |

### L2 Character

| Field | Required | Description |
|-------|----------|-------------|
| `role` | Yes | Title/position |
| `faction` | Yes | Polity or organization affiliation |
| `sources` | Yes | Where this character was first mentioned |

### L2 Ship

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Ship class description |
| `faction` | No | Controlling polity or faction |
| `registry_class` | No | Classification if part of a navy |
| `crew_notes` | No | Key crew or notable attributes |

### L2 Mechanic (Simulation Rule)

| Field | Required | Description |
|-------|----------|-------------|
| `mechanic_id` | Yes | Unique identifier |
| `category` | Yes | `diplomacy`, `economy`, `military`, `culture`, `science`, `governance` |
| `description` | Yes | What the mechanic does |
| `parameters` | No | Configurable values |
| `function_ref` | No | Reference to implementing function in codebase |

---

## L3 — Symbolic/Governance Entities

L3 entities are protocol-level definitions. They rarely come in as "drafts" but when they
do, they require the strictest validation.

### L3 Protocol Update

| Field | Required | Description |
|-------|----------|-------------|
| `protocol_name` | Yes | e.g., `Picard_Delta_3` |
| `version` | Yes | Semantic version |
| `change_description` | Yes | What's changing and why |
| `affected_layers` | Yes | Which layers this impacts |
| `backward_compatible` | Yes | Boolean |
| `anchor_impact` | Yes | Does this affect any anchors? |

---

## ID Prefix Conventions (L2)

| Entity Kind | Prefix Pattern | Example |
|-------------|---------------|---------|
| Union core systems | `GU-CORE-##` | `GU-CORE-01` |
| Velar systems | `VEL-###-##` | `VEL-PRI-03` |
| AI collective | `AI-###-##` | `AI-CORE-01` |
| Separatist | `SEP-###-##` | `SEP-CORE-01` |
| Zyphari | `ZY-###-##` or `ZYP-###-##` | `ZY-TRADE-01` |
| Outer colonies | `OUTER-##` | `OUTER-01` |
| PMC Syndicate | `PMC-###-##` | `PMC-HQ-01` |
| Crimson Pact | `CP-###-##` | `CP-CORE-01` |
| Anomalies | `ANOM-###` | `ANOM-001` |
| Trade routes | `ROUTE-###` | `ROUTE-001` |

**Note:** There is a known normalization issue with Zyphari IDs (`ZY-` vs `ZYP-`). The
reconciler should flag any Zyphari entity and confirm which prefix is canonical. Prefer
`ZY-` as the shorter form unless the user specifies otherwise.

---

## Validation Error Severity

| Severity | Meaning | Action |
|----------|---------|--------|
| **BLOCK** | Cannot proceed. Missing required field or invalid certainty tag. | Must fix before any output. |
| **WARN** | Non-critical issue. Deprecated field, approximate data, orphan reference. | Flag in report, proceed. |
| **INFO** | Notable but not problematic. New entity, first mention, batch dependency. | Note in report. |

---

## v1.1 Additions

### Known L1 Clearance Levels

The validator now checks clearance levels against a known set. Unknown levels produce a
WARN rather than a BLOCK, since new clearance tiers may be legitimately introduced.

| Level | Description |
|-------|-------------|
| `L1_GENERAL` | General station access |
| `L2_OPERATIONAL` | Operational systems access |
| `L3_TECHNICAL` | Technical/engineering systems (most specialists) |
| `L3_RESEARCH` | Research systems and data (science division) |
| `L4_COMMAND` | Command-level access (Thorne, Shepard) |
| `L5_EXECUTIVE` | Executive/override access |

### L2 Domain Subtypes

The `domain` entity type now requires a `subtype` field. Valid values:

| Subtype | Use For |
|---------|---------|
| `precursor_site` | Ancient/dormant infrastructure (Orak'Thuun, Vorthan, Sythrex, Shroudborn) |
| `anomalous_region` | Spatially anomalous areas (rifts, null zones) |
| `contested_zone` | Areas under multi-faction dispute without clear governance |
| `trade_corridor` | Economic zones not controlled by a single polity |
| `unknown` | Catch-all for unclassified domains |

### Cross-Layer Contamination Detection

The validator now scans L1 entities for L2-specific content. Detection uses three signal
types, and the severity escalates with signal count:

| Signal Count | Severity | Code | Meaning |
|-------------|----------|------|---------|
| 0 | — | — | Clean L1 entity |
| 1 | INFO | `POSSIBLE_L2_REFERENCE` | Possible but not conclusive L2 reference |
| 2+ | WARN | `CROSS_LAYER_CONTAMINATION` | High confidence cross-layer issue |

**Signals checked:**
- Known L2 faction/polity names in any text field
- L2 system ID patterns (e.g., `GU-CORE-01`, `VEL-BORDER-01`, `SEP-CORE-01`) in links or text
- Simulation/GUMAS-origin patterns in `origin_file` (e.g., filenames containing "gumas", "simulation", "sim_run")

### Batch Duplicate Detection

When multiple entities are validated in one run, the validator checks for:
- **Name collisions:** Two entities sharing the same `name`/`canonical_name` (case-insensitive)
- **Alias cross-collisions:** An entity's alias matching another entity's primary name
- **ID collisions:** Two entities sharing the same `canonical_id`/`character_id`/`event_id`

Duplicates produce `WARN` severity with code `BATCH_DUPLICATE` on both affected entities.
