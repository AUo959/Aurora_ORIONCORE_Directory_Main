# THREADCORE Artifact Contracts

## Families

- `checkpoint`
- `continuity_log`
- `payload_capsule`
- `delta_chain`
- `beacon_markdown`

## Required Fields

### checkpoint

- `augmentation`
- `version`
- `checkpoint.id`
- `checkpoint.anchor_seed`
- `checkpoint.ethics_protocol`
- `threadcore_directives`

### continuity_log

- `symbolic_tool`
- `deployment_key`
- `activation_phrase`
- `ethics_protocol`
- `timestamp`
- `status`

### payload_capsule

Required identity:

- `capsule_id` OR (`augmentation` + `version`)

Required governance:

- `role`
- `ethics_protocol`
- `anchor_seed` (not required for `capsule_type=DRIFTPULSE`)

### delta_chain

- `delta_chain_version`
- `entries[]`

For each entry:

- `version`
- `label`
- `cdk`
- `ethics`

### beacon_markdown

- Header marker: `THREADCORE BEACON::VISIBLE_THREAD`
- Identity block marker: `Thread Identity Marker` or `Thread Title:`
- Registry marker format: `THREADCORE::VISIBLE_NODE.ORION.*`

## Severity Rules

Balanced profile:

- `BLOCK`: malformed artifacts, missing required identity fields, ethics or anchor violations
- `WARN`: recoverable drift, legacy naming variants, optional structure gaps
- `INFO`: duplicate identity signals and normalization hints

Strict profile:

- escalates warning-level compatibility issues to `BLOCK`

Lenient profile:

- downgrades non-parse `BLOCK` findings to `WARN`
