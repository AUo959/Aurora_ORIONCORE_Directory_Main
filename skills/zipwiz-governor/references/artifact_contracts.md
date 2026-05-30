# ZIPWIZ Artifact Contracts

## Family: `bundle_manifest`

Detection:
- `bundle.manifest.json`
- `*BUNDLE_MANIFEST*.json`

Required:
- `bundle_id`
- `anchor_seed` (`EOS_SEED_ORION`)
- `ethics_protocol` (`Picard_Delta_3`)
- one of `created_at` or `created_at_utc`
- one of `contents[]` or `files[]`

Blocking checks:
- missing identity/anchor/ethics
- noncanonical anchor/ethics values
- invalid SHA256 hashes

Warning checks:
- role taxonomy drift

Info checks:
- `created_at_utc` and `files[]` variants are treated as mappable migration hints
- mappable `bytes -> size_bytes` variants are aggregated as informational normalization hints
- known legacy role aliases are normalized in-report and emitted as informational mappings

## Family: `staging_manifest`

Detection:
- `STAGING_MANIFEST__*.json`

Required:
- `staging_bay`
- `bundle`
- `generated_at_local`
- `build`
- `classification.layer`
- `classification.domain`
- `files[]` entries with `path`, `role`, `sha256`, `bytes`

Cross-check warnings:
- staging `bundle` mismatches sibling bundle manifest `bundle_id`
- file count mismatch against sibling bundle manifest

## Family: `zipwiz_protocol_doc`

Detection:
- markdown with ZIPWIZ packaging protocol docid/title markers

Required frontmatter:
- `docid`
- `doctype`
- `version`
- `anchor_seed`
- `ethics_protocol`

Warning:
- `authority: draft`

## Family: `beacon_capsule`

Detection:
- `*Beacon*Capsule*.json`
- JSON with `Output_Format: .beacon.json`

Required identity:
- `Designation`
- `Action_Request`
- `Thread_Metadata.Thread_Name`

Ethics checks:
- block if both canonical and legacy ethics markers are missing
- warn when only legacy `Ethics_Lock` exists

Additional warning:
- missing `Thread_Identity_Affirmation.Trust_Anchor`

## Family: `runtime_alignment`

Detection paths:
- `scripts/zipwiz.py`
- `services/command_node/modules/zipwiz.js`
- `src/core/zipcomm.js`

Checks:
- warn when stub-like runtime modules conflict with ZIPWIZ protocol/tooling claims
- info when canonical handshake sequence is present

## Family: `evolution_evidence`

Purpose:
- build timeline milestones from curated ZIPWIZ evidence

Policy:
- reference-only sources never emit BLOCK
- milestones emit INFO
- contradictory version/date records emit WARN
