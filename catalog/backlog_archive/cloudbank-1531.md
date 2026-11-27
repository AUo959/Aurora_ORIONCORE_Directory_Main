# aurora-cloudbank-symbolic#1531: feat(edusim): recover governed participatory Game experience over GUMAS

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1531
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T03:04:14Z
- Updated: 2026-08-18T03:07:06Z
- Labels: backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- none

## Branches named in the issue

- none

## Original body

## Lineage

Focused salvage/recovery follow-up related to:

- #1526 — provenance-aware corpus archaeology and intent recovery;
- current GUMAS/L2 simulation architecture;
- current Narrative River causal-continuity workflow;
- current Playground as a separate developer experimentation surface;
- retained legacy configs:
  - `config/examples/Aurora_GameMode_Module_v1.0.json`
  - `config/examples/Aurora_GameEngine_EduSim_v1.0.json`

## Recovered design intent

Native Aurora architecture defined a **Game Mode** as an interactive experience for one or more participants, with an emphasis on engaging educational simulation rather than unrestricted system control.

Two repository artifacts preserve a concrete version of that intent.

`Aurora_GameMode_Module_v1.0.json` describes:

- Level-2 educational simulation;
- cascading startup questions;
- adaptive game-mode selection;
- MLTM/multilingual support;
- target audience of middle-school multilingual learners;
- RPG, classwide simulation, puzzle quest, civics timeline, and environmental/social-justice simulation formats.

`Aurora_GameEngine_EduSim_v1.0.json` further specifies:

- full-class and individual modes;
- adaptive clue systems;
- dynamic role assignment;
- branching narratives;
- era navigation;
- multilingual awareness and translation toggle;
- middle-school age calibration;
- puzzle, RPG, class simulation, story-adventure, and exploration formats.

Both configs reference loader/runtime dependencies such as `aurora_gamemode_loader.py`, `aurora_game_engine_loader.py`, and `aurora_mltm_runtime.py`. Targeted current-repository search in this salvage pass did not locate those runtime entry points. The configs therefore appear to be preserved design/compatibility artifacts rather than an active implementation.

## Recovery interpretation

Do **not** restore a global historical `Game Mode` switch or resurrect missing loaders blindly.

The durable capability is better expressed as a governed **participatory L2 simulation experience adapter** over current GUMAS and continuity infrastructure.

```text
participant/session request
        ↓
experience profile
  - audience / age support
  - individual or group
  - accessibility / language
  - scenario format
  - role selection
        ↓
GUMAS/L2 scenario boundary
        ↓
participant choices / observations
        ↓
deterministic or explicitly seeded simulation transitions
        ↓
continuity / consequence projection
        ↓
participant-facing output
```

The experience layer should adapt presentation and interaction. It must not create a second simulation authority.

## Architectural separation

- **GUMAS/L2** owns simulation/world causality.
- **Game experience adapter** owns participant session structure, role/choice presentation, pedagogical scaffolding, and accessibility/language options.
- **Narrative River** may provide scene/continuity projection where prose-driven experiences use it.
- **RiverCycle** (#1528) may provide persistent pressure/feedback state once implemented.
- **CanonRec/Git** remain canon authorities.
- **Playground** remains the developer code-experimentation surface; it is not the educational game runtime.
- **Pilot** remains the Earth-side institutional L1 operator role and must not be silently converted into a player avatar.

## Participant model

The first modern contract should distinguish participant identity, role, session state, and simulated character/entity identity.

A participant may control or advise a simulated role without becoming L1 canon or acquiring real institutional authority.

Suggested concepts:

```yaml
experience_session:
  session_id: string
  experience_profile: string
  participant_mode: individual | group
  participant_refs: []
  language_preferences: []
  accessibility_preferences: {}
  scenario_ref: string
  simulation_run_ref: string | null
  persistence_class: ephemeral | resumable | project_persistent
```

```yaml
participant_assignment:
  participant_ref: string
  simulated_role_ref: string | null
  permissions: []
  objectives: []
  available_information: []
```

Exact names should reuse existing schemas where available.

## Educational/gameplay invariants

1. **Presentation must not become causality.** A hint, simplified explanation, or UI choice does not secretly alter GUMAS state unless an explicit simulation action results.
2. **Difficulty is not falsification.** Accessibility/age calibration may change wording, scaffolding, timing, or information presentation but must not silently rewrite underlying evidence/state.
3. **Participant knowledge is bounded.** Players receive only the information their session/role is allowed to observe.
4. **Role assignment is explicit.** A participant does not inherit real or simulated authority merely because the UI addresses them by a role name.
5. **Consequences persist when the underlying run persists.** Ending a class period, scene, or UI session must not imply that unresolved simulation state disappeared.
6. **Group participation remains attributable.** Where multiple participants contribute choices, the system should preserve which participant/role supplied which input when appropriate.
7. **Branching is state-driven.** Branches arise from choices and simulation state, not hidden narrative favoritism.
8. **Language support preserves meaning.** Translation/scaffolding should retain provenance and avoid silently converting uncertain claims into facts.
9. **No automatic canon promotion.** Educational run outcomes remain L2 run state unless separately reviewed.
10. **Fun does not override safety/ethics boundaries.** Game framing does not weaken the L1/L2/L3 or real/simulated authority model.

## Relationship to the old configs

Treat the retained JSON files as lineage evidence and migration fixtures.

A compatibility adapter may eventually parse their durable fields, but unsupported/deprecated fields should produce an explicit migration report rather than synthetic success.

The missing historical loader names should not be recreated merely to satisfy the filenames.

## Phase 0 — lineage and reuse report

Before implementation, map the old config capabilities against current systems:

- GUMAS scenario/runtime contracts;
- Narrative River;
- current participant/session/auth primitives, if any;
- current translation/accessibility utilities, if any;
- Playground boundaries;
- L1 Pilot/mesh boundaries;
- current persistence and run-state contracts.

Classify each historical capability as:

- preserved by a current subsystem;
- partial successor;
- orphaned;
- obsolete;
- requires evidence/review.

## Phase 1 — deterministic thin vertical slice

Implement one minimal experience profile without requiring a model/network dependency.

Suggested fixture:

1. create an individual or small-group L2 session;
2. select from two or more simulated roles;
3. expose role-bounded information;
4. accept a participant choice;
5. route it to a deterministic prepared GUMAS fixture or governed simulation adapter;
6. preserve consequence/state across a second interaction;
7. render age-appropriate participant output from the same underlying state;
8. emit a machine-readable session receipt;
9. perform no L1/canon mutation.

A multilingual presentation fixture can follow in the same phase if a trustworthy current translation boundary already exists; otherwise specify the contract first.

## Acceptance criteria

- [ ] Historical GameMode/EduSim artifacts are explicitly classified as lineage inputs, not current runtime proof.
- [ ] Missing historical loaders are not silently recreated as placeholders.
- [ ] The modern experience adapter is downstream of GUMAS rather than a duplicate simulation engine.
- [ ] Individual and group session semantics are representable.
- [ ] Participant identity and simulated role/entity identity remain distinct.
- [ ] Role-bounded knowledge is preserved.
- [ ] Participant choices have attributable, explicit simulation effects.
- [ ] Session/class-period boundaries do not erase persistent underlying consequence.
- [ ] Accessibility/age/language presentation cannot alter underlying simulation truth silently.
- [ ] Fixed fixture inputs produce deterministic transition results under the declared equivalence contract.
- [ ] No L1 authority, Pilot embodiment, or canon promotion occurs from game participation.
- [ ] A session receipt records scenario/run lineage, participant assignments, inputs, outputs, and persistence state.
- [ ] At least one legacy config can be analyzed into a migration/compatibility report.

## Non-goals

- rebuilding every historical game format at once;
- creating a monolithic new game engine;
- restoring missing loaders verbatim;
- making the Playground the game runtime;
- turning Pilot into a player avatar;
- replacing GUMAS;
- automatic curriculum grading in Phase 1;
- automatic canon promotion;
- sacrificing simulation integrity for engagement.

## Design principle

**Make the simulation playable without making the world play to the participant.**


## Comments (0)
