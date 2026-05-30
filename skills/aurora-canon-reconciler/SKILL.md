---
name: aurora-canon-reconciler
description: Reconcile draft Aurora OS content against established canon and prepare it for Git commit. Use when draft characters, entities, locations, ships, systems, mechanics, simulation output, hour-block logs, or ChatGPT/Claude exports must be checked for contradictions, missing fields, drift artifacts, and promotion readiness. Trigger on requests like reconcile, canonize, promote to canon, check continuity, staging to canon, CANON_PROMOTE, merge this draft, or Canon Protocol references; also trigger when users paste Aurora worldbuilding and ask to clean it up or get it commit-ready. Not for pure code review, CI/CD work, or non-Aurora content.
author: Aurora ORIONCORE
---

# Aurora Canon Reconciler

A structured skill for reconciling draft Aurora OS content against canonical truth and producing
Git-commit-ready outputs with proper schemas, certainty tags, and drift documentation.

## Why This Exists

Aurora OS maintains a strict canon hierarchy (Primary → Secondary → Tertiary) governed by the
Canon Protocol. Content flows from simulations, brainstorming, ChatGPT/Claude sessions, and
hour-block logs into the repository — but only after reconciliation. Without a consistent
process, drift artifacts accumulate: duplicate names, conflicting roles, ghost entities, and
schema violations that compound over time.

This skill encodes the reconciliation workflow so it's applied consistently every time, across
both L1 (Orion Station) and L2 (GUMAS) entity types.

---

## Step 0: Identify What You're Working With

Before doing anything, classify the input along three dimensions:

### Layer
- **L1** — Orion Station: characters, personnel, systems, vessels, departments, station architecture, timeline events
- **L2** — GUMAS: polities, species, characters, ships, locations, anomalies, simulation mechanics
- **L3** — ThreadCore/symbolic: governance rules, schema definitions, protocol updates

**Critical rule:** L2 simulation entities must NEVER be mapped to L1 physical operations without
explicit user authorization. If the draft mixes layers, flag it immediately and ask the user to
confirm intent before proceeding.

### Entity Type
Determine which schema applies. Read `references/entity_schemas.md` for the complete field
requirements per entity type.

| Layer | Entity Types |
|-------|-------------|
| L1 | character, vessel, system, department, timeline_event, station_architecture |
| L2 | polity, species, character, ship, location, anomaly, mechanic, cultural_artifact |
| L3 | protocol_update, schema_definition, anchor_rule |

### Input Format
The input will typically be one of:
- **Structured markdown** with YAML frontmatter and/or JSON blocks → parse directly
- **Loose narrative** from a ChatGPT/Claude session or brainstorm → extract entities first
- **Simulation export** with structured data but possibly inconsistent schemas → normalize
- **Hour-block log** with inline entity mentions → extract and classify

For loose/unstructured input, extract all identifiable entities before proceeding to Step 1.

---

## Step 1: Validate Required Fields

Run the validation script against the extracted entities:

```bash
python /path/to/skill/scripts/validate_entity.py --input <draft_file> --layer <L1|L2> --type <entity_type>
```

This checks for:
- All required fields present for the entity type (per `references/entity_schemas.md`)
- Field format compliance (IDs, certainty tags, date formats)
- No orphan references (e.g., a character referencing a department that doesn't exist in canon)

The script outputs a validation report. If fields are missing, it generates a **fill template**
showing exactly what needs to be added, with inline comments explaining each field.

For L1 characters specifically, the Canon Protocol requires:
- Name, Rank/Position, Division/Assignment, Clearance Level
- Responsibilities, Background summary
- Links to missions/ships/systems
- Origin file (where introduced)

For L2 entities, the staging dossier schema requires:
- `canonical_id` (stable, never changes once assigned)
- `canonical_name`, `aliases`
- `entity_kind` + `subtype` (using the normalized vocabulary)
- `certainty` tag (from the approved set)
- `doc_sources` (provenance)
- `notes` (contradictions, gaps)

---

## Step 2: Cross-Reference Against Canon



### Step 2A (Optional): Emit an EG-lite Evidence Receipt

If you want downstream systems (Promotion Pipeline / `MutationRequest.gate_receipts`) to be able to
reference your validation results **without re-parsing**, generate an `evidence_receipt.json`
directly from the validation-run JSON output:

```bash
python /path/to/skill/scripts/emit_evidence_receipt.py \
  --validation-run out/validation_run.json \
  --out out/evidence_receipt.json \
  --canon-targets out/canon_targets.json
```

This script is intentionally non-interpretive: it emits a **provenance ledger** over the existing
validation output, with explicit claim statuses (`SUPPORTED | ASSUMPTION | UNKNOWN`) and a boring,
mechanical verdict rule set.

---
This is the core reconciliation step. Search the project knowledge and any available canon
files for conflicts.

### What to check:

**Identity collisions:**
- Does this entity name or any alias already exist in canon?
- If so, is this an update to an existing entity or a genuinely new one?
- For characters: does the rank/role/division conflict with existing roster entries?

**Structural contradictions:**
- Does a claimed relationship (e.g., "reports to Commander X") match what canon says?
- For locations: do adjacency claims conflict with the established map?
- For ships: does registry class/faction alignment hold?

**Timeline integrity:**
- Does the draft reference events that haven't happened yet in canonical timeline?
- Does it contradict committed history? (Committed history is never erased.)

**Schema drift:**
- Is the entity using deprecated field names? (e.g., `type` where `subtype` is now canonical)
- Are certainty tags from the approved set?
- Are IDs following the established prefix conventions?

### How to search:

Use the project knowledge search tool to find existing canon entries. Search for:
1. The entity name and all aliases
2. Related entity names (faction, department, assigned vessel)
3. The entity type + layer combination

Document every conflict found. For each conflict, record:
- What the draft says vs. what canon says
- Which canon source has primacy
- Proposed resolution (defer to canon / adapt draft / synthesize)

---

## Step 3: Assign Certainty Tags

Based on the reconciliation results, use the **ReconciliationAdvisor** (`scripts/reconciliation_advisor.py`)
to generate a scored recommendation with confidence and explanation. The advisor adapts HDE++
(Heuristic Decision Engine PlusPlus) patterns for canon decision-making:

```python
from reconciliation_advisor import recommend_from_validation

result = recommend_from_validation(
    data=entity_data,
    validation_findings=findings_from_step_1,
    layer="L1",
    entity_type="character",
    entity_name="Kai Okonkwo",
    has_conflicts=False,
    origin_is_simulation=False,
)
# result["recommended_tag"]  → "STAGING"
# result["confidence"]       → 0.78
# result["explanation"]      → "Recommending 'STAGING' for 'Kai Okonkwo' (score: 7.70)..."
# result["alternatives"]     → [{"tag": "CANON_PROMOTE", "score": 6.12}, ...]
# result["audit_entry"]      → full machine-readable audit trail
```

The advisor scores entities across six readiness dimensions — field_completeness, conflict_freedom,
provenance_strength, schema_compliance, layer_integrity, and review_status — then finds the
highest-bar certainty tag the entity qualifies for. It calculates a confidence score based on the
gap between the best tag and its closest alternative, and produces an explainable audit entry
documenting exactly why that tag was recommended.

The valid certainty tags are:

```
CANON             — Already committed and locked. Don't re-tag existing canon.
CANON_PROMOTE     — Reconciled, all fields valid, ready for commit. User must approve.
LOCKED_POSITION   — (L2 locations) Placement frozen, attributes may evolve.
PLACED            — (L2 locations) In current map, but revisable.
STAGING           — Usable but may be revised. Default for new content that passes validation.
UNCONFIRMED       — Mentioned/implied but not validated against a source-of-truth artifact.
LEGEND_CONTESTED  — In-universe rumor, myth, propaganda, or disputed account.
APPROX            — Approximate quantity/date/extent.
```

**Decision logic:**
- New entity, all required fields present, no conflicts found → propose `STAGING`
- Entity has been reviewed by user and approved for promotion → propose `CANON_PROMOTE`
- Entity has unresolved conflicts → hold at `STAGING` or `UNCONFIRMED`, document why
- Entity references unverified sources → `UNCONFIRMED`
- Never propose `CANON` — that happens only on Git commit per the Canon Protocol

---

## Step 4: Produce Outputs

Generate the following outputs based on reconciliation results:

### A. Reconciliation Report

A markdown document summarizing everything found. Structure:

```markdown
# Canon Reconciliation Report
**Date:** <timestamp>
**Input:** <source description>
**Layer:** L1 / L2 / L3
**Entities processed:** <count>

## Validation Summary
<table of entities with pass/fail status and missing fields>

## Conflicts Found
<for each conflict: what draft says, what canon says, resolution>

## Drift Artifacts
<any schema drift, deprecated fields, naming inconsistencies>

## Promotion Assessment
<for each entity: proposed certainty tag with reasoning>

## Action Items
<numbered list of what the user needs to decide or fix>
```

### B. Promotion-Ready Files

For each entity that passes validation and has no unresolved conflicts, generate a clean
markdown file with:
- Proper YAML frontmatter (entity_id, entity_type, layer, certainty, doc_sources)
- All required fields populated
- Proper formatting per the layer's conventions

For L1 characters, output should match the v2.5 L1 Canon Edition format (see Tobias Qin
profile as the reference implementation).

For L2 entities, output should be a JSON block compatible with the staging dossier schema.

### C. DRIFT_LOG Entry

If any contradictions were found, generate a markdown block formatted for append to
`DRIFT_LOG.md`:

```markdown
## Drift Entry — <date>
- **Source:** <input source description>
- **Type:** <duplicate name | conflicting role | ghost entity | schema drift | timeline conflict>
- **Entities affected:** <list>
- **Description:** <what happened>
- **Resolution:** <how it was resolved, or "PENDING — requires user decision">
```

### D. Claim Ledger Entry (L2 only)

For L2 entities going through the evidence → placement pipeline, generate a JSON claim:

```json
{
  "entity_id": "<canonical_id>",
  "claim_type": "<placement | attribute | relationship>",
  "value": "<the claimed fact>",
  "certainty": "<tag>",
  "doc_source": "<where this came from>",
  "conflicts_with": "<canon entry if any, or null>",
  "notes": "<resolution or open question>"
}
```

---

## Step 5: Present for Review

Always present the reconciliation report first, then the promotion-ready files. The user
must explicitly approve before anything reaches `CANON_PROMOTE` status.

If there are unresolved conflicts or missing information, present clear options:

- **Option A:** Defer to existing canon (adapt the draft)
- **Option B:** Update canon with draft content (justify why the draft supersedes)
- **Option C:** Synthesize both into a merged revision
- **Option D:** Hold in STAGING until more information is available

Never auto-promote. The human is the gatekeeper.

---

## Edge Cases

### Batch processing
If the user brings in content with multiple entities, process each independently but
present a unified report. Flag any inter-entity dependencies (e.g., "Character X references
Ship Y, which is also new in this batch").

### Cross-layer content
If draft content spans layers (e.g., an L2 character who has an L1 station assignment),
flag it prominently and ask the user to confirm the cross-layer bridge is intentional.
Document the bridge in both layers' outputs.

### Partial updates
If the draft is updating an existing canon entity (not creating new), diff against the
existing version. Show what's changing and confirm the update preserves all previously
required fields.

### Simulation → Canon pipeline
Simulation exports (Tertiary Canon) require extra scrutiny per Canon Protocol §5:
1. Alignment with existing canon
2. Role/rank consistency
3. Compatibility with station architecture
4. Absence of structural contradictions

Apply all four checks before proposing any certainty tag above `UNCONFIRMED`.

### Moving entities (L2)
Ships, nomad fleets, and megafauna must NEVER be stored as fixed coordinates. If the draft
assigns fixed coordinates to a moving entity, flag it and apply the moving entity policy.

---

## Quick Reference: Canon Hierarchy

| Level | Source | Authority | Mutability |
|-------|--------|-----------|------------|
| Primary Canon | Git-committed files | Binding | Only via new commit |
| Secondary Canon | Drafts, sessions, simulations | Moldable | Until committed |
| Tertiary Canon | Simulation instance output | Instance-local | Only if explicitly promoted |

**The reconciliation skill operates at the Secondary → Primary boundary.**

---

## File References

- `references/entity_schemas.md` — Complete field requirements per entity type and layer
- `scripts/validate_entity.py` — Validation script for entity field checking (v1.1: cross-layer, batch, clearance, domain)
- `scripts/reconciliation_advisor.py` — HDE++-derived certainty tag recommendation engine with confidence scoring and audit logging
- `assets/templates/` — Output templates for reports, drift logs, and claim entries


---
## CanonRec v1.3 Notes
- Auto-detect now distinguishes L2 entity types: location/facility/domain/anomaly.
- Field completeness scoring prefers required_fields_total when provided.
- Advisor confidence is labeled as a heuristic gap score (HEURISTIC_GAP).
- Audit timestamps can be overridden via context: {timestamp, timestamp_source}.
- Validator emits WARN MISSING_PROVENANCE_POINTER when neither doc_sources nor origin_file is present.
