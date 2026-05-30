---
name: aurora-narrative-tone-governor
description: Canonical-source-first governance scan for Aurora narrative outputs. Use when users ask to run a narrative linter, tone/cadence governance check, anti-flourish validation, or LLM writing style audit against ORION rules (R1-R6, LINT-NARR-001..006, CTL P001+), and return findings-only pass/review/block results without rewriting.
author: Aurora ORIONCORE
---

# Aurora Narrative Tone Governor

## Overview
Run a deterministic governance scan for narrative text using Aurora canonical L3 policy documents. Emit findings only by default and avoid rewrite generation unless the user explicitly requests rewrite guidance.

## Canonical Source Routing
Resolve authority before evaluating text.

1. Load [references/source_map.md](references/source_map.md).
2. Use canonical governance docs first.
3. Treat archived, duplicated, or research-only artifacts as non-authoritative unless the user explicitly asks to include them.

## Input Contract
Accept this minimal input shape:

```yaml
candidate_text: <required string>
mode: MODE_RECAP  # optional, default MODE_RECAP
metadata_flags:   # optional
  has_event_ledger_id: false
  has_paired_output_id: false
  has_trace_map: false
  has_story_nodes: false
  has_entity_registry_lookup: false
```

Interpretation rules:
- Default `mode` to `MODE_RECAP` when unspecified.
- Treat missing metadata flags as `false`.
- Keep evaluation strict for `MODE_LOG` and `MODE_RECAP`.

## Scan Workflow
Execute the workflow in this order.

1. Normalize scope
- Confirm this is a governance scan request.
- If input is mixed with non-narrative data, isolate narrative prose for evaluation.

2. Resolve rule set
- Load [references/rule_crosswalk.md](references/rule_crosswalk.md).
- Evaluate against:
  - NarrativeLinter principles `R1-R6`.
  - Lint IDs `LINT-NARR-001..006`.
  - CTL pattern families (`P001+`, `P101+`, `P201+`, `P301+`).

3. Run deterministic checks
- Identify rule hits with quoted evidence spans.
- Classify severity from canonical policy (`error`/`warn`).
- Run metadata-dependent checks:
  - `LINT-NARR-005` for unexplained identifiers when registry mapping is absent.
  - `LINT-NARR-006` for missing stakes/decisions in `MODE_RECAP` when story graph metadata is absent.

4. Decide verdict
- `BLOCK`:
  - Any `error` hit on `LINT-NARR-001`, `002`, or `004`.
  - CTL hard override equivalents (`P001_NO_NO_JUST` or `P301_CERTAINTY_INFLATION`) with unresolved risk.
- `REVIEW`:
  - Warning-only outcomes (`LINT-NARR-003`, `005`, `006`) or ambiguous metadata coverage.
  - CTL anti-pattern density that indicates style drift but not hard reject.
- `PASS`:
  - No blocking hits, no material warning drift, and metadata support is sufficient for claim traceability.

5. Set promotion readiness
- `NOT_READY` for `BLOCK`.
- `CONDITIONAL` for `REVIEW`.
- `READY` for `PASS`.

6. Emit report
- Use [references/report_template.md](references/report_template.md).
- Keep output findings-only and deterministic.

## Repo Scan CLI
For repository preflight or orchestration use the bundled scanner:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-narrative-tone-governor/scripts/narrative_tone_scan.py \
  --repo /path/to/repo \
  --out-json /tmp/narrative_tone_scan.json \
  --out-md /tmp/narrative_tone_scan.md
```

Optional controls:
- `--roots <csv>`: override canonical roots
- `--paths <csv>`: scan only changed paths or specific files
- `--strictness balanced|strict|lenient`
- `--fail-on-block`

## Output Contract
Return this structure:

```yaml
verdict: PASS|REVIEW|BLOCK
promotion_readiness: READY|CONDITIONAL|NOT_READY
rule_hits:
  - rule_id: <id>
    severity: error|warn
    evidence: <short quoted span>
    rationale: <one-sentence reason>
canonical_sources_used:
  - <path>
notes:
  - <optional operator note>
```

When participating in multi-skill governance workflows, align individual findings to the shared schema at `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/finding_schema.md`.

## Workflow Position

- Upstream: `aurora-skill-finder`, `gumas-simulation-engine`, or `aurora-quantum-forge-ops` when prose artifacts need governance.
- Downstream: hand merged promotion gating to `aurora-governance-orchestrator`; hand polished summaries to `aurora-exec-brief-pipeline`.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

## Query Discipline
Use reproducible repository queries from [references/query_recipes.md](references/query_recipes.md).

## Guardrails
- Do not treat archive duplicates as authoritative by default.
- Do not silently merge conflicting rule definitions from different versions.
- Do not output rewrites unless explicitly requested by the user.
- Keep findings tied to rule IDs and concrete evidence.

## Resources
- `scripts/narrative_tone_scan.py`: deterministic repo scanner for narrative/tone governance preflight
- `references/source_map.md`: canonical source precedence
- `references/rule_crosswalk.md`: rule-to-rule binding across NarrativeLinter and CTL
- `references/report_template.md`: findings-only report shape
