# Root Recovered Text Batch

Status: staged, non-canon
Prepared: 2026-03-20T18:42:33Z
Source scope: top-level root `.txt` artifacts only

## Workshop Instructions For Future Agents And LLMs

Treat this batch as `raw early-canonical source material` for a workshop
environment. It is useful seed stock for rebuilding Quantum Forge / QForge,
CharacterForge / CharForge, THREADCORE-adjacent agent tooling, memory-native
capsules, and simulation support modules, but it is not active canon or a live
runtime surface.

Hard rules:

- Use this batch for `workshop` and `forge-input` work, not silent canon merge.
- Workshop first, Forge second. Do not call a pass `Forge`, `complete`, or
  `shippable` unless it meets the run-gate rules and deliverables in
  `ORION_L3_WORKSHOPGATES_0001__v1.0.1__2026-02-13.md`.
- Keep lifecycle labels explicit: `recovered`, `draft`, `staged`, `include`,
  `backup_only`, `quarantine`, `canonical`.
- Preserve anchor constants and ethics gates: `EOS_SEED_ORION` and
  `Picard_Delta_3`.
- Aurora remains the front door and coordinating layer across L1, L2, and L3.
  Recovered modules do not bypass Aurora or canon governance.
- Prefer the `include` shortlist as build material. Use `backup_only` artifacts
  for fallback, diffing, or resilience testing only.
- Preserve provenance on every derivative: original root artifact, routed
  recovered copy, and new derived output.
- Never silently promote recovered material into canon. Promotion requires an
  explicit canon action in the relevant repo.

Workshop objective:

- Reassemble early source into deterministic prototypes, non-convergent agent
  generation flows, Quantum Forge support modules, draft manifests, and
  simulation-facing logic.
- Use CharacterForge-style recovered material to build agent capsules,
  dossiers, or memory-seeded profiles that remain auditable and non-convergent.
- Use Quantum Forge-style recovered material as raw inputs for module design,
  vector/rule extraction, and research-grade experimentation rather than as
  already-validated outputs.

Minimum receipt expectation for new work built from this batch:

- component inventory
- dependency graph
- flow map
- seams and faultlines
- module specs
- patch list
- fact / inference / assumption log

Reference guide: `RECOVERED_MODULE_WORKSHOP_GUIDE__2026-03-22.md`

## Purpose

This bundle sorts and indexes the recovered root text artifacts without
renaming or relocating the original files. The originals remain untouched
at the repo root; this bundle provides the review surface we can use to
name, dedupe, and move them safely in a later pass.

## Inventory Snapshot

- Artifacts indexed: `244`
- Exact duplicate groups: `6`
- Normalized duplicate groups: `0`
- Extracted logic/code files: `12`

## Category Counts

- `blueprint_or_protocol`: `3`
- `config_manifest`: `61`
- `conversation_or_chat_export`: `3`
- `fragment_or_note`: `91`
- `javascript_module`: `9`
- `prompt_template_or_agent`: `29`
- `python_prototype`: `6`
- `research_brief`: `21`
- `sensitive_or_auth`: `6`
- `simulation_logic`: `10`
- `worldbuilding_registry`: `5`

## High-Priority Salvage Candidates

- `text_Au_mod_core.txt` -> `blueprint_or_protocol` [future bucket: `docs/draft_protocols`; extracted: `extracted_logic/blueprints/aurora_modular_core_v2_3.md`]
- `text_Au_mod_core_first.txt` -> `blueprint_or_protocol` [future bucket: `docs/draft_protocols`; extracted: `extracted_logic/blueprints/aurora_modular_core_v2_1.md`]
- `text_GitIngestion.txt` -> `blueprint_or_protocol` [future bucket: `docs/draft_protocols`; extracted: `extracted_logic/blueprints/aurora_system_ingestion_pipeline_capsule_v1.md`]
- `Text_109.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_105.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_107.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_109 2.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_111.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_112.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_113.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_119.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_123.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_138.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_139.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_141.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_19.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_28.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_29.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_31.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]
- `text_34.txt` -> `config_manifest` [future bucket: `catalog/draft_manifests or .github/workflows`; extracted: `not auto-extracted`]

## Sensitive Review

- `text_79.txt` [quarantine_and_review]
- `text_AES_Key.txt` [quarantine_and_review]
- `text_au_key.txt` [quarantine_and_review]
- `text_conversation_PDK001.txt` [quarantine_and_review]
- `text_core_auth.txt` [quarantine_and_review]
- `text_master_sync.txt` [quarantine_and_review]

## Outputs

- `artifact_index.csv`: full sortable review index
- `artifact_inventory.json`: machine-readable inventory
- `duplicate_groups.json`: exact and normalized duplicate clusters
- `extraction_manifest.json`: provenance for extracted logic/code
- `NAMING_AND_ROUTING_QUEUE.md`: curated shortlist for the rename-and-move pass
- `RECOVERED_MODULE_WORKSHOP_GUIDE__2026-03-22.md`: workshop operating
  instructions for future agents and LLMs
- `extracted_logic/`: staged code, config, and blueprint recoveries
