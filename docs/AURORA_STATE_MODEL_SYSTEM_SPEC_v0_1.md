# Aurora State Model System Specification v0.1

Status: DRAFT ADOPTION-READY DESIGN
Runtime status: NOT IMPLEMENTED
Authority: ROOT CONTROL-PLANE PROPOSAL
Normative language: MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

## 1. Purpose

This specification defines the first cross-repository contract for generating,
validating, storing, training on, evaluating, and serving Aurora State Model
episodes.

It does not select a model vendor, training framework, storage service, or
deployment platform. It defines the stable learning object that those choices
must consume and produce.

## 2. Scope

Version 0.1 covers:

- simulation-authority world-state transitions
- simulation-authority epistemic traces
- immutable dataset manifests
- repository and authority boundaries
- reproducibility requirements
- training and evaluation gates
- the ASM-001 implementation slice

Version 0.1 does not cover:

- mutation of canonical Aurora state by a model
- promotion of synthetic records into QGIA truth ledgers
- production deployment
- public model or dataset release
- real-world forecasting claims

## 3. Terms

World state
: The typed state of the simulated environment at a discrete step.

Observation view
: The subset or transformation of world state available to a modeled
participant.

Epistemic state
: Beliefs, probabilities, disagreements, visibility, and confidence held by an
agent, group, or population.

Episode
: A governed record connecting a state and intervention to teacher-produced
transition targets.

Teacher
: A deterministic or seeded Aurora engine that produces target transitions.

Learner
: A statistical model trained to predict a teacher-compatible transition.

Authority
: The trust domain of an artifact. Version 0.1 permits simulation,
evaluation, and synthetic-fixture authority only.

Promotion
: An explicit governed act that changes an artifact's authority or canonical
status.

## 4. Repository responsibilities

### 4.1 Root control plane

The root repository MUST own:

- the cross-repository contract
- JSON schemas and synthetic conformance fixtures
- adoption status and design receipts
- dataset and model promotion gates
- cross-repository compatibility requirements

The root repository MUST NOT impersonate repo-local runtime implementation.

### 4.2 GUMAS and simulation repositories

Simulation repositories SHOULD own:

- scenario compilation once a repo-local compiler is implemented
- authoritative simulated world state
- intervention application
- state-transition and event generation
- deterministic replay adapters

They MUST emit or adapt to the episode schema without changing the root
authority model.

The current GUMAS `build_default_scenario(scenario_id, seed)` surface MUST NOT
be represented as a parameterized scenario compiler. It builds one fixed world.
L2 scenario cards MAY seed future families only after a versioned adapter maps
their prose knobs to typed `GUMASState` and intervention parameters.

### 4.3 QGIA Knowledge Library

The library SHOULD own real evidence and resolved outcome semantics after the
existing QGIA closed-loop contract is adopted.

For ASM generation it MAY provide curated retrieval inputs and schema-compatible
synthetic evidence templates. It MUST NOT receive synthetic outcomes in its
canonical truth ledger.

### 4.4 QGIA Knowledge Spine

The spine SHOULD own forecast, prior, resolution, calibration, and methodology
semantics after adoption of the QGIA closed-loop contract.

For ASM generation it SHOULD define how synthetic forecasts, priors, and
calibration targets are shaped. Simulation-authority records MUST remain
separate from operational or real-world ledgers.

### 4.5 CloudBank

CloudBank SHOULD own:

- scalable episode-generation jobs
- QSFE epistemic-state adapters
- isolated seed scopes
- generated artifact storage adapters
- learner inference orchestration
- simulation-only serving endpoints

CloudBank MUST NOT expose learner output as canonical truth.

### 4.6 CanonRec

CanonRec SHOULD own:

- invariant validation adapters
- canonical-reference checks
- rejection reasons
- any future promotion decision that crosses from simulated proposal to
  canon-eligible material

Learned output MUST remain rejectable by CanonRec and deterministic
repo-local validators.

### 4.7 DuelSim

DuelSim MAY become an additional teacher for paired, adversarial, or
counterfactual episodes. Its adoption is not required for ASM-001.

## 5. Authority model

Every episode, epistemic trace, dataset manifest, checkpoint, evaluation, and
inference response MUST declare an authority.

Allowed v0.1 authorities:

- simulation
- evaluation
- synthetic_fixture

Prohibited v0.1 authorities:

- canon
- operational_truth
- adjudicated_real_world_outcome

The schemas intentionally prevent a v0.1 episode from claiming canon
authority.

## 6. Canonical learning objects

### 6.1 Episode

The canonical episode schema is:

catalog/schemas/aurora_state_episode_v1.schema.json

An episode MUST contain:

- identity, version, authority, classification, and timestamp
- exact source revisions, requested and realized seed bundles, and a
  post-initialization RNG-state fingerprint
- scenario identity and step
- world state before the intervention
- intervention
- observation view
- teacher-produced world state after the intervention
- state delta and emitted events
- target bundle
- validation results
- an explicit non-promotion record

An episode SHOULD reference an epistemic trace. It MAY inline a small trace only
when the storage adapter preserves the same schema.

### 6.2 Epistemic trace

The canonical trace schema is:

catalog/schemas/aurora_epistemic_trace_v1.schema.json

A trace MUST preserve:

- producer and seed
- topology or network hash
- population and round counts
- observation or evidence mask
- time-ordered aggregate belief snapshots
- dissent and echo indicators
- forecast distribution and confidence components

Agent-level latent values MAY be stored in a referenced shard. Aggregate-only
storage MUST be declared in the trace.

### 6.3 Dataset manifest

The canonical manifest schema is:

catalog/schemas/aurora_dataset_manifest_v1.schema.json

A manifest MUST preserve:

- immutable dataset identity and version
- exact source revisions
- generator and serializer versions
- artifact paths and content hashes
- split policy and scenario-family isolation
- episode counts and authority distribution
- quality-gate results
- classification, disclosure, and licensing decisions
- known limitations
- explicit promotion ineligibility until reviewed

### 6.4 Teacher-sufficiency report

The canonical teacher-sufficiency schema is:

catalog/schemas/aurora_teacher_sufficiency_report_v1.schema.json

The report MUST preserve:

- the measured dataset and generator references
- the complete planned seed-by-parameter grid and dataset horizons
- joint event entropy and conditional event entropy given the previous turn
- macro-trajectory spread at the declared horizons
- declared and effective scenario-family counts after deduplication
- predeclared decision thresholds and G1.5 status
- known limitations and explicit non-promotion

Dataset volume, byte size, and unconditional event diversity MUST NOT be used
alone as evidence of teacher sufficiency.

## 7. Episode lifecycle

1. Resolve exact repository revisions.
2. Resolve a scenario version and configuration.
3. Allocate independent requested seed scopes for world, epistemic,
   intervention, and serialization behavior.
4. Generate the world transition.
5. Generate or retrieve the epistemic trace.
6. Assemble the episode without mutating teacher outputs.
7. Validate schemas, references, invariants, and authority.
8. Record and validate the realized post-initialization seeds plus an RNG-state
   fingerprint, then replay the episode from that realized state.
9. Write an immutable episode shard.
10. Update a new dataset manifest version.

Append-only records SHOULD be used once a dataset version is published
internally. Corrections SHOULD create a superseding version rather than
silently rewriting the original.

## 8. Determinism and replay

The generation system MUST:

- record independent seeds for world, epistemic, intervention, and
  serialization scopes
- assert requested seeds against the teacher's realized post-initialization
  seeds and fail unexplained mismatches
- fingerprint the RNG state immediately after teacher initialization
- record exact source repository revisions
- hash effective configuration after defaults are resolved
- avoid shared mutable random-number generator state between episodes
- specify ordering rules for maps, agents, events, and floating-point output
- record whether replay is byte-stable, structurally stable, or nondeterministic
- fail the ASM-001 gate if unexplained nondeterminism remains

Deterministic replay does not require that every simulator be deterministic. A
stochastic simulator is acceptable when the seed, implementation, and
environment reproduce the same governed output.

## 9. State representation

The v0.1 contract permits JSON-compatible state values:

- objects
- arrays
- strings
- finite numbers
- booleans
- null

Adapters MUST define stable identifiers for entities and relations. They SHOULD
encode changes as typed operations such as set, add, remove, increment, link,
and unlink.

State-delta order MUST be stable. If operations commute, the adapter MUST apply
a canonical ordering before hashing or serialization.

## 10. Epistemic representation

World state and epistemic state MUST remain independently addressable.

An epistemic trace MUST distinguish:

- what was observable
- what evidence was delivered
- what each stored population aggregate believed
- what forecast distribution was emitted
- how confidence was decomposed
- what dissent or echo condition was present

Reliability values MUST be data, not an implicit control parameter whose
meaning is absent from the record.

## 11. Training interface

The minimum learner input is:

- world_state_before
- intervention
- observation_view
- optional prior epistemic state
- optional retrieved evidence references

The minimum learner targets are:

- state_delta
- event labels
- belief_delta_summary
- forecast probabilities when defined

The learner MAY also predict:

- world_state_after
- confidence components
- terminal outcome distribution
- invariant-risk score

Training jobs MUST consume a frozen dataset manifest. They MUST NOT discover
unmanifested files at runtime.

### 11.1 Initial learner scope and earned scale

The first learned ASM baseline MUST be deliberately small and specialized
relative to the architectures and task breadth available to the project. Its
purpose is to demonstrate that governed learning adds a measurable capability
that Aurora's deterministic validators, retrieval surfaces, simulation engines,
and surrounding runtime do not already provide economically or reliably.

Model size, parameter count, or task breadth MUST NOT be treated as evidence of
Aurora nativeness or model quality. A proposal to increase parameter count,
architecture complexity, training scope, or task breadth SHOULD identify a
measured deficiency in the smaller baseline and SHOULD predeclare the metric or
capability improvement that the added scale is expected to deliver.

Scale SHOULD be earned through demonstrated deficiencies and measurable gains,
not assumed as a default development direction. Specialized learned components
MAY later be composed under shared Aurora governance; version 0.1 does not
require or presume a single monolithic Aurora model.

## 12. Inference interface

A future inference endpoint SHOULD accept:

- model release identifier
- scenario and state schema versions
- current state
- intervention
- observation view
- optional epistemic state
- sampling controls and seed

It SHOULD return:

- a schema-compatible proposed transition
- model and dataset provenance
- uncertainty
- validator results
- simulation authority

The endpoint MUST reject requests that ask the model to claim or mutate canon.

## 13. Dataset splits

Random row splitting is prohibited.

Splits MUST be grouped by:

- scenario family
- generator version
- intervention lineage
- near-duplicate content hash

At least one complete scenario family SHOULD be held out. A manifest MUST NOT
mark its leakage check `passed` unless it contains at least two effective
scenario families; a single-family ASM-001 fixture MUST report `not_run`.
Counterfactual pairs MUST remain in the same split unless the evaluation
explicitly tests generalization across intervention families.

## 14. Quality gates

### Gate G0: contract conformance

- all files parse
- every schema passes Draft 2020-12 metaschema validation
- every fixture passes full Draft 2020-12 validation, including nested and
  conditional constraints
- all authority and promotion rules pass

### Gate G1: generator reproducibility

- complete provenance
- replay classification recorded
- no unexplained drift
- stable identifiers and ordering

### Gate G1.5: teacher sufficiency

- joint event entropy and conditional event entropy given the previous turn are
  measured against predeclared thresholds
- macro-trajectory spread is measured over the complete seed-by-parameter grid
  at each dataset horizon
- effective scenario-family count is measured after deduplication
- any comparison against a copy-previous-state baseline is reproducible
- failure blocks adapter expansion and training, but does not invalidate or
  delay completion of ASM-001

### Gate G2: dataset integrity

- no split leakage
- content hashes verified
- no synthetic truth-ledger writes
- disclosure and license review recorded

### Gate G3: baseline utility

- one-step baseline beats a no-change predictor
- event classifier beats majority-class baseline
- probability targets are scored when present
- invalid transition rate is reported

### Gate G4: rollout utility

- divergence by horizon reported
- invariant violations reported
- counterfactual sensitivity evaluated

### Gate G5: serving readiness

- simulation-only authority enforced
- model and dataset provenance returned
- deterministic validators active
- rollback and disable path tested

Passing one gate does not imply passing a later gate.

## 15. Security, privacy, and disclosure

Generation and training pipelines MUST:

- enforce classification-aware allowlists
- exclude secrets and non-approved private material
- retain source and derivative lineage
- support artifact-level deletion or quarantine
- record licenses or usage restrictions
- prevent public release when any source is unresolved

A model checkpoint is a derivative artifact and MUST inherit the strongest
applicable restriction from its training manifest until a review says
otherwise.

## 16. ASM-001 acceptance specification

ASM-001 MUST generate exactly 12 governed episodes from:

- one 20-turn scenario
- one intervention family
- three evidence masks
- two world seeds
- two epistemic seeds

It MUST produce:

- episode files
- epistemic trace files
- one dataset manifest
- replay receipts
- a validation report
- a teacher-sufficiency report

It MUST NOT:

- train a model
- write to a canonical QGIA ledger
- change a nested repository's authority declaration
- claim real-world calibration

ASM-001 MUST record G1.5 evidence after generation. It MAY complete with G1.5
failed; in that state no adapter expansion or model-training proposal is
authorized.

## 17. Adoption protocol

Adoption is staged:

1. Root contract and schemas are reviewed.
2. Each nested repository proposes a local adapter and records its own
   validation.
3. Cross-repository conformance is tested against synthetic fixtures.
4. ASM-001 is generated in a clean integration environment.
5. The root receipt changes from design-ready to generator-validated.
6. G1.5 is evaluated from the generated evidence.
7. A baseline training proposal may be opened only if G1.5 passes.

The machine-readable contract remains a proposal until repo-local adoption is
confirmed by committed code and tests.

## 18. Versioning

Schema-breaking changes require a new major schema filename.

Additive optional fields MAY be introduced in a minor contract revision.
Changes to authority, promotion, seed semantics, or required provenance MUST be
treated as breaking even if the JSON shape remains compatible.
