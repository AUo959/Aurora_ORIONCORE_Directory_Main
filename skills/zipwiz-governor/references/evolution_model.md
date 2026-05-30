# ZIPWIZ Evolution Model

## Goal

Extract a deterministic timeline of ZIPWIZ evolution from curated evidence without treating symbolic archives as canonical blocking sources.

## Milestone fields

- `date`: `YYYY-MM-DD` when detectable
- `version`: semantic version token (`vX.Y` etc.) when detectable
- `source_file`: relative file path
- `signal_type`: coarse classifier (`packaging_protocol`, `bundle_schema`, `symbolic_chamber`, `functional_patch`, `evidence_doc`)
- `summary`: first meaningful heading/line

## Signal expectations (V1)

Expected timeline anchors in this repo:
1. `2025-04-25` chamber symbolic identity phase
2. `2026-02-08` packaging protocol/schema phase
3. `2026-02-16` ZIPWIZARD + THREADCORE functional patch narrative

## Contradiction policy

If the same version token appears with multiple dates across evidence files, emit `W_EVOLUTION_VERSION_DATE_CONTRADICTION`.

## Source classes

- `canonical`: governance/packaging/runtime roots
- `reference_only`: chamber/technical-reference roots

`reference_only` events contribute timeline insight but do not create BLOCK findings.
