# Aurora State Model

## A native learned model of simulated world and belief state

Version: 0.1
Date: 2026-07-29
Status: DRAFT DESIGN PROPOSAL
Activation: NOT RUNTIME-ACTIVE
Canon authority: NONE

## Abstract

Aurora already contains most of the machinery needed to produce a new kind of
native model: a learned model whose primary language is simulated state rather
than prose.

The proposed Aurora State Model (ASM) learns from governed simulation episodes.
Each episode records a world state, an intervention, observations available to
participants, the next world state, emitted events, changes in agent beliefs,
and forecast or uncertainty targets. GUMAS and related simulators provide the
ontic teacher: what changed in the simulated world. QGIA provides the epistemic
teacher: what was knowable, believed, forecast, contested, or miscalibrated.
CanonRec remains the deterministic judge for invariants and promotion.
CloudBank provides the likely generation, orchestration, and serving surface.

The result should not initially be framed as a general-purpose large language
model. It is better understood as a structured world-and-belief transition
model that may use language-model components where they are useful. Its core
output is a typed state transition with calibrated uncertainty. Natural
language is an optional explanation or control interface, never the
authoritative state.

This paper argues that the idea is feasible with Aurora's current architecture,
defines the strongest version of the concept, identifies the missing contracts,
and proposes an incremental path from deterministic data generation to a
credible learned emulator.

## 1. The thesis

The most valuable Aurora-native model is not a chatbot trained on Aurora
documents. It is a model trained on Aurora's governed trajectories.

Let:

- S(t) be the authoritative simulated world state at step t
- I(t) be an intervention, action, or policy applied at t
- O(t) be the observation surface available to a participant
- B(t) be the epistemic state of an agent, cell, or population
- E(t+1) be events emitted by the transition
- Y be a terminal or adjudicated outcome

The deterministic or stochastic Aurora infrastructure supplies samples of:

    S(t), I(t), O(t), B(t) -> delta-S(t+1), E(t+1), delta-B(t+1), P(Y)

ASM learns a conditional distribution over those targets. In practical terms,
it can become a fast surrogate for expensive simulation, a counterfactual
engine, a policy-testing instrument, a state-compression model, and a generator
of plausible next states under uncertainty.

The key design choice is to teach both world dynamics and belief dynamics.
Many systems can predict what happens next. Aurora can also model how evidence,
partial observability, reliability, dissent, echo effects, and prior beliefs
shape what different actors think will happen next. That ontic/epistemic split
is the strongest differentiator available in the current project.

## 2. Why call it native

ASM is Aurora-native if all of the following are true:

1. Its training records are produced by Aurora-controlled simulation and
   forecasting infrastructure.
2. Its state vocabulary is typed and versioned by Aurora contracts.
3. Its outputs preserve the boundary between simulated state, belief state,
   forecast, and canonical truth.
4. Its provenance includes repository revisions, configuration hashes, seeds,
   validator results, and authority labels.
5. Its learned output can be rejected or corrected by deterministic Aurora
   validators.
6. Its datasets and model releases pass Aurora governance, disclosure, and
   licensing gates.

Native does not mean trained from random initialization or free of external
foundation models. The first useful implementation may use an existing
sequence model, graph model, or language model as a component. What makes the
system native is the state contract, teacher pipeline, authority model, and
evaluation regime.

## 3. Existing substrate

The current repository constellation already provides distinct parts of the
teacher system.

| Surface | Proposed role | Current design evidence |
| --- | --- | --- |
| Root control plane | Contracts, schemas, governance, receipts, cross-repo adoption | Existing machine-readable catalogs, QGIA closed-loop contract, session and validation tooling |
| GUMAS simulation architecture | World-state transitions and controlled scenario generation | Scenario, simulation, and generated-output infrastructure |
| CloudBank QSFE | Agent-network belief propagation and scalable episode generation | Seeded network simulations, reliability-weighted propagation, API and test surfaces |
| QGIA Knowledge Library | Evidence semantics, curated domain knowledge, eventual resolved outcomes | Evidence-oriented corpus and an adoption-ready closed-loop authority contract |
| QGIA Knowledge Spine | Forecast semantics, priors, calibration, resolution policy | Forecast schemas and methodology structure; canonical ledgers still require adoption and population |
| CanonRec | Invariant enforcement and canonical promotion gate | Deterministic reconciliation and authority-preserving workflows |
| DuelSim | Focused adversarial or paired-agent scenario source | Separate simulation boundary suitable for later episode adapters |

This is enough to justify a design and data-contract phase. It is not yet enough
to claim that a training-ready corpus exists.

### 3.1 Evidence snapshot

The design inspection on 2026-07-29 found:

- the root QGIA closed-loop package is adoption-ready but not active in the two
  QGIA repositories
- the library and spine have independent authority boundaries and validators
- canonical QGIA forecast, prior, outcome, and calibration surfaces are not yet
  populated enough to train or score a forecasting model
- CloudBank's QSFE can generate structured belief propagation, but its current
  public result shape does not preserve the full latent belief trajectory
- a shared stochastic runtime can advance random state across calls, so seed
  isolation and replay receipts must become explicit dataset requirements
- some legacy and canonical QGIA data paths coexist and should be normalized
  before they become training inputs
- the QGIA Library's local checkout contains pre-existing uncommitted work and
  was intentionally left untouched by this proposal

These are tractable contract and adapter gaps, not evidence against the model.

## 4. The model should predict state, not prose

The first ASM target should be a structured transition bundle:

- world-state delta
- event labels and event payload summaries
- epistemic-state delta
- forecast distribution
- calibrated confidence components
- constraint or invariant risk
- terminal outcome distribution when the scenario defines one

Text can be attached as:

- an intervention description
- an observation
- a retrieved evidence item
- an explanation of a structured transition

Text should not replace typed state. A fluent paragraph is difficult to replay,
score, reconcile, or promote safely. A structured state delta can be validated,
compared against a teacher trajectory, and rendered into prose afterward.

## 5. Proposed architecture

The architecture has two planes.

~~~mermaid
flowchart LR
    SC["Scenario compiler"] --> GW["GUMAS world teacher"]
    EM["Evidence and visibility masks"] --> QE["QGIA and QSFE epistemic teacher"]
    QL["QGIA Library semantics"] --> QE
    QS["QGIA Spine forecast semantics"] --> QE
    GW --> EA["Episode assembler"]
    QE --> EA
    EA --> CV["CanonRec and deterministic validators"]
    CV --> DS["Immutable dataset manifest and shards"]
    DS --> LM["Aurora State Model learner"]
    LM --> SI["Simulation-only inference"]
    SI --> CV
~~~

### 5.1 Teacher plane

The teacher plane creates governed episodes.

1. A scenario compiler selects a scenario version, parameter set, intervention
   family, visibility mask, and seed bundle.
2. A GUMAS-compatible simulator produces world-state transitions and events.
3. QGIA/QSFE produces the corresponding belief trajectory, disagreement
   structure, forecasts, and confidence decomposition.
4. CanonRec and repo-local validators check invariants, provenance, replay, and
   authority labels.
5. An episode assembler writes immutable episode shards and a dataset manifest.
6. A disclosure gate decides whether the artifact may remain internal, be
   shared for evaluation, or become eligible for a public model release.

### 5.2 Learner plane

The learner plane consumes immutable, versioned episodes.

1. A serializer maps heterogeneous state graphs into a canonical token, graph,
   or hybrid representation.
2. A model encodes current world state, partial observations, belief state, and
   intervention.
3. Separate heads predict state delta, events, belief delta, forecast
   probability, and confidence.
4. A constraint-aware decoder emits the v1 episode target shape.
5. Deterministic validators reject invalid proposals.
6. Evaluation compares the learned rollout with held-out teacher trajectories
   and counterfactual pairs.

The learner never writes directly to canonical state. It proposes simulated
transitions at simulation authority.

## 6. Model families

The contract should remain architecture-neutral. Three implementation families
are plausible.

### 6.1 Structured sequence model

Serialize typed state and event records into a deterministic sequence and
fine-tune an existing transformer. This is the fastest path to a working
baseline and handles mixed symbolic/text inputs well. Its main weakness is
maintaining long-range graph consistency.

### 6.2 Graph transition model

Represent agents, assets, institutions, locations, claims, and relationships as
a dynamic graph. Predict node/edge deltas and event distributions. This is
better aligned with QSFE and multi-agent state, but requires stronger adapters
and a more specialized training stack.

### 6.3 Hybrid state model

Use graph encoders for world and belief topology, a sequence component for
evidence and event history, and typed decoder heads for outputs. This is the
strongest long-term design, but it should follow a simpler baseline so its
benefits can be measured.

The recommended order is structured baseline, graph baseline, then hybrid.

## 7. Training curriculum

### Phase A: deterministic one-step imitation

Train on one-step state deltas from simple, replayable scenarios. The objective
is schema-correctness, event accuracy, and low state-delta error.

### Phase B: epistemic dynamics

Add evidence visibility, source reliability, priors, dissent, echo effects, and
belief updates. Score both population aggregates and subgroup trajectories.

### Phase C: multi-step rollout

Train and evaluate autoregressive rollouts. Measure divergence by horizon and
require invariant validation at every step.

### Phase D: counterfactual pairs

Generate paired episodes that differ in one controlled intervention, evidence
mask, or seed. Train the model to preserve causal sensitivity without
memorizing terminal narratives.

### Phase E: distillation and serving

Use the learned model as a fast proposal engine under CloudBank orchestration.
Keep deterministic simulation as the teacher, audit source, and escalation
path.

## 8. QGIA's central role

QGIA is not merely training text. It supplies the model's epistemic grammar.

The Knowledge Library should contribute:

- typed evidence records and provenance
- domain and entity references
- source reliability annotations
- resolved outcome records when real outcomes exist
- curated case material after explicit promotion

The Knowledge Spine should contribute:

- forecast record structure
- priors and base rates
- resolution policy
- calibration reports
- methodology and confidence decomposition

QSFE contributes a simulation analogue of those surfaces:

- synthetic evidence arrival
- partial observability
- network-mediated belief propagation
- dissent and echo structures
- synthetic forecast distributions

Synthetic QGIA-shaped outputs must remain distinct from the real evidence and
truth ledgers. The common schema is useful; the authority level is not
interchangeable.

## 9. Evaluation

A credible ASM evaluation suite needs more than next-token loss.

### 9.1 Structural validity

- schema-valid output rate
- identifier and reference integrity
- valid state transitions
- no prohibited authority escalation

### 9.2 One-step fidelity

- numerical state-delta error
- categorical event precision, recall, and F1
- belief-distribution distance
- probability Brier score and log loss

### 9.3 Rollout fidelity

- divergence by horizon
- invariant violation rate
- terminal-outcome distribution distance
- recovery after teacher-state correction

### 9.4 Counterfactual sensitivity

- directionally correct response to intervention
- invariance to irrelevant serialization changes
- controlled-seed consistency
- separation between uncertainty caused by hidden state and uncertainty caused
  by stochastic dynamics

### 9.5 Epistemic calibration

- calibration by scenario family
- calibration by visibility regime
- calibration by evidence reliability
- calibration by network topology and dissent level

No single aggregate score should be treated as sufficient.

## 10. Governance and safety

The principal risks are architectural, not only model-theoretic.

### Synthetic truth leakage

Simulated outcomes could be mistaken for adjudicated real-world outcomes.
Mitigation: every record carries authority and classification; synthetic
episodes are prohibited from QGIA truth ledgers.

### Canon mutation

A learned model could emit plausible but invalid canonical state.
Mitigation: model output remains a proposal; CanonRec and deterministic
validators retain final authority.

### Scenario leakage

Near-duplicate scenarios could cross train/test boundaries.
Mitigation: split by scenario family, generator version, and intervention
lineage, not by individual row.

### Reproducibility failure

Stochastic services can produce untraceable drift.
Mitigation: isolate seed scopes, hash configs, record repository revisions, and
require replay receipts.

### Sensitive or proprietary data exposure

QGIA sources may not be suitable for public weights or hosted inference.
Mitigation: classification-aware manifests, training allowlists, artifact
lineage, and a disclosure review before any model publication.

### Simulator overfitting

The model may imitate simulator assumptions rather than reality.
Mitigation: label it a simulation model, use multiple generators, hold out
scenario families, compare against real resolved outcomes only when the QGIA
closed loop is populated, and communicate epistemic limits.

## 11. First implementable slice

The proposed first slice is ASM-001: Reproducible World-and-Belief Episode.

It should contain:

- one 20-turn GUMAS-compatible scenario
- one intervention family
- three observation or evidence masks
- two world-simulation seeds
- two QGIA/QSFE seeds
- 12 governed episode manifests
- no model training

Exit criteria:

- all episodes validate against the v1 schemas
- repeated generation with the same seed bundle is byte-stable or produces an
  explicitly documented nondeterminism receipt
- world state and belief state remain separately addressable
- every episode names exact source revisions and config hashes
- no synthetic record is written to canonical QGIA truth or forecast ledgers
- a dataset manifest can be regenerated and audited

This slice tests the hardest assumption first: whether Aurora can produce a
stable learning object from its existing engines.

## 12. Roadmap

1. Adopt the v1 episode and epistemic trace contracts in repo-local adapters.
2. Implement ASM-001 and publish only internal synthetic fixtures and receipts.
3. Build a deterministic serializer and one-step baseline.
4. Establish held-out scenario-family evaluation.
5. Add counterfactual pairs and multi-step rollouts.
6. Populate and validate the real QGIA closed loop before attempting
   real-world calibration claims.
7. Introduce a graph or hybrid model only after the sequence baseline exposes
   measurable limitations.
8. Evaluate CloudBank serving behind an explicit simulation-only API.
9. Run disclosure, license, and canon-authority reviews before any wider
   distribution.

## 13. Conclusion

An Aurora-native learned state model is feasible and strategically coherent,
provided the project resists the temptation to begin with model training.

The durable asset is the governed episode factory: a repeatable method for
turning Aurora simulation, QGIA epistemics, and CanonRec validation into
immutable learning objects. Once that exists, model architecture becomes an
empirical choice rather than a speculative commitment.

The immediate work is therefore contractual and infrastructural. Define state,
capture belief, isolate authority, record provenance, prove replay, and only
then train.

## Appendix A: Companion artifacts

- System specification: docs/AURORA_STATE_MODEL_SYSTEM_SPEC_v0_1.md
- Implementation plan: docs/AURORA_STATE_MODEL_IMPLEMENTATION_PLAN_v0_1.md
- Machine-readable contract:
  catalog/contracts/aurora_state_model_contract_v0_1.json
- Episode schema: catalog/schemas/aurora_state_episode_v1.schema.json
- Epistemic trace schema:
  catalog/schemas/aurora_epistemic_trace_v1.schema.json
- Dataset manifest schema:
  catalog/schemas/aurora_dataset_manifest_v1.schema.json
