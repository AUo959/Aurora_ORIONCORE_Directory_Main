---
name: aurora-selective-integration
description: Build selective-integration capsules for Aurora by triaging external kit/archive modules into include, backup_only, or reject decisions with deterministic criteria, specialist routing notes, and rollback-ready canonization metadata. Use when users ask to absorb parts of a ZIP/archive safely, run selective integration, create or validate selective integration capsules, map modules into integration paths, or apply the Aurora_SelectiveIntegrationProtocol_v2.5 workflow. Not for broad governance preflight or THREADCORE/ZIPWIZ audits; route those to aurora-governance-orchestrator, threadcore-governor, zipwiz-governor, aurora-script-governor, or aurora-canon-reconciler.
author: Aurora ORIONCORE
---

# Aurora Selective Integration

## Overview

Convert external kits/archives into deterministic selective-integration capsules that preserve doctrine, reduce drift, and keep rollback metadata ready. Use this skill to classify candidate modules and produce machine-readable capsule output plus a human review report.

## Quick Start

Run the capsule builder:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-selective-integration/scripts/build_selective_integration_capsule.py \
  --protocol-json /path/to/Aurora_SelectiveIntegrationProtocol_v2.5_VIEW.json \
  --modules-json /path/to/modules_manifest.json \
  --source-name "GUMAS_AI_Agents_Kit.zip" \
  --source-type zip \
  --source-uri "local:/path/to/GUMAS_AI_Agents_Kit.zip" \
  --out-json /tmp/selective_integration_capsule.json \
  --out-md /tmp/selective_integration_report.md
```

## Input Contracts

### Protocol JSON

Provide the v2.5 protocol document. Required keys:
- `protocol_id`
- `version`
- `purpose`
- `decision_thresholds`
- `workflow`

### Modules Manifest JSON

Provide an array of modules. Minimum recommended fields per module:
- `id`
- `category`
- `path`
- `integration_path`
- `redundancy_flag`
- `telemetry`
- `notes`
- `utility_score`
- `improvement_score`
- `maintenance_burden`
- `conflict_risk`
- `specialist`

Optional module field:
- `decision` (manual override: `include`, `backup_only`, `reject`)

See `references/module_manifest_schema.md` for full details.

## Decision Logic

The script applies deterministic triage rules when no explicit decision is supplied:
- `include`: high utility and improvement, low maintenance/conflict, not redundant
- `backup_only`: moderate value or redundant resilience candidate
- `reject`: poor threshold fit or elevated risk

Optional triage overrides (`--triage-json`) can force specialist/decision/risk notes/backout plans.

## Outputs

### Capsule JSON

Primary artifact includes:
- `capsule_id`, `created_utc`, `protocol_ref`, `protocol_version`
- `source`
- `extracted_modules` with decisions and rationale
- `triage`
- `approvals`
- `canonization` (`merge_uri`, `rollback_capsule_id`, `meta_retro_ref`)
- aggregate `metrics`

### Markdown Report (optional)

The report includes:
- Decision snapshot
- Threshold and workflow reference
- Module decisions with risk + backout notes
- Canonization plan and approval statuses

## Guardrails

- Keep selective integration scoped to module intake and capsule construction.
- Do not use this as a replacement for governance orchestrator scans.
- Always keep rollback capsule references in output.
- Use `--fail-on-reject` when rejections should block execution.

## Workflow Position

- Upstream: `aurora-skill-finder` when ingest scope is unclear.
- Downstream: specialist governors for affected domains, then `aurora-governance-orchestrator` for the final gate.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

## References

- Protocol mapping: `references/protocol_mapping_v2_5.md`
- Module manifest schema: `references/module_manifest_schema.md`

## Trigger Examples

Use this skill when prompts look like:
- "Create a selective integration capsule from this external ZIP kit."
- "Run include/backup/reject triage for these candidate modules."
- "Apply Aurora SelectiveIntegrationProtocol v2.5 to this ingest batch."
- "Generate rollback-ready merge metadata for selective module intake."
