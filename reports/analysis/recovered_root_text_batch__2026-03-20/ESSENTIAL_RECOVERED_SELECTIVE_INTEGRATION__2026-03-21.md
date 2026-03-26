# Selective Integration Report

## Workshop Instructions For Future Agents And LLMs

Use this essential recovered set as workshop-grade raw material, not as active
canon. These modules are here to help rebuild a governed workshop environment
for Quantum Forge / QForge, CharacterForge / CharForge, memory-native
capsules, THREADCORE support, and simulation-facing prototypes from early
canonical source.

Non-negotiable rules:

- Keep labels explicit: `recovered`, `draft`, `include`, `backup_only`,
  `canonical`.
- Aurora remains the coordinating front door across L1, L2, and L3.
- Preserve `EOS_SEED_ORION` and `Picard_Delta_3`.
- `include` means essential build stock; it does not mean live, validated, or
  canon-promoted.
- `backup_only` means fallback material, not default integration target.
- Do not call downstream work a `Forge` run unless it satisfies the workshop
  gate protocol and emits the required receipts.
- Preserve provenance from original artifact to routed recovered copy to any new
  derivative.

See `RECOVERED_MODULE_WORKSHOP_GUIDE__2026-03-22.md` for the full operating
model.

## Decision Snapshot
- Protocol: `AURORA.SelectiveIntegration.v2.5` v`2.5.0`
- Capsule: `AURORA_SI_RECOVERED_ROOT_MATERIAL_20260322`
- Created UTC: `2026-03-22T02:56:29.600517Z`
- Source: `Recovered Root Material` (folder)
- Include: `25` | Backup Only: `16` | Reject: `0`

## Threshold Reference
- `include`: Unique utility; measurable improvement; low maintenance burden.
- `backup_only`: Redundant but potentially useful for resilience; disabled by default.
- `reject`: No clear value; conflicts with canon; increases drift/bloat risk.

## Workflow Reference
1. Pre-Screen (Alex+Relay Lead)
2. Extraction+Classification (Aurora)
3. Specialist Triage (Alex-routed)
4. Canonization (Aurora executes)
5. Post-Merge Review + Meta-Retrospective entry

## Module Decisions
- `memory_system_prototype` -> `include` (Simulation Systems)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for memory_system_prototype from tools/prototypes/python/ and restore prior state from rollback capsule.
- `symbolic_model_selector_threadsense` -> `include` (Simulation Systems)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for symbolic_model_selector_threadsense from tools/prototypes/python/ and restore prior state from rollback capsule.
- `thread_context_tagging_agent_v2` -> `include` (Tooling)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for thread_context_tagging_agent_v2 from tools/prototypes/python/ and restore prior state from rollback capsule.
- `threadcore_v3_6_macrodrift` -> `include` (THREADCORE)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for threadcore_v3_6_macrodrift from tools/prototypes/javascript/ and restore prior state from rollback capsule.
- `aurora_modular_core_v2_3` -> `include` (Aurora Core)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_modular_core_v2_3 from docs/draft_protocols/ and restore prior state from rollback capsule.
- `aurora_system_ingestion_pipeline_capsule_v1` -> `include` (Ingest Pipeline)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_system_ingestion_pipeline_capsule_v1 from docs/draft_protocols/ and restore prior state from rollback capsule.
- `aurora_system_ingestion_pipeline_capsule_v1_1` -> `include` (Ingest Pipeline)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_system_ingestion_pipeline_capsule_v1_1 from docs/draft_protocols/ and restore prior state from rollback capsule.
- `oppy_symbolic_capsule_integration_protocol` -> `include` (Memory Systems)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for oppy_symbolic_capsule_integration_protocol from docs/draft_protocols/ and restore prior state from rollback capsule.
- `zipwizard_recovery_readme_v2_3_1` -> `include` (ZIPWIZ)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for zipwizard_recovery_readme_v2_3_1 from docs/draft_protocols/ and restore prior state from rollback capsule.
- `aurora_l1_middleware_system_prompt` -> `include` (Aurora Core)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_l1_middleware_system_prompt from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `aurora_seed_pulse_999_comet_echo` -> `include` (Aurora Core)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_seed_pulse_999_comet_echo from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `threadcore_unified_thread_identity_tool_patched` -> `include` (THREADCORE)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for threadcore_unified_thread_identity_tool_patched from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `aurora_interlink_fabric_concept` -> `include` (Architecture)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_interlink_fabric_concept from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `galactic_union_state_variables` -> `include` (Simulation Logic)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for galactic_union_state_variables from GUMAS_SIM_2.5/draft_logic/ and restore prior state from rollback capsule.
- `early_simulation_formulas` -> `include` (Simulation Logic)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for early_simulation_formulas from GUMAS_SIM_2.5/draft_logic/ and restore prior state from rollback capsule.
- `galactic_union_simulation_math_framework` -> `include` (Simulation Logic)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for galactic_union_simulation_math_framework from GUMAS_SIM_2.5/draft_logic/ and restore prior state from rollback capsule.
- `immersive_directive_protocol_spec` -> `include` (Simulation Logic)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for immersive_directive_protocol_spec from GUMAS_SIM_2.5/draft_logic/ and restore prior state from rollback capsule.
- `factions_registry_draft` -> `include` (Worldbuilding)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for factions_registry_draft from GUMAS_SIM_2.5/draft_worldbuilding/ and restore prior state from rollback capsule.
- `galactic_union_character_registry` -> `include` (Worldbuilding)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for galactic_union_character_registry from GUMAS_SIM_2.5/draft_worldbuilding/ and restore prior state from rollback capsule.
- `zylox_and_union_command_character_profiles` -> `include` (Worldbuilding)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for zylox_and_union_command_character_profiles from GUMAS_SIM_2.5/draft_worldbuilding/ and restore prior state from rollback capsule.
- `aurora_shuttlecraft_registry` -> `include` (Worldbuilding)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for aurora_shuttlecraft_registry from GUMAS_SIM_2.5/draft_worldbuilding/ and restore prior state from rollback capsule.
- `orion_core_crew_registry_recovered` -> `include` (Canon Support)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for orion_core_crew_registry_recovered from reports/analysis/canon_support/ and restore prior state from rollback capsule.
- `threadcore_symbolic_deployment_snapshot` -> `include` (THREADCORE)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for threadcore_symbolic_deployment_snapshot from catalog/draft_manifests/ and restore prior state from rollback capsule.
- `sigma_ingestion_operations_controller` -> `include` (Ingest Pipeline)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for sigma_ingestion_operations_controller from catalog/draft_manifests/ and restore prior state from rollback capsule.
- `vector_chain_context_transfer` -> `include` (THREADCORE)
  Risk: Low risk if scoped to declared integration_path and monitored via telemetry.
  Backout: Remove integrated artifacts for vector_chain_context_transfer from catalog/draft_manifests/ and restore prior state from rollback capsule.
- `memory_system_manager` -> `backup_only` (Simulation Systems)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for memory_system_manager from tools/prototypes/python/ and restore prior state from rollback capsule.
- `thread_context_tagging_agent_v1` -> `backup_only` (Tooling)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for thread_context_tagging_agent_v1 from tools/prototypes/python/ and restore prior state from rollback capsule.
- `threadcore_sidebar_alias_generator_v3_6` -> `backup_only` (THREADCORE)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for threadcore_sidebar_alias_generator_v3_6 from tools/prototypes/javascript/ and restore prior state from rollback capsule.
- `orion_deployment_controller` -> `backup_only` (Deploy Ops)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for orion_deployment_controller from tools/prototypes/python/ and restore prior state from rollback capsule.
- `symbiosis_threadcore_injection` -> `backup_only` (Patch Ops)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for symbiosis_threadcore_injection from tools/prototypes/python/ and restore prior state from rollback capsule.
- `aurora_modular_core_v2_1` -> `backup_only` (Aurora Core)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for aurora_modular_core_v2_1 from docs/draft_protocols/ and restore prior state from rollback capsule.
- `injectable_patch_capsule_format_template` -> `backup_only` (Protocol Docs)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for injectable_patch_capsule_format_template from docs/draft_protocols/ and restore prior state from rollback capsule.
- `gpt_editor_augmentation_package` -> `backup_only` (Aurora Core)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for gpt_editor_augmentation_package from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `aurora_cloudbank_runtime_vault_summary` -> `backup_only` (Aurora Core)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for aurora_cloudbank_runtime_vault_summary from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `aurora_cloudbank_runtime_vault_quickstart` -> `backup_only` (Aurora Core)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for aurora_cloudbank_runtime_vault_quickstart from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `auroralite_bridgeagent_bundle_manifest` -> `backup_only` (AuroraLite)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for auroralite_bridgeagent_bundle_manifest from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `quantum_symbolic_enhancement_roadmap` -> `backup_only` (Architecture)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for quantum_symbolic_enhancement_roadmap from docs/draft_protocols/agents/ and restore prior state from rollback capsule.
- `galactic_union_memory_optimization_plan` -> `backup_only` (Simulation Logic)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for galactic_union_memory_optimization_plan from GUMAS_SIM_2.5/draft_logic/ and restore prior state from rollback capsule.
- `constellation_registration_capsule` -> `backup_only` (THREADCORE)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for constellation_registration_capsule from catalog/draft_manifests/ and restore prior state from rollback capsule.
- `reflection_chamber_activation_capsule` -> `backup_only` (Agent Ops)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for reflection_chamber_activation_capsule from catalog/draft_manifests/agents/ and restore prior state from rollback capsule.
- `starling_au_commlink_capsule` -> `backup_only` (Worldbuilding)
  Risk: Store as disabled fallback; avoid active merge without specialist retest.
  Backout: Remove integrated artifacts for starling_au_commlink_capsule from catalog/draft_manifests/agents/ and restore prior state from rollback capsule.

## Canonization Plan
- Merge URI: `@mesh://canon/aurora/si/aurora_si_recovered_root_material_20260322`
- Rollback Capsule: `AURORA_SI_RECOVERED_ROOT_MATERIAL_20260322_ROLLBACK`
- Meta Retro Ref: `@mesh://meta_retro/entries/2026-03-22-aurora_si_recovered_root_material_20260322`

## Approvals
- Alex: `pending`
- Aurora: `prepared`
- Pilot: `not_required`
