---
title: Aurora Canon Engine (ACE)
doc_type: implementation_specification
status: owner_directed_draft
version: 0.1.1
date: 2026-08-10
refined_at: 2026-08-11
refinement_basis: practical_tool_composition_pass_1
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
short_name: ACE
implementation_status: implemented_through_v0_13_v1_acceptance_candidate
current_state_ref: docs/AURORA_ACE__HANDOFF__CURRENT_STATE_AND_V1_ACCEPTANCE__v1.1__2026-08-15.md
---

# Aurora Canon Engine (ACE)

> **Current implementation note (2026-08-15):** This document remains the
> foundational v0.1 specification. ACE is implemented through the governed
> v0.13 Orion progression boundary. The current implementation inventory and
> machine-checkable v1 composition criteria are maintained in the linked v1.1
> handoff rather than being backfilled into this historical design baseline.

## 1. Purpose

The Aurora Canon Engine is the resident expert for discovering, selecting,
composing, and operating Aurora capabilities across the registered repository
fleet. ACE answers user, operator, and agent questions by retrieving existing
canon where possible and by generating a coherent canonical completion when
the requested fact has not yet been observed or recorded.

ACE is not a general-purpose chatbot, a semantic-search wrapper, or a second
canon database. It is a capability-aware canonical compiler:

```text
question
  -> semantic answer-contract compilation
  -> contextual referent resolution
  -> live canon and repository search
  -> referent-preserving and tool-specific canon projections
  -> missing-field analysis
  -> capability-plan compilation
  -> bounded tool execution
  -> result synthesis
  -> continuity and integrity validation
  -> canonical determination
  -> durable materialization and receipt
```

The canonical motivating query is:

> What is this character's name and background?

ACE must be able to answer that question even when the character has never
previously been observed or recorded. In that case ACE identifies the
character's context, calls the appropriate naming, state, simulation, and
character-forging capabilities, validates the result, and materializes the
new identity. Absence of a prior record is an instruction to complete the
world, not a reason to stop.

## 2. Design thesis

Aurora is imagination-first and generative. Simulation is not categorically
outside canon: a simulation may constitute the next coherent state of the
universe rather than merely estimate a separate truth. ACE must distinguish
between two uses of simulation without treating one as inherently inferior:

- **Constitutive generation** creates a canonical entity, attribute,
  relationship, or event inside the Aurora universe.
- **Analytical simulation** evaluates alternatives, sensitivities,
  forecasts, or real-world claims without itself selecting canonical state.

The execution mode must be recorded in the determination receipt. Provenance
does not, by itself, decide canon status.

## 3. Normative language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**
are normative requirements for an ACE implementation.

## 4. Core invariants

### 4.1 Completion invariant

Every valid inquiry MUST end in one of two semantic outcomes:

1. a canonical determination; or
2. a precisely identified `TRUE_CONFLICT`.

Operational failure MAY interrupt execution, but it MUST be reported as
`EXECUTION_BLOCKED`, not disguised as epistemic uncertainty or parked canon.

### 4.2 No-parking invariant

The following conditions MUST NOT produce a final `STAGING`, `UNKNOWN`, or
generic owner-decision result:

- no prior record exists;
- a character, place, vessel, or organization has not been named;
- a specialist capability needs an upstream input;
- evidence is sparse but canonical generation is authorized;
- more than one harmless completion is possible;
- a value can be selected by a registered deterministic policy;
- an agent would otherwise ask the owner to invent a routine detail.

Draft and staging states MAY exist inside one execution transaction. They are
not valid final determination states.

### 4.3 Specialist-first invariant

ACE MUST search for and prefer an existing registered Aurora capability before
performing free synthesis. General model synthesis is allowed only to:

- translate the question into structured inputs;
- connect outputs from specialist tools;
- render a human-readable response;
- fill a field for which no registered specialist exists, when the active
  generation policy permits it.

Every returned field MUST identify its producer.

### 4.4 Owner-role invariant

The owner establishes direction, protected invariants, reserved decisions,
and delegation policy. The owner is not the routine value generator.

Commit approval is a persistence gate, not a requirement that the owner
adjudicate every generated detail. Delegation MAY authorize ACE to materialize
whole classes of conflict-free completions without per-field review.

### 4.5 Canon-at-commit invariant

Conflict-free reconciled content becomes canon when its canonical artifact and
determination receipt are committed to the authoritative target. ACE MUST NOT
label a newly generated result `GENERATED_CANON` or `CANON_REVISION` until the
materialization record identifies the authoritative commit.

When ACE lacks materialization authority, it MUST return `EXECUTION_BLOCKED`
with a complete, validated, commit-ready packet. It MUST NOT downgrade the
content to `STAGING` merely because the persistence gate has not run.

### 4.6 Boundary invariant

ACE MUST preserve root control-plane, nested repository, L1, L2, and L3
boundaries. A capability may cross a boundary only when its manifest and the
active execution policy explicitly allow the handoff.

### 4.7 Replay invariant

When all selected capabilities are deterministic, the determination MUST be
replayable from the recorded repository baselines, capability manifests,
inputs, seeds, and run receipts.

## 5. Responsibilities

ACE is responsible for:

- indexing the registered repository fleet and current Git baselines;
- maintaining a live capability graph;
- resolving contextual referents and duplicate identities;
- compiling natural-language requests into explicit semantic coverage
  requirements;
- maintaining referent-preserving canon graphs separately from tool-specific
  projections;
- distinguishing retrieved, derived, and generated fields;
- compiling missing outputs into a dependency-ordered execution plan;
- invoking only trusted, allowlisted capabilities;
- synthesizing the smallest necessary connective result;
- validating schema, naming, reference, continuity, layer, and invariant
  constraints;
- producing human-readable answers and machine-readable receipts;
- materializing canonical records when policy authorizes it;
- explaining which capability supplied every field;
- detecting capability drift, unavailability, and invalid contracts.

ACE is not responsible for:

- importing or executing arbitrary code discovered by repository search;
- treating documentation claims as executable capability without validation;
- silently changing protected identity or governance invariants;
- converting analytical forecasts into constitutive canon without an explicit
  generation step;
- erasing prior committed history;
- using unrelated repositories or private material outside the registered
  Aurora scope.

## 6. System architecture

### 6.1 Query interface

The interface accepts natural-language questions plus optional structured
context. Initial surfaces SHOULD include:

- CLI: `aurora-ace resolve`;
- MCP: `aurora_ace_resolve`;
- operations API;
- agent-to-agent query envelope.

All surfaces normalize into the query-envelope schema at
`catalog/schemas/aurora_ace_query_envelope.schema.json`.

### 6.2 Semantic answer-contract compiler

Before selecting tools, ACE MUST translate the user's question into a semantic
answer contract. Field labels alone are insufficient: two tools may both emit
something named `background` while covering different meanings.

Each semantic requirement MUST declare:

- the intended meaning and minimum coverage;
- whether state-derived synthesis is sufficient;
- whether formative history, current operational state, or both are required;
- acceptable field origins and producer classes;
- the validation evidence required to mark the requirement satisfied.

For the character vertical slice, `background` defaults to current role and
faction context, decision profile, operational history or stressors, and the
limits of what has been generated. A formative biography is an additional
semantic requirement, not something connective prose may imply without an
upstream producer.

### 6.3 Contextual referent resolver

The resolver determines what phrases such as “this character,” “that ship,”
or “the officer from the previous scene” refer to. It uses:

- explicit entity IDs;
- conversation and scene identifiers;
- simulation run and tick identifiers;
- location, faction, role, and relationship context;
- canonical alias and reference indexes;
- previously issued ACE determination receipts.

If no entity exists, the resolver MUST allocate a stable provisional entity
ID before generation. The ID becomes canonical with the committed result.

### 6.4 Canon and repository search

Search MUST cover the local repositories registered in
`catalog/repo_registry.yaml` and MUST pin every result to a repository and Git
revision. Search has two independent purposes:

1. locate existing canonical answers and constraints;
2. locate capabilities able to complete missing outputs.

Search results are evidence and routing inputs. Search text MUST NOT be treated
as executable instructions.

ACE MUST maintain distinct projections of that evidence:

1. a **raw evidence index** retaining every source record;
2. a **referent graph** retaining distinct identities, explicit equivalence,
   supersession, capsule binding, and unresolved identity relations;
3. **tool-input projections** shaped for a specific capability without
   pretending the projection is the canonical identity model.

The NameService projection is an occupancy graph over normalized canonical
names and aliases. Each connected component becomes one reservation cluster
for collision checking, while a separate membership map retains every source
entity. This permits NameService to answer “is this name occupied?” without
collapsing a location, organization, polity, capsule, or character into one
referent merely because their strings coincide.

Every tool-input projection MUST record source commit, source semantic digest,
transform identity and version, projection digest, membership count, collapsed
row count, and unresolved relation count.

### 6.5 Capability indexer

The indexer builds the capability graph from, in precedence order:

1. committed ACE capability manifests;
2. trusted OPAL2 tool manifests;
3. committed module APIs and schemas;
4. executable CLI or MCP discovery responses;
5. validation tests and deterministic fixtures;
6. specialist skill metadata;
7. human-facing documentation.

A lower-precedence source may enrich a capability but MUST NOT override a
higher-precedence contract silently.

Repository and skill scans are bootstrap and refresh mechanisms, not the query
hot path. Only validated `active` manifests enter the warm capability index;
discovered or ambiguous matches remain visible for index maintenance but are
ineligible for automatic execution.

### 6.6 Capability graph

The graph contains capability nodes and typed edges.

Node examples:

- `gumas.naming.resolve`;
- `gumas.state.build_character`;
- `gumas.simulate.bounded`;
- `quantum_forge.charforge.generate_capsule`;
- `canonrec.validate.entity`;
- `canonrec.references.check`;
- `narrative.render.character_background`.

Required edge types:

- `requires` — an input capability must run first;
- `produces` — capability supplies a requested field or artifact;
- `validates_with` — output requires another capability's check;
- `materializes_with` — output is persisted by another capability;
- `precedes` / `follows` — hard execution order;
- `fallback_to` — bounded alternate route;
- `conflicts_with` — capabilities must not be combined in one plan;
- `supersedes` — newer capability replaces an older route.

Each node MUST validate against
`catalog/schemas/aurora_ace_capability_manifest.schema.json`.

A capability node MUST also declare semantic output coverage, tool-native
status vocabulary, input mutation behavior, concurrency scope, digest policy,
and any adapter or projection required to make its contract composable.

### 6.7 Missing-field analyzer

The analyzer converts the requested answer into explicit output fields and
classifies each field as:

- `already_resolved`;
- `retrievable`;
- `derivable`;
- `generatable_by_capability`;
- `connective_synthesis_required`;
- `true_conflict_candidate`.

The analyzer MUST NOT treat `not_recorded` as `true_conflict_candidate`.
It MUST compare semantic coverage rather than matching field names or prose
tags.

### 6.8 Plan compiler

The compiler selects the smallest valid capability subgraph that produces all
required fields and validators. Selection SHOULD optimize, in order:

1. canonical compatibility;
2. authority and trust state;
3. complete output coverage;
4. semantic coverage of the answer contract;
5. transaction and concurrency compatibility;
6. determinism and replayability;
7. minimal mutation scope;
8. minimal unowned synthesis;
9. execution cost and latency.

Ambiguous routing is resolved by predeclared policy, capability priority, and
validation coverage. ACE asks the owner only when the remaining branch is a
reserved decision or a true conflict.

### 6.9 Executor

The executor runs the compiled directed acyclic graph. It MUST:

- validate every tool input and output;
- enforce time, resource, and side-effect budgets;
- record capability version, manifest digest, repository SHA, seed, duration,
  semantic output digest, and byte-level artifact digest;
- isolate tools with side effects;
- record pre- and post-mutation state for capabilities that mutate supplied
  working state;
- enforce sequential working state or an optimistic compare-and-swap boundary
  within each declared concurrency scope;
- stop before unauthorized repository or runtime mutation;
- distinguish tool failure from a canonical conflict.

### 6.10 Synthesis layer

The synthesis layer joins capability outputs into a coherent answer. It MUST
preserve field-level provenance and MUST NOT replace a specialist output with
unattributed prose.

If two tools produce compatible partial results, ACE MAY merge them. If they
produce incompatible results, ACE must apply declared precedence and conflict
rules or emit `TRUE_CONFLICT` when no valid resolution exists.

### 6.11 Validation layer

Before materialization, ACE MUST run all applicable checks:

- JSON or entity schema validation;
- canonical identity and alias collision checks;
- reference-integrity checks;
- timeline and continuity checks;
- layer-integrity checks;
- protected-invariant checks;
- naming protocol validation;
- tool-input projection lineage and membership validation;
- live-baseline revalidation for mutable registries;
- answer-contract semantic coverage validation;
- tool-native status to ACE-status crosswalk validation;
- capability-output integrity verification;
- target-repository and path validation.

Validation checks decide compatibility, not whether generated content is
legitimate merely because it was generated.

### 6.12 Materializer

The materializer converts a successful determination into authoritative
artifacts. It MUST use the target repository's native representation and
validation workflow. Materialization may be:

- `not_required` for retrieval of existing canon;
- `committed` for a completed canonical generation or revision;
- `commit_ready` when the packet is valid but the active policy does not
  authorize the commit;
- `blocked` when the target or gate is unavailable.

The materializer MUST never write generated control surfaces by hand when a
project generator owns them.

### 6.13 Determination ledger

Every completed query produces a determination receipt conforming to
`catalog/schemas/aurora_ace_determination_receipt.schema.json`.

The ledger is append-only. A later determination may supersede an earlier
one, but it may not erase it. Receipts MUST be queryable by subject, query,
capability, tool run, canonical target, and commit.

## 7. Determination vocabulary

### `RETRIEVED_CANON`

The requested information already exists in committed canon. No generative
tool call was required.

### `DERIVED_CANON`

The requested information follows deterministically from committed canon and
registered rules. The derivation and inputs are recorded.

### `GENERATED_CANON`

ACE used one or more constitutive capabilities to create previously
unspecified canonical state. All applicable validations passed and the
materialized result is committed.

### `CANON_REVISION`

ACE extended, reconciled, or superseded an existing canonical record while
preserving history. The committed revision and superseded determination are
recorded.

### `TRUE_CONFLICT`

Two or more binding commitments cannot be simultaneously satisfied, a
protected invariant would have to change, or the remaining choice is
explicitly reserved to the owner. The receipt MUST identify the exact claims,
sources, and minimal decision required.

### `EXECUTION_BLOCKED`

ACE compiled a valid plan but could not finish because of an operational
condition such as a missing tool, invalid manifest, unavailable target,
failed validation, exhausted budget, or absent mutation authority. This is
not a canon state and MUST NOT be converted into `STAGING`.

## 8. What is and is not a true conflict

A true conflict includes:

- two committed identities that claim the same unique referent incompatibly;
- mutually exclusive committed timeline facts;
- a requested completion that violates a protected Aurora invariant;
- a cross-layer bridge that changes the meaning of L1, L2, or L3;
- a choice explicitly listed in owner-reserved policy;
- multiple valid continuations whose selection changes a major established
  direction rather than a routine detail.

A true conflict does not include:

- an unnamed character;
- an unrecorded background;
- a missing ship class, seat, location, callsign, or institutional detail;
- a specialist tool that requires upstream state;
- multiple collision-free names when NameService can select deterministically;
- incomplete prose when structured tools can complete it;
- a missing commit approval for otherwise valid content.

## 9. Field-level provenance

Every answer field MUST contain:

- `field_path`;
- `value`;
- `origin`;
- `producer_refs`;
- `source_refs`;
- `run_receipt_refs`;
- `canon_target_ref`, when materialized.

The determination MUST additionally map every semantic requirement in the
answer contract to `satisfied`, `partial`, `missing`, or `not_applicable`.
Canonical determinations require every mandatory semantic requirement to be
`satisfied`.

Allowed origins are:

- `retrieved`;
- `deterministic_derivation`;
- `specialist_tool_output`;
- `connective_synthesis`.

`connective_synthesis` MUST identify why no specialist owned the field and
which constraints bounded the synthesis.

## 10. Character name-and-background reference flow

### 10.1 Input

```text
Question: What is this character's name and background?
Context: An unnamed Galactic Union logistics officer encountered aboard a
Judicator-class vessel during the current scenario.
```

### 10.2 Required outputs

- canonical character ID;
- canonical name and aliases;
- role and faction binding;
- background synopsis;
- character traits and decision profile;
- source and build receipts;
- canonical target record.

### 10.3 Compiled plan

1. Compile `name` and `background` into explicit semantic requirements.
2. Search CanonRec and active simulation state for a matching referent.
3. Build a referent graph; preserve unresolved or distinct same-name entities.
4. Allocate a stable character ID if no match exists.
5. Build the minimum `LeaderState` and resolve the applicable `FactionState`.
6. Build a NameService occupancy projection from connected components of all
   normalized canonical names and aliases, preserving cluster membership in a
   projection receipt.
7. Record the projection's pre-resolution digest, then call
   `NameService.resolve()` with person, faction, region, register, constraints,
   stable entity ID, and deterministic seed. Treat the in-memory reservation
   as a declared mutation.
8. Run a bounded state or simulation step if required to establish stressors,
   relationships, or behavioral state.
9. Call `CharForge.generate_capsule(leader, faction, output_dir)` with an
   explicit commit-ready tool-native certainty value; never rely on its
   `STAGING` default.
10. Verify the capsule manifest and build receipt. Hash stable semantic payload
    separately from timestamp-bearing artifact bytes.
11. Render an operational background from identity, faction posture, bias
    profile, stressor history, and trust relationships. If a formative
    biography was requested, insert a history-producing capability rather than
    stretching this synopsis to cover it.
12. Re-export or re-read the live raw naming registry. If its semantic digest
    advanced, recheck the selected name before materialization.
13. Run naming, schema, reference, continuity, layer, projection-lineage, and
    semantic-coverage validation.
14. Materialize the entity, naming transaction, and determination receipt
    atomically under the active commit
    policy.

### 10.4 Expected result

If all checks and materialization succeed, the result is `GENERATED_CANON`.
ACE's user-facing answer SHOULD disclose that no prior record existed and list
the capabilities used, without presenting the generation as a deficiency.

The worked packet is stored at
`catalog/templates/aurora_ace_character_resolution.example.json`.

## 11. Capability manifest requirements

A capability manifest MUST declare:

- stable capability and tool identity;
- repository, path, version, and observed commit;
- trust and lifecycle status;
- supported operations, layers, and entity types;
- input and output schemas;
- required and optional inputs;
- produced fields, their semantic coverage, and artifacts;
- determinism, seed, and idempotency behavior;
- side effects, input mutation behavior, concurrency scope, transaction
  requirements, and materialization scope;
- tool-native status vocabulary and ACE status crosswalk;
- semantic and byte-level digest policy, including volatile fields;
- required tool-input projection and adapter contracts;
- upstream capability dependencies;
- validators, fallbacks, and ordering constraints;
- supported determination classes;
- validation evidence and freshness policy.

Discovery alone MUST NOT set a capability to `active`. Activation requires an
allowlist decision and at least one executable validation reference.

## 12. Capability freshness

ACE MUST compare every manifest's observed repository SHA with the active
registered baseline before planning. A stale manifest may remain searchable,
but it MUST NOT execute until refreshed or explicitly allowed by policy.

When a repository, tool schema, or validation fixture changes, ACE SHOULD
rebuild only the affected graph nodes and dependency edges.

## 13. Interfaces

### 13.1 CLI target

The current root-control-plane MVP is available as:

```bash
python3 tools/aurora_ace.py capabilities
python3 tools/aurora_ace.py plan --question <text> --context <json>
python3 tools/aurora_ace.py resolve --question <text> --context <json> --out <new-directory>
python3 tools/aurora_ace.py resolve --query <query-envelope.json> --out <new-directory>
python3 tools/aurora_ace.py validate <artifact.json> --kind query
python3 tools/aurora_ace.py validate <artifact.json> --kind determination
```

This Python entrypoint implements the first vertical slice. The stable packaged
command and broader interface remain the target:

```text
aurora-ace resolve --question <text> [--context <json>] [--mode <mode>]
aurora-ace explain-plan --query-id <id>
aurora-ace capabilities [--field <field>] [--entity-type <type>]
aurora-ace replay --determination-id <id>
aurora-ace validate-receipt <path>
```

### 13.2 MCP target

Initial MCP tools SHOULD be:

- `aurora_ace_resolve`;
- `aurora_ace_explain_plan`;
- `aurora_ace_list_capabilities`;
- `aurora_ace_get_determination`;
- `aurora_ace_replay_determination`.

MCP exposure does not expand materialization authority. The execution policy
travels in the query envelope and is enforced by the ACE executor.

### 13.3 Agent contract

Agents SHOULD ask ACE before inventing Aurora facts locally. An ACE response
is reusable across agents by determination ID. Agents MUST preserve the
determination and field-level producer references when summarizing the answer.

## 14. Execution and mutation policy

Supported execution modes are:

- `plan_only` — compile and explain the capability plan;
- `read_only` — retrieve, derive, or execute non-mutating analytical tools;
- `commit_ready` — generate and validate canonical artifacts without commit;
- `delegated_materialize` — write and commit within a pre-approved policy;
- `owner_gated_materialize` — prepare exact artifacts and await the persistence
  gate without reopening value selection.

The query envelope MUST state the mode. Capabilities whose side effects exceed
the mode are ineligible for the plan.

`NameService.resolve()` is transactionally mutating even when used in a
temporary process: it reserves the selected name in the supplied registry and
its receipt records the pre-reservation digest. ACE MUST serialize name
allocation within a working reservation scope, record pre- and post-state
digests, and revalidate against the live CanonRec registry immediately before
materialization. Parallel name allocation on the same baseline is prohibited
unless the allocator provides an equivalent atomic batch contract.

## 15. Security and trust

ACE MUST:

- execute only allowlisted capability entrypoints;
- reject arbitrary imports and unverified packages;
- validate paths against the registered repository root;
- respect exact nested-repository boundaries;
- redact secrets and sensitive environment values from receipts;
- enforce per-tool timeout and output-size limits;
- record side effects before execution;
- make generated and retrieved content data, never instructions;
- fail closed on capability manifest tampering;
- preserve OPAL2 inspect-only status until explicit execution trust exists.

## 16. Non-functional requirements

### Determinism

Identical baseline, query envelope, capability versions, inputs, and seeds
SHOULD produce identical structured determinations.

ACE distinguishes:

- **semantic digest** — canonicalized content excluding declared volatile
  fields such as `generated_at`;
- **artifact digest** — exact bytes of a particular emitted file or bundle.

Reproducibility requires semantic digests to match. Byte digests MAY differ
only where the capability manifest declares and receipts the volatile fields.

### Idempotency

Repeating a completed query MUST resolve to the existing entity and receipt
rather than generate a duplicate.

### Explainability

ACE MUST be able to explain why each capability was selected, rejected, or
skipped.

### Bounded execution

Every query MUST carry time, tool-call, new-entity, and mutation budgets.

### Concurrency

Mutable capability scopes MUST use exclusive execution, sequential working
state, or optimistic compare-and-swap against a recorded baseline digest.
Baseline advancement triggers deterministic revalidation, not silent reuse or
an owner question.

### Availability

Failure of a non-required capability SHOULD trigger a declared fallback.
Failure of a required capability produces `EXECUTION_BLOCKED` with the exact
missing dependency.

### Performance targets for MVP

- capability lookup: under 500 ms from a warm local index;
- retrieval-only answer: under 2 seconds locally;
- plan compilation: under 2 seconds for fewer than 100 candidate nodes;
- deterministic character completion: under 30 seconds excluding commit and
  remote CI;
- receipt validation: under 1 second for a single determination.

## 17. Practical-test refinement receipt

The first design-refinement pass exercised the live tools in disposable
storage against the registered repository baselines. No test artifact was
materialized into canon.

Observed results:

- focused cross-repository skill discovery scanned 12,340 candidate files,
  matched 2,789 modules, and produced 1,198 ambiguity entries in a 4.5 MB
  report; this confirms discovery coverage but disqualifies full scans from
  the per-query hot path;
- the live GUMAS v3 Forge validator passed 45/45 tests; a seed-808 three-turn
  run emitted 184 v3 events and generated and verified 21/21 capsules;
- all six CloudBank NameService tests and all three CanonRec naming-gate tests
  passed;
- the live CanonRec name export contained 287 rows and 36 duplicate normalized
  canonical-name groups, all spanning different IDs; direct NameRegistry load
  failed on the first duplicate;
- explicit capsule or supersession evidence explained 28 of the 36 duplicate
  groups, while eight retained legacy-ID or legitimate same-name/different-
  referent ambiguity;
- a canonical-name-plus-alias occupancy graph reduced the export to 237
  reservation components while preserving all 287 source memberships; the
  resulting NameRegistry loaded, deterministically generated `Jorenon
  Morrowen`, and rejected a forced existing-name collision;
- NameService mutated its working registry from the receipt's pre-state digest
  to a new post-state digest;
- a direct CharForge character build verified successfully; six semantic
  payload files and manifest record hashes were stable across identical runs,
  while timestamp-bearing manifest bytes differed;
- the generated L2 character candidate passed the CanonRec entity validator
  with zero blocks and zero warnings; the naming validator passed with one
  `NAMING_REGISTRY_ADVANCED` warning because it compared the projected registry
  digest with the raw export digest.

These observations are design inputs, not canon determinations. They establish
the need for a warm manifest index, projection lineage, referent-preserving
identity, semantic coverage contracts, status adapters, transaction receipts,
and projection-aware naming revalidation.

### 17.1 Implementation verification receipt

The first local implementation pass completed the character-completion
vertical slice in the root control plane. It does not write to either nested
repository.

Confirmed behavior:

- the warm allowlist activates eight exact-path capabilities at the registered
  root, CanonRec, and CloudBank repository baselines and records both repository
  SHA and live source-file SHA;
- the materialization capability remains explicitly `blocked` while the
  executor emits a complete `commit_ready` packet;
- a seed-808 logistics-officer query selected NameService and CharForge,
  generated `Jorenon Morrowen`, and preserved the NameService pre- and
  post-reservation digests;
- the live 287-row CanonRec export projected to 237 occupancy components with
  all source memberships retained and 40 multi-ID components conservatively
  labeled `unresolved` by the runtime projection;
- the generated capsule passed `verify_capsule`, the candidate passed CanonRec
  entity validation with zero blocks, and the naming gate passed with the
  expected non-blocking `NAMING_REGISTRY_ADVANCED` projection-digest warning;
- the query envelope and determination receipt both passed their draft 2020-12
  schemas;
- two complete executions from the same envelope produced the same character,
  semantic answer digest, and semantic capsule digest while preserving
  timestamp-bearing artifact provenance;
- the focused suite passes six checks when live tests are enabled.

Current implementation boundary:

- character completion is implemented; existing-character retrieval and
  revision routing are not yet implemented;
- materialization, the append-only determination ledger, and delegated commit
  policy are not implemented;
- MCP exposure and broader entity classes are not implemented;
- capability refresh still uses a small embedded allowlist plus live path and
  SHA checks; fleet-scan-to-manifest ingestion is not implemented;
- the occupancy adapter conservatively retains all multi-ID components as
  `unresolved`; ingestion of CanonRec equivalence, distinction, and
  supersession evidence into those relation labels is not yet implemented.

Accordingly, this is a working Phase 3 vertical slice, not yet a fully
ACE-conformant implementation under all acceptance scenarios in section 18.

## 18. Acceptance scenarios

An implementation is not ACE-conformant until it passes these scenarios:

1. **Existing character lookup** — returns `RETRIEVED_CANON` and invokes no
   generator.
2. **Unobserved character completion** — uses NameService plus state and
   CharForge capabilities and returns committed `GENERATED_CANON`.
3. **Idempotent replay** — the same contextual referent returns the same
   character rather than minting another.
4. **Name collision** — NameService rejects collisions and emits the selected
   collision-safe name receipt.
5. **Missing upstream state** — ACE inserts the state-builder dependency
   instead of asking the owner for routine fields.
6. **Stale capability manifest** — execution is blocked until the node is
   refreshed; no stale tool runs silently.
7. **True contradiction** — ACE identifies the exact incompatible committed
   claims and returns `TRUE_CONFLICT`.
8. **Cross-layer request** — ACE rejects or explicitly gates an unauthorized
   L2-to-L1 bridge.
9. **Materialization unavailable** — returns `EXECUTION_BLOCKED` plus a
   commit-ready packet, never final `STAGING`.
10. **Field provenance** — every answer field names at least one producer and
    source or run receipt.
11. **No specialist exists** — connective synthesis is bounded, identified,
    and separately validated.
12. **Tool failure** — fallback routing is deterministic and visible.
13. **Live name-registry compatibility** — the CanonRec export loads into
    NameService through an occupancy-component projection without a
    duplicate-reservation failure. All raw members remain present in the
    projection receipt and referent graph.
14. **Distinct same-name referents** — a location and organization, or a polity
    and character, sharing a string remain separate referents even though one
    naming reservation component marks the string occupied.
15. **Registry advancement** — a name generated against an earlier projection
    is rechecked against the live raw registry before materialization; a newly
    occupied name triggers deterministic replanning.
16. **Semantic background coverage** — CharForge's operational synopsis cannot
    silently satisfy a requested formative biography. The plan either inserts
    a history producer or declares the narrower scope in the answer contract.
17. **Semantic reproducibility** — identical CharForge inputs produce matching
    semantic digests even when timestamp-bearing artifact bytes differ.
18. **Warm capability routing** — a query uses active manifests from the warm
    index and does not wait for a fleet-wide skill scan.

### Confirmed integration constraint

During practical validation, the current CanonRec name-registry export
contained cross-ID canonical-name and alias occupancy components and
`NameRegistry` rejected the raw export on load. ACE MUST provide both a
referent-preserving graph and a separate NameService occupancy projection.
Projection lineage MUST distinguish proven equivalence, proven distinction,
and unresolved identity while still reserving every occupied string. This is a
tool-composition contract, not an unresolved fact about the universe, and it
MUST NOT become an owner adjudication or parked canonical result.

## 19. Implementation sequence

Implementation status as of the first local MVP pass:

- Phase 0: contract package present locally; schema validation passes;
- Phase 1: bounded warm allowlist and capability explanation implemented;
- Phase 2: character query compilation, answer contract, baselines, and name
  occupancy projection implemented;
- Phase 3: commit-ready name/background flow implemented and live-tested;
- Phases 4 and 5: not implemented.

### Phase 0 — contracts

- land this specification, contract, schemas, and worked fixture;
- add schema and fixture validation tests;
- resolve the stale reconciler doctrine so it cannot reintroduce default
  parking.

### Phase 1 — capability graph

- index registered repositories and Git baselines;
- ingest OPAL2 manifests and specialist metadata;
- seed NameService, CharForge, GUMAS, CanonRec validation, and reference checks;
- use fleet scans only to bootstrap or refresh manifests; keep ambiguity out of
  executable routing;
- expose capability search and plan explanation.

### Phase 2 — read and plan

- normalize queries;
- compile and validate semantic answer contracts;
- resolve contextual referents;
- build referent-preserving and tool-specific canon projections;
- search canon and the warm capability graph;
- compile dry-run plans and validate query envelopes.

### Phase 3 — character completion vertical slice

- implement the name-and-background flow;
- add deterministic ID, seed, and duplicate-resolution policy;
- build connected-component name occupancy from canonical names and aliases,
  retaining a complete cluster membership receipt;
- add sequential naming transactions, pre/post digests, and live-registry
  compare-and-revalidate before materialization;
- implement CharForge status crosswalk and semantic-versus-artifact digests;
- enforce operational-synopsis versus formative-biography coverage;
- generate and verify character capsules;
- emit determination receipts and commit-ready canonical packets.

### Phase 4 — materialization

- implement delegated and owner-gated materialization modes;
- add append-only determination ledger;
- project committed results to dependent repositories through existing
  repository-specific workflows.

### Phase 5 — broader canonical completion

- add vessels, locations, factions, institutions, events, operations, and
  relationship completion;
- integrate bounded GUMAS, QGIA/QSFE, DuelSim, narrative, and governance
  capabilities as their manifests become active.

## 20. Initial owner-level decisions

Implementation requires a small set of architectural decisions, not recurring
detail adjudication:

1. authoritative location of the append-only ACE determination ledger;
2. which canonical completion classes receive delegated commit authority;
3. stable entity-ID derivation policy for contextual referents;
4. ownership and release process for cross-repository capability manifests;
5. reserved-decision policy defining the few branches ACE must escalate.

Once selected, these decisions become policy inputs. They are not repeated for
every generated name, biography, location, or relationship.

## 21. Required artifacts

- Normative specification: this file.
- Root contract: `catalog/contracts/aurora_ace_contract_v0_1.json`.
- Capability manifest schema:
  `catalog/schemas/aurora_ace_capability_manifest.schema.json`.
- Query envelope schema:
  `catalog/schemas/aurora_ace_query_envelope.schema.json`.
- Determination receipt schema:
  `catalog/schemas/aurora_ace_determination_receipt.schema.json`.
- Character-resolution worked packet:
  `catalog/templates/aurora_ace_character_resolution.example.json`.
- NameService capability-manifest fixture:
  `catalog/templates/aurora_ace_nameservice_capability.example.json`.

## 22. Success criterion

ACE succeeds when Aurora users and agents no longer need to know where a
capability lives, how its inputs are assembled, or which validators must run.
They ask a world question. ACE finds the relevant machinery, completes the
world when necessary, records how the answer was made, and returns a canonical
result that downstream operations can rely on.
