# Findings Report Template

Use this template for deterministic findings-only outputs.

## 1) Input Summary
- `mode`: MODE_LOG | MODE_RECAP | MODE_SCENE (default MODE_RECAP)
- `text_length`: <chars/words>
- `metadata_flags`:
  - `has_event_ledger_id`: true|false
  - `has_paired_output_id`: true|false
  - `has_trace_map`: true|false
  - `has_story_nodes`: true|false
  - `has_entity_registry_lookup`: true|false

## 2) Canonical Sources Used
- `<path>`
- `<path>`

## 3) Rule Hits

| rule_id | severity | evidence | rationale |
|---|---|---|---|
| LINT-NARR-001 | error | "..." | Meta-narration pattern in STRICT mode |

If no hits:
- `No rule hits detected.`

## 4) Verdict
- `verdict`: PASS | REVIEW | BLOCK
- `promotion_readiness`: READY | CONDITIONAL | NOT_READY

## 5) Operator Notes
- Keep notes factual and tied to specific rule IDs.
- Do not propose rewrites unless explicitly requested.

## 6) Optional Machine-Readable Block

```json
{
  "verdict": "REVIEW",
  "promotion_readiness": "CONDITIONAL",
  "rule_hits": [
    {
      "rule_id": "LINT-NARR-005",
      "severity": "warn",
      "evidence": "ABC-77 clearance was revoked",
      "rationale": "Identifier appears without first-use explanation."
    }
  ],
  "canonical_sources_used": [
    "GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0/L3_GOV__ORION_PROJ_NARRLINT_0001__v0.1.2__2026-02-07.md"
  ]
}
```
