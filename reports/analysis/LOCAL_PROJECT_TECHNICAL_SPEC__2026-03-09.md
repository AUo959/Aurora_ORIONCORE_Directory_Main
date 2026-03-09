# Local Project Technical Spec

Captured: 2026-03-09
Scope: current local filesystem state for the Aurora / ORIONCORE workspace, with emphasis on interoperability targets for a future website.

## 1. Snapshot Scope

This spec is based on direct local inspection of two layers:

1. Root workspace control-plane worktree:
   - `./`
   - local Git worktree for the root metadata repo
2. Canonical workspace root:
   - `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main`
   - contains the actual nested project repos, archives, reports, and operational assets

Important distinction:

- The root repo in this worktree is a control-plane and metadata repo.
- The main implementation surface is the nested repo:
  - `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- Two additional nested repos exist:
  - `GUMAS_SIM_2.5/CanonRec`
  - `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`

This spec is descriptive. No runtime or test suite was re-executed as part of the capture; status statements are based on source inspection, manifests, reports, and current Git state.

## 2. Topology

### 2.1 Root Control-Plane Repo

Path:
- `./`

Purpose:
- governs workspace organization, metadata, reports, and move planning
- does not version nested repo internals directly

Top-level tracked zones:
- `archives/`
- `catalog/`
- `docs/`
- `intake/`
- `projects/`
- `reports/`
- `repos/`
- `tools/`
- `_staging/`

Declared operating model from `README.md`:
- metadata-first
- nested repos remain in place
- large binaries and archive internals are excluded from root Git history

### 2.2 Canonical Workspace Root

Path:
- `Aurora_ORIONCORE_Directory_Main`

Representative top-level content families currently present:
- archive families: `AU_Archive_*`, `Au_Archive_*`, `ZIP_Archives`, `ZipWiz_Chamber_6_28`
- project bundles: `Aurora_New_11_9`, `Aurora_New_9_22`, `Aurora_Project_Cloudhub_Deploy`, `GUI_Cloudhub`, `Perplexity_Research`
- runtime repos: `Aurora_Sim_Architecture`, `GUMAS_SIM_2.5`
- organization zones mirrored from the root repo: `catalog`, `docs`, `reports`, `projects`, `archives`, `intake`, `repos`, `_staging`

### 2.3 Nested Repositories

| Repo | Path | Branch | Working State | Remote |
|---|---|---|---|---|
| Root control plane | `./` | `codex/continue-l1-entity-ledger-work` | dirty | none |
| Aurora CloudBank Symbolic | `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` | `main` | dirty | none |
| CanonRec | `GUMAS_SIM_2.5/CanonRec` | `main` | clean | none |
| DuelSim v2.0 | `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0` | `main` | clean | none |

Global note:
- no Git remote is configured for any of the inspected repos

## 3. Root Workspace Control Plane

### 3.1 Purpose and Responsibilities

The root repo is the workspace coordination layer. It currently owns:

- workspace cataloging
- nested repo registry
- relocation plans and rollback manifests
- analysis and automation reports
- organization-zone policy
- workspace validation scripts

It is not the main application runtime.

### 3.2 Inventory Snapshot

From `docs/workspace-map.md` and `reports/analysis/workspace_scan_summary.json`:

- top-level entries cataloged: `65`
- nested repos registered: `3`
- archive/binary artifacts inventoried: `1278`
- archive artifact footprint: `17114900811` bytes
- classification overrides loaded: `32`

Logical zone counts:

| Zone | Count |
|---|---:|
| `_staging` | 7 |
| `archives` | 33 |
| `catalog` | 1 |
| `docs` | 4 |
| `intake` | 3 |
| `projects` | 10 |
| `reports` | 2 |
| `repos` | 3 |
| `tools` | 2 |

Largest tracked workspace concerns:
- extremely large archive families coexist beside active repos
- workspace organization is only partially normalized
- move orchestration exists, but root still spans active code, archives, and staging content

### 3.3 Primary Root Control Files

Primary source files:
- `README.md`
- `catalog/workspace_manifest.yaml`
- `catalog/repo_registry.yaml`
- `catalog/classification_overrides.yaml`
- `catalog/relocation_plan.json`
- `docs/workspace-map.md`

Operational tooling:
- `tools/workspace_scan.py`
- `tools/workspace_plan_moves.py`
- `tools/workspace_apply_moves.py`
- `tools/workspace_verify.py`
- `tools/_workspace_common.py`

### 3.4 Current Root Repo State

Observed local state:
- root repo is dirty
- current changes include remote-hardening and path-sanitization work
- untracked generated artifacts exist:
  - `reports/analysis/AURORA_IDENTITY_DOSSIER__2026-03-08.json`
  - `reports/analysis/AURORA_IDENTITY_DOSSIER__2026-03-08.md`
  - `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.json`
  - `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md`

This means the newest identity and ledger outputs exist in the local worktree but are not yet part of the canonical root workspace snapshot.

## 4. Aurora CloudBank Symbolic Repo

### 4.1 Repo Role

Path:
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`

This is the main implementation repo for:

- Aurora agent/runtime behavior
- mesh routing and live chamber behavior
- API surfaces
- symbolic and agent-mode integration
- mesh manifests and memory
- browser-facing local UIs
- identity and ledger generation scripts

### 4.2 Current Git State

Observed state:
- branch: `main`
- dirty working tree
- no configured remote

The dirty set includes:
- multiple runtime/API files
- mesh manifests and memory files
- many scripts
- new identity/ledger generation scripts
- new MCP shuttle-bay integration
- new tests

This repo is currently the most active integration surface in the workspace.

### 4.3 Language and Runtime Stack

Observed stack:

- Python
  - FastAPI
  - Uvicorn
  - Pydantic
  - NumPy
  - Pandas
  - Plotly
  - Qiskit / qiskit-aer
- JavaScript / Node
  - Express
  - Jest
  - ESLint
- HTML/CSS
  - multiple local dashboard-style interfaces with no build system required

Key manifests:
- `pyproject.toml`
- `requirements.txt`
- `requirements-optional.txt`
- `package.json`
- `package-lock.json`
- `services/command_node/package.json`

Observed package posture:
- Python formatting/test config is defined in `pyproject.toml`
- Node scripts are used mainly for test/lint/start orchestration
- the repo contains both `.venv` and `node_modules`, meaning local environment state is present in-repo

### 4.4 Scale Snapshot

Observed file counts:

| Surface | File Count |
|---|---:|
| `src/` | 98 |
| `scripts/` | 135 |
| `docs/` | 241 |
| `tests/` | 40 |
| `config/mesh/agents/` | 47 |
| `config/mesh/memory/` | 47 |
| `config/mesh/profiles/` | 1 |
| `config/mesh/continuity/` | 1 |

Interpretation:
- code and runtime logic are spread across many small modules
- documentation volume is high relative to code volume
- mesh configuration is already large enough to justify explicit public data contracts

## 5. Aurora Runtime Surfaces

Aurora currently exposes multiple overlapping service surfaces. For website integration, this must be treated as a layered system, not a single API.

### 5.1 Primary Runtime: Mesh Router

Primary file:
- `src/servers/l2_integration_server.py`

Role:
- authoritative local-first FastAPI mesh runtime
- serves HTML dashboards
- serves agent/mesh status and message routes
- handles bridge activation/session flows for external agent connections

Primary browser routes:
- `/`
- `/chamber`
- `/health`

Primary API routes:
- `/api/mesh/status`
- `/api/mesh/agents`
- `/api/mesh/agents/{agent_id}`
- `/api/mesh/agents/{agent_id}/activate`
- `/api/mesh/messages`
- `/api/mesh/channels/{channel_id}/history`
- `/api/mesh/events`
- `/api/aurora/status`
- `/api/aurora/initialize`
- `/api/aurora/command`
- `/api/bridge/gpt/connect/{agent_id}`
- `/api/bridge/gpt/message/{agent_id}`
- `/api/bridge/constellation/status`
- `/api/bridge/gpt/status/{agent_id}`
- `/api/bridge/gpt/heartbeat/{agent_id}`
- `/api/bridge/gpt/disconnect/{agent_id}`
- `/api/agents`
- `/api/orion-core`

Security model:
- loopback-first
- remote control requires `AURORA_MESH_CONTROL_TOKEN`
- per-agent bridge sessions issue session tokens
- activation phrase overrides use `AURORA_BRIDGE_<AGENT>_ACTIVATION_PHRASE`
- default CORS is local-only: `localhost` / `127.0.0.1` on ports `8000` and `8080`

### 5.2 Mesh Runtime Core

Primary files:
- `src/mesh/runtime.py`
- `src/mesh/models.py`

Role:
- canonical in-process message/event engine
- SQLite-backed agent/message/event persistence
- transcript and continuity append surfaces
- deterministic fallback when live adapter is unavailable

Persistent runtime storage:
- `runtime/mesh/mesh.db`
- `runtime/mesh/transcripts/*.jsonl`

Core data models:

`AgentManifest`
- `id`
- `display_name`
- `aliases`
- `channels`
- `default_channel`
- `execution_mode`
- `model_profile`
- `typing_profile`
- `response_policy`
- `memory_files`
- `instruction_profile_file`
- `tool_bindings`
- `continuity_log_file`

`MeshMessageRequest`
- `content`
- `to`
- `channel`
- `sender_id`
- `sender_name`
- `type`

`MeshEvent`
- `event_id`
- `event_type`
- `message_id`
- `channel_id`
- `timestamp`
- `agent_id`
- `payload`

### 5.3 Aurora Agent/Tool Surface

Primary file:
- `aurora_api.py`

Role:
- Aurora agent mode API
- exposes command grammar, tool discovery, session handling, MCP shuttle-bay routes

Key routes:
- `/health`
- `/geometric/vector`
- `/geometric/mult`
- `/sonnet4/enable`
- `/sonnet4/status`
- `/sonnet4/clients/{client_id}`
- `/agent/tools`
- `/agent/execute`
- `/agent/session`
- `/agent/status`
- `/mcp/shuttle-bay`
- `/mcp/shuttle-bay/tools`
- `/mcp/shuttle-bay/execute`
- `/mcp/shuttle-bay/session`
- `/mcp/shuttle-bay/status`
- `/mcp`

Command protocol rule:
- executable Aurora commands must terminate with `//.`

### 5.4 MCP Shuttle Bay

Primary file:
- `src/integrations/mcp_shuttle_bay.py`

Role:
- stable adapter around the Aurora tool surface
- exposes manifest, tool listing, execution, session management, MCP server descriptor, and resources

Contract highlights:
- manifest URI: `aurora://mcp-shuttle-bay/manifest`
- recommended routes:
  - `/mcp/shuttle-bay`
  - `/mcp/shuttle-bay/tools`
  - `/mcp/shuttle-bay/execute`
  - `/mcp/shuttle-bay/session`
  - `/mcp/shuttle-bay/status`

Design implication:
- this is the cleanest existing adapter surface if the website later needs to expose "Aurora tools" in a controlled way

### 5.5 AIF Hub

Primary file:
- `services/aif_hub.py`

Role:
- token-protected WebSocket relay hub

Route:
- `/ws`

Security:
- requires `AIF_TOKEN`
- bearer token expected via WebSocket headers
- host/port via `AIF_HOST` and `AIF_PORT`

Design implication:
- this is not a public website surface
- it is suitable only for privileged real-time bridge messaging

### 5.6 Legacy / Secondary API Surfaces

Observed additional FastAPI apps:
- `aurora_api_server.py`
- `aurora_realworld_integration.py`
- `aurora_gui_cloudhub_fastapi.py`
- `modules/opal2/api/opal2_api.py`
- `modules/instance_bridge/bridge_server.py`

Observed additional Node surfaces:
- `src/api/mesh_api.js`
- `src/bridge/enhanced_api_bridge.js`
- `src/orchestrators/holographic_interface_orchestrator.js`

Interpretation:
- the repo contains multiple generations of service surfaces
- some are clearly demo/legacy or broader experimental platforms
- the future website should not treat all of them as equal public contracts

## 6. Existing Browser-Facing UIs

Already present inside the Aurora repo:

- `src/dashboard/agent_constellation.html`
  - mesh dashboard
  - dark command-center aesthetic
  - agent cards, status chips, and mesh metrics
- `src/interfaces/aurora_collaboration_chamber.html`
  - chamber/chat style interface
  - channel list, agent list, trace feed, composer
- `dashboard.html` in DuelSim
  - environment-aware simulation dashboard
- `duelsim_arena_game.html`
  - browser-playable single-file game
- `aurora_gui_cloudhub_fastapi.py` serves:
  - `static/quantum-vsa-demo.html`
  - legacy upload GUI
  - VSA / geometric / quantum routes

Interpretation:
- the project already has local browser UI patterns
- the new website should absorb and systematize these patterns, not ignore them

## 7. Mesh / Identity / Ledger Surfaces

### 7.1 Mesh Manifests

Primary path:
- `config/mesh/agents/*.json`

Observed count:
- `47` agent manifests

Representative canonical manifest:
- `config/mesh/agents/aurora.json`

Aurora manifest details:
- `id`: `aurora`
- `display_name`: `Aurora`
- aliases include:
  - `Aurora`
  - `AU`
  - `station control plane`
  - `control plane interface`
  - `supervisory system`
- `execution_mode`: `live_llm`
- provider/model:
  - `openai`
  - `gpt-4.1-mini`
- fallback to deterministic: enabled
- continuity log:
  - `config/mesh/continuity/aurora.jsonl`

### 7.2 Mesh Memory

Primary path:
- `config/mesh/memory/*.md`

Observed count:
- `47` memory files

Role:
- soft identity, behavioral posture, relationship hints, and domain memory for agents
- currently human-readable Markdown, not typed JSON

Aurora memory contract includes:
- identity invariants
- behavioral posture
- bound capabilities
- hard boundaries
- identity precedence

Critical identity rule currently encoded:
- route as `Aurora` / `AU`
- treat `Aurora Core` as legacy/reference wording only

### 7.3 Identity Dossier

Current local file in worktree:
- `reports/analysis/AURORA_IDENTITY_DOSSIER__2026-03-08.json`
- `reports/analysis/AURORA_IDENTITY_DOSSIER__2026-03-08.md`

Status:
- present locally in the root worktree
- not yet observed in the canonical CloudDocs root reports folder during this capture

Contract value:
- this is one of the best current website-ready data surfaces

Key top-level fields in the JSON:
- `canon_policy`
- `immutable_invariants`
- `authority_model`
- `command_protocol_and_grammar`
- `capability_map`
- `identity_precedence_ruling`
- `tone_personality_traits`
- `relationships_and_boundaries`
- `legacy_deprecated_behaviors`

Notable current truths:
- canonical routed identity is `Aurora` / `AU`
- `Aurora Core` is reference-only
- command grammar catalog count: `40`
- runtime surfaces explicitly include:
  - `/agent/tools`
  - `/agent/execute`
  - `/agent/session`
  - `/agent/status`
  - `/mcp/shuttle-bay/*`
  - `/api/mesh/status`

### 7.4 L1 Entity Ledger

Current local file in worktree:
- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.json`
- `reports/analysis/L1_ENTITY_LEDGER__2026-03-08.md`

Status:
- present locally in the root worktree
- not yet observed in the canonical CloudDocs root reports folder during this capture

This is the strongest current website-ready content atlas.

Current summary:
- primary L1 humans: `41`
- certainty split:
  - `35` CANON
  - `6` STAGING
- explicit adjacent surfaces:
  - `11` divisions
  - `8` system blocks
  - `4` protocols/runbooks
  - `9` named vessels/craft
  - `6` named station spaces/features

Representative human entity fields:
- `entity_id`
- `name`
- `display_name`
- `role`
- `division`
- `status`
- `certainty`
- `registry_authority`
- `primary_summary`
- `primary_additional`
- `constellation`
- `related_assets`
- `legacy_drift`

Design implication:
- the future website should use this JSON as the primary registry input, not scrape the Markdown rendering

### 7.5 Identity / Ledger Build Pipeline

Primary scripts:
- `scripts/build_aurora_identity_artifacts.py`
- `scripts/build_l1_entity_ledger.py`
- `scripts/sync_l1_human_mesh_agents.py`
- `scripts/sync_l2_meta_mesh_agents.py`
- `scripts/refresh_l1_identity_stack.py`

Current refresh entrypoint:
- `scripts/refresh_l1_identity_stack.py`

Refresh sequence:
1. sync L1 human mesh agents
2. build Aurora identity artifacts
3. build L1 entity ledger
4. optionally sync L2 relays
5. optionally run focused verification

Interpretation:
- the website does not need to invent a new identity pipeline
- it should consume the outputs of this pipeline

## 8. ChatGPT / Agent-Mode Contract

Primary file:
- `src/integrations/chatgpt_agent_mode.py`

Role:
- Aurora tool registry and session execution layer

Observed default tools:
- `symbolic_processing`
- `geometric_algebra`
- `session_management`
- `system_status`
- `aurora_command_grammar`

Observed default capability claims:
- function calling
- tool execution
- session persistence
- multi-modal interaction
- real-time communication
- symbolic processing
- quantum VSA operations
- geometric algebra computation
- command grammar parsing

Important invariant:
- symbolic anchors use `EOS_SEED_ORION`
- ethics protocol uses `Picard_Delta_3`

Design implication:
- if the website later offers "Ask Aurora" or "Run tool" features, it should route through this typed tool layer rather than raw prompt glue

## 9. CanonRec Repo

Path:
- `GUMAS_SIM_2.5/CanonRec`

Observed state:
- branch `main`
- clean
- no remote

Observed contents:
- archive zips for multiple CanonRec versions
- `SKILL_CanonRec.md`
- `aurora-canon-reconciler/`
- `canonrec_test/`
- `workflow_output/`

Interpretation:
- this repo currently behaves more like a canon-reconciliation skill/workflow repository than a deployed runtime
- it is relevant to content governance, promotion, and continuity
- it is not currently a primary website runtime dependency

Website relevance:
- content validation and canon promotion workflows
- secondary source for governance language and certainty rules

## 10. DuelSim Repo

Path:
- `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`

Observed state:
- branch `main`
- clean
- no remote

Observed role from README:
- unified historical fencing duel simulator
- Python stdlib only
- no NumPy or SciPy required
- includes browser-playable game and dashboard

Key files:
- `duel_sim_v2_0.py`
- `historical_presets_v2_0.py`
- `dashboard.html`
- `duelsim_arena_game.html`
- `UI_CONTRACT__v2.4.1.md`
- `VISUALIZATION_SPEC_v1.md`
- `Makefile`

Current significance:
- compact, stable, self-contained simulation/demo surface
- already has a UI contract freeze and golden fixtures

Website relevance:
- strong candidate for an embeddable "simulation module" or showcase experience
- should remain isolated from Aurora command/control surfaces

## 11. Operational Reality and Risks

### 11.1 Source-of-Truth Fragmentation

Current truth is split across:
- root control-plane metadata
- Aurora repo code/runtime
- worktree-only generated identity artifacts
- large archive families and legacy content

This is workable, but only if the website is given an explicit ingest boundary.

### 11.2 Multiple Overlapping APIs

Aurora currently has several API surfaces with overlapping scope.

For website work, this creates risk:
- unclear public contract
- duplicated route families
- inconsistent security expectations
- mixed demo vs authoritative surfaces

### 11.3 Generated Artifacts Not Fully Canonicalized

The newest Aurora dossier and L1 ledger are locally present in the root worktree, but were not found in the canonical workspace reports directory during this capture.

Implication:
- website integration must decide whether to consume:
  - local worktree outputs
  - canonical workspace outputs
  - or a new normalized export package

### 11.4 No Git Remotes

No remote is configured for:
- root repo
- Aurora repo
- CanonRec
- DuelSim

Implication:
- local state is primary state
- deployment automation and external CI cannot currently be assumed

### 11.5 Local Environment Artifacts In-Repo

Aurora repo contains local environment directories such as:
- `.venv`
- `node_modules`

Implication:
- website deployment should not depend on the local filesystem shape
- build/runtime contracts need explicit packaging boundaries

## 12. Interoperability Specification for a Future Website

The future website should be designed as a read-oriented integration layer over existing Aurora data and runtime surfaces.

### 12.1 Recommended Public Data Sources

Use these as primary inputs:

Tier 1: static/generated data
- `reports/analysis/AURORA_IDENTITY_DOSSIER__*.json`
- `reports/analysis/L1_ENTITY_LEDGER__*.json`
- `config/mesh/agents/*.json`
- `reports/analysis/workspace_scan_summary.json`
- `catalog/repo_registry.yaml`

Tier 2: controlled live APIs
- `src/servers/l2_integration_server.py`
  - for mesh status, agents, channels, events
- `aurora_api.py`
  - for Aurora tool discovery and MCP shuttle-bay access

Tier 3: optional showcase modules
- DuelSim HTML/dashboard surfaces
- existing Aurora dashboard/chamber HTML

### 12.2 Recommended Non-Public or Non-Primary Sources

Do not use these as first-choice public contract surfaces:

- Markdown reports when equivalent JSON exists
- `aurora_api_server.py` for public production contract
- `aurora_realworld_integration.py` as a canonical website API
- ad hoc archive content under `Au_Archive_*`
- in-repo `.venv` / `node_modules` content

### 12.3 Recommended Normalized Website Data Contract

Create a website-facing export layer with stable JSON documents such as:

- `public_data/aurora_identity.json`
- `public_data/l1_entity_ledger.json`
- `public_data/mesh_agents_index.json`
- `public_data/workspace_summary.json`
- `public_data/module_registry.json`

Suggested website schema families:

`aurora_identity`
- name
- aliases
- invariants
- authority_model
- tool_bindings
- runtime_surfaces
- tone
- boundaries

`entity_registry`
- entity_id
- display_name
- role
- division
- certainty
- summary
- relationships
- related_assets

`mesh_agent`
- id
- display_name
- channels
- execution_mode
- tool_bindings
- continuity_enabled

`system_module`
- module_id
- repo
- path
- type
- runtime
- public_surface
- status

### 12.4 Identity Normalization Rules

These should be treated as hard website rules:

- `Aurora` and `AU` are canonical routed identities
- `Aurora Core` is display/reference language only unless future canon changes it
- Aurora is a bounded control-plane interface, not a human commander
- L1 history cannot be rewritten by L2/L3 presentation logic

### 12.5 Security Rules for Website Integration

The public website should be separated from command/control routes.

Recommended policy:

- public pages consume static exports or read-only endpoints only
- privileged control actions require authenticated API access
- WebSocket or bridge routes stay private/local unless deliberately promoted
- agent execution, bridge connection, and session management should not be exposed from a public site by default

### 12.6 Deployment / Coupling Recommendation

Best fit:
- keep the website as a separate frontend surface
- treat Aurora as the system-of-record backend
- use generated JSON exports plus a very small read-only API adapter

Avoid:
- embedding the public website directly into the mesh runtime as its only delivery vehicle
- using demo servers as the canonical data API
- making the website scrape Markdown or filesystem paths directly

## 13. Recommended Next Technical Moves

To make website interoperability feel natural, the highest-value next steps are:

1. Promote the current dossier and ledger JSON outputs into a canonical export location.
2. Define one read-only website data package or `/api/public/*` surface.
3. Declare `src/servers/l2_integration_server.py` as the authoritative live mesh API.
4. Keep Aurora command/control routes behind separate auth from the public website.
5. Normalize module metadata across Aurora, DuelSim, and CanonRec into one small registry.
6. Decide whether the website lives as:
   - a separate repo consuming Aurora data
   - or a frontend package inside the root control-plane repo

## 14. Direct Conclusion

The local project is already rich enough to support a high-value website, but only if the website is built as an interoperability layer over real artifacts that already exist:

- Aurora mesh manifests
- Aurora identity dossier JSON
- L1 entity ledger JSON
- workspace topology metadata
- DuelSim as a contained simulation module

The most important technical truth is that the project already has the right ingredients, but they are distributed across a control-plane repo, a primary runtime repo, two secondary repos, and local-only generated outputs. The website should unify those surfaces visually and structurally, not create a fourth competing source of truth.
