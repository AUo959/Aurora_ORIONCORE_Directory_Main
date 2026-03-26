# Naming And Routing Queue

Use this queue for the next pass, when we rename artifacts and move them out of the
root. It deliberately focuses on the highest-signal files rather than the entire batch.

## Immediate Salvage

- `text_mem_system_py.txt`
  - Extracted to `extracted_logic/python/memory_system_prototype.py`
  - Contains the strongest directly reusable Python prototype in the batch
  - Likely future bucket: `tools/prototypes/python` or a GUMAS memory subsystem draft area

- `text_tagging_agent.txt`
  - Extracted to `extracted_logic/python/thread_context_tagging_agent.py`
  - Small but coherent utility for keyword-based thread routing
  - Likely future bucket: `tools/prototypes/python`

- `text_threadcore_3_6.txt`
  - Extracted to `extracted_logic/javascript/threadcore_v3_6_macrodrift.js`
  - Fully formed JS module with export surface intact
  - Duplicate note: same content as `text_13.txt`
  - Likely future bucket: `tools/prototypes/javascript` or THREADCORE draft docs

- `text_node_js_webpack.txt`
  - Extracted to `extracted_logic/config/github_actions_nodejs_webpack.yml`
  - Recoverable GitHub Actions workflow fragment
  - Likely future bucket: `.github/workflows` or `catalog/draft_manifests`

- `text_factions_reg.txt`
  - Extracted to `extracted_logic/config/factions_registry_draft.yaml`
  - Strong structured worldbuilding registry
  - Likely future bucket: `GUMAS_SIM_2.5/draft_worldbuilding`

- `text_GitDeploy_root.txt`
  - Extracted to `extracted_logic/config/root_deploy_inventory_draft.json`
  - Useful as a historical inventory snapshot of a deploy root
  - Likely future bucket: `catalog/draft_manifests` or ops archive

- `text_early_sim_logic.txt`
  - Extracted to `extracted_logic/logic/early_simulation_formulas.md`
  - Compact formula set worth preserving as early mechanics notes
  - Likely future bucket: `GUMAS_SIM_2.5/draft_logic`

- `text_early_logic.txt`
  - Extracted to `extracted_logic/logic/galactic_union_state_variables.md`
  - High-signal state-variable seed for simulation parameters
  - Likely future bucket: `GUMAS_SIM_2.5/draft_logic`

- `text_Au_mod_core.txt`
  - Extracted to `extracted_logic/blueprints/aurora_modular_core_v2_3.md`
  - Best late-version Aurora interface blueprint in this batch
  - Likely future bucket: `docs/draft_protocols`

- `text_Au_mod_core_first.txt`
  - Extracted to `extracted_logic/blueprints/aurora_modular_core_v2_1.md`
  - Early baseline for the modular core before later updates
  - Likely future bucket: `docs/draft_protocols`

- `text_GitIngestion.txt`
  - Extracted to `extracted_logic/blueprints/aurora_system_ingestion_pipeline_capsule_v1.md`
  - Useful logic blueprint for intake, parsing, and modular synthesis
  - Likely future bucket: `docs/draft_protocols`

- `text_Au_lite_agent.txt`
  - Extracted to `extracted_logic/blueprints/auroralite_bridge_agent.md`
  - Mixed JSON plus prompt scaffold for AuroraLite bridge behavior
  - Likely future bucket: `archives/prompt_recovery` or `docs/draft_protocols`

## Duplicate Clusters To Collapse

- `text_1.txt` == `text_3.txt`
- `text_13.txt` == `text_threadcore_3_6.txt`
- `text_152.txt` == `text_158.txt`
- `text_49.txt` == `text_50.txt`
- `text_58.txt` == `text_59.txt` == `text_threadcore_summon.txt`
- `text_72.txt` == `text_73.txt`

## Hold / Quarantine

- `text_AES_Key.txt`
  - Contains a recoverable script surface, but it presents as key-related material and should stay quarantined until reviewed

- `text_au_key.txt`
  - Key phrase / invocation content, not code to promote directly

- `text_core_auth.txt`
  - Auth or invocation fragment, keep out of extracted logic

- `text_conversation_PDK001.txt`
  - Long continuity/security-oriented transcript with key phrase content

- `text_master_sync.txt`
  - Review manually before reuse because it reads like governance/control logic rather than neutral implementation

- `text_79.txt`
  - Flagged by the analyzer for auth/sensitive review

## Archive-Likely Transcripts

- `text_16.txt`
- `text_25.txt`
- `text_26.txt`
- `text_gov_game.txt`

These look more like chat-session recovery artifacts than direct implementation files.
They may still contain ideas worth mining later, but they should not block the naming
pass for the stronger salvage set above.

## Worldbuilding Batch

- `text_factions_reg.txt`
- `text_L2_characters .txt`
- `text_characters_zylox.txt`
- `text_zylox_senario.txt`
- `text_GitThreadcore.txt`

These should probably be named together once we decide whether they belong in a
GUMAS draft worldbuilding lane, a THREADCORE continuity lane, or both.
