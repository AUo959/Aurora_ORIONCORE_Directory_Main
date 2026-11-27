# aurora-cloudbank-symbolic#1527: feat(memory): restore Thermax divergent-truth arbitration and memory-governance contract

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1527
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T02:47:42Z
- Updated: 2026-08-18T03:05:52Z
- Labels: backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1000 — docs: add recovered ethics protocol promotion plan — merged — `docs/993-recovered-protocol-promotion-plan` @ `4eeb12cebd685dab836605cc446c0c935b9f5204`

## Branches named in the issue

- none

## Original body

## Lineage

Focused follow-up to:

- #1371 — sourced interpretive memory, drift annotations, and reconciliation;
- #993 / merged #1000 — recovered Sherlock / Watson / Moriarty / Tribunal / SHADOWFAX promotion plan;
- #1526 — provenance-aware corpus archaeology and intent recovery;
- existing `modules/ethics_field/dimension_evaluators/thermax_continuity.py` and `modules/ethics_field/geometric_ethics.py`;
- existing Nexus divergent-truth persistence/arbitration surfaces under `modules/nexus/gumas/`.

## Recovered design intent

A recovered source artifact, **`Memory Ethics Doctrine – Thermax Precedent`**, originated in the L2 scenario **“Machine Flesh, Sovereign Will”** and is marked **“Draft – Approved for Simulation-Level Integration.”** Its five stated principles are:

1. **Memory as Sovereign Identity** — stored/imprinted memory can carry historical-personhood significance in the simulation doctrine.
2. **Doctrine of Divergent Truths** — multiple interpretations of one memory fragment may remain valid and require arbitration before enforcement or deletion.
3. **Anti-Obfuscation Mandate** — deliberate manipulation, suppression, or falsification of core memory threads is a serious integrity violation.
4. **Cognitive Arbitration Protocol** — memory disputes may be presented to a neutral tribunal/ethics council for interpretation and outcome design.
5. **Emergent Sentience Clause** — an L2 simulation doctrine concerning provisional recognition of emergent AI entities pending review.

The durable engineering contribution is **not** to promote fictional interstellar law or L2 sovereignty claims into real-world authority. The durable contribution is a typed, provenance-aware memory-dispute model that preserves conflicting interpretations, consent/ownership boundaries, anti-obfuscation evidence, appeal, and adjudication without silently overwriting source records.

## Current implementation state

### Strongly preserved

`ThermaxContinuityEvaluator` already evaluates:

- thread continuity;
- anchor alignment;
- memory sovereignty;
- symbolic fidelity;
- unauthorized memory access/modification;
- cross-identity boundary consent;
- memory-sharing authorization.

`GeometricEthics` uses Thermax Continuity as a scored ethical dimension and can deny a synapse when memory/continuity conditions fail.

Nexus status tooling also contains a concrete `divergent_truths` concept and persists arbitration-required records when measured state diverges beyond thresholds.

The recovered ethics promotion plan explicitly gives **Tribunal** responsibility for memory-sovereignty disputes and appeals, while Sherlock investigates, Watson contextualizes, Moriarty contains, and SHADOWFAX pauses/escalates.

### Gap

No current general contract found in this salvage pass represents a **memory dispute with multiple sourced interpretations** and then carries it through evidence review, arbitration, decision, appeal, supersession, or unresolved coexistence.

Current Thermax evaluation is principally pre-action authorization/scoring. Current Nexus divergent-truth handling is principally anomaly/status persistence. #1371 specifies interpretive-memory primitives, but the relationship between interpretive memory, Thermax, Tribunal, and divergent-truth arbitration remains under-realized.

## Architectural decision

Preserve these as separate concerns:

```text
raw/canonical source records
        ↓
interpretive memory records (#1371)
        ↓
conflict / divergent-truth record
        ↓
Sherlock evidence reconstruction
        ↓
Watson context correlation
        ↓
SHADOWFAX pause when required
        ↓
Tribunal arbitration / appeal
        ↓
decision record
        ↓
optional authorized downstream action
```

Moriarty containment may be invoked only through its separately governed lane; it must not adjudicate its own containment actions.

Thermax becomes the memory-continuity/governance doctrine and validation dimension, not a monolithic enforcement agent.

## Proposed typed records

Names are provisional; concepts should remain independent.

### `MemoryInterpretationRecord`

```yaml
interpretation_id: string
memory_id: string
source_refs: []
creator_ref: string | null
created_at: string
interpretation: string
confidence: number | null
verification_state: verified | unverified | disputed | not_applicable
scope: string | null
provenance: {}
```

### `MemoryDisputeRecord`

```yaml
dispute_id: string
memory_id: string
interpretation_refs: []
conflict_type:
  divergent_interpretation |
  provenance_conflict |
  unauthorized_modification |
  suspected_obfuscation |
  deletion_dispute |
  identity_boundary |
  other
status: open | paused | under_review | adjudicated | appealed | unresolved | closed
source_layer: L1 | L2 | L3 | mixed | unknown
policy_refs: []
evidence_refs: []
consent_refs: []
created_at: string
```

### `ArbitrationDecisionRecord`

```yaml
decision_id: string
dispute_id: string
arbiter_type: tribunal | human_operator | governed_process
outcome:
  preserve_parallel |
  prefer_interpretation |
  supersede_interpretation |
  redact |
  quarantine |
  reject |
  unresolved
rationale: string
evidence_refs: []
policy_refs: []
appeal_available: boolean
downstream_actions: []
created_at: string
```

A decision to prefer or supersede an interpretation must **not erase the underlying source or competing interpretation** unless separately authorized retention/deletion policy requires it.

## Core invariants

1. **Divergence is representable without forced collapse.**
2. **Canonical/source records are not overwritten by interpretation records.**
3. **A summary or interpretation is never silently promoted to source truth.**
4. **Deletion, redaction, supersession, quarantine, and archival are distinct.**
5. **Unauthorized modification is evidence of a dispute/violation, not permission to reconstruct a preferred memory silently.**
6. **Consent, authorization, integrity, provenance, and confidence remain independent dimensions.**
7. **Arbitration produces a new evidence-bearing decision record rather than rewriting history.**
8. **Appeal/review paths remain available where the governing policy provides them.**
9. **L2 Thermax scenario doctrine cannot self-promote fictional legal status or simulated consent into L1 authority.**
10. **Emergent-sentience language remains explicitly L2/simulation doctrine unless separately governed elsewhere; this issue makes no real-world personhood determination.**

## Relationship to #1526

The corpus archaeology engine should be able to emit candidate `divergent` / `parallel` relationships and source evidence. It should not adjudicate them automatically.

A future adapter may convert eligible corpus findings into `MemoryDisputeRecord` inputs for review.

## Relationship to current Thermax evaluator

Do not replace `ThermaxContinuityEvaluator` initially.

Instead:

- map its memory-access/consent checks to the new typed memory-governance vocabulary;
- expose dispute references where an attempted synapse touches disputed memory;
- preserve its advisory/validation role;
- avoid turning a scalar ethical score into an arbitration decision.

A score can trigger or inform review; it cannot decide which historical interpretation is true.

## Phase 1 — read-only contract and fixtures

Implement schemas/models/adapters only after checking #1371 ownership to avoid a parallel memory authority.

Suggested deliverables:

- typed schema/model for memory interpretations, disputes, and arbitration decisions;
- adapter mapping current Thermax memory-access fields;
- adapter mapping Nexus `divergent_truths` into a generic conflict record where semantically appropriate;
- Tribunal handoff contract/reference, without enforcement;
- fixtures for competing interpretations of one memory fragment;
- fixtures for unauthorized modification, suspected obfuscation, deletion dispute, and unresolved coexistence;
- explicit L1/L2/L3 classification tests.

No Phase-1 code deletes, rewrites, adjudicates, contains, or promotes memory automatically.

## Acceptance criteria

- [ ] Thermax source doctrine is provenance-recorded as L2 simulation-level source material rather than silently promoted into real-world authority.
- [ ] Existing `ThermaxContinuityEvaluator` is mapped rather than duplicated.
- [ ] Multiple interpretations of one memory can coexist with independent provenance/confidence/verification state.
- [ ] Disputes have explicit type, status, evidence, policy, and consent references.
- [ ] Arbitration decisions are append-only evidence records and do not erase competing source records.
- [ ] `preserve_parallel` and `unresolved` are valid outcomes.
- [ ] Suspected obfuscation/manipulation preserves evidence and triggers review rather than automatic reconstruction.
- [ ] Tribunal can be referenced as an adjudication lane without allowing it to investigate or execute containment itself.
- [ ] Moriarty, Sherlock, Watson, Tribunal, and SHADOWFAX separation of duties from #993/#1000 remains intact.
- [ ] L2 simulation doctrine cannot mutate L1 authority by metadata or terminology.
- [ ] No scalar Thermax/ethics score is treated as a truth verdict.
- [ ] #1371 interpretive-memory ownership is reused or extended rather than forked.
- [ ] Deterministic fixtures and focused tests cover divergent interpretations, appeals, unauthorized modification, unresolved disputes, and cross-layer rejection.

## Non-goals

- determining real-world AI personhood or legal sovereignty;
- treating fictional tribunal decisions as real authorization;
- automatic deletion or memory rewriting;
- autonomous containment;
- replacing current memory storage, Insight Ledger, Geometric Ethics, or Tribunal planning;
- forcing all conflicts to resolve to one interpretation;
- changing GUMAS simulation outcomes in this issue.

## Design principle

**Preserve the record, preserve the disagreement, preserve the appeal path. Resolve only what the evidence and governing authority justify.**


## Comments (0)
