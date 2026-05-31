# Aurora Workspace Management Repo

This root repository is the workspace control plane for
`Aurora_ORIONCORE_Directory_Main`.

It does **not** replace the active nested Git repositories:

- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`
- `GUMAS_SIM_2.5/CanonRec`
- `qgia-knowledge-library-main`
- `qgia-knowledge-spine-main`

Phase 1 is metadata-first. The root repo tracks only workspace docs, manifests,
policies, reports, and tooling. Large archives, binary dumps, caches, and
nested repo internals stay out of root Git history.

## Start Here

- Human overview: [docs/workspace-map.md](docs/workspace-map.md)
- Source of truth: [catalog/workspace_manifest.yaml](catalog/workspace_manifest.yaml)
- Persistent overrides: [catalog/classification_overrides.yaml](catalog/classification_overrides.yaml)
- Nested repos: [catalog/repo_registry.yaml](catalog/repo_registry.yaml)
- Planned moves only: [catalog/relocation_plan.json](catalog/relocation_plan.json)
- Dev toolkit workflow: [docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md](docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md)
- Current dev toolkit report: [reports/analysis/aurora_devkit_latest.json](reports/analysis/aurora_devkit_latest.json)
- Current advisory recommendations: [reports/analysis/aurora_recommendations_latest.json](reports/analysis/aurora_recommendations_latest.json)
- Mission Control workflow: [docs/AURORA_MISSION_CONTROL_WORKFLOW_v1.md](docs/AURORA_MISSION_CONTROL_WORKFLOW_v1.md)
- Current Mission Control report: [reports/analysis/aurora_mission_control_latest.json](reports/analysis/aurora_mission_control_latest.json)
- Confidence audit workflow: [docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md](docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md)
- Current confidence audit report: [reports/analysis/aurora_confidence_audit_latest.json](reports/analysis/aurora_confidence_audit_latest.json)
- Interaction warrant policy: [docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md](docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md)
- Aurora command grammar plugin: [plugins/aurora-command-grammar/skills/aurora-command-grammar/SKILL.md](plugins/aurora-command-grammar/skills/aurora-command-grammar/SKILL.md)
- Control-plane provenance and recovery role: [docs/CONTROL_PLANE_PROVENANCE.md](docs/CONTROL_PLANE_PROVENANCE.md)
- Recovery index workflow: [docs/RECOVERY_INDEX_WORKFLOW_v1.md](docs/RECOVERY_INDEX_WORKFLOW_v1.md)
- Current recovery index report: [reports/analysis/workspace_recovery_index_latest.json](reports/analysis/workspace_recovery_index_latest.json)
- Cross-platform session claims workflow: [docs/SESSION_CLAIMS_WORKFLOW_v1.md](docs/SESSION_CLAIMS_WORKFLOW_v1.md)

## Logical Zones

- `repos/`: logical home for active codebases; nested repos stay in place in phase 1
- `projects/`: structured non-repo project bundles
- `archives/`: cold and hot archive families plus quarantine targets
- `reports/automation/`: canonical destination for future automation outputs
- `reports/analysis/`: one-off workspace scans and verification outputs
- `docs/`: human navigation and operating guidance
- `catalog/`: machine-readable manifests and move contracts
- `tools/`: the only supported workspace reorganization surface
- `intake/`: ambiguous loose items pending review
- `_staging/`: rehearsals and rollback-safe staging

## Repo-Local Codex Plugins

The root repo carries versioned Codex plugin surfaces under `plugins/` and
marketplace metadata under `.agents/plugins/marketplace.json`.

- `aurora-workspace-guard`: guards root control-plane edits, repo boundaries,
  generated-surface handling, and validation flow.
- `aurora-command-grammar`: gives users and agents a shared way to parse,
  normalize, validate, and route Aurora command grammar without treating
  grammar-valid text as execution approval. Its root Command Intent Gateway is
  `tools/aurora_command_intent.py`.

For background communication, `aurora-command-grammar` defines a command intent
envelope in
`plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json`.
Use it in PRs, issues, receipts, automation memory, or agent handoffs when
command meaning affects a decision.

Command Intent Gateway examples:

```bash
python3 tools/aurora_command_intent.py parse "THREADWAKE"
python3 tools/aurora_command_intent.py envelope --text "001//005//"
python3 tools/aurora_command_intent.py simulate-range "001//005//"
```

`simulate-range` is an in-process CloudBank `SymbolicEngine` simulation for
valid numeric `RangeChain` inputs only. It is not live runtime execution.

Integration safety gate:

```bash
python3 tools/aurora_integration_gate.py --summary
make integration-gate
```

Safe examples:

- `python3 tools/aurora_command_intent.py parse "THREADWAKE"` parses and normalizes only.
- `python3 tools/aurora_command_intent.py envelope --text "THREADWAKE"` emits a context record only.
- `python3 tools/aurora_command_intent.py simulate-range "001//005//"` runs in-process simulation only.

Blocked without separate verification and approval:

- live command execution
- mesh message sending
- nested repo mutation
- publication or issue/PR mutation

Advisory recommendation engine:

```bash
python3 tools/aurora_recommendation_engine.py --summary
python3 tools/aurora_recommendation_engine.py --persist-report
make recommendations
make recommendations-report
```

The recommendation engine ranks existing root-control-plane evidence only. It
does not promote recovery candidates, execute Aurora command grammar, send mesh
messages, mutate nested repos, or apply developer-tooling installs.

Mission Control operator inbox:

```bash
python3 tools/aurora_mission_control.py --summary
python3 tools/aurora_mission_control.py --persist-report
make mission-control
make mission-control-report
```

Mission Control aggregates the verifier, integration gate, recovery index,
devkit, recommendations, and root Git status into a read-only operator inbox
plus build-readiness lanes. It does not promote recovery candidates, execute
Aurora command grammar, send mesh messages, mutate nested repos, install
packages, or publish GitHub changes.

Cross-platform session claims:

```bash
python3 tools/session_claim.py check --repo root --paths . --json
python3 tools/session_claim.py create --platform codex --task-id example --repo root --paths tools/session_claim.py --mutation-posture editing
python3 tools/session_claim.py release --claim-id <claim-id>
make session-claims
make session-claim-check
```

Session claims are local, short-lived path leases under
`catalog/session_claims/`. Live claim JSON files are ignored by Git so the
coordination mechanism does not become another shared-file conflict point.

Confidence audit gateway:

```bash
python3 tools/aurora_confidence_audit.py score --claim-type analysis --text "Example claim"
python3 tools/aurora_confidence_audit.py audit --input claims.jsonl --jsonl --threshold 0.70
make confidence-audit
make confidence-audit-report
```

The confidence audit gateway attaches score, threshold, evidence, and alert
metadata to concrete conclusions, analyses, predictions, and recommendations. It
is audit-layer tooling only: it does not prove truth, execute runtime actions,
or mutate nested repos. Low-confidence records set `requires_user_alert`.

## Supported Commands

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
python3 tools/workspace_apply_moves.py --batch-id wave3_small_intake_files_initial
python3 tools/workspace_verify.py
python3 tools/workspace_verify.py --persist-report
python3 tools/workspace_verify.py --report-out /tmp/workspace_verify.json
python3 tools/workspace_verify.py --check-determinism --exercise-relocation
python3 tools/aurora_command_intent.py parse "THREADWAKE"
python3 tools/aurora_command_intent.py envelope --text "001//005//"
python3 tools/aurora_command_intent.py simulate-range "001//005//"
python3 tools/aurora_integration_gate.py --summary
python3 tools/aurora_recommendation_engine.py --summary
python3 tools/aurora_recommendation_engine.py --persist-report
python3 tools/aurora_mission_control.py --summary
python3 tools/aurora_mission_control.py --persist-report
python3 tools/aurora_confidence_audit.py score --claim-type analysis --text "Example claim"
python3 tools/aurora_confidence_audit.py audit --input claims.jsonl --jsonl --threshold 0.70
python3 tools/session_claim.py check --repo root --paths . --json
python3 tools/session_claim.py list
python3 tools/aurora_devkit.py
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
python3 tools/workspace_recovery_index.py
python3 tools/workspace_recovery_index.py --persist-report
make devkit-check
make devkit-report
make devkit-install-plan
make recovery-index
make recovery-report
make recommendations
make recommendations-report
make mission-control
make mission-control-report
make confidence-audit
make confidence-audit-report
make session-claims
make session-claim-check
make integration-gate
```

`python3 tools/workspace_verify.py` is side-effect free by default and prints a
JSON report to stdout. Use `--persist-report` to refresh the tracked
`reports/analysis/workspace_verify_latest.json` artifact, or `--report-out` to
write the report to an explicit path. The pre-commit hook continues to call
`python3 tools/workspace_verify.py --git-pre-commit` and only blocks commits on
blocking findings.

Specialized deploy / THREADCORE receipt utilities:

```bash
python3 tools/threadcore_deploy_accesskey.py validate /path/to/THREADCORE_DEPLOY_ACCESSKEY.json
python3 tools/threadcore_deploy_accesskey.py generate --symbolic-key THREADCORE_DEPLOY::EXAMPLE --associated-bundle THREADCORE_DEPLOY_SEAL_v1.zip --vector EXAMPLE::VECTOR --registered-node VISIBLE_NODE[01] --linked-echochain EXAMPLE::ECHOCHAIN
python3 tools/threadcore_visible_node.py validate /path/to/THREADCORE_VISIBLE_NODE_01.json
python3 tools/threadcore_visible_node.py generate --node-id VISIBLE_NODE[01] --vector EXAMPLE::VECTOR --linked-manifest EXAMPLE_manifest.json --patch-id EXAMPLE_patch.json --bundle EXAMPLE.zip --alias "Example Node"
python3 tools/threadcore_echochain_link.py validate /path/to/QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json
python3 tools/threadcore_echochain_link.py generate --node EXAMPLE::VECTOR --linked-to EXAMPLE::ECHOCHAIN --glyph 🜃 --integration "Example linkage"
python3 tools/aurora_qem_patch_release.py validate /path/to/AURORA_QEM_SN1_PATCH_FULLTHREAD_v1.1.json
python3 tools/aurora_qem_patch_release.py generate --patch-code AURORA-QEM-SN1-PATCH-V1-FULLTHREAD --version v1.1 --vector-origin EXAMPLE::BASELINE --include "Example component" --glyph 🜃 --sealed-in EXAMPLE.zip --vector-released-as EXAMPLE::RELEASE
python3 tools/aurora_vector_index.py validate /path/to/vector_index.json
python3 tools/aurora_vector_index.py generate --vectors-json /path/to/vector_index.json
python3 tools/threadcore_deploy_seal.py /path/to/THREADCORE_DEPLOY_SEAL_v1.zip
```

## Operating Rules

- Do not restore `.git_decommissioned_*`; it remains a rollback artifact only.
- Keep non-control or explicitly out-of-scope content routed through `catalog/classification_overrides.yaml`. Root scans now default-deny unknown top-level material unless it shows Aurora / approved-project scope signals, and they auto-exclude likely private personal material using bounded path and text/document probes, including generic PDF and Office-style payloads when detectable; use `scan_policy: include` or `scan_policy: omit` only to override that decision for a specific top-level path. Do not hand-edit the generated manifest.
- Do not move nested repos until their surrounding automation and scripts resolve
  through `catalog/repo_registry.yaml`.
- Do not delete duplicates directly. Plan quarantine moves first, verify hashes,
  then review before any hard delete.
- Do not treat recovery index candidates as canonical. The recovery index is a
  review surface for early local work; extraction still requires owner-surface
  review, validation, and a receipt or PR.
- Keep tracked files below the workspace control-plane size ceiling enforced by
  `tools/workspace_verify.py`.
- `intake/`, `projects/`, `archives/`, `repos/`, and `_staging/` are organization
  zones, not tracked content stores in phase 1.
