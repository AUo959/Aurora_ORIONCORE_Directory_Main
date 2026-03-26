# Deep Triage Queue

This queue is the second-pass importance sort for the recovered root text batch.
It is intended to drive the next naming and routing work.

## Immediate Hold

Do not route these into operational folders until someone reviews the control-surface or auth implications.

- `text_oppy_node.txt` -> `_entropy_quarantine or catalog/draft_manifests` [config_manifest; score `132`] Control-surface artifact with command or authority markers; review before any routing.
- `text_56.txt` -> `_entropy_quarantine or catalog/draft_manifests` [config_manifest; score `130`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v2.txt` -> `_entropy_quarantine or catalog/draft_manifests` [javascript_module; score `129`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v3.txt` -> `_entropy_quarantine or catalog/draft_manifests` [javascript_module; score `125`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v4.txt` -> `_entropy_quarantine or catalog/draft_manifests` [javascript_module; score `125`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v5.txt` -> `_entropy_quarantine or catalog/draft_manifests` [javascript_module; score `125`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v6.txt` -> `_entropy_quarantine or catalog/draft_manifests` [javascript_module; score `125`] Control-surface artifact with command or authority markers; review before any routing.
- `text_44.txt` -> `_entropy_quarantine or catalog/draft_manifests` [javascript_module; score `124`] Control-surface artifact with command or authority markers; review before any routing.
- `text_AES_Key.txt` -> `_entropy_quarantine` [sensitive_or_auth; score `108`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_conversation_PDK001.txt` -> `_entropy_quarantine` [sensitive_or_auth; score `104`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_core_auth.txt` -> `_entropy_quarantine` [sensitive_or_auth; score `104`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_79.txt` -> `_entropy_quarantine` [sensitive_or_auth; score `102`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_au_key.txt` -> `_entropy_quarantine` [sensitive_or_auth; score `96`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_master_sync.txt` -> `_entropy_quarantine` [sensitive_or_auth; score `96`] High-risk auth or key-like material requiring quarantine before reuse.

## Immediate Salvage

These are the strongest code or protocol recoveries to name and place next.

- `text_15.txt` -> `tools/prototypes/javascript` [javascript_module; score `120`] Directly reusable code or protocol surface with strong salvage value.
- `text_tagging_agent.txt` -> `tools/prototypes/python` [python_prototype; score `120`] Directly reusable code or protocol surface with strong salvage value.
- `text_thread_tag.txt` -> `tools/prototypes/python` [python_prototype; score `120`] Directly reusable code or protocol surface with strong salvage value.
- `text_52.txt` -> `tools/prototypes/python` [python_prototype; score `119`] Directly reusable code or protocol surface with strong salvage value.
- `text_mem_system.txt` -> `tools/prototypes/python` [python_prototype; score `119`] Directly reusable code or protocol surface with strong salvage value.
- `text_mem_system_py.txt` -> `tools/prototypes/python` [python_prototype; score `119`] Directly reusable code or protocol surface with strong salvage value.
- `text_24.txt` -> `tools/prototypes/python` [python_prototype; score `118`] Directly reusable code or protocol surface with strong salvage value.
- `text_Au_mod_core.txt` -> `docs/draft_protocols` [blueprint_or_protocol; score `112`] Directly reusable code or protocol surface with strong salvage value.
- `text_Au_mod_core_first.txt` -> `docs/draft_protocols` [blueprint_or_protocol; score `111`] Directly reusable code or protocol surface with strong salvage value.
- `text_GitIngestion.txt` -> `docs/draft_protocols` [blueprint_or_protocol; score `108`] Directly reusable code or protocol surface with strong salvage value.
- `text_13.txt` -> `tools/prototypes/javascript` [javascript_module; score `97`] Directly reusable code or protocol surface with strong salvage value.
- `text_threadcore_3_6.txt` -> `tools/prototypes/javascript` [javascript_module; score `97`] Directly reusable code or protocol surface with strong salvage value.
- `text_symbiosis_graft.txt` -> `tools/prototypes/python` [prompt_template_or_agent; score `54`] Executable patch-graft script with concrete file mutations and anchor binding; preserve as a recovered prototype and do not run unreviewed.

## Canon And Logic Follow-Up

These should feed worldbuilding, mechanics, or reconciliation passes soon after the immediate salvage set.

- `text_157.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `121`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_155.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `119`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_162.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `117`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_early_logic.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `117`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_159.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `114`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_L2_characters .txt` -> `GUMAS_SIM_2.5/draft_worldbuilding` [worldbuilding_registry; score `112`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_characters_zylox.txt` -> `GUMAS_SIM_2.5/draft_worldbuilding` [worldbuilding_registry; score `112`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_27.txt` -> `GUMAS_SIM_2.5/draft_worldbuilding` [worldbuilding_registry; score `109`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_160.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `108`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_GitThreadcore.txt` -> `GUMAS_SIM_2.5/draft_worldbuilding` [worldbuilding_registry; score `108`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_factions_reg.txt` -> `GUMAS_SIM_2.5/draft_worldbuilding` [worldbuilding_registry; score `108`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_161.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `105`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_early_sim_logic.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `105`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_152.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `86`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_158.txt` -> `GUMAS_SIM_2.5/draft_logic` [simulation_logic; score `86`] High-value worldbuilding or mechanics material that should feed canon or logic reconciliation next.
- `text_Au_Shuttlecraft.txt` -> `GUMAS_SIM_2.5/draft_worldbuilding or docs/draft_protocols` [prompt_template_or_agent; score `57`] Structured shuttlecraft registry with named agents, manifests, and thread bindings; treat as worldbuilding or protocol follow-up, not prompt residue.
- `text_42.txt` -> `GUMAS_SIM_2.5/draft_worldbuilding or docs/draft_protocols` [fragment_or_note; score `16`] Symbiosis module graft capsule bundles named ecosystem modules and continuity bindings; treat as worldbuilding and continuity follow-up.
- `text_Orion_Crew.txt` -> `reports/analysis/canon_support or L1 recovery corpus` [fragment_or_note; score `16`] Recovered L1 crew registry already proved useful for character reconciliation and should remain elevated for canon follow-up.

## Ops Recovery

These are structured manifests worth preserving after the first two tiers.

- `Text_109.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `116`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_archy_core.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `116`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_62.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `115`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_Riverthread_Relay.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `115`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_fluentia_v1.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `115`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_team_charter.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `115`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_38.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `114`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_34.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `113`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_31.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `112`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_54.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `112`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_55.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `112`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_105.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `111`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_111.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `111`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_58 2.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `111`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_archy_relay.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `111`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_starling_relay.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `111`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_eos_agent.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `110`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_112.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `109`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_37.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `109`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.
- `text_Vector_Chain_Seed.txt` -> `catalog/draft_manifests or .github/workflows` [config_manifest; score `109`] Structured manifest or config fragment worth preserving, but not ahead of code and canon material.

