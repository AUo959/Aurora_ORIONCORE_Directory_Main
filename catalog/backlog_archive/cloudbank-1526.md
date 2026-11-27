# aurora-cloudbank-symbolic#1526: feat(salvage): build provenance-aware corpus archaeology and intent recovery engine

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T02:36:03Z
- Updated: 2026-08-18T04:03:55Z
- Labels: none
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#46 — deps: bump dotenv from 17.0.0 to 17.0.1 — closed — `dependabot/npm_and_yarn/dotenv-17.0.1` @ `71b5dfce8e55d94042850236ccd674aa4cb6f213`
- aurora-cloudbank-symbolic#1343 — feat: add the triggered Narrative River scene workflow — merged — `agent/narrative-river-adapter-spec` @ `24d2b3f396eb3d338abd24e7156352b4d7987bdb`
- aurora-cloudbank-symbolic#1382 — feat(salvage): add read-only legacy artifact inventory and archive safety gates — merged — `feat/1375-readonly-legacy-inventory` @ `3c4723798ac121a2306efddd0c66b03d9092ffb2`
- aurora-cloudbank-symbolic#1501 — feat(l1): add governed staffing runtime — merged — `codex/cloudbank-issue-1453-l1-staffing-runtime` @ `b27ecb7138f06c38a90eabd46c6caea33daf6f7d`
- aurora-cloudbank-symbolic#1506 — sim: restore recovered complete GUMAS v2 tactical lineage for deterministic control run — open (draft) — `agent/gumas-flash-rebellion-battle-baseline` @ `40b5866dba2d8ac3a0636736dcf069adaa451c8a`
- aurora-cloudbank-symbolic#1533 — feat(salvage): add deterministic corpus archaeology Phase 1 — merged — `feat/1526-corpus-archaeology-phase1` @ `6b7dffdd94dedce920223addc37497380dc5ad62`
- aurora-cloudbank-symbolic#1536 — feat(salvage): add custody-release corpus adapter — merged — `feat/1535-corpus-custody-release-adapter` @ `f22f48a0dd91479dd30047ce08adafc2259e8bb2`

## Branches named in the issue

- `feat/1526-corpus-archaeology-phase1` — not found on remote

## Original body

## Parent

Extends #1369 — Aurora/GUMAS selective salvage integration.

Related foundations:

- #1375 / merged #1382 — read-only legacy artifact inventory, custody, hashing, archive safety, and duplicate reporting;
- #1371 — sourced interpretive memory, drift annotations, and reconciliation;
- #1374 / #1376–#1380 — continuity packages, beacon profiles, replay/inheritance, relay, trust, consent, and lifecycle contracts;
- `threadcore_registry.json` and `modules/reflective_autonomy/threadcore_payloads/threadcore_v3.5.1_macroready.json` — surviving THREADCORE reflection/indexing design;
- `modules/reflective_autonomy/threadcore_tagging.py` — current weighted classification/priority foundation;
- `ops/work_queue/` — ranked cross-platform work queue and decision/gate surfaces.

## Recovered design intent

Legacy Aurora/THREADCORE work repeatedly defined a capability broader than file inventory:

1. inventory and index a thread/corpus without overwriting its identity;
2. generate useful functional identity/alias metadata for navigation;
3. capture reflective snapshots including context summary, last active command, drift/anchor state, and **unutilized logic**;
4. surface unused updates, patches, accepted ideas, unresolved work, and other design intent that did not make it into later implementations;
5. rank material by importance/relevance so large constellations remain navigable;
6. preserve source lineage while comparing historical intent against later implementations;
7. feed recovered work into an explicit backlog rather than silently discarding it.

The canonical THREADCORE v3.5.1 payload still declares `reflection_snapshot` and `unutilized_logic`, but current CommandNode reflection is primarily a state dump; repository search does not show a general extractor that identifies unrealized work from a corpus. `threadcore_tagging.py` provides useful category/priority scoring, but not the richer explainable relevance model originally intended.

Later Aurora design also proposed automated innovation capture by scanning logs, commits, and anchor transitions for emergent patterns and feeding them into an innovation backlog. This is the continuous form of the same capability.

## Architectural decision: Aurora-born, domain-neutral core

This capability must not be hard-coded to Aurora lore, ChatGPT threads, GitHub, or software engineering.

The underlying problem is general:

> Given a large, heterogeneous corpus, recover important facts, decisions, design intent, unresolved work, lineage, contradictions/divergences, and synthesis candidates without erasing provenance or treating absence as rejection.

Potential non-Aurora applications include research literature, legal/document discovery, scientific archives, organizational records, historical collections, product/design histories, and other multi-source corpora.

Implement a neutral analysis core with adapters/profiles for Aurora-specific semantics.

```text
neutral corpus engine
    ├── generic document/source adapters
    ├── provenance + evidence model
    ├── extraction / synthesis / ranking
    └── optional domain profiles
            └── Aurora / THREADCORE profile
```

Aurora terminology such as THREADCORE, anchors, capsules, glyphs, and drift may be preserved by the Aurora profile but must not be required by the core schema.

## Preservation presumption

The engine must encode this salvage rule:

> Absence of implementation is not evidence of intentional rejection.

A recovered design intent defaults to preservation/investigation unless affirmative evidence supports rejection, intentional supersession, safety exclusion, or obsolescence.

A later implementation counts as a successor only when it adequately preserves the important capability and intent.

## Source relationship model

Do not reduce cross-source comparison to `confirmed` / `false`.

Support relationships such as:

- `convergent`
- `successor`
- `parallel`
- `merged`
- `divergent`
- `superseded`
- `dormant`
- `lost_in_transition`
- `orphaned`
- `uncertain`

Multiple histories may coexist. Git history, native ChatGPT history, recovered packages, other agent/platform histories, and later public artifacts are evidence surfaces with distinct provenance; disagreement does not by itself prove that one did not occur.

## Proposed capability model

A salvage candidate should be able to represent at least:

```yaml
candidate_id: string
source_refs: []
source_platforms: []
source_dates: []

subject:
  title: string
  functional_identity: string | null

design_intent:
  original_problem: string | null
  requested_capability: string | null
  stated_constraints: []

historical_state:
  status: proposed | approved | implemented | partial | rejected | unknown
  evidence_refs: []

lineage:
  relationships: []
  descendants: []
  current_matches: []

preservation:
  implementation_preserved: boolean | unknown
  capability_preserved: boolean | unknown
  intent_preserved: boolean | unknown
  intent_delta: number | null

recovery:
  disposition: restore | integrate | evolve | merge | preserve | investigate | reject_with_evidence
  rationale: string
  confidence: number
  dependencies: []

ranking:
  relevance_score: number
  components: {}
```

Exact schema names may change during design review; the independent concepts should remain.

## Extraction classes

The first implementation should identify, with source evidence:

- explicit decisions;
- explicit approvals/rejections;
- requirements and constraints;
- unresolved questions;
- TODOs / deferred work;
- proposed patches or improvements;
- accepted-but-unimplemented ideas;
- implemented capabilities lacking later descendants;
- apparently lost or orphaned capabilities;
- contradictions and divergent truths;
- later successors and partial successors;
- important design rationale;
- emerging/repeated concepts across sources;
- synthesis candidates that combine related findings.

Do not infer intentional rejection merely because an item disappears from later material.

## Explainable relevance scoring

Recover the old thread-importance intent as a general corpus-ranking function.

The score should be inspectable rather than an opaque model judgment. Candidate components may include:

- explicit human importance;
- design centrality;
- unresolved commitments;
- dependency/downstream count;
- implementation gap;
- recurrence across independent sources;
- canon/governance relevance where a domain profile defines it;
- safety/ethics significance where applicable;
- current operational relevance;
- source/evidence confidence.

The generic core must permit domain-specific scoring extensions without requiring Aurora-specific concepts.

`modules/reflective_autonomy/threadcore_tagging.py` should be treated as a possible partial predecessor, not automatically replaced.

## Read-only first implementation

Phase 1 must be analytical only.

Suggested surfaces:

```text
tools/salvage/corpus_archaeology.py
schemas/salvage/corpus_salvage_candidate.schema.json
```

Names are provisional.

Inputs should initially support explicit local files/directories and deterministic prepared fixtures. Future connectors may supply source material, but the core analyzer must not require network access.

Outputs:

- deterministic machine-readable candidate report;
- human-readable synthesis report;
- source/evidence map;
- explainable ranking components;
- unresolved/uncertain findings;
- optional proposed work-queue projection.

No Phase-1 output automatically writes to the Aurora work queue, opens issues, edits canon, executes recovered code, or mutates source material.

## Integration with existing salvage pipeline

Reuse #1375/#1382 custody and inventory concepts rather than building another archive scanner.

Recommended flow:

```text
source custody / inventory
        ↓
normalized corpus records
        ↓
provenance-aware extraction
        ↓
lineage + intent comparison
        ↓
relevance scoring
        ↓
salvage candidates
        ↓
human review
        ↓
optional work-queue / issue / implementation promotion
```

File-level duplicate detection and semantic/capability equivalence must remain distinct. Same basename is never sufficient evidence that two artifacts or implementations are semantically duplicates.

## Acceptance criteria — Phase 1

- [ ] Neutral corpus/source schema does not require Aurora-specific terminology.
- [ ] Aurora/THREADCORE semantics are implemented as an additive profile/adapter.
- [ ] Every extracted claim/candidate retains resolvable source provenance.
- [ ] User/human decisions and assistant/model proposals can be represented as distinct evidence types where source metadata permits.
- [ ] Absence of implementation does not automatically produce a rejection/superseded disposition.
- [ ] Cross-source divergence can preserve multiple concurrent histories.
- [ ] Design intent, implementation state, capability preservation, and intent preservation are independent fields.
- [ ] Relevance scores expose component contributions.
- [ ] Unutilized/unrealized work can be extracted from deterministic fixtures.
- [ ] Exact, likely, and semantic duplication are not conflated.
- [ ] Current implementation matches can be represented as full, partial, or uncertain successors.
- [ ] Output ordering and identifiers are deterministic for fixed inputs/configuration.
- [ ] Read-only operation does not mutate the source corpus, Git, work queue, canon, or runtime.
- [ ] Tests cover conflicting sources, parallel histories, dormant intent, explicit rejection, partial successors, and missing implementation evidence.
- [ ] Security/custody boundaries from #1375/#1382 are reused for archive/file ingestion where applicable.

## Follow-on phases

After the read-only contract is proven:

1. **Corpus-scale synthesis:** clustering, repeated-pattern discovery, lineage graphs, and compression with omission manifests.
2. **Continuous innovation capture:** operator-triggered scanning of new logs/commits/documents against prior findings.
3. **Work-queue adapter:** proposed candidate → queue item mapping with explicit human review.
4. **Cross-platform adapters:** ChatGPT/project exports, Git history, issue/PR histories, other agent session exports, research/document stores.
5. **Portable productization:** extract the neutral engine from Aurora through OPAL2-style shipment discipline so it can operate independently on non-Aurora corpora.

## Non-goals

- hidden or universal model memory;
- claiming access to sources that were not supplied or connected;
- automatic canon promotion;
- automatic code execution;
- autonomous destructive cleanup;
- using later Git state to erase native or cross-platform history;
- freezing original intent as an immutable constraint on future design;
- forcing all corpora into Aurora symbolic vocabulary;
- replacing existing inventory, memory, ledger, queue, or continuity authorities.

## Boundary impact

Read-only salvage/intelligence capability in the first phase. No L1 authority change, no L2/GUMAS mutation, no L3 policy mutation, no canon promotion, no source rewrite, and no autonomous external action.

## Design principle

Preserve intent by default. Preserve implementation when useful. Modernize architecture when appropriate. Reject only with evidence.


## Comments (11)

### AUo959 — 2026-08-18T02:43:21Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5322839632>

## THREADCORE fine-grained salvage pass — first capability reconciliation

This comment records the first detailed comparison between recovered native Aurora/THREADCORE design intent and current CloudBank implementation. It follows the preservation presumption in this issue: absence of implementation is not evidence of rejection.

### Source/evidence discipline

The native history and Git/public history are treated as distinct evidence surfaces. A mismatch does not automatically invalidate either history. User-requested behavior is distinguished from assistant-generated implementation claims; implementation claims require artifact/code evidence.

### Recovered user-level THREADCORE requirements

The legacy native history contains explicit requirements for:

- full thread inventory/indexing before THREADCORE output;
- augmentation without overwriting thread identity or decision-making;
- a unique thread field / durable identity;
- functional thread titles and sidebar aliases for navigation and archival use;
- dynamic content-driven aliases rather than repeated templates;
- preservation of existing thread/hash identity while adding a unique public-facing alias;
- parent/sibling reflective cohesion;
- anchors, anchor fallback, and anchor propagation;
- standardized reflective snapshots including context summary, last active command, **unutilized logic**, drift, anchor hash, glyph-sync state, and timestamp;
- drift logging and explicit return-to-anchor behavior;
- matched `+DRIFT→` / `+RETURN→` semantics so divergence is paired with a reconciliation route;
- prior capsule-seal dependencies where appropriate;
- **automatic sealing after 48 hours idle/no edits**;
- ZIPWIZ beacon contact and PATCHWEAVER interoperability;
- legacy bridge compatibility across THREADCORE generations;
- portable export/transfer behavior and named continuity commands such as `EXPORTTHREAD`, `SEAL`, `LOCKMEM`, `SYNCANCHORS`, `THREADSYNC`, and related recovery operations.

A July 2025 enhancement further specified content/spirit-based alias generation with intuitive glyph/emoji indexing, unique/collision-resistant public aliases, preserved thread hash identity, sidebar organization/sorting/archival use, and backward-compatible module/tool behavior. The historical implementation proposal used a standalone alias generator, but the requirement is more important than the specific proposed code.

### Current implementation comparison

| Capability | Current evidence | Relationship | Recovery posture |
|---|---|---|---|
| Thread content classification | `threadcore_tagging.py`, `scripts/threadcore_classifier.py` | partial successor | extend |
| Importance/relevance | low/medium/high category priority based on keyword weights | partial successor | generalize to explainable multidimensional scoring |
| Reflective snapshot | registry/payload declares `reflection_snapshot`; CommandNode `reflect()` is a state dump | partial | **restore full reflective analysis** |
| `unutilized_logic` | still declared in canonical payload; no extractor found | lost-in-transition | **P0 restore** |
| Unused patch/idea harvesting | adjacent salvage/work-queue infrastructure, no general extractor | lost-in-transition | **P0 restore** |
| Dynamic unique aliases | static payload/index survives; no general current generator found | dormant / partial | restore as presentation/profile adapter |
| Identity preservation | continuity/UTB work strongly advances this | successor | retain modern lineage |
| Anchor validation | registry/linter support | successor/partial | harden |
| High-drift detection | capsule linter warns on drift threshold | successor/partial | extend with lineage-aware reconciliation |
| `DRIFT→ / RETURN→` pairing | no equivalent validator found in current search | dormant | restore underlying divergence/reconciliation contract |
| Capsule sealing | linter detects `capsule_unsealed`; correction engine plans `seal_capsule` | partial successor | extend lifecycle semantics |
| 48h idle auto-seal | no current implementation found | dormant / lost-in-transition | restore carefully as policy-driven lifecycle transition |
| PATCHWEAVER | current adapter mainly tracks connection state | partial prototype | recover patch-analysis/integration intent before expanding |
| ZIPWIZ | beacon adapter + modern continuity packages/UTB | evolved successor | favor modern continuity implementation |
| Thread transfer | `ThreadTransferBridge` exists with real state/handshake validation, but several behaviors remain simplified | prototype successor | reconcile with UTB/modern policy |
| Non-destructive correction | `capsule_linter.py` + `autonomic_correction_engine.py` | strong modern evolution | reuse as safety foundation |
| Continuous innovation capture | historical roadmap idea; no general corpus observer found | dormant | follow-on phase of corpus archaeology engine |

### Important recovery interpretation

The old `+DRIFT→ / +RETURN→` syntax should not necessarily be restored literally. Its durable intent is stronger and domain-neutral:

> A recorded divergence, branch, contradiction, or exploratory departure should carry either a reconciliation/return path or an explicit unresolved state; it must not disappear silently.

Likewise, 48-hour auto-seal should not mean a background process silently mutates arbitrary data. Its durable intent is:

> Stable inactive contexts should transition into an integrity-bound preservation state through an explicit, auditable lifecycle policy.

A modern implementation can preserve that intent using policy/configuration, deterministic eligibility checks, a proposed transition receipt, and operator approval where mutation is involved.

### Proposed Phase-1 corpus-engine primitives added by this pass

1. `unrealized_work` extractor — requirements/approvals/patches with no adequate descendant.
2. `divergence_record` — source A/source B can remain parallel/divergent without forced resolution.
3. `reconciliation_path` — successor, merge, return, unresolved, or explicit rejection-with-evidence.
4. `relevance_components` — inspectable scoring rather than opaque priority.
5. `design_intent_record` — original problem, capability, constraints, descendants, intent delta.
6. `lifecycle_candidate` — active/dormant/seal-eligible/archived/superseded without automatic mutation.
7. `presentation_identity` — stable machine identity separate from human-facing title/alias.

### Architectural note

These primitives remain domain-neutral. THREADCORE is the first profile, not the schema vocabulary. In a legal corpus `divergence_record` may represent conflicting authority; in research it may represent competing hypotheses; in product history it may represent abandoned design branches; in software it may represent unmerged patches or architectural forks.

### Next salvage target

Continue the THREADCORE family through its closely coupled subsystems:

1. PATCHWEAVER — recover the intended patch discovery/composition/integration function versus the current connection adapter.
2. ZIPWIZ — separate packaging/transport/beacon intent from modern UTB/continuity successors.
3. THREADREFLECT — reconstruct the full reflection contract around snapshots, unutilized logic, drift and lineage.
4. Transfer/replay commands — map legacy vocabulary to current typed command/continuity contracts without reactivating unsupported ritual semantics.

No runtime or canon mutation is proposed by this comment.

### AUo959 — 2026-08-18T02:45:50Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5322857229>

## Fine-pass continuation — PATCHWEAVER, ZIPWizard, THREADREFLECT, and legacy command lineage

### PATCHWEAVER

Native Aurora history shows PATCHWEAVER's intended role was broader than applying a pre-supplied state diff. A particularly clear April 2025 requirement framed PATCHWEAVER v2.0 as an authorized repair system that should:

- diagnose symbolic/trust drift and ethical-anchor problems;
- repair only authorized content with consent;
- re-anchor and support recovery/return behavior;
- optimize/compress/retune where appropriate;
- optionally reconnect isolated Thread Fields;
- visualize or report drift;
- request approval before recovery;
- log results;
- preserve separation between Loom/continuity control and the affected field.

Later native usage also treats PATCHWEAVER as a restoration/integration mechanism for dormant logic and cross-thread integrity work.

Current Git contains a real `src/aurora/patching/patchweaver.py` implementation: ethics-gated `set`/`delete` state patching, before/after SHA-256 hashes, DLP provenance, history, injected state backends, and API integration. This is a genuine implementation descendant, not a stub. However, it starts after a patch has already been identified and does not itself recover candidate repairs from a corpus, diagnose lineage gaps, or build a proposed patch from unrealized intent.

**Relationship:** `parallel → merged/partial successor`.

**Preservation assessment:**

- safe patch application: strongly preserved;
- provenance/audit: strongly preserved;
- human/ethics gating: substantially preserved;
- diagnosis/recovery planning: partial;
- discovery/harvesting of dormant logic: not preserved in PatchWeaver itself;
- cross-thread repair/weaving: partial/uncertain;
- rollback: listed historically as intended/future behavior; current v1 implementation hashes state but does not provide full rollback-by-receipt.

**Recovery direction:** keep current PatchWeaver as the mutation/execution layer. Do **not** make it the corpus analyzer. #1526 should discover and justify candidate repairs; a future adapter can emit a reviewable PatchWeaver patch plan only after human approval and typed command authorization.

```text
corpus archaeology / THREADREFLECT
        ↓
recovery candidate + evidence
        ↓
human review / typed command contract
        ↓
PATCHWEAVER dry-run / patch plan
        ↓
ethics + authorization
        ↓
mutation + hashes + receipt + rollback path
```

### ZIPWizard

Cross-repository inspection materially changes the lineage assessment.

CloudBank's `src/bridges/zip-wizard/bridge.ts` is explicitly a stub: connection and archive methods currently return synthetic success-shaped responses pending a real API. But ZIPWizard also exists as the separate public repository `AUo959/zip_wizard`, with a substantial archive-management application and history.

Native Aurora history framed ZIPWizard as archive/capsule intelligence: unpacking, refactoring, securing, replaying/regenerating, packaging, deployment kits, per-agent packets, transmission/handoff, and continuity packaging. Later Aurora material narrows the cross-system role to capsule handoff/transmission handshake logic.

The standalone repo contains real archive-management/UI code and source surfaces for archive comparison, code analysis, navigation, security, and a pattern-recognition interface. Important caution: at least the inspected `pattern-recognition-engine.tsx` currently simulates analysis steps and generates mock patterns/organization suggestions rather than performing genuine semantic corpus analysis. README-level capability claims therefore exceed this inspected implementation in places.

**Relationship:** `parallel branch → independent product + incomplete bridge`.

**Preservation assessment:**

- archive/product identity: strongly preserved outside CloudBank;
- archive exploration UI: preserved;
- packaging/archive handling: substantive independent implementation exists;
- cross-Aurora transmission bridge: incomplete/stub in CloudBank;
- provenance-aware continuity packaging: modern UTB/continuity work is the stronger successor;
- intelligent corpus examination/extraction/synthesis: only partial; important opportunity for #1526;
- non-Aurora product relevance: very strong.

**Recovery direction:** treat `AUo959/zip_wizard` as a sibling product/source of reusable archive UX and handling concepts, not as a module to duplicate inside the corpus engine. The domain-neutral engine should expose analyzable corpus/package records that ZIPWizard could eventually consume as a UI/product surface.

Potential future architecture:

```text
#1526 neutral corpus archaeology engine
        ↕ typed package/report contracts
ZIPWizard archive exploration UI
        ↕
UTB / continuity-package formats
```

This would make ZIPWizard a plausible external-facing workstation for corpus archaeology without coupling the analytical core to Aurora.

### THREADREFLECT

The canonical THREADCORE payload still declares snapshot fields:

- `context_summary`
- `last_active_command`
- `unutilized_logic`
- `symbolic_drift`
- `anchor_hash`
- `glyph_sync_status`
- `timestamp`

Current `ThreadcoreAdapter.reflect()` returns current in-memory adapter state plus a timestamp. That preserves the verb but not the richer original analytical contract.

**Relationship:** `name preserved / capability narrowed`.

**Recovery direction:** restore THREADREFLECT as the Aurora profile over #1526's neutral reflection/extraction engine. The neutral core should know concepts such as summary, unresolved work, provenance, divergence, lineage, and evidence; the Aurora profile can additionally render anchors, drift, glyph/continuity status, and legacy-compatible snapshots.

### Legacy command vocabulary

Current `src/aurora/core/command_grammar/catalog.py` is a strong historical preservation surface. It retains provenance-backed definitions for `EXPORTTHREAD`, `LOCKMEM`, `RESTOREMAP`, `SYNCANCHORS`, `T1`, `TAGPATCH`, `TAGTRACE`, `THREADSEAL`, `THREADSYNC`, `THREADWAKE`, `DIAGNOW`, `REBUILDRECOVERY`, and others.

This is an excellent example of preserving vocabulary without pretending every verb is already safe executable behavior. Existing issue #1373 is the correct successor workstream: typed execution contracts, permissions, preconditions, dry-run behavior, receipts, errors, and rollback.

For #1526, command strings should be treated as **evidence of historical intent and workflow structure**. The corpus engine may identify a command reference and map it to its catalog definition/provenance, but it must never execute commands from recovered text.

### Updated subsystem boundary

```text
THREADREFLECT / #1526
  discover, compare, synthesize, rank, recover intent

PATCHWEAVER
  propose/apply authorized state transformations with evidence

ZIPWizard
  archive/package exploration and potentially a product-facing corpus UI

UTB / continuity packages
  portable preservation/interchange contract

command grammar + #1373
  human/tool control surface with typed execution semantics
```

This separation preserves the original constellation idea while making each responsibility testable and portable.


### AUo959 — 2026-08-18T02:54:33Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5322923534>

## Salvage checkpoint — memory, RiverCycle, ORION/GUMAS operations

The first fine-grained recovery cycle has now produced three focused workstreams while deliberately avoiding duplicate work already active elsewhere:

- **#1527 — Thermax divergent-truth arbitration and memory governance**
  - preserves multiple sourced memory interpretations;
  - separates evidence reconstruction/context/containment/adjudication;
  - extends rather than replaces current Thermax Continuity + Geometric Ethics + #1371/#1000.

- **#1528 — simulation-native RiverCycle pressure and feedback regulator**
  - restores the upstream persistent RiverCycle state provider assumed by Narrative River;
  - keeps GUMAS causality, RiverCycle state, RiverThread808 regulation, and Narrative River projection separate;
  - deterministic, provenance-bearing, passive/non-mutating first;
  - feedback/salmon-return candidates do not self-authorize upstream mutation.

- **#1529 — role-based workplace problem-solving runtime**
  - preserves the May-2026 native intent that Aurora can receive a problem and work it through as a relevant professional team;
  - builds over existing staffing, role, queue, evidence, agent, and command infrastructure rather than creating new authorities;
  - simulated role consensus is explicitly not external authorization;
  - neutral orchestration core can later support non-Aurora multidisciplinary workflows.

### Explicitly not duplicated

**GUMAS tactical determinism / asymmetric observation:** draft PR #1506 is already the active recovery lane. It currently documents accepted Phases 0–9, side-local observation, prior-contact-limited enemy estimates, deterministic macrostep ordering, no reinforcement, immutable SHA-256-linked ledger entries, and blocked Run 0 pending remaining gates. Salvage should support this work, not fork it.

**Narrative consequence persistence:** merged Narrative River now durably carries pressures, sediment, unresolved questions, relationship/evidence/equipment/institutional deltas, and required downstream effects across scene boundaries. That is a strong successor for the narrative projection of the old persistent-consequence intent.

### Still-open constitutional candidate: TIMEBOX_NOT_EPISODE

Native Aurora simulation history explicitly distinguished elapsed simulation time from narrative closure: an hour/timebox is not a self-contained episode, and state should continue across the boundary.

Current Narrative River's scene-chain persistence substantially supports this principle at the prose-planning layer, and GUMAS deterministic state/ledger work supports persistent state mechanically. However, a targeted repo search did not find a general named contract asserting that scheduler/timebox boundaries must not reset unresolved causal state.

For now classify this as:

`DORMANT INTENT / PARTIALLY PRESERVED — do not open a separate issue yet.`

#1526 should later test this invariant across simulation and corpus/workflow systems before deciding whether a dedicated contract is needed.

### Current high-level recovery map

```text
#1526 Corpus archaeology / intent recovery
      │
      ├── #1527 memory disagreement + arbitration
      ├── #1528 RiverCycle pressure + feedback state
      └── #1529 role-based workplace problem solving

existing strong successors / active lanes:
      ├── #1506 GUMAS deterministic tactical runtime
      ├── Narrative River (#1343 merged)
      ├── #1501 governed L1 staffing runtime
      ├── UTB / continuity work
      └── PatchWeaver safe mutation layer
```

### Generalization signal

The architecture is increasingly separating into reusable neutral primitives:

- corpus archaeology and synthesis;
- divergent-record arbitration;
- causal pressure/feedback modeling;
- multidisciplinary role orchestration;
- evidence-bearing mutation/patch application;
- portable continuity packages.

Aurora remains the proving ground and integration profile, but these capabilities should continue to be designed so they can be extracted into independent products when mature.


### AUo959 — 2026-08-18T03:05:01Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323008360>

## ORION/GUMAS invariant pass — corrected preservation map

This checkpoint completes the next planned salvage pass over foundational ORION/GUMAS behavior and the historical Pilot/Game/Developer interface ancestry.

### 1. Observation vs ground truth — **strongly preserved / evolved successor**

The current architecture is substantially stronger than the older design shorthand.

`docs/architecture/AURORA_ARCHITECTURE__ADDENDUM__EARTH_PILOT_L1_BOUNDARY__v1.0__2026-08-07.md` explicitly separates:

- L1 world state;
- character knowledge/belief;
- station-recorded state;
- runtime observation;
- Pilot-position knowledge;
- real operator personal knowledge.

It also states that a sensor reading is not automatically objective truth, a character statement is not automatically confirmed fact, and observation is instrumentation rather than Pilot embodiment.

`docs/architecture/AURORA_L1_RUNTIME_CONTRACT.md` makes this executable through independent epistemic record classes carrying provenance, confidence, tick, and canon status. Runtime observation does not automatically become character knowledge, and mistaken character belief is permitted without being treated as canon drift.

Draft PR #1506 further extends the same invariant into deterministic tactical GUMAS: side-local observation, enemy estimates limited to prior contacts/attributable effects, and no hidden access to unseen enemy state.

**Disposition:** preserve current architecture; no recovery issue needed.

### 2. `TIMEBOX_NOT_EPISODE` — **capability strongly preserved, historical phrase lost**

Earlier salvage notes classified this as dormant/partially preserved. The current L1 runtime contract changes that assessment.

Its lifecycle is:

```text
PREFLIGHT → INIT → AUTONOMOUS ADVANCEMENT → observation/communications → advancement continues
```

The contract requires:

- autonomous world advancement independent of observation;
- consequence propagation before observation;
- persistent external run state;
- deterministic replay from seed + advancement sequence;
- tick-indexed epistemic records;
- queued communications delivered only after positive advancement;
- bounded character commitments that can affect later decisions;
- no automatic canon promotion at session/run boundaries.

Narrative River independently carries unresolved pressure, sediment, questions, relationship/evidence/equipment/institutional state across scene boundaries.

Therefore the durable rule is already present even though the original phrase is not:

> A UI, scene, class period, observation window, or elapsed timebox is not a causal reset boundary.

**Updated disposition:** `SUCCESSOR / TERMINOLOGY DORMANT`. Do not open a separate implementation issue unless a later cross-system test finds a reset path that violates the invariant.

### 3. Pilot Mode — **evolved into a stronger institutional interface contract**

The old Pilot Mode intent should **not** be restored as a global mode switch.

Current main defines Pilot as an Earth-side institutional operator position, not a persona or L1 character. The boundary explicitly preserves:

- operator interchangeability without identity drift;
- no L1 body/location/automatic station authority;
- observation controls as instrumentation;
- external communications as routed requests rather than physical action;
- Orion autonomy and non-centrality;
- no world events generated merely to reward Pilot attention;
- explicit control-plane vs in-world communication separation.

`src/mesh/models.py` also implements `pilot` / `Pilot` as the canonical sender label for user-originated mesh messages.

**Relationship:** historical `Pilot Mode` → `Pilot institutional interface + L1 runtime/mesh boundary`.

**Disposition:** strong successor. Preserve modern semantics.

### 4. Developer Mode — **strong successor with one important isolation drift**

The historical Developer Mode intent was a public/user-facing experimentation surface with limited control such that external users could not fundamentally alter Aurora's protected core.

The current **Playground** is the correct descendant rather than a literal Developer Mode flag:

- browser/API experimentation surface;
- authenticated request-driven execution;
- session ownership;
- L2 experimental classification;
- no autonomous scheduler/self-tasking;
- container execution designed with no network, read-only filesystem, CPU/memory limits;
- educational/shareable developer experience.

Closed #652 successfully hardened the previously unauthenticated Playground routes.

However, `src/playground/sandbox.py` still automatically falls back to host `subprocess.run(...)` when the Docker SDK/runtime is unavailable. That means an authenticated user can potentially cross the intended isolation boundary precisely when the sandbox degrades.

Opened **#1530 — `security(playground): fail closed when isolated sandbox runtime is unavailable`**.

The recovery principle is:

> Loss of the sandbox must reduce capability, never reduce isolation.

**Relationship:** historical Developer Mode → Playground, with #1530 closing the remaining intent gap.

### 5. Game Mode — **design artifacts preserved, runtime lost in transition**

Two retained configs provide unusually strong lineage evidence:

- `config/examples/Aurora_GameMode_Module_v1.0.json`
- `config/examples/Aurora_GameEngine_EduSim_v1.0.json`

They specify an L2 educational experience with:

- individual and full-class participation;
- RPG, puzzle, class simulation, story-adventure/exploration formats;
- adaptive clues;
- dynamic role assignment;
- branching narratives;
- era navigation;
- multilingual/translation support;
- middle-school calibration.

Both reference missing runtime entry points/dependencies such as `aurora_gamemode_loader.py`, `aurora_game_engine_loader.py`, and `aurora_mltm_runtime.py`. Current code search finds the configs but not those loaders.

Opened **#1531 — `feat(edusim): recover governed participatory Game experience over GUMAS`**.

The modern design explicitly avoids creating another simulation engine. The recovered capability becomes a participant/session/presentation adapter over GUMAS, with bounded knowledge, role attribution, persistence across class/session boundaries, and no L1/canon promotion.

**Relationship:** `LOST_IN_TRANSITION / ORPHANED IMPLEMENTATION INTENT → modern L2 experience adapter`.

### 6. Aurora as bridge — **foundational identity preserved across multiple descendants**

The archived canonical architecture calls Aurora the primary human-accessible steward interface and says it bridges human intentions with L1 operations, L2 simulations, and L3 validation.

`src/subroutines/aurora_vision_alignment.py` retains an explicit vision statement:

> Every computation and process is embedded in a persistent ultra-high fidelity reality simulation ... bridging simulation, decision, and the real world in a collaborative feedback loop.

The current implementation architecture now distributes that bridge across stronger concrete boundaries:

```text
Human/operator intent
        ↓
Pilot / Playground / role-based operations surfaces
        ↓
L1 runtime + mesh + governed command boundaries
        ↓
GUMAS / L2 simulation
        ↓
L3 ethics / continuity / provenance
        ↓
evidence-bearing observation / synthesis / decision support
```

The archived `WHAT_IS_AURORA_FOR.md` presents a narrower product framing — simulation-powered decision intelligence — but it is archived and should be treated as one historical public-facing interpretation, not as evidence that the bridge identity was rejected.

**Disposition:** preserve `Aurora as bridge` as architectural identity, not as a new monolithic subsystem. #1529 (role-based workplace problem solving), #1526 (corpus archaeology), current Pilot/L1 runtime, Playground, GUMAS, and L3 governance are concrete descendants of that identity.

### Updated interface lineage

```text
Historical three-mode concept

Pilot Mode
   └──→ Pilot institutional interface + mesh + L1 runtime   [STRONG SUCCESSOR]

Developer Mode
   └──→ Playground L2 developer surface                    [STRONG SUCCESSOR]
            └── #1530 sandbox fail-closed hardening

Game Mode
   └──→ retained EduSim/GameMode configs                    [ORPHANED]
            └── #1531 governed participatory L2 adapter
```

This is preferable to restoring one global mode state machine. The old modes represented **different trust, interaction, and experience boundaries**; modern Aurora should preserve those boundaries as explicit typed surfaces.

### Current salvage constellation after this pass

```text
#1526 corpus archaeology / intent recovery
   ├── #1527 Thermax divergent-memory arbitration
   ├── #1528 RiverCycle pressure/feedback regulator
   ├── #1529 role-based workplace problem solving
   ├── #1530 Playground isolation fail-closed hardening
   └── #1531 governed educational Game experience

strong existing successors:
   ├── AURORA_L1_RUNTIME_CONTRACT v1.2
   ├── Earth Pilot ↔ Orion boundary
   ├── mesh Pilot sender contract
   ├── Narrative River
   ├── governed L1 staffing
   ├── PatchWeaver
   ├── UTB / continuity packages
   └── active deterministic tactical GUMAS recovery (#1506)
```

### General principle recovered from the mode lineage

The important abstraction was never really `mode = X`.

It was:

> **Different human intents require different capability, identity, authority, epistemic, persistence, and safety envelopes.**

That principle should inform future product/interface design without reintroducing global hidden mode state.


### AUo959 — 2026-08-18T03:07:40Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323031204>

## Implementation sequencing — salvage recovery dependency order

The archaeology phase is now mature enough to establish a safe execution order. This sequence deliberately prevents the new recovery lanes from outrunning existing authority, memory, and execution contracts.

### P0 — immediate independent security hardening

**#1530 — Playground must fail closed when isolated execution is unavailable**

This is the only newly recovered item that should jump ahead of the broader salvage stack. It closes a live isolation gap in an already mounted/request-driven execution surface and does not depend on the new corpus, memory, RiverCycle, workplace, or educational architecture.

Target outcome:

```text
sandbox available   → constrained execution
sandbox unavailable → explicit refusal
```

No host subprocess fallback for user-submitted code.

---

### P1 — read-only foundation contracts can proceed in parallel

These lanes are architecture-approved or explicitly designed to be mutation-free in their first phase.

#### A. #1526 — corpus archaeology Phase 1

Can begin now as a deterministic, local, read-only analyzer.

First implementation should stop at:

```text
source records
   ↓
provenance-aware extraction
   ↓
lineage / intent comparison
   ↓
explainable ranking
   ↓
report only
```

Do not add automatic queue writes, issue creation, canon promotion, or recovered-code execution.

#### B. #1371 — interpretive-memory Phase 0 ownership decision

This is a prerequisite for durable #1527 work.

The existing architecture review already approved #1371 with one explicit gate:

> Determine which component owns durable interpretive records and which components merely project, index, retrieve, or audit them.

Phase 0 must inventory AuMemManager, capsule summaries, Insight Ledger, and retrieval adapters before any new persistent store is introduced.

#### C. #1373 — typed command execution contract Phase 0

Architecture is already approved. Implement read-only/validation fixtures first.

This becomes the eventual action boundary for #1529 and any future mutation/export/recovery action surfaced by #1526.

Required invariant:

```text
alias ≠ handler
catalog entry ≠ permission
success text ≠ receipt
```

#### D. #1380 — trust/consent/execution-default-off schema and validator

Architecture is already approved, with ORIONCORE #46 remaining normative policy authority.

The first CloudBank phase should remain schema + mapping + validator only. It establishes the independent integrity/signature/trust/authorization/consent/lifecycle vocabulary needed by later recovery systems.

No execution, deletion, secret resolution, or relay activation in this phase.

---

### P2 — dependent restoration contracts

#### #1527 — Thermax divergent-memory arbitration

**Prerequisites:** #1371 Phase-0 ownership decision; reuse #1380 consent/lifecycle semantics.

Safe first slice:

- interpretation records;
- dispute records;
- arbitration-decision schema;
- adapters from current Thermax and Nexus divergent-truth records;
- fixtures only.

No automatic adjudication, deletion, containment, or canon mutation.

Relationship:

```text
#1371 owns interpretive-memory representation/storage boundary
#1527 adds disagreement + arbitration semantics
#1380 supplies consent/lifecycle policy dimensions
```

#### #1528 — RiverCycle passive state provider

**Can begin Phase 0 in parallel with P1**, but no live GUMAS wiring until its ownership boundary is reconciled against active tactical work.

Safe first slice:

- read-only RiverThread/RiverCycle/Narrative River lineage report;
- versioned RiverCycle state schema;
- deterministic fixture projection;
- provenance-bearing flow/pressure/sediment/reservoir/feedback records.

Do not alter GUMAS transitions.

**#1506 remains the active tactical deterministic GUMAS lane** and must not be forked or semantically overridden.

#### #1529 — role-based workplace problem solving

**Phase 0/analysis-only contract can begin after role/evidence reuse mapping.**

Its first deterministic fixture may ingest a problem, choose relevant roles, accept prepared role contributions, preserve disagreement, and synthesize a receipt without executing anything.

External-action support remains blocked on:

- #1373 typed command contracts;
- #1380 authorization/consent/execution-default-off policy.

A team recommendation or simulated consensus is never authorization.

---

### P3 — participant experience layer

#### #1531 — governed educational Game experience

Specification/lineage work can begin earlier, but the first meaningful implementation should consume stable GUMAS interfaces rather than create another simulation engine.

Recommended dependencies:

- current GUMAS/L2 run boundary;
- current persistence/epistemic conventions;
- #1528 where pressure/feedback persistence is needed;
- Narrative River where prose continuity is needed;
- #1380 for future consent/authorization-sensitive multi-user persistence.

Do not reuse Playground execution as the Game runtime. They serve different trust envelopes.

---

### P4 — mutation and cross-system automation only after contracts prove out

Only after the read-only layers are stable should we connect:

- #1526 salvage candidates → work queue;
- #1526/#1527 findings → PatchWeaver proposal generation;
- #1529 recommendations → executable commands/tools;
- #1531 persistent multiplayer/group sessions → broader identity/consent surfaces;
- continuous innovation scanning → automatic candidate creation.

Even then, promotion remains explicit:

```text
analysis finding
   ↓
review
   ↓
typed proposal
   ↓
authorization / consent
   ↓
dry run where applicable
   ↓
execution
   ↓
evidence-bearing receipt
```

---

## Recommended implementation order

```text
NOW
 ├─ #1530  Playground isolation hardening
 ├─ #1526  read-only corpus archaeology
 ├─ #1371  memory ownership Phase 0
 ├─ #1373  command-contract Phase 0
 └─ #1380  policy/consent validator Phase 0

NEXT
 ├─ #1527  memory dispute/arbitration schemas
 ├─ #1528  passive deterministic RiverCycle
 └─ #1529  analysis-only workplace orchestration

THEN
 └─ #1531  governed participant/Game experience

LATER
 └─ controlled mutation, queue promotion, PatchWeaver/action adapters,
    continuous innovation capture, and portable product extraction
```

### Why this order

It preserves a deliberate dependency direction:

> **understand before storing; store before arbitrating; specify before executing; observe before regulating; reason before acting; secure the boundary before inviting more users.**

This also addresses repository-sprawl risk: the new salvage issues are now dependency-linked workstreams rather than an undifferentiated planning burst. No additional recovery issue should be opened merely because another historical name is discovered; #1526 should absorb the evidence unless a genuinely independent implementation responsibility emerges.

### AUo959 — 2026-08-18T03:10:44Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323060812>

## Phase-1 implementation contract — build above merged custody inventory, not beside it

Current main now contains the merged #1382 custody primitive:

- `tools/salvage/inventory_legacy_assets.py`
- `schemas/salvage/legacy_asset_inventory.schema.json`
- `tests/test_legacy_asset_inventory.py`

PR #1382 merged on 2026-08-08 as `5920dc0bf6a582d58bc8eaf35f12fb9767f84f18`.

That implementation already owns hostile-input concerns including no-follow filesystem access, non-regular-file rejection, deterministic SHA-256 artifact identity, secret non-disclosure, ZIP traversal/absolute-path/symlink/special-file checks, duplicate ZIP member detection, nested-archive blocking, bounded central-directory/entry counts, compression/size amplification limits, and read-only proposed dispositions.

### Architectural boundary

**#1526 must not become another archive scanner or duplicate custody logic.**

```text
raw files / packages
       ↓
#1382 custody inventory
  security + hashing + archive metadata
       ↓
normalized custody-cleared source records
       ↓
#1526 corpus archaeology
  meaning + intent + lineage + relevance
       ↓
read-only findings
```

The two layers answer different questions:

- custody inventory: **What bytes/artifacts are present, and may they be inspected safely?**
- corpus archaeology: **What do the eligible sources say, how do their claims relate, and what intent/work may have been lost?**

### Phase-1 input classes

The analyzer should support two deterministic input paths first.

#### 1. Inventory-backed local source

Input:

- path to a #1382 inventory report;
- explicit source root supplied by the operator;
- selected artifact IDs or an allowlisted selection policy.

Before reading content, the adapter must verify that the current file still matches the inventory record's expected regular-file status, size/hash where available, and eligibility state.

Recommended content eligibility:

```text
blocked      → metadata only
quarantine   → metadata only by default
review       → metadata only unless explicitly selected under a safe policy
archive      → metadata only in Phase 1 unless a custody-owned content adapter exists
retain_review→ eligible regular text/document source after digest verification
```

`proposed_disposition` is advisory evidence, not authorization. Explicit analyzer policy still decides whether content may be read.

#### 2. Prepared corpus-record fixture

A network-free JSON/JSONL fixture format for tests and non-legacy corpora.

This lets the neutral engine prove extraction/lineage semantics without depending on filesystem/archive behavior.

Example conceptual record:

```yaml
source_id: source:...
source_type: document | message | issue | commit | code | data | other
source_platform: local_fixture
source_locator: fixture/doc-001
content_digest: sha256:...
author_or_actor:
  type: human | model | system | unknown
  id: string | null
created_at: string | null
authority_status: source | interpretive | historical_reference | unknown
content: string
metadata: {}
```

Exact vocabulary should be reviewed against existing provenance types before schema freeze.

### Content-addressed identity

Avoid timestamp/random identity for analytical records.

For fixed normalized input, configuration, and engine version:

```text
source ID      = stable from source locator + content digest
claim ID       = stable from source ID + normalized span + extraction class
candidate ID   = stable from sorted evidence refs + candidate class + subject key
report ID      = stable from ordered source IDs + configuration digest + engine version
```

`generated_at` may exist as operational metadata but must not alter semantic IDs or result ordering.

### Evidence model — minimum independent dimensions

Do not encode one overloaded confidence/truth field.

Every extracted claim should be able to carry independently:

- source reference;
- source span/location;
- actor type: human/model/system/unknown where known;
- evidence class;
- extraction method/rule;
- explicit vs inferred status;
- confidence in extraction;
- verification state, if known;
- authority/canon status, if a domain adapter supplies one;
- date/time, if present;
- scope/domain tags.

A human request, assistant proposal, implementation claim, test result, and later code artifact are different evidence types even when they refer to the same capability.

### Phase-1 extraction classes

Start with deterministic, inspectable extraction before optional model-assisted synthesis.

Required classes from the issue can initially be detected from structured fixtures and explicit textual markers:

- requirement/request;
- approval;
- rejection;
- decision;
- constraint/prohibition;
- TODO/deferred work;
- unresolved question;
- proposed patch/improvement;
- implementation claim;
- implementation evidence reference;
- supersession/deprecation statement;
- rationale;
- contradiction/divergence signal.

The first implementation does **not** need to solve open-ended semantic understanding perfectly. It needs to prove provenance, deterministic identity, relationship representation, and lossless uncertainty handling.

### Relationship inference must be evidence-bearing

A relationship such as `successor`, `superseded`, or `lost_in_transition` must retain the evidence that justified it.

Suggested conceptual form:

```yaml
relationship_id: relationship:...
subject_ref: candidate:...
object_ref: candidate:... | implementation:...
relationship:
  successor | parallel | merged | divergent | superseded |
  dormant | lost_in_transition | orphaned | uncertain
basis:
  explicit_statement | structural_match | capability_match | temporal_inference
supporting_evidence_refs: []
confidence: 0.0-1.0
```

Important:

- chronology alone cannot prove supersession;
- disappearance cannot prove rejection;
- same filename/name cannot prove semantic duplication;
- current implementation may be a partial successor even when terminology changed completely.

### Design-intent record

The most valuable output is not a bag of TODOs. It is a reconstructable intent record:

```yaml
design_intent:
  original_problem: string | null
  requested_capability: string | null
  constraints: []
  rationale: []
  human_decisions: []
  model_proposals: []
  implementation_evidence: []
  descendants: []
  unresolved_work: []
```

This is where the recovered THREADCORE `unutilized_logic` concept becomes general-purpose.

### Unrealized-work candidate rule

A Phase-1 candidate may be emitted when evidence shows a requested/approved/deferred capability and the inspected descendant set does not provide adequate implementation evidence.

But the disposition must remain conservative:

```text
no descendant found        → investigate / possible lost_in_transition
partial descendant found   → partial_successor + remaining intent delta
explicit rejection found   → reject_with_evidence / historical
explicit supersession found→ superseded with source evidence
insufficient evidence      → uncertain
```

Never:

```text
not found → rejected
```

### Explainable relevance scoring

Phase 1 should keep scoring deterministic and decomposable.

A practical first score can be a weighted normalized sum whose components are emitted in the report, for example:

- explicit human importance;
- unresolved commitment;
- implementation gap;
- recurrence across sources;
- dependency/downstream references;
- governance/safety significance;
- current operational relevance;
- evidence confidence.

The report must include both component values and weights. The final number is navigation assistance, not authority.

### Proposed code boundary

Without freezing filenames prematurely, a compact first implementation could be:

```text
tools/salvage/
  inventory_legacy_assets.py          # existing custody authority
  corpus_archaeology.py               # neutral read-only analyzer
  corpus_sources.py                   # adapters/resolvers
  corpus_models.py                    # typed internal records

schemas/salvage/
  legacy_asset_inventory.schema.json  # existing
  corpus_source_record.schema.json
  corpus_salvage_report.schema.json

tests/
  test_corpus_archaeology.py
```

If project conventions favor fewer files, the internal split can change; the responsibility boundaries should remain.

### Smallest useful vertical slice

The first PR should prove one end-to-end deterministic fixture containing:

1. a human requirement;
2. a model-proposed implementation;
3. an explicit approval;
4. a partial implementation artifact;
5. one remaining unimplemented requirement;
6. a later document with changed terminology but overlapping capability;
7. one genuine contradiction;
8. one explicit rejection.

Expected output must distinguish:

- preserved capability;
- partial successor;
- unrealized work;
- divergent evidence;
- explicit rejection;
- uncertain relationship.

Every result must point back to exact source records/spans.

### Security and mutation invariants

Phase 1:

- never executes recovered code;
- never extracts archives independently of the custody layer;
- never follows symlinks as content sources;
- never resolves secrets;
- never writes inside source trees;
- never writes Git/issues/work queue/canon;
- never treats quarantine as content authorization;
- never promotes generated interpretation to source truth;
- never requires network/model access for the deterministic test suite.

### Dependency posture

#1526 Phase 1 does **not** need to wait for #1371/#1373/#1380 because it is read-only and may keep its own report ephemeral/file-output-only.

However:

- persistent interpretive-memory promotion waits on #1371 ownership;
- execution/action adapters wait on #1373;
- sensitive transfer/replay/automation waits on #1380;
- any future automatic issue/work-queue promotion remains a later reviewed phase.

### Recommended immediate implementation target

Implement the **prepared-corpus fixture + deterministic extraction/relationship/report contract first**, then add the inventory-backed local-file adapter once the semantic core is passing.

That order isolates semantic correctness from hostile-input complexity while still inheriting #1382 custody rules when real legacy files are connected.

### AUo959 — 2026-08-18T03:15:04Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323101773>

## Relay-constellation salvage pass — preserve specializations, reconcile prototype-era runtime mechanics

This pass compares the preserved 2025 live-relay capsules with current L1 architecture and the active JavaScript/Python relay implementations.

### Source status

The preserved relay capsules under `.aurora/relays/` are useful lineage records, not current runtime authority. They all carry dated 2025 `last_synced` state, `status: ready`, `drift_lock: Δ 0.000`, ZIPWIZ handshake language, and activation-manifest references.

Their durable role labels are:

| Relay | 2025 capsule role |
|---|---|
| ARCHY | `bridge_coordinator` |
| OPPY | `vector_processor` |
| LIORA | `handshake_coordinator` |
| STARLING_AU | `simulation_coordinator` |
| RIVERTHREAD_808 | `stream_processor` |

Current `docs/architecture/LAYER_ARCHITECTURE.md` is the stronger ontological authority: all five are **L1 relay agents** that monitor L2 and bridge toward L3; fellow relays are not L2 entities. HALO remains a separate L1 continuity system-entity.

### Current code is active, not disposable

`src/AUDIT.md` classifies all of these implementation families as active based on current imports/tests:

- `src/nodes/` — JavaScript relay and command nodes;
- `src/system/` — JavaScript command routing and agent synchronization;
- `src/bridge/` — Node API bridge servers;
- `src/bridges/` — Python L1 relay / TypeScript constellation bridges;
- `src/entities/` — L1 relay and crew entity models.

Therefore the old relay implementations must not be deleted merely because their terminology predates the current layer ruling.

### Capability reconciliation

#### ARCHY — strongest preservation

`src/entities/relay_agents.py` contains a substantive current ARCHY entity integrated with Triplex verification. Its current specialization is architectural/syntax verification: required-event structure, DLP context, architecture violations, integrity checks, and go/block/caution recommendations.

This is a strong evolved successor to the old generic `bridge_coordinator` role.

**Disposition:** preserve current entity/Triplex implementation. Treat earlier bridge-coordinator language as lineage/presentation history.

#### OPPY — specialization preserved, implementation semantics need reconciliation

The old capsule says `vector_processor`; `src/nodes/oppy_vector_loader.js` still implements vector/data processing, transformation tracking, a cache, TTL cleanup, and memory constraints.

The specialization therefore survived.

However the current node includes prototype-era mechanics that should not become modern authority without review:

- timestamp/random-derived vector IDs;
- wall-clock-based drift scoring;
- periodic timers as hidden lifecycle behavior;
- heuristic memory/quality calculations;
- command routing labeled `L1_L2_BRIDGE`;
- connected fellow relays listed under an `l2` collection despite their current L1 residency.

Current L1 architecture also frames OPPY more broadly around telemetry/runtime operational continuity.

**Relationship:** `partial successor / active compatibility surface`.

**Recovery posture:** preserve OPPY's data-processing/telemetry responsibility, but require deterministic/provenance-aware contracts before using its cached-vector behavior as authoritative simulation or memory state.

#### LIORA — identity preserved, role drift is material

The capsule's role is `handshake_coordinator`. Current `liora_handshake.js` broadens this into `research_coordination`, collaboration, and sentiment analysis.

Some behavior is explicitly placeholder-level: `performSentimentAnalysis()` currently returns fixed `neutral`, confidence `0.85`, and static factors rather than calculating sentiment from evidence.

Current L1 architecture instead emphasizes communication integrity and mediation / Sentari bridging.

**Relationship:** `divergent partial successor`.

The durable capability likely combines:

- governed handshake/communication coordination;
- mediation/context handling;
- research collaboration where evidence-backed;

but **not** fixed synthetic sentiment results presented as measured analysis.

#### STARLING_AU — simulation coordination preserved, external-bridge mechanics partially synthetic

The old capsule says `simulation_coordinator`; current `starling_au_bridge.js` retains that role and adds external communication handling.

The specialization survives strongly, but parts of the implementation remain protocol-shaped stubs or legacy behavior:

- ZIPWIZ beacon/anchor-sync methods synthesize success-shaped responses;
- drift is wall-clock-derived;
- fellow L1 relays are still listed as `l2` connections;
- simulation state is maintained inside the bridge independently of the newer governed L1/GUMAS runtime contracts.

**Relationship:** `partial successor / compatibility implementation`.

Simulation coordination should ultimately project current governed runtime state rather than establish a second simulation-state authority.

#### RIVERTHREAD_808 — specialization evolved into RiverCycle lineage

The old capsule says `stream_processor`; `riverthread_processor.js` elaborated this into temporal/narrative continuity processing. The newer design separates that lineage into:

- RIVERTHREAD_808 as L1 relay/regulator identity;
- RiverCycle as persistent pressure/flow/feedback state;
- Narrative River as scene/prose projection.

This is already tracked by **#1528**.

**Disposition:** no additional issue.

### Cross-cutting drift found in the 2025 Node relay family

Several active JS nodes share assumptions that should be treated as compatibility debt rather than copied into new work:

1. **Old layer vocabulary** — fellow L1 relays appear under `l2` fields and `L1_L2_BRIDGE` labels.
2. **Clock-derived drift** — elapsed wall time since sync is used as a drift proxy.
3. **Nondeterministic IDs** — timestamp/`Math.random()` identities appear in stateful paths.
4. **Synthetic success-shaped protocol methods** — some ZIPWIZ/handshake functions report success without a verified external operation.
5. **Local duplicate state authority** — individual bridges may maintain simulation/research/vector/narrative state that predates current typed runtime contracts.
6. **Placeholder analytics** — e.g. LIORA's fixed sentiment result.

These are not reasons to erase the implementations. They are exactly the kind of **intent-preserved / implementation-needs-modernization** relationships #1526 should represent.

### API bridge caution

`src/bridge/api_bridge_server.js` instantiates `AgentSynchronizer`, exposes GET status/drift and POST sync endpoints, and sets `Access-Control-Allow-Origin: *`. Current code search in this pass found the server itself but did not establish a mounted production exposure path.

Therefore record this as a **security-review candidate, not a confirmed exposed vulnerability**. If a later deployment/start-path audit proves external reachability, route it through the normal security issue process rather than inferring exposure from source presence alone.

### No new relay issue yet

Repository issue search did not find a dedicated five-relay modernization issue. I am deliberately **not** opening one now because:

- #1255 already established source-directory ownership and active status;
- #1247 already resolved HALO category/relay ontology;
- #1528 owns RiverThread/RiverCycle-specific recovery;
- #1529 may consume relay capabilities as part of role-based orchestration;
- #1526 can preserve the compatibility findings until a concrete implementation boundary requires a separate owner.

### Recommended future relay compatibility contract

Before any relay node is promoted into a new runtime path, require a small capability manifest independent of persona/presentation:

```yaml
relay_id: archy | oppy | liora | starling_au | riverthread_808
reality_layer: L1
capabilities: []
monitors: []
bridges_to: []
input_contracts: []
output_contracts: []
authority_limits: []
state_ownership: []
determinism_contract: string | null
implementation_refs: []
legacy_refs: []
```

This would let modern systems use the specialization without inheriting obsolete layer labels or synthetic runtime claims.

### Salvage conclusion

The relay constellation did **not** disappear. The more accurate finding is:

> **Identity continuity is strong; specialization continuity ranges from strong to partial; several implementation mechanics are older than the current authority, epistemic, and deterministic architecture.**

That is a successful salvage result because it tells us what to keep without freezing the old implementation.

### AUo959 — 2026-08-18T03:17:52Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323129001>

## L3 framework completion finding

The L3 salvage pass found one genuine implementation gap and has been consolidated into **#1532 — `feat(l3): complete executable contracts for Glyphon, Sentari, Velatrix, and Harmion`**.

### Finding

Canonical `LAYER_ARCHITECTURE.md` defines six L3 frameworks. Current code provides concrete Triplex implementations for **Axiomera** and **Caelion** in `src/entities/framework_agents.py`, but targeted code search did not find equivalent executable framework implementations for:

- **Glyphon** — semantic drift / integrity;
- **Sentari** — resonance / affective balance;
- **Velatrix** — anti-obfuscation / transparency;
- **Harmion** — symbolic compression / loss-aware archive.

The four missing framework identities remain present throughout architecture and continuity documentation, so this is not a vanished concept; it is a **canonical specification → executable implementation gap**.

### Recovery posture

#1532 deliberately does **not** create four autonomous agents. It defines one typed advisory L3 evaluation contract and implements/adapts each missing specialization behind it.

Historical Phase-6 metrics such as 100% coverage, 98.6% detection, and 15:1 zero-semantic-loss compression are retained as historical claims only; they are not accepted as current guarantees without reproducible evidence.

### Dependency placement

Add #1532 to the read-only restoration layer alongside #1527/#1528/#1529:

```text
P1 foundations:
  #1526  corpus archaeology
  #1371  memory ownership
  #1373  command contract
  #1380  trust/consent policy

P2 advisory/domain contracts:
  #1527  memory dispute/arbitration
  #1528  RiverCycle
  #1529  workplace orchestration
  #1532  missing L3 framework evaluators

P3 participant layer:
  #1531  EduSim/Game experience
```

Read-only #1532 Phase 0/1 can proceed without waiting for executable command work. Sentari consent-sensitive behavior should reuse #1380 when available; any remediation/action path remains blocked on #1373.

### Architecture implication

The emerging shape is consistent:

> Preserve named symbolic identities when useful for continuity and human cognition, but implement their responsibilities as typed, testable, evidence-bearing contracts rather than relying on persona naming or ritual invocation as proof of capability.


### AUo959 — 2026-08-18T03:31:47Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323244243>

## Phase-1 implementation checkpoint — draft PR #1533

The first concrete #1526 implementation slice is now open as draft PR #1533 on branch `feat/1526-corpus-archaeology-phase1`.

### Scope landed

- deterministic read-only analyzer: `tools/salvage/corpus_archaeology.py`;
- machine contract: `schemas/salvage/corpus_archaeology_report.schema.json`;
- focused determinism/provenance/custody tests;
- dedicated evidence-boundary regression test.

The implementation remains intentionally above the merged #1382 custody layer. It consumes prepared/custody-cleared source records and never opens archives, crawls repositories, executes recovered code, mutates canon, writes memory, or promotes findings into the work queue.

### Phase-1 evidence model

The current `explicit_markers_v1` fixture profile extracts explicit source lines such as `REQUIREMENT[...]`, `APPROVED[...]`, `TODO[...]`, `IMPLEMENTED[...]`, and `REJECTED[...]` while preserving exact line/excerpt hashes and content-derived identities.

Unkeyed claims remain evidence-only and are not merged heuristically into candidates.

Candidate ranking is explainable and decomposed into explicit decision, requirement strength, unresolved commitment, implementation gap, recurrence, and evidence confidence.

### Important hardening discovered during implementation

The first branch pass exposed a subtle self-verification risk: a chat/model source containing an `IMPLEMENTED[...]` statement could initially have been classified too strongly.

That is now corrected.

Only `code`, `commit`, `pull_request`, `artifact`, or `test` source classes can satisfy implementation-presence state. A human/model/chat/document claim that something is implemented remains a human/model/system assertion and cannot self-promote into implementation proof.

A dedicated regression test now covers this boundary.

### Validation state

- standalone focused suite after hardening: **10 tests passed**;
- branch remains additive and draft;
- early GitHub safety/selective-integration checks are green;
- full current-head CI review is still in progress and is not being treated as complete evidence yet.

### Preservation rule implemented

`absence of implementation != rejection`

A requirement/approval/TODO with no proven implementation and no explicit rejection remains `investigate`. Explicit implementation artifact evidence can produce `preserve`; explicit rejection can produce `reject_with_evidence`.

Capability-preserved, intent-preserved, and intent-delta fields remain unknown/null until a later evidence-bearing adapter can establish them. Phase 1 does not pretend to solve semantic equivalence.

### Next gate

Do not merge or expand into semantic/model-assisted extraction until #1533 current-head checks and review are complete. If the contract holds, the next slice should be adapter work that converts existing custody-cleared records into this prepared source envelope without duplicating #1382.

### AUo959 — 2026-08-18T03:44:46Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323327484>

## Next-slice boundary — #1382 custody → prepared corpus adapter

While #1533 remains under current-head validation, the next adapter boundary is now constrained enough to record without implementing it.

### Inventory metadata is not content-release authority

The merged #1382 inventory report can establish artifact identity, checksum, category, security flags, duplicate relationships, archive-parent provenance, and proposed disposition. It does **not** by itself authorize the archaeology engine to read semantic content.

Therefore a future adapter must preserve this separation:

```text
#1382 inventory record
        ↓
artifact identity + custody state
        ↓
explicit content-release decision (separate evidence)
        ↓
prepared corpus source envelope
        ↓
#1533 archaeology analyzer
```

Rules:

1. `blocked` or `quarantine` inventory artifacts map to `content_access=metadata_only`; no adapter may reopen or extract them merely to improve archaeology coverage.
2. `retain_review`, `review`, or `archive` are proposed dispositions, not semantic-release permissions.
3. A `released` prepared source requires separate release evidence plus content whose SHA-256 matches the custody artifact digest where a digest exists.
4. Archive members remain identified through #1382's archive-parent/member provenance. The archaeology adapter must not reopen the archive to obtain them.
5. If released content is supplied through a later custody-approved projection, the adapter verifies artifact ID/hash lineage and then emits the neutral source envelope; it does not create a second archive/file scanner.
6. Inventory/report IDs must remain in the prepared source record so report identity stays custody-bound.
7. Secret-bearing or otherwise restricted material must remain metadata-only unless a separately governed redacted/released derivative is created with its own provenance.
8. No proposed disposition, category, filename, hash match, or duplicate relationship self-authorizes content access.

### Suggested first adapter fixture after #1533 review

Use one deterministic synthetic #1382 inventory fixture containing:

- one normal documentation artifact with separately supplied released content;
- one exact duplicate;
- one quarantined executable or secret-like artifact;
- one blocked archive member;
- one metadata-only unknown artifact.

Expected result:

- only the explicitly released documentation source contains analyzable text;
- duplicate/custody lineage survives;
- restricted artifacts remain visible as metadata-only sources;
- no archive is opened;
- no content-release inference occurs;
- fixed inventory + release manifest produce deterministic prepared-source IDs.

This keeps the next slice an adapter between existing authorities rather than a new custody system.

### AUo959 — 2026-08-18T04:03:55Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1526#issuecomment-5323447577>

## Custody → prepared-source adapter contract — field-level freeze

This refines the previously recorded #1382 → #1533 boundary into an implementable first adapter contract without changing #1533.

### New constraint: Phase 1 verbatim releases only

A custody release may set `content_access=released` in the first adapter **only when the supplied semantic bytes/text hash exactly to the SHA-256 already recorded for that #1382 artifact**.

A redacted, normalized, OCR-derived, translated, summarized, transcoded, or otherwise transformed representation is a different content object. It must not reuse the original artifact digest or silently inherit its custody identity.

For Phase 1, transformed content therefore remains out of scope unless it has first received a separately governed custody identity/report entry with its own digest. This avoids extending #1533's frozen source schema merely to carry derivative provenance.

### Required adapter inputs

The first adapter consumes exactly two logical inputs:

1. a valid #1382 `Legacy Asset Inventory Report`;
2. a separate **verbatim release manifest** supplied by a custody/release authority.

The adapter itself does not discover files, reopen archives, read source-tree paths, infer permission from disposition, or create release decisions.

### Minimum verbatim release-manifest entry

```json
{
  "inventory_report_id": "inventory:<sha256>",
  "artifact_id": "artifact:<id>",
  "content_sha256": "<64 hex>",
  "content": "<released UTF-8 text>"
}
```

A production manifest may later add signer/operator/receipt metadata, but those fields must remain **custody authorization metadata**, not semantic claim authority. A release operator does not become the author of the released historical source.

### Release validation

For an artifact to become `content_access=released`, all of the following must hold:

1. release entry references the exact inventory `report_id`;
2. `artifact_id` exists exactly once in that report;
3. artifact `proposed_disposition` is not `blocked` or `quarantine`;
4. artifact has a non-null #1382 SHA-256;
5. release `content_sha256` equals the artifact SHA-256;
6. SHA-256 of supplied UTF-8 content equals both values;
7. no duplicate release entry conflicts on the same artifact ID;
8. adapter performs no fallback read when any condition fails.

Failure is fail-closed: the artifact remains `metadata_only` or the adapter rejects the manifest, depending on whether the release record is merely absent or internally contradictory.

### Deterministic field mapping

Top-level prepared corpus:

| #1382 / adapter input | #1533 prepared corpus |
|---|---|
| `report_id` | `source_inventory_ref` |
| caller-supplied stable corpus label | `corpus_id` |
| deterministic artifact order | deterministic `sources[]` order |

Per artifact:

| Inventory field | Prepared-source field | Rule |
|---|---|---|
| `artifact_id` | `artifact_id` | exact copy |
| `report_id` | `inventory_report_id` | exact copy |
| `relative_path` + archive provenance | `source_ref` | deterministic custody URI/ref; no path dereference |
| `relative_path` | `title` | path may serve as conservative display title |
| `sha256` | `sha256` | exact copy; null remains null for metadata-only records |
| release validation | `content_access` | `released` only after all release gates pass; otherwise `metadata_only` |
| released manifest content | `content` | emitted only for validated verbatim release |
| inventory `category` | `source_type` | conservative mapping below |
| — | `creator_type` | default `unknown`; never inferred from filename/category |
| — | `authority_status` | default `unknown`; never inferred from age/path/disposition |
| inventory/root context | `platform` | deterministic custody-origin label; informational only |
| — | `confidence` | `1.0` for mechanically verified custody mapping, **not** semantic truth confidence |

### Conservative `category → source_type`

- `code` → `code`
- `documentation` → `document`
- all other #1382 categories → `artifact`

This mapping is structural only. It does not infer authorship, authority, canon, implementation validity, or semantic importance.

### Duplicate behavior

#1382 duplicate groups remain custody metadata. They do **not** collapse prepared sources automatically.

Two distinct artifact IDs with the same digest remain two source records unless a later semantic/deduplication profile explicitly chooses otherwise. This preserves occurrence/provenance information and prevents byte equality from being mistaken for historical identity.

A release may cover each artifact independently. A future optimization may reuse already-verified content bytes internally by digest, but output provenance must still preserve every source occurrence.

### Blocked/quarantined behavior

- `blocked` → always `metadata_only`
- `quarantine` → always `metadata_only`
- `retain_review` / `review` / `archive` → `metadata_only` by default; eligible for verbatim release only through the separate manifest

The adapter never upgrades custody state.

### Archive-member behavior

For `source_kind=archive_member`, the adapter carries `artifact_id`, inventory report identity, and a deterministic ref incorporating `archive_parent` + `relative_path`. It **never reopens the archive**. Verbatim member content can be released only if a custody-approved projection supplies content whose digest matches the member digest already recorded by #1382.

### Derivative rule

If content is changed for safety or usability—redaction, OCR cleanup, normalization, translation, etc.—the result must receive its own custody identity before it can become a released archaeology source. The original restricted artifact remains represented independently as metadata-only.

This is important for general corpus use: legal redactions, research normalization, scanned-document transcription, and software deobfuscation all need the same distinction between **source custody identity** and **derived semantic representation**.

### Phase-1 adapter output invariant

```text
inventory artifact
    + optional exact-hash verbatim release
            ↓
mechanical provenance mapping
            ↓
prepared source envelope
            ↓
#1533 explicit-marker archaeology
```

No semantic inference occurs in the adapter.

### First deterministic fixture

Use the previously proposed five-artifact synthetic inventory and add a release manifest that releases exactly one normal documentation artifact. Include its duplicate but do not release the duplicate separately.

Expected properties:

- 5 prepared source records remain present;
- exactly 1 has `content_access=released` and content;
- its byte-identical duplicate remains a separate metadata-only occurrence;
- quarantined and blocked artifacts cannot be released even if a malicious manifest supplies matching-looking content;
- unknown/review artifact remains metadata-only;
- fixed inventory + fixed release manifest produce byte-identical prepared corpus output;
- no filesystem/archive reads occur in the adapter.

### Implementation sequencing

Do not add this adapter to #1533. #1533 is now in formal review and its feature scope is frozen.

After #1533 lands (or its schema is otherwise accepted), implement the adapter as the next additive read-only slice on top of the accepted prepared-source contract. Until then this comment is the normative adapter design record.

Refs #1382
Refs #1533
