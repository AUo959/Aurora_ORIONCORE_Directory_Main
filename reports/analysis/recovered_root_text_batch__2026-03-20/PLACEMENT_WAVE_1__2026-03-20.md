# Placement Wave 1

This pass places the immediate-salvage `P1` recovered artifacts into stable
destination folders without modifying or removing the root originals.

## Scope

- Placement basis: refreshed deep triage after the final manual audit
- Root originals preserved: `true`
- Duplicate collapse applied: `text_13.txt` + `text_threadcore_3_6.txt`
- Placement lanes created:
  - `tools/prototypes/javascript/recovered`
  - `tools/prototypes/python/recovered`
  - `docs/draft_protocols/recovered`

## Routed Artifacts

- `text_15.txt` -> `tools/prototypes/javascript/recovered/threadcore_sidebar_alias_generator_v3_6.js`
- `text_13.txt` + `text_threadcore_3_6.txt` -> `tools/prototypes/javascript/recovered/threadcore_v3_6_macrodrift.js`
- `text_tagging_agent.txt` -> `tools/prototypes/python/recovered/thread_context_tagging_agent.py`
- `text_thread_tag.txt` -> `tools/prototypes/python/recovered/thread_context_tagging_agent_v2.py`
- `text_52.txt` -> `tools/prototypes/python/recovered/orion_deployment_controller.py`
- `text_mem_system_py.txt` -> `tools/prototypes/python/recovered/memory_system_prototype.py`
- `text_mem_system.txt` -> `tools/prototypes/python/recovered/memory_system_manager.py`
- `text_24.txt` -> `tools/prototypes/python/recovered/symbolic_model_selector_threadsense.py`
- `text_Au_mod_core.txt` -> `docs/draft_protocols/recovered/aurora_modular_core_v2_3.md`
- `text_Au_mod_core_first.txt` -> `docs/draft_protocols/recovered/aurora_modular_core_v2_1.md`
- `text_GitIngestion.txt` -> `docs/draft_protocols/recovered/aurora_system_ingestion_pipeline_capsule_v1.md`

## Extra-Pass Elevations Confirmed

- `text_Au_Shuttlecraft.txt` -> elevated to `P2`
- `text_Orion_Crew.txt` -> elevated to `P2`
- `text_recovery_README.txt` -> elevated to `P3`
- `text_47.txt` -> elevated to `P3`
- `text_oppy_integration.txt` -> elevated to `P3`
- `text_stellar_sync_patch.txt` -> elevated to `P3`
- `text_Orion_deploy_prototype.txt` -> elevated to `P3`
- `text_relay_deploy_prototype.txt` -> elevated to `P3`
- `text_GitDeploy_Prototype.txt` -> elevated to `P3`

## Notes

- `memory_system_manager.py` was lightly salvaged with import headers so its
  dependency on the recovered memory prototype is explicit.
- The routed files are still recovered drafts, not promoted canon or production
  modules.
- `P0` hold files remain quarantined and were not placed in this wave.
