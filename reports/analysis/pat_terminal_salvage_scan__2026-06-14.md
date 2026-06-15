# PAT Terminal Salvage Scan - 2026-06-14

## Scope

This scan looked for PATs as Personal Access Terminals, related terminal-routing
design, and existing implementation surfaces. It also records the acronym
collision with PAT as Personnel Attention Tags so future promotion work does not
collapse two different abstractions.

No canon, runtime, or nested repo files were changed by this scan.

## Evidence Sources

### Early terminal design packet

- `archives/session_archives/Au_Archive_323_41/GUMAS_Project_Instructions.txt`
  - Defines the GUMAS simulation framework and lists `GUMAS_Team_Culture_Charter.html`
    as the source for terminal behavior and ethics logic.
  - Explicitly expects terminal personalization and interaction logs per character.
- `archives/session_archives/Au_Archive_323_41/GUMAS_Team_Culture_Charter.html`
  - States that live terminal messages are open to all team members and that
    anyone can ping anyone, including the Pilot.
  - Frames terminal structure as part of the culture layer, not only UI chrome.
- `archives/session_archives/Au_Archive_323_41/GUMAS_Terminal_Routing_and_Namespace.json`
  - Preserves `dev.*`, `sim.*`, and `aurora.core` routing namespaces.
  - Separates developer commands from simulation commands and routes unknown
    commands through Aurora with layer awareness.
- `archives/session_archives/Au_Archive_323_41/The_Pilot_Terminal_Shell.html`
  - Prototype implementation for the Pilot terminal shell.
  - Links `Aurora Core`, `MMR`, `PAT Shells`, and `Command Broadcast Layer`.
- `archives/session_archives/Au_Archive_323_41/filtered_galactic_union_conversations.json`
  - Recovered conversation text marks `All-Terminal Communication Protocol`
    enabled, `PAT Communications Layer` online/active, Aurora terminal shells
    in rollout, and the Pilot terminal as containing active comm logs and direct
    Aurora command relay.

### Later PAT operational overlay

- `archives/structured_archives/AURORA_GUMAS_PAT_LIVE_SUBSET_SSOT__v0.1.0__2026-03-14__STRUCTURED_ARCHIVE.zip`
  - Unique archive in `catalog/archive_inventory.jsonl`.
  - Contains a 9-person PAT live subset with profiles, anchor groups, alignment
    matrix, and resolution log.
  - Its readme states the PAT subset is an operational routing layer and should
    ride on top of the full staff registry.
  - Its resolution log says canonical identity comes from the staff SSOT while
    PAT contributes only `pat_role`, `status`, `visibility`, `anchor_node`, and
    `thread`.
  - Anchor groups:
    - `aurora.dev.code.query`: Carmen Rivas, Ira Menon, Tobias Qin
    - `aurora.rnd.crossdomain.query`: Dr. Amina Velin, Haneul Park, Kai Drev
    - `aurora.rnd.self.query`: Dr. Elira Noor, Maren Koss, Vincent Kale

### Current owner surfaces

- CloudBank mesh runtime:
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/config/mesh/agents/*.json`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/mesh/models.py`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/mesh/manifests.py`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/mesh/runtime.py`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/servers/l2_integration_server.py`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/interfaces/aurora_collaboration_chamber.html`
- CloudBank crew-agent runtime:
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/agents/crew/base_agent.py`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/modules/crew_agents/api.py`
- CanonRec:
  - `GUMAS_SIM_2.5/CanonRec/canon/L1/station/ORION_STATION_CANONICAL_STAFF_REGISTRY.json`
  - `GUMAS_SIM_2.5/CanonRec/canon/L1/station/staging_2026-04/ORION__CANON__L1_ENTITY_REGISTRY__v2.0__2026-04-08.md`
  - `GUMAS_SIM_2.5/CanonRec/canon/L1/station/staging_2026-04/ORION__CANON__ORION_STATION_ENVIRONMENT__v2.0__2026-04-08.md`
  - `GUMAS_SIM_2.5/CanonRec/canon/L1/station/reference_sources/orion_station_technical_addendum_equipment_and_personnel.md`
  - `GUMAS_SIM_2.5/CanonRec/canon/L1/station/operational_library_v2_2/ORION__L1_DISPATCH_PROTOCOL__v1.1.md`

## Current-State Read

CloudBank already has the live communication substrate:

- 47 mesh agent manifests with `id`, `display_name`, `aliases`, `channels`,
  `default_channel`, `execution_mode`, memory files, model profile, and response
  policy.
- Private crew channels such as `private:crew:carmen_rivas`.
- Runtime target resolution by agent id, alias, channel, or default channel.
- API endpoints for mesh status, messages, channel history, events, and agents.
- Chamber UI that exposes channels as broadcast/direct lines and agents as
  direct targets.

CloudBank does not currently preserve the terminal abstraction:

- No `terminal_id`.
- No `terminal_namespace` such as `{department}.{firstname}.term`.
- No PAT overlay fields: `pat_role`, `visibility`, `anchor_node`, `thread`.
- No terminal personalization settings.
- No per-terminal interaction log abstraction beyond mesh channel transcripts.
- No all-terminal compatibility route that treats terminal aliases as first-class.

CanonRec has two PAT-related signals that must stay distinct:

- Personal Access Terminal model: identified in the station environment staging
  file as enhancement/proposal-layer material, useful for simulation behavior
  and interface design, but not settled environment canon by default.
- Personnel Attention Tags: a separate EVA/HUD communication format in the
  technical addendum, with syntax like `{{@Carmen-Rivas:::message}}`. This is
  not the same thing as Personal Access Terminals.

The current L1 dispatch protocol is intentionally minimal: dispatch fields and
logging only. It does not own terminal identity, terminal routing, or PAT shell
behavior.

## L1 Reality Mapping Constraint

The PAT terminal bridge should map to L1 reality, not only to the recovered
9-person PAT overlay.

CanonRec's L1 entity registry describes the station cast as layered rather than
flat:

- 35 safely reconstructable human L1 staff.
- 1 unresolved declared human slot that must remain visible rather than invented.
- Aurora as the station AI core.
- 6 L2 relays.
- 6 L3 frameworks.
- Legacy core staff preserved where later machine-readable normalization is
  weaker.

The station environment packet also says major functional clusters belong to
particular decks rather than treating all staff as placeless, and that L2 relays
and L3 frameworks are embedded in the station operating environment rather than
being only abstract software labels.

Current CloudBank mesh evidence shows 41 private/captain human-like channels and
6 direct runtime nodes. That is close to the desired access model, but it is not
yet an L1 terminal model because it lacks a terminal-owner class, source posture,
location/workstation semantics, and reconciliation against CanonRec's layered
entity classes.

Promotion rule:

- Every named L1 human crew member that is canonical, canonical-machine-readable,
  or preserved legacy seed should have a coherent terminal profile when a
  matching CloudBank mesh agent exists.
- The unresolved L1 human slot should be represented as `unresolved`, not filled.
- Aurora, L2 relays, and L3 frameworks may have terminal-like access surfaces,
  but they must not be counted as human crew terminals.
- A terminal profile should be anchored to L1 station reality with at least:
  owner class, CanonRec entity/source pointer, station layer, terminal namespace,
  mesh route, and optional physical/workstation context when known.
- Broader PAT-heavy station behavior remains proposal-layer until separately
  promoted.

## Salvage Verdict

Carry forward the PAT terminal abstraction, but only as a CloudBank mesh bridge
and compatibility layer at first.

Do not promote the full PAT-heavy station interaction model into CanonRec
environment canon yet. CanonRec already warns that this is proposal-layer
material unless adopted by a higher-priority source.

Do not replace CloudBank mesh with PATs. The correct shape is:

```text
CanonRec L1 entity / staff identity
  -> L1 terminal profile
  -> CloudBank mesh agent manifest
  -> mesh channel / direct target / transcript
```

The recovered value is not a new agent system. It is the missing terminal entity
between crew identity and mesh routing.

## Missing Behaviors Worth Carrying Forward

1. Terminal identity overlay
   - `terminal_id`
   - `owner_agent_id`
   - `owner_display_name`
   - `owner_class`: `human_l1`, `ai_core`, `l2_relay`, `l3_framework`,
     `legacy_seed`, or `unresolved`
   - `canon_entity_id` or source pointer when available
   - `l1_station_layer`
   - `terminal_namespace`
   - `terminal_type` such as `pilot`, `crew`, `aurora`, or `system`
   - optional `station_context` for deck, office, duty post, or workstation
     when the source actually states it

2. PAT routing overlay
   - `pat_role`
   - `status`
   - `visibility`
   - `anchor_node`
   - optional `thread`
   - source evidence pointer back to the PAT live subset archive

3. Legacy namespace aliases
   - `{department}.{firstname}.term`
   - `aurora.dev.code.query`
   - `aurora.rnd.crossdomain.query`
   - `aurora.rnd.self.query`
   - `dev.*`, `sim.*`, and `aurora.core` routing concepts as compatibility
     aliases, not command-execution approval.

4. Terminal personalization
   - optional theme/title/status widgets from the Pilot terminal shell
   - owner-specific panels for active comm logs and direct Aurora relay
   - no hard dependency on the old HTML shell

5. Interaction logging by terminal
   - mesh transcripts already exist per channel.
   - the missing behavior is a terminal-level view/index that can show which
     terminal received, sent, or relayed a message.

6. Acronym disambiguation
   - Personal Access Terminals and Personnel Attention Tags need explicit test
     coverage so a future parser does not route EVA HUD tags as terminal ids.

## Tests Worth Adding

Add focused CloudBank tests rather than broad UI snapshots first:

1. `tests/test_mesh_pat_terminals.py`
   - Loads the PAT terminal registry.
   - Confirms the 9 PAT records are present.
   - Confirms Carmen, Ira, and Tobias share `aurora.dev.code.query`.
   - Confirms `core_development.carmen.term` and `aurora.dev.code.query`
     resolve to the expected mesh agent ids or terminal group.
   - Confirms PAT subset records are an overlay on broader L1 terminal profiles,
     not the full terminal universe.

2. `tests/test_mesh_runtime_surface.py`
   - Confirms `MeshRuntime.get_terminal(...)` resolves by terminal id,
     namespace, owner alias, and anchor node.
   - Confirms sending to a terminal alias routes through the owner's existing
     `default_channel`.
   - Confirms every materialized human L1 terminal with a mesh agent has a
     routable channel.

3. `tests/test_mesh_runtime_api_surface.py`
   - Adds `GET /api/mesh/terminals`.
   - Adds `GET /api/mesh/terminals/{terminal_id}`.
   - Optionally adds `POST /api/mesh/messages` with `to` set to a terminal
     namespace.

4. Negative parser test
   - Confirms a Personnel Attention Tag string such as
     `{{@Carmen-Rivas:::message}}` is not treated as a Personal Access Terminal
     id by default.

5. L1 reconciliation test
   - Confirms human L1, AI core, L2 relay, and L3 framework records stay in
     separate owner classes.
   - Confirms the unresolved human slot is represented explicitly and does not
     create a fake routable person.

## Promotion-Safe Next Edits

Implement in the nested CloudBank repo on a branch. Do not mutate CanonRec until
CloudBank has a tested compatibility layer.

Concrete next edit set:

1. Add terminal models:
   - `src/mesh/terminals.py`
   - Define `PersonalTerminalProfile` and helpers for id/alias normalization.
   - Include owner class and CanonRec source fields so terminal profiles map to
     L1 reality before routing.

2. Add terminal registry data:
   - `config/mesh/terminals/l1_terminal_registry.v1.json`
   - Seed it from the existing CloudBank mesh agents plus CanonRec's L1 entity
     registry, preserving source posture.
   - Include `config/mesh/terminals/pat_live_subset.v1.json` as an overlay or
     subsection, not as the whole registry.
   - Extract the 9 PAT profiles from
     `AURORA_GUMAS_PAT_LIVE_SUBSET_SSOT__v0.1.0__2026-03-14__STRUCTURED_ARCHIVE.zip`.
   - Store source pointers, not just normalized fields.

3. Wire runtime loading:
   - Update `src/mesh/runtime.py` to load terminal profiles alongside agent
     manifests.
   - Add `list_terminals()`, `get_terminal(...)`, and terminal-aware target
     resolution.
   - Preserve existing agent/channel behavior.

4. Expose API routes:
   - Update `src/servers/l2_integration_server.py`.
   - Add `GET /api/mesh/terminals`.
   - Add `GET /api/mesh/terminals/{terminal_id}`.

5. Add tests:
   - `tests/test_mesh_pat_terminals.py`
   - `tests/test_mesh_l1_terminal_registry.py`
   - Extend existing mesh runtime/API tests only where needed.

6. Optional UI follow-up:
   - Update `src/interfaces/aurora_collaboration_chamber.html` to show terminal
     metadata in the agent drawer after the API contract is stable.

7. CanonRec follow-up only after CloudBank tests pass:
   - Add a short operational-library note that the PAT terminal bridge exists
     as runtime/interface compatibility.
   - Keep the broader PAT-heavy station interaction model marked proposal-layer
     unless explicitly promoted.

## Non-Carry-Forward Items

- Do not carry forward the old Pilot terminal shell as production UI unchanged.
  It is useful as a prototype and evidence source only.
- Do not import the entire recovered conversation JSON into runtime.
- Do not parse Personnel Attention Tags as Personal Access Terminal routes.
- Do not hand-edit generated root control surfaces for this scan.

## Bottom Line

The terminal abstraction was not lost completely. It survives in three layers:

1. Early terminal-shell and terminal-routing design in `Au_Archive_323_41`.
2. A later 9-person PAT live subset SSOT with operational routing overlays.
3. Current CloudBank mesh agents/channels that can own the runtime bridge.

The missing piece is a first-class L1 terminal profile registry that binds crew
identity, station/source posture, PAT overlay metadata, and mesh routes without
overwriting canonical staff identity or replacing the mesh runtime. The registry
must let each L1 crew member access their terminal coherently while keeping
Aurora, relays, frameworks, legacy seeds, and unresolved slots in their proper
classes.
