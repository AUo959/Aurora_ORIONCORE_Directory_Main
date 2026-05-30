# Shared Finding Schema

Use this schema for cross-skill governance findings so scanners, governors, and the orchestrator can chain without adapters.

## Report-level fields
- `domain`: scanner domain for single-domain reports
- `verdict`: `PASS` | `REVIEW` | `BLOCK`
- `promotion_readiness`: `READY` | `CONDITIONAL` | `NOT_READY`
- `summary`: stable counts keyed by `BLOCK` / `WARN` / `INFO`
- `findings`: ordered list using the finding-level schema below

## Required finding-level fields
- `severity`: `BLOCK` | `WARN` | `INFO`
- `domain`: emitting governance domain, for example `threadcore`, `zipwiz`, `script_governor`, `narrative_tone`, `canon`
- `rule_id`: stable machine-readable identifier
- `file`: repository-relative path or synthetic placeholder like `<threadcore_roots>`
- `source_path`: stable file or file:line locator used by downstream tools
- `message`: concise finding statement
- `rationale`: one-sentence explanation of why the finding matters
- `evidence`: quoted snippet, line excerpt, field name, or other concrete support
- `remediation`: deterministic next action or fix guidance

## Strongly recommended fields
- `family`: optional grouping label used by the source scanner
- `source_tool`: scanner or normalizer that produced the finding
- `blocking_scope`: `authoritative` | `reference_only` | `advisory` | `execution_health`
- `suggested_fix`: kept only for backward compatibility; mirror the same value into `remediation`

## Compatibility aliases
- `id`: alias of `rule_id` for downstream package and automation consumers
- `scope`: alias of `blocking_scope` for downstream package and automation consumers

## Ordering rule
When emitting findings or remediation queues, order rationale lines as:
1. rule trigger / severity
2. gating decision or blocking scope
3. evidence
4. remediation

## Example
```json
{
  "severity": "WARN",
  "domain": "narrative_tone",
  "rule_id": "LINT-NARR-005",
  "file": "GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0/Thread 3 Run.md:228",
  "source_path": "GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0/Thread 3 Run.md:228",
  "message": "Identifier appears without first-use explanation.",
  "rationale": "Identifier appears without first-use explanation.",
  "evidence": "ABC-77 revoked PDL-3 access for Dock 2",
  "remediation": "Expand the first occurrence into human-readable language before using the identifier again."
}
```
