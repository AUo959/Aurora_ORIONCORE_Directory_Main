# Protocol Mapping: Aurora SelectiveIntegration v2.5

This reference maps protocol fields to capsule-generation behavior.

## Source Protocol

Example protocol path used during development:
`/Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main/projects/Auora2.5_DEV/Aurora_SelectiveIntegrationProtocol_v2.5_VIEW.json`

## Field Mapping

- `protocol_id` -> `capsule.protocol_ref`
- `version` -> `capsule.protocol_version`
- `decision_thresholds` -> markdown threshold section and decision rationale context
- `workflow[]` -> markdown workflow section for operator traceability
- `schema_uri` -> `capsule.references.schema_uri`
- `example_uri` -> `capsule.references.example_uri`

## Operational Mapping

### Governance and roles

Protocol governance/roles are treated as doctrinal context. The generator does not enforce identity-level permissions but records approval slots under:
- `approvals.alex`
- `approvals.aurora`
- `approvals.pilot`

### Threshold intent

Protocol threshold intent is encoded in deterministic score logic:
- Include: high utility + improvement, low maintenance + conflict, non-redundant
- Backup only: redundant resilience or moderate utility profile
- Reject: low net value or elevated risk profile

### Security intent

Protocol security expectations are represented by:
- source hash in `capsule.source.hash`
- rollback reference in `canonization.rollback_capsule_id`
- merge metadata and retro linkage for audit continuity

## Known Limits

- The generator does not execute live merge actions.
- Mesh URIs are emitted as metadata references only.
- Specialist decisions are represented as triage outputs; external systems must enforce sign-off policy.
