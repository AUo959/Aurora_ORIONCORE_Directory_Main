# Deep Importance Triage

Generated: `2026-03-21T21:57:35Z`

This pass revisits the recovered root text batch with a deeper importance model.
It separates high-value salvage from high-risk control surfaces so that the next
naming pass does not confuse importance with safety.

## Summary

- Artifacts reviewed: `244`
- P0 critical-risk hold: `14`
- P1 critical salvage: `13`
- P2 canon and logic follow-up: `18`
- P3 ops and config recovery: `75`
- P4 context archive: `50`
- P5 low residue: `74`

## Notes

- P0 means important because it can affect control surfaces, invocation paths, or auth-like behavior.
- P1 means important because the artifact is directly reusable code or a protocol surface worth preserving quickly.
- P2 means important because it should feed canon or mechanics reconciliation, even if it is not executable code.

## P0 Critical-Risk Hold

- `text_oppy_node.txt` -> `config_manifest` [score `132`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_56.txt` -> `config_manifest` [score `130`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v2.txt` -> `javascript_module` [score `129`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v3.txt` -> `javascript_module` [score `125`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v4.txt` -> `javascript_module` [score `125`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v5.txt` -> `javascript_module` [score `125`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_CN_v6.txt` -> `javascript_module` [score `125`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_44.txt` -> `javascript_module` [score `124`; destination `_entropy_quarantine or catalog/draft_manifests`] Control-surface artifact with command or authority markers; review before any routing.
- `text_AES_Key.txt` -> `sensitive_or_auth` [score `108`; destination `_entropy_quarantine`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_conversation_PDK001.txt` -> `sensitive_or_auth` [score `104`; destination `_entropy_quarantine`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_core_auth.txt` -> `sensitive_or_auth` [score `104`; destination `_entropy_quarantine`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_79.txt` -> `sensitive_or_auth` [score `102`; destination `_entropy_quarantine`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_au_key.txt` -> `sensitive_or_auth` [score `96`; destination `_entropy_quarantine`] High-risk auth or key-like material requiring quarantine before reuse.
- `text_master_sync.txt` -> `sensitive_or_auth` [score `96`; destination `_entropy_quarantine`] High-risk auth or key-like material requiring quarantine before reuse.

## P1 Critical Salvage

- `text_15.txt` -> `javascript_module` [score `120`; destination `tools/prototypes/javascript`] first line: `/**`
- `text_tagging_agent.txt` -> `python_prototype` [score `120`; destination `tools/prototypes/python`] first line: `# Drop-In Thread Context Tagging Agent`
- `text_thread_tag.txt` -> `python_prototype` [score `120`; destination `tools/prototypes/python`] first line: `# 🔍 Drop-In Thread Context Tagging Agent v2.0`
- `text_52.txt` -> `python_prototype` [score `119`; destination `tools/prototypes/python`] first line: `# ORION DEPLOYMENT CONTROLLER :: Master Deployment Orchestration Module`
- `text_mem_system.txt` -> `python_prototype` [score `119`; destination `tools/prototypes/python`] first line: `class MemorySystem:`
- `text_mem_system_py.txt` -> `python_prototype` [score `119`; destination `tools/prototypes/python`] first line: `# memory_system.py`
- `text_24.txt` -> `python_prototype` [score `118`; destination `tools/prototypes/python`] first line: `# Symbolic_ModelSelector_ThreadSense`
- `text_Au_mod_core.txt` -> `blueprint_or_protocol` [score `112`; destination `docs/draft_protocols`] first line: `🧬 **AURORA MODULAR CORE | Update to Simulation Middleware Interface Blueprint**`
- `text_Au_mod_core_first.txt` -> `blueprint_or_protocol` [score `111`; destination `docs/draft_protocols`] first line: `AURORA MODULAR CORE — GUMAS Interface GPT`
- `text_GitIngestion.txt` -> `blueprint_or_protocol` [score `108`; destination `docs/draft_protocols`] first line: `🚀 ACKNOWLEDGED — GENERATING SYSTEM INGESTION / PARSING / MODULAR SYNTHESIS CAPSULE`
- `text_13.txt` -> `javascript_module` [score `97`; destination `tools/prototypes/javascript`] first line: `/**`
- `text_threadcore_3_6.txt` -> `javascript_module` [score `97`; destination `tools/prototypes/javascript`] first line: `/**`
- `text_symbiosis_graft.txt` -> `prompt_template_or_agent` [score `54`; destination `tools/prototypes/python`] first line: `# 🧩 SYMBIOSIS GRAFT – Threadcore Injection (v1.0.1)`

## P2 Canon And Logic Follow-Up

- `text_157.txt` -> `simulation_logic` [score `121`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding,security_sensitive,git_deploy`
- `text_155.txt` -> `simulation_logic` [score `119`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding,memory_system,security_sensitive`
- `text_162.txt` -> `simulation_logic` [score `117`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding,memory_system,threadcore_continuity`
- `text_early_logic.txt` -> `simulation_logic` [score `117`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding,git_deploy,memory_system`
- `text_159.txt` -> `simulation_logic` [score `114`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding,memory_system,git_deploy`
- `text_L2_characters .txt` -> `worldbuilding_registry` [score `112`; destination `GUMAS_SIM_2.5/draft_worldbuilding`] themes: `gumas_worldbuilding,research_education,security_sensitive`
- `text_characters_zylox.txt` -> `worldbuilding_registry` [score `112`; destination `GUMAS_SIM_2.5/draft_worldbuilding`] themes: `gumas_worldbuilding,git_deploy,security_sensitive`
- `text_27.txt` -> `worldbuilding_registry` [score `109`; destination `GUMAS_SIM_2.5/draft_worldbuilding`] themes: `threadcore_continuity,memory_system,prompt_agent`
- `text_160.txt` -> `simulation_logic` [score `108`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding,memory_system,research_education`
- `text_GitThreadcore.txt` -> `worldbuilding_registry` [score `108`; destination `GUMAS_SIM_2.5/draft_worldbuilding`] themes: `threadcore_continuity,git_deploy,gumas_worldbuilding`
- `text_factions_reg.txt` -> `worldbuilding_registry` [score `108`; destination `GUMAS_SIM_2.5/draft_worldbuilding`] themes: `gumas_worldbuilding,memory_system,research_education`
- `text_161.txt` -> `simulation_logic` [score `105`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `git_deploy,gumas_worldbuilding`
- `text_early_sim_logic.txt` -> `simulation_logic` [score `105`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `gumas_worldbuilding`
- `text_152.txt` -> `simulation_logic` [score `86`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `memory_system,gumas_worldbuilding,research_education`
- `text_158.txt` -> `simulation_logic` [score `86`; destination `GUMAS_SIM_2.5/draft_logic`] themes: `memory_system,gumas_worldbuilding,research_education`
- `text_Au_Shuttlecraft.txt` -> `prompt_template_or_agent` [score `57`; destination `GUMAS_SIM_2.5/draft_worldbuilding or docs/draft_protocols`] themes: `memory_system,prompt_agent,aurora_interface`
- `text_42.txt` -> `fragment_or_note` [score `16`; destination `GUMAS_SIM_2.5/draft_worldbuilding or docs/draft_protocols`] themes: `threadcore_continuity,aurora_interface,memory_system`
- `text_Orion_Crew.txt` -> `fragment_or_note` [score `16`; destination `reports/analysis/canon_support or L1 recovery corpus`] themes: `threadcore_continuity,aurora_interface,memory_system`

## P3 Ops And Config Recovery

- `Text_109.txt` [score `116`] destination `catalog/draft_manifests or .github/workflows`
- `text_archy_core.txt` [score `116`] destination `catalog/draft_manifests or .github/workflows`
- `text_62.txt` [score `115`] destination `catalog/draft_manifests or .github/workflows`
- `text_Riverthread_Relay.txt` [score `115`] destination `catalog/draft_manifests or .github/workflows`
- `text_fluentia_v1.txt` [score `115`] destination `catalog/draft_manifests or .github/workflows`
- `text_team_charter.txt` [score `115`] destination `catalog/draft_manifests or .github/workflows`
- `text_38.txt` [score `114`] destination `catalog/draft_manifests or .github/workflows`
- `text_34.txt` [score `113`] destination `catalog/draft_manifests or .github/workflows`
- `text_31.txt` [score `112`] destination `catalog/draft_manifests or .github/workflows`
- `text_54.txt` [score `112`] destination `catalog/draft_manifests or .github/workflows`
- `text_55.txt` [score `112`] destination `catalog/draft_manifests or .github/workflows`
- `text_105.txt` [score `111`] destination `catalog/draft_manifests or .github/workflows`
- `text_111.txt` [score `111`] destination `catalog/draft_manifests or .github/workflows`
- `text_58 2.txt` [score `111`] destination `catalog/draft_manifests or .github/workflows`
- `text_archy_relay.txt` [score `111`] destination `catalog/draft_manifests or .github/workflows`

## P4 And P5 Snapshot

- Review-for-naming or archive-context artifacts: `50`
- Low-signal residue artifacts: `74`
- Original first-pass actions still map to: `{'archive_or_discard': 91, 'dedupe_then_review': 13, 'extract_and_route': 88, 'quarantine_and_review': 6, 'review_for_naming': 46}`

## Outputs

- `importance_triage__2026-03-20.json`
- `importance_triage__2026-03-20.csv`
- `DEEP_TRIAGE_QUEUE__2026-03-20.md`
