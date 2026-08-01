# Aurora State Model Implementation Plan v0.1

Status: INITIAL PLAN
Planning horizon: contract adoption through first trained baseline
Current authorization: DESIGN PACKAGE ONLY

## 1. Outcome

The program should deliver a governed episode factory before it delivers a
model.

The first meaningful milestone is not a checkpoint. It is a reproducible,
schema-valid dataset of Aurora world-and-belief transitions that can be audited
across repository boundaries.

## 2. Workstreams

| Workstream | Primary repository | Deliverable |
| --- | --- | --- |
| WS0 Governance | Root control plane | Adopted contract, schemas, promotion and disclosure gates |
| WS1 World adapter | GUMAS/CloudBank simulation boundary | Stable world-state and transition adapter |
| WS2 Epistemic adapter | CloudBank QSFE with QGIA Spine semantics | Complete replayable belief trace |
| WS3 Evidence semantics | QGIA Library | Simulation-safe evidence templates and strict truth-ledger separation |
| WS4 Forecast semantics | QGIA Spine | Synthetic forecast/prior/calibration adapter |
| WS5 Validation | CanonRec plus repo-local validators | Invariant and authority validation |
| WS6 Dataset factory | CloudBank orchestration | Episode assembler, shards, manifests, receipts |
| WS7 Baselines | New model workspace selected after G2 | No-change, sequence, and graph baselines |
| WS8 Serving | CloudBank | Simulation-only inference surface |

No nested repository is authorized by this plan alone. Each workstream requires
a repo-local issue, branch, tests, and adoption receipt.

## 3. Phase plan

### Phase 0: Root contract review

Goal: settle the learning object and authority boundary.

Tasks:

- review the white paper and system specification
- review the episode, epistemic-trace, and dataset-manifest schemas
- decide whether the name Aurora State Model should remain the program name
- assign durable owners for world state, epistemic state, validation, and
  release governance
- resolve training-data disclosure and licensing policy
- mark the root contract adopted without marking runtime active

Exit:

- reviewed contract
- no unresolved authority ambiguity
- explicit owner for every cross-repo interface

### Phase 1: Adapter discovery

Goal: map existing runtime outputs to the v1 contract without redesigning the
engines.

Tasks:

- inventory the smallest complete GUMAS world-state snapshot
- inventory CloudBank QSFE internal latent beliefs, events, and seed flow
- identify QGIA forecast and evidence fields reusable in simulation authority
- define canonical entity identifiers and state-delta operations
- determine which CanonRec checks can run per step and per episode
- document all legacy/canonical path conflicts before adapter implementation

Exit:

- adapter mapping document per participating repository
- no required v1 field lacks a source or an explicit derivation rule

### Phase 2: ASM-001 generator

Goal: produce the first 12 governed episodes.

Tasks:

- implement independent seed scopes
- add a 20-turn scenario adapter
- add one intervention family
- add three evidence masks
- export world-state before/after and stable deltas
- export QGIA-shaped epistemic traces
- assemble episode and trace files
- generate manifest, hashes, replay receipts, and validation report

Exit:

- 12 schema-valid episodes
- replay requirement satisfied
- no canonical ledger mutation
- dataset manifest passes G0, G1, and G2

### Phase 3: Evaluation harness

Goal: make model utility measurable before training.

Tasks:

- define no-change and empirical-frequency baselines
- implement structural, numerical, event, forecast, and rollout metrics
- group dataset splits by scenario family and generator lineage
- add counterfactual-pair checks
- add invariant-violation summaries

Exit:

- versioned metric definitions
- baseline report reproducible from the frozen manifest

### Phase 4: First learned baseline

Goal: determine whether a learned surrogate captures useful state dynamics.

Tasks:

- implement deterministic serializer
- train a small structured sequence baseline
- compare against no-change and empirical baselines
- record model, code, dataset, and environment provenance
- perform one-step evaluation only

Exit:

- baseline beats declared trivial baselines on preselected metrics
- invalid transition rate is acceptable or its failure modes are actionable
- no public release claim

### Phase 5: Epistemic and rollout model

Goal: add belief dynamics and multi-step behavior.

Tasks:

- add epistemic-trace inputs and targets
- add graph or hybrid baseline
- train on evidence-mask and network-topology variation
- evaluate calibration and dissent sensitivity
- evaluate multi-step divergence
- add teacher-correction and fallback behavior

Exit:

- G4 evaluation complete
- model limitations documented by scenario family and horizon

### Phase 6: Controlled serving

Goal: expose a reversible simulation-only service.

Tasks:

- add CloudBank inference adapter
- return model and dataset provenance on every response
- run deterministic validators before returning proposals
- add quotas, logging, disable switch, and rollback
- prohibit canonical mutation in API and authorization layers

Exit:

- G5 passed
- owner approval recorded
- no unresolved disclosure or licensing issue

## 4. Initial issue backlog

Suggested issue IDs are planning identifiers, not current tracker records.

### ASM-001: Reproducible World-and-Belief Episode

Owner: cross-repo integration
Depends on: root contract review
Acceptance: system specification section 16

### ASM-002: GUMAS state adapter

Owner: simulation repository
Deliver:

- stable state snapshot
- typed delta operations
- event mapping
- replay entrypoint

### ASM-003: QSFE epistemic export

Owner: CloudBank
Deliver:

- isolated seed scope
- latent or aggregate belief snapshots
- network hash
- evidence-mask identity
- dissent, echo, forecast, and confidence fields

### ASM-004: QGIA simulation namespace

Owner: QGIA Library and Spine
Deliver:

- naming and storage rules for synthetic evidence and forecasts
- hard prohibition on truth-ledger writes
- adapter tests using root fixtures

### ASM-005: CanonRec episode validator

Owner: CanonRec
Deliver:

- invariant validation interface
- authority and promotion checks
- stable rejection codes

### ASM-006: Dataset manifest builder

Owner: CloudBank or a dedicated data workspace
Deliver:

- content hashing
- immutable shard inventory
- split lineage
- disclosure and license metadata
- quality-gate aggregation

### ASM-007: Baseline evaluation harness

Owner: model workspace selected after ASM-001
Deliver:

- trivial baselines
- metric implementations
- held-out scenario-family split
- reproducible report

### ASM-008: Sequence transition baseline

Owner: model workspace
Depends on: ASM-001, ASM-006, ASM-007
Deliver:

- deterministic serializer
- training configuration
- checkpoint receipt
- one-step evaluation

### ASM-009: Simulation-only inference API

Owner: CloudBank
Depends on: a baseline that passes G3
Deliver:

- versioned request/response contract
- validator integration
- provenance response
- disable and rollback controls

## 5. Decisions required before implementation

### D1: Durable dataset home

Recommendation: keep contracts in root and generated data outside Git, with
manifests and small synthetic fixtures committed. Select object storage only
after classification and deletion requirements are resolved.

### D2: World-state boundary

Recommendation: begin with the smallest state slice that supports one complete
scenario. Do not attempt a universal Aurora ontology in ASM-001.

### D3: Belief-trace granularity

Recommendation: preserve full latent traces in internal shards when permitted,
and always publish aggregate summaries in the contract record.

### D4: Model workspace

Recommendation: create or designate a model repository only after ASM-001
passes G2. Until then, a model repo would encode guesses about inputs.

### D5: Public release posture

Recommendation: default to internal-only artifacts. Treat dataset and checkpoint
publication as separate owner-approved decisions.

## 6. Dependency graph

    Root contract
      -> world adapter
      -> epistemic adapter
      -> CanonRec validator
      -> ASM-001 generator
      -> dataset manifest and evaluation harness
      -> sequence baseline
      -> epistemic/rollout model
      -> simulation-only serving

QGIA closed-loop adoption runs alongside the first adapters and is required
before real-world calibration claims, but not before generation of explicitly
synthetic ASM-001 traces.

## 7. Risk register

| Risk | Early signal | Mitigation | Stop condition |
| --- | --- | --- | --- |
| State schema becomes universal and unbounded | Adapter requires unrelated domains | Scope ASM-001 to one scenario state slice | No stable minimal state after discovery |
| QSFE replay is not isolated | Same seed produces different traces | Per-episode RNG and environment receipt | Unexplained drift remains |
| Synthetic and real QGIA data mix | Shared ledger/path without authority filter | Separate namespace and schema authority | Any synthetic truth-ledger write |
| Dataset leakage | Near-identical scenarios cross splits | Family and lineage grouped splits | Cannot reconstruct split lineage |
| Model emits invalid state | High invariant rejection rate | Typed decoder and validator feedback | Model does not beat trivial baseline |
| License/disclosure unclear | Source without usable rights metadata | Internal-only allowlist and review | Any planned public artifact has unresolved source |
| Simulator bias is mistaken for reality | Real-world claims from synthetic score | Simulation labeling and QGIA outcome comparison | Marketing or API removes authority label |
| Cross-repo drift | Adapter assumes stale schema or SHA | Version negotiation and conformance fixtures | Required repo cannot pin contract version |

## 8. Definition of done by artifact

### Adapter

- committed in its owning repository
- references exact root contract version
- passes local tests and root conformance fixtures
- records unsupported fields explicitly
- does not change authority boundaries

### Dataset

- immutable manifest and hashes
- replay and validator receipts
- split lineage
- classification and license review
- known limitations

### Model

- exact dataset manifest reference
- training code and environment provenance
- comparison with trivial baselines
- structural and task-specific evaluation
- documented authority and intended use

### Service

- versioned contract
- simulation-only authority
- validator integration
- provenance per response
- observable disable and rollback controls

## 9. Recommended first development sequence

1. Open one root review issue for this design package.
2. Open ASM-002 and ASM-003 as read-only adapter-discovery tasks.
3. Resolve D1 through D3.
4. Implement root fixture conformance in each participating repository.
5. Implement ASM-001 in a clean integration branch.
6. Publish the generator receipt for review.
7. Decide whether a dedicated model repository is warranted.
8. Only then authorize ASM-007 and ASM-008.

## 10. Handoff rule

Future sessions should begin from:

- this plan
- the machine-readable root contract
- the latest design-package receipt
- repo-local adoption receipts, when they exist

Conversational summaries are secondary. A workstream is not active merely
because it appears in this plan.
