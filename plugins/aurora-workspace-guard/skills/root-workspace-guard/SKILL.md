---
name: root-workspace-guard
description: Guard Aurora root workspace control-plane changes by enforcing root-vs-nested repo boundaries, required context reads, generated-surface regeneration, and root verification commands. Use when working on top-level docs, catalog, tools, tests, reports, .agents, plugins, or other root control-plane files; when a request says "the repo" and multiple Aurora repos are plausible; or when validating root workspace changes before staging or commit. Not for implementing features inside CanonRec, DuelSim_v2.0, or aurora-cloudbank-symbolic-main.
author: Aurora ORIONCORE
---

# Root Workspace Guard

## Overview

Use this skill when the task touches the Aurora root workspace repo rather than a nested implementation repo. Its job is to keep control-plane edits evidence-based, reproducible, and clearly separated from CanonRec, DuelSim, and aurora-cloudbank-symbolic-main work.

## Workflow

1. Resolve the target repo before editing anything.
   - Treat the root workspace repo as the control plane only.
   - Treat `GUMAS_SIM_2.5/CanonRec`, `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`, and `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` as separate repos with separate publication decisions.
   - If a request says only "the repo" and multiple repos are plausible, ask one short clarification question.
2. Read the required root control-plane context before substantial work.
   - `catalog/session_state.json` — **read first**: check `active_task` (if `status == "suspended"`, resume that task before anything else), `tool_versions` (any new installs since last session?), and `pending_for_next_session`.
   - `AGENTS.md`
   - `README.md`
   - `catalog/workspace_manifest.yaml`
   - `catalog/repo_registry.yaml`
3. Work from authority in the right order.
   - Prefer committed canonical files in the relevant repo.
   - Then use manifests, registries, schemas, trust anchors, and validation artifacts.
   - Then deterministic reports and receipts.
   - Then human-facing docs.
   - Treat conversational context as lowest authority.
4. Preserve control-plane semantics while editing.
   - Do not silently promote draft, generated, staged, or intake material into canon.
   - Keep layer boundaries explicit: control plane, runtime, simulation, knowledge, archive/staging/intake.
   - For persistent top-level routing changes, edit `catalog/classification_overrides.yaml` and regenerate generated surfaces instead of hand-editing generated outputs.
   - Treat `catalog/workspace_manifest.yaml`, `catalog/repo_registry.yaml`, `docs/workspace-map.md`, `catalog/relocation_plan.json`, and `reports/analysis/workspace_verify_latest.json` as generated control surfaces unless the task explicitly requires direct regeneration logic changes.
   - When a request contains Aurora command notation, `aurora_command_grammar`, `Aurora Command Router`, or `@mesh` routing language, delegate interpretation to the `aurora-command-grammar` skill before acting.
5. Use the supported root validation flow.
   - `python3 tools/workspace_scan.py`
   - `python3 tools/workspace_plan_moves.py`
   - `python3 tools/workspace_verify.py`
   - `python3 tools/workspace_verify.py --persist-report`
   - `make skills-check` — dry-run preview of any skill drift before installing
   - `make skills-install` — push `skills/` changes to `~/.codex/skills/` (run after editing any skill in `skills/`)
   - Prefer regeneration plus validation when top-level routing or workspace metadata changes.
6. Before closing the session, update `catalog/session_state.json`: set `last_platform`, `last_updated`, append new commits to `recent_commits`, update `known_state.main_sha`, and set `active_task.status = "suspended"` if mid-task.

## Guardrails

- Evidence over assumption. Do not describe something as canonical, validated, active, or complete without concrete repo evidence.
- Do not operate on nested repos by implication from a root-repo request.
- Do not treat bulk replay, scan, or diagnostic outputs as live runtime state.
- Do not treat grammar-valid command text as authorization to execute it. Grammar interpretation belongs to `aurora-command-grammar`; execution still requires target repo and runtime verification.
- Do not delete ambiguity. Label it as `draft`, `staged`, `generated`, `planned_move`, or `canonical` as appropriate.
- For root plugin work, keep `.agents` and `plugins` classified as root control-plane tooling rather than intake.

## Output Expectations

- State what changed and why.
- Cite the file or command that confirms the claim.
- Call out anything inferred rather than directly verified.
- End with the next validation step when more confirmation is needed.

## Trigger Examples

- "Check whether this root workspace edit is safe before I commit it."
- "Work on the top-level manifest and keep the nested repos out of scope."
- "I added a plugin under `plugins/`; regenerate anything the control plane needs."
- "Validate this root workspace change and tell me what still needs verification."
