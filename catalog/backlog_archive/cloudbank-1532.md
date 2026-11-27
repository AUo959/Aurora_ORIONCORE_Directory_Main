# aurora-cloudbank-symbolic#1532: feat(l3): complete executable contracts for Glyphon, Sentari, Velatrix, and Harmion

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1532
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T03:17:25Z
- Updated: 2026-08-18T03:17:37Z
- Labels: backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- none

## Branches named in the issue

- none

## Original body

## Lineage

Focused recovery/completion work related to:

- #1526 — provenance-aware corpus archaeology and intent recovery;
- #1373 — typed execution contracts and receipts;
- #1380 — trust/consent/execution-default-off controls;
- `docs/architecture/LAYER_ARCHITECTURE.md` — canonical L1/L2/L3 ontology;
- `src/entities/framework_agents.py` — current Axiomera and Caelion Triplex implementations;
- `src/aurora_orchestrator/triplex_handshake.py` — current Triplex orchestration;
- historical Phase-6 framework descriptions and THREADCORE/continuity references.

## Current canonical architecture

`docs/architecture/LAYER_ARCHITECTURE.md` defines six L3 conceptual frameworks:

| Framework | Canonical function |
|---|---|
| Axiomera | Ethics Arbitration |
| Caelion | Anchor Propagation & Provenance Verification |
| Sentari | Resonance Stabilization & Affective Balance |
| Velatrix | Anti-Obfuscation & Transparency Enforcement |
| Glyphon | Drift Alignment & Semantic Integrity |
| Harmion | Symbolic Compression & Lossless Archive |

L3 frameworks are abstract logic systems that constrain/evaluate operations across layers. They are not L2 simulation actors and do not acquire L1 human authority.

Current Triplex documentation explicitly invokes Axiomera and Caelion in the L3 step and allows other L3 frameworks to check relevant constraints.

## Implementation evidence found

`src/entities/framework_agents.py` contains concrete current implementations for:

- `AxiomeraEntity` — ethical assessment / Picard_Delta_3-oriented screening;
- `CaelionEntity` — anchor/continuity validation.

Both are used by the Triplex architecture.

Targeted current-repository searches in this salvage pass did **not** find equivalent `GlyphonEntity`, `SentariEntity`, `VelatrixEntity`, or `HarmionEntity` implementations or another clearly owned executable framework providing their full canonical responsibilities.

The four names remain present across architecture, continuity, transfer, dossier, and historical integration documents.

**Relationship:** `canonical specification preserved / executable framework incomplete`.

## Evidence caution

Historical documents such as `simulation/CODEX_PHASE6_L2_L3_SYSTEMS_COMPLETE.md` contain numerical claims including 100% coverage, 99.x% accuracy, sub-second detection, and 15:1 zero-semantic-loss compression.

Those values are **historical implementation claims**, not verified current measurements. They must not be imported as runtime guarantees or test thresholds without reproducible instrumentation and evidence.

Likewise, older language describing L3 frameworks as "living entities" is presentation/history. Current ontology should govern implementation: L3 is conceptual/framework logic; human/L1 authorization remains separate.

## Architectural decision

Do not build four autonomous agents.

Define one small, typed **L3 framework evaluation contract** and implement each missing specialization as a deterministic/advisory framework behind it.

Conceptual interface:

```yaml
framework_request:
  framework_id: glyphon | sentari | velatrix | harmion
  request_id: string
  operation_type: string
  source_refs: []
  input_state: {}
  policy_refs: []
  layer_context: L1 | L2 | L3 | mixed

framework_evaluation:
  framework_id: string
  request_id: string
  status: pass | caution | fail | not_applicable | insufficient_evidence
  findings: []
  evidence_refs: []
  recommendations: []
  confidence: number | null
  deterministic_receipt: string
  mutation_performed: false
```

Exact field names should align with existing event/Triplex/validation models before schema freeze.

## Framework-specific Phase-1 semantics

### Glyphon — semantic drift / integrity

Phase 1 should detect and report **evidence-backed semantic divergence**, not automatically rewrite meaning.

Minimum capabilities:

- compare explicitly supplied prior/current semantic records;
- identify terminology or meaning changes;
- distinguish known migration/renaming from unexplained divergence when mappings are supplied;
- preserve both versions and supporting evidence;
- return `insufficient_evidence` where semantic equivalence cannot be established deterministically.

Do not claim open-ended semantic understanding or automatic correction in Phase 1.

Potential reuse:

- #1526 lineage/intent relationships;
- existing drift annotations/memory work;
- typed alias/supersession registries where available.

### Sentari — resonance / affective balance

Phase 1 should be an **advisory context-quality contract**, not emotion inference presented as objective fact.

Minimum capabilities:

- accept explicit affect/sentiment signals with provenance;
- identify contradictory or extreme supplied signals;
- flag missing consent/scope where personal communication analysis is requested;
- distinguish observed text/features from interpretation;
- avoid psychiatric, psychological, or intent claims unsupported by evidence.

Do not reproduce placeholder-style fixed sentiment scores such as the current LIORA bridge's synthetic `neutral / 0.85` result.

Consent-sensitive analysis must inherit #1380 policy rather than inventing a separate consent model.

### Velatrix — anti-obfuscation / transparency

Phase 1 should evaluate **explainability and disclosure structure**, not infer malicious concealment merely from complexity.

Minimum capabilities:

- identify missing rationale/evidence references where a governed record requires them;
- identify contradictory claims or unexplained confidence/authority elevation;
- distinguish privacy/redaction from obfuscation;
- preserve the reason a field is unavailable when known;
- return advisory findings with exact field/source references.

Potential reuse:

- command receipts (#1373);
- memory/arbitration records (#1527);
- corpus archaeology (#1526);
- ethics/transparency infrastructure already present.

### Harmion — symbolic compression / loss-aware packaging

Do **not** implement or promise magical semantic-lossless compression.

Phase 1 should define a measurable **structured condensation contract**:

- preserve source references;
- emit an omission manifest;
- separate exact retained facts from summaries/derived compression;
- preserve unresolved questions, dissent, and high-importance constraints;
- verify byte/integrity hashes for source and generated artifact where applicable;
- allow deterministic round-trip verification of retained structured fields, not reconstruction of omitted prose.

Potential reuse:

- UTB/continuity packages;
- #1526 corpus synthesis;
- THREADCORE reflection snapshots;
- ZIPWizard export/report UX later.

## Axiomera/Caelion compatibility review

This issue should not rewrite the existing implementations by default, but Phase 0 should document their current contract and known simplifications so the six-framework interface does not encode accidental behavior.

Examples to review:

- Axiomera's current scalar score is heuristic and must not become a universal moral-truth metric.
- Caelion's current T1/SRB validation uses simplified expected progression; provenance/anchor validation should remain evidence-bearing.
- L3 recommendations must remain distinct from L1 human authorization.

If adapter wrappers are sufficient, prefer wrappers over invasive rewrites.

## Triplex integration boundary

Current Triplex sequence remains:

```text
L3 framework evaluation
        ↓
L1 relay verification (Triplex middleware role)
        ↓
L1 human consent/authorization
```

Adding framework implementations must not change that authority order.

Phase 1 should expose the four missing evaluations for explicit invocation/testing. Automatic inclusion in every Triplex operation is a later policy decision, not implied by implementation existence.

A framework may report `not_applicable`; not every operation needs all six checks.

## Determinism and evidence

For fixed normalized request + policy/config + framework version:

- result structure/order must be deterministic;
- finding IDs/receipts must be content-derived;
- no ambient randomness;
- no wall-clock value may affect evaluation semantics;
- every material finding identifies the evidence/input field that produced it;
- generated timestamps may exist only as operational metadata.

## Phase 0 — ownership and overlap map

Before implementation, inventory existing capabilities that partially overlap:

- ethics engine / geometric ethics / transparency evaluators;
- semantic drift tooling;
- continuity and provenance validators;
- memory compression/summarization utilities;
- narrative validation;
- #1371 interpretive memory;
- #1526 corpus archaeology;
- current Thread Transfer / UTB surfaces.

For each canonical L3 responsibility, identify:

```text
existing authority
partial implementation
adapter candidate
true gap
```

Do not create duplicate validators under glyph names when a mature generic component already owns the capability.

## Phase 1 — smallest vertical slice

Implement the shared typed evaluation contract plus one deterministic fixture for each missing framework:

1. **Glyphon:** known rename plus one unexplained semantic change.
2. **Sentari:** explicit, provenance-bearing affect signals with one conflict and one consent boundary.
3. **Velatrix:** record with missing rationale/evidence plus legitimate privacy redaction.
4. **Harmion:** structured source condensed with exact retained fields + omission manifest.

All evaluations are read-only/advisory.

## Acceptance criteria

- [ ] Canonical L3 roles match `LAYER_ARCHITECTURE.md`.
- [ ] Existing Axiomera/Caelion ownership is reused rather than duplicated.
- [ ] Shared framework request/evaluation contract exists.
- [ ] Glyphon, Sentari, Velatrix, and Harmion each have an executable deterministic Phase-1 evaluator or explicit adapter to a proven existing owner.
- [ ] No historical numerical performance claim is accepted without reproducible evidence.
- [ ] L3 framework output is advisory/validation output, not L1 authorization.
- [ ] `not_applicable` and `insufficient_evidence` are valid outcomes.
- [ ] Semantic drift findings preserve source versions and do not auto-rewrite.
- [ ] Sentari does not fabricate emotion/intent and inherits consent boundaries.
- [ ] Velatrix distinguishes privacy/redaction from obfuscation/insufficient explanation.
- [ ] Harmion emits an omission manifest and does not claim reconstruction of omitted semantics.
- [ ] Fixed fixtures produce deterministic evaluation content and ordering.
- [ ] Findings retain exact evidence/input references.
- [ ] No L1/L2 state mutation, canon promotion, or autonomous Triplex activation occurs in Phase 1.
- [ ] Tests cover layer separation and human-authorization preservation.

## Dependencies

- Read-only Phase 0/1 can proceed independently.
- Consent-sensitive Sentari behavior should reuse #1380 once policy schema lands.
- Any executable remediation path waits on #1373 typed command/action contracts.
- Corpus/semantic adapters should coordinate with #1526 rather than duplicating its lineage engine.

## Non-goals

- creating autonomous L3 personas;
- claiming consciousness/personhood for conceptual frameworks;
- automatic moral adjudication;
- automatic semantic rewriting;
- psychological diagnosis;
- forced transparency of legitimately private data;
- magical lossless semantic compression;
- changing Triplex authority order;
- making all six frameworks mandatory for every operation;
- reproducing historical performance metrics without measurement.

## Design principle

**Make the framework testable before making it powerful.**


## Comments (0)
