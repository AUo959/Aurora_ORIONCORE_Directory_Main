---
name: zipwiz-governor
description: Govern ZIPWIZ packaging and export artifacts with deterministic validation, remediation reporting, and evolution mapping. Use when bundle manifests, staging manifests, ZIPWIZ packaging protocol docs, beacon capsule JSON, or ZIPWIZ runtime alignment evidence must be checked for anchor and ethics integrity, structural drift, and timeline continuity. Trigger on requests such as validate ZIPWIZ artifacts, audit zipwiz packaging, check zipwizard export manifests, generate ZIPWIZ evolution timeline, or produce ZIPWIZ governance diagnostics. Not for broad script hardening, CI stabilization, or THREADCORE artifact governance.
author: Aurora ORIONCORE
---

# ZipWiz Governor

## Overview

Run deterministic ZIPWIZ governance checks over packaging artifacts and produce dual outputs:
- machine-readable findings JSON
- remediation-focused markdown diagnostics

Also generate an evolution timeline from curated ZIPWIZ sources to explain how ZIPWIZ changed across phases.

## Non-Overlap Boundaries

Keep this skill focused on ZIPWIZ packaging/export governance and ZIPWIZ evolution evidence.

Route requests out when they leave scope:
- Script hazard remediation, hook hardening, or CI stabilization: use `aurora-script-governor` or `aurora-repo-stabilizer`.
- THREADCORE artifact family validation: use `threadcore-governor`.
- Repo-wide refactors not tied to ZIPWIZ governance: do not handle here.

## Workflow

### Step 1: Run a Focused Scan

```bash
python /path/to/skill/scripts/zipwiz_governance_scan.py \
  --repo /path/to/repo \
  --out-json /tmp/zipwiz_scan.json \
  --out-md /tmp/zipwiz_scan.md
```

Core options:
- `--roots <csv>`: override canonical roots.
- `--reference-roots <csv>`: override reference-only evolution roots.
- `--strictness balanced|strict|lenient`: default `balanced`.
- `--emit-l3-bridge <path>`: optional bridge artifact.
- `--diagnostic-mode`: run balanced/strict/lenient/no-evolution matrix and print summary.
- `--diagnostic-json <path>`: optionally persist diagnostic matrix JSON.
- `--warn-threshold <n>`: optional WARN threshold in diagnostic summaries.
- `--fail-on-block`: nonzero exit when `BLOCK` findings exist.

Evolution options:
- `--include-evolution`: include timeline mapping (default true).
- `--no-include-evolution`: disable evolution extraction.

### Step 2: Read Severity and Family Results

Family model:
- `bundle_manifest`
- `staging_manifest`
- `zipwiz_protocol_doc`
- `beacon_capsule`
- `runtime_alignment`
- `evolution_evidence`

Severity model:
- `BLOCK`: structural governance violations.
- `WARN`: recoverable drift.
- `INFO`: advisory guidance and timeline milestones.

### Step 3: Apply Remediation by Order

1. Fix anchor and ethics integrity in manifests/protocol docs.
2. Fix missing required identity and structure keys.
3. Resolve hash and role taxonomy drift.
4. Address runtime alignment warnings without broad script rewrites.

Do not auto-rewrite source artifacts unless explicitly requested.

### Step 4: Generate Bridge Artifacts (Optional)

Bridge entities are emitted in standalone JSON when requested:
- `protocol_update`
- `schema_definition`
- `anchor_rule`

These are compatible with downstream L3 canon workflows and have no hard runtime dependency on other skills.

## Defaults and Policy

- Preserve Unicode exactly (`UTF-8`, `ensure_ascii=False`).
- Default to curated roots and reference-only evolution sources.
- Exclude archive-heavy mirror paths by default.
- Always emit both JSON and markdown outputs.
- Align findings to the shared schema at `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/finding_schema.md` for multi-skill governance workflows.

## Workflow Position

- Upstream: `aurora-skill-finder` or `aurora-selective-integration` when ZIPWIZ surfaces are part of a wider batch.
- Downstream: hand findings to `aurora-governance-orchestrator` for any merged promotion verdict.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

## Resources

- `scripts/zipwiz_governance_scan.py`: CLI entrypoint.
- `scripts/zipwiz_rules.py`: deterministic detectors and validators.
- `scripts/zipwiz_report.py`: markdown renderer.
- `references/artifact_contracts.md`: family contracts and invariants.
- `references/canonical_roots.md`: authority roots and exclusion policy.
- `references/evolution_model.md`: timeline extraction model.
- `references/skill_boundaries.md`: routing and non-overlap guidance.
- `references/l3_bridge_mapping.md`: bridge schema alignment.
- `assets/templates/`: minimal beacon/report/receipt templates.
