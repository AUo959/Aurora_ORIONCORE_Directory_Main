---
name: threadcore-governor
description: Govern THREADCORE artifacts with deterministic validation, diagnostics, and L3 bridge outputs. Use when checkpoint manifests, continuity logs, payload or capsule JSON, delta-chain records, or THREADCORE beacon and THREADREFLECT markdown blocks must be validated for required fields, ethics and anchor integrity, identity continuity, and remediation readiness. Trigger on requests such as validate THREADCORE, audit threadcore artifacts, check continuity bundle, beacon lint, drift governance review, produce THREADCORE diagnostics, or generate L3 bridge entities from THREADCORE materials. Not for broad repo script hardening or non-THREADCORE canonization.
author: Aurora ORIONCORE
---

# Threadcore Governor

## Overview

Run deterministic THREADCORE governance checks over JSON and beacon markdown artifacts, then emit machine-readable findings plus a remediation-focused markdown report.

## Workflow

### Step 1: Run a Focused Scan

Use the scanner against a target repo root. Default authority roots are fixed to the focused cross-root canonical set.

```bash
python /path/to/skill/scripts/threadcore_governance_scan.py \
  --repo /path/to/repo \
  --out-json /tmp/threadcore_scan.json \
  --out-md /tmp/threadcore_scan.md
```

Optional controls:

- `--roots <csv>`: override authority roots (absolute or repo-relative)
- `--strictness balanced|strict|lenient`: validation profile, default `balanced`
- `--emit-l3-bridge <path>`: emit standalone bridge payload
- `--fail-on-block`: nonzero exit when BLOCK findings exist

### Step 2: Interpret Severity and Family Results

Use the report sections in this order:

1. Scope
2. Blocking Findings
3. Warnings
4. Suggested Patch Plan
5. L3 Bridge Preview

Severity model:

- `BLOCK`: required structural or governance violations
- `WARN`: recoverable drift or legacy compatibility issues
- `INFO`: non-blocking advisories and dedupe signals

Family model:

- `checkpoint`
- `continuity_log`
- `payload_capsule`
- `delta_chain`
- `beacon_markdown`

### Step 3: Apply Governance Remediation

Treat scan output as the source of truth for patch planning.

Core remediation order:

1. Fix `ethics_protocol` and `anchor_seed` integrity issues.
2. Fix family identity and required-field violations.
3. Normalize legacy key variants with mapped canonical keys.
4. Resolve alias or title drift and optional substructure warnings.

Do not auto-rewrite source artifacts unless explicitly requested.

### Step 4: Generate L3 Bridge Artifacts (Optional)

When requested, emit bridge entities compatible with L3 canon workflows:

- `protocol_update`
- `schema_definition`
- `anchor_rule`

Bridge output is standalone JSON and does not import or require runtime coupling to `aurora-canon-reconciler`.

## Defaults and Policy

- Preserve Unicode exactly in source-derived content.
- Limit default scan scope to focused canonical roots.
- Use `balanced` strictness by default.
- Produce both JSON and Markdown outputs each run.
- Align findings to the shared schema at `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/finding_schema.md` for multi-skill governance workflows.

## Workflow Position

- Upstream: `aurora-skill-finder` or `aurora-selective-integration` when the affected domain is unclear.
- Downstream: hand findings to `aurora-governance-orchestrator` when THREADCORE is part of a wider promotion gate.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

## Resources

- `scripts/threadcore_governance_scan.py`: CLI entrypoint for scanning and output emission.
- `scripts/threadcore_rules.py`: deterministic family detection and rule engine.
- `scripts/threadcore_report.py`: markdown renderer from JSON findings.
- `references/artifact_contracts.md`: family field requirements and checks.
- `references/canonical_roots.md`: default authority roots and scan policy.
- `references/l3_bridge_mapping.md`: bridge contracts for L3 entities.
- `assets/templates/`: minimal beacon, report, and remediation receipt templates.
