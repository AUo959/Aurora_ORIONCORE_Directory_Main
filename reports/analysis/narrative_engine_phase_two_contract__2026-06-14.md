# Narrative Engine Phase Two Contract - 2026-06-14

## Scope

Task resumed from `catalog/session_state.json` queue item
`narrative-promotion-continuation-2026-06`, limited to the phase-two narrative
engine design seed:

- LLM front end as `state_builder`: prose or mixed evidence to canonical state
  extraction.
- Deterministic engine remains the judge.
- Candidate first pipeline: GUMAS turn output to `next_event_continuity_check`
  to a promotion gate.

This receipt is design only. It does not promote canon, mutate CloudBank, write
CanonRec, or execute live mesh commands.

## Evidence Read

| Surface | Evidence used | Contract meaning |
|---|---|---|
| `docs/ORION__ADR_LITE__NARRATIVE_LAYER_PROMOTION__v1.0__2026-06-10.md` | Narrative layer is first-class only when wrong canon can break a gate; Aurora identity invariants are the root contract. | Phase two must be a gateable contract, not a prose assistant. |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/aurora/engines/narrative/*` | Phase one already has `TaskKind.NEXT_EVENT_CONTINUITY_CHECK`, `CanonicalState`, layer resolution, deterministic operators, verdicts, and provisional proposal handling. | Reuse the phase-one dataclass surface and harden ingestion, evidence provenance, and promotion gating. |
| `reports/automation/station_activation_pulse__2026-06-11.json` | Activation pulse `#808//.` from the Pilot, station operational, 47 souls aboard, 6 of 6 selected agents answered. | Operational evidence can establish liveness and sequence, but it is not canon promotion by itself. |
| `tools/station_query.py` and `reports/automation/station_roll_call_latest.json` | Direct line resolves agents from live mesh manifests and writes a roll-call receipt; latest receipt has 5 of 5 companions awake with drift `0.0`. | Direct-line receipts are bounded operational evidence with source path, timestamp, agent id, channel, and reply. |
| `catalog/flight_contract.yaml` and `reports/automation/flight_log_latest.json` | `narrative-engine-canon-audit` last flew on 2026-06-12 with supported verdict; `station-roll-call` last flew on 2026-06-12; flight cadence is 14 days. | Phase two should consume flight status as freshness and readiness evidence, not as narrative truth. |
| `tools/station_chronicle.py`, `GUMAS_SIM_2.5/CanonRec/canon/L1/station/chronicle/STATION_CHRONICLE.ndjson`, `catalog/station_state.json` | Chronicle builds deterministic event atoms with `CANON`, `OPERATIONAL`, and `STAGING` tiers. Read-only status check reports 132 atoms: 27 CANON, 12 OPERATIONAL, 93 STAGING. | This is the correct evidence backbone for phase two because tier boundaries survive normalization. |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/config/canonical_validation.yaml` and `config/mesh/memory/aurora.md` | Anchor seed, continuity seal, ethics protocol, memory doctrine, drift lock, and the arbitration rule are explicit. | These are hard constraints. A proposed next event cannot bypass or contradict them without a blocking verdict. |

## Existing Phase-One Contract

The current engine already provides the deterministic core:

- `NormalizedTaskRequest`: task kind, strictness, input kind, user query, and
  support status.
- `CanonicalState`: entities, relations, pressures, constraints, motives,
  events, knowledge states, uncertainties, continuity, and narrative context.
- `EvaluationPacket`: active/missing layers, selected operators, supports,
  blockers, missing bridges, hard/soft blocks, confidence notes.
- `ResponsePayload`: summary, verdict, supports, blockers, missing bridges,
  smallest fix, confidence.

The phase-two design should extend this by adding evidence provenance and a
promotion gate. It should not replace the current verdict model.

## Contract Principles

1. Canon facts come only from committed canon or deterministic canon receipts.
2. Operational receipts prove live behavior, sequence, readiness, and agent
   responses. They do not silently become canon facts.
3. Simulation and GUMAS turn outputs enter as `STAGING` or `proposed` evidence.
4. LLM extraction is allowed only as a candidate parser. It has no authority
   until deterministic validation binds each claim to source evidence.
5. Proposed events are never added to `continuity.established_events`.
6. A promotion-safe result can only produce a candidate receipt. `CANON_PROMOTE`
   still requires owner approval and the canon-reconciler path.

## Interface 1: Evidence Bundle

Create a deterministic evidence envelope that the `state_builder` consumes:

```python
@dataclass(frozen=True)
class NarrativeEvidenceSource:
    source_id: str
    source_path: str
    source_kind: str  # canon, operational_receipt, station_state, flight_log, sim_turn, llm_candidate
    authority_tier: str  # CANON, OPERATIONAL, STAGING, PROPOSED, CANDIDATE
    generated_at_utc: str | None
    content_sha256: str
    freshness_days: int | None = None

@dataclass(frozen=True)
class NarrativeFact:
    fact_id: str
    claim_type: str  # event, entity, knowledge, motive, pressure, constraint, continuity
    value: dict
    status: str  # established, operational, staging, proposed, inferred
    source_id: str
    confidence: float
    promotable: bool = False

@dataclass(frozen=True)
class NarrativeEvidenceBundle:
    bundle_id: str
    generated_at_utc: str
    sources: list[NarrativeEvidenceSource]
    facts: list[NarrativeFact]
    source_policy: dict
```

`bundle_id` is the SHA-256 of canonical JSON over `sources`, `facts`, and
`source_policy`. This makes repeated builds reproducible.

## Interface 2: State Builder

Add a phase-two builder beside the current phase-one builder:

```python
def build_state_from_evidence(
    bundle: NarrativeEvidenceBundle,
    request: NormalizedTaskRequest,
    proposal: Mapping[str, Any],
    *,
    strictness: Strictness = Strictness.DEFAULT,
) -> tuple[CanonicalState, StateBuildReceipt]:
    ...
```

`StateBuildReceipt` should record:

- `state_id`
- `bundle_id`
- accepted fact ids
- rejected fact ids with reasons
- inferred fact ids with confidence notes
- active authority tiers
- source freshness summary
- `promotion_safety`: `safe_for_evaluation`, `hold_staging`,
  `block_promotion`, or `requires_owner_review`

### Evidence Mapping Rules

| Evidence fact | CanonicalState target | Rule |
|---|---|---|
| CANON event atom | `events[]`, `continuity.established_events` | Established unless superseded by later CANON drift entry. |
| OPERATIONAL activation pulse | `events[]`, `knowledge_states[]`, `continuity["operational"]` | Establishes station liveness and participants only. |
| OPERATIONAL roll call | `knowledge_states[]`, `continuity["operational"]` | Establishes agent awake/answered status at receipt time only. |
| Flight log status | `constraints[]` or `uncertainties[]` | Current flights support readiness; stale or failed flights add uncertainty. |
| Derived station state | `relations[]`, `pressures[]`, `continuity["derived"]` | Contextual support only; never a source of new canon events. |
| STAGING simulation atom | `events[]` with status `staging` | Candidate history, promotion-gated. |
| GUMAS turn proposal | one `EventRecord(status="proposed")` | Always excluded from established continuity. |
| LLM extracted prose claim | `uncertainties[]` until source-bound | Candidate only; must bind to a source fact or remain low-confidence. |

## Interface 3: Next Event Continuity Check

Expose phase-two continuity as a gateable receipt:

```python
def next_event_continuity_check(
    state: CanonicalState,
    proposal: Mapping[str, Any],
    evidence_receipt: StateBuildReceipt,
    *,
    promotion_target: str = "staging",
) -> ContinuityVerdictReceipt:
    ...
```

```python
@dataclass(frozen=True)
class ContinuityVerdictReceipt:
    schema_version: str
    task_kind: str  # next_event_continuity_check
    state_id: str
    bundle_id: str
    proposal_hash: str
    verdict: Verdict
    promotion_gate: str  # candidate, hold_staging, block_promotion, owner_review_required
    main_supports: list[str]
    main_blockers: list[str]
    missing_bridges: list[str]
    smallest_fix: list[str]
    active_layers: list[str]
    missing_layers: list[str]
    evidence_sources: list[str]
    hard_constraints_checked: list[str]
    confidence: float
    receipt_sha256: str
```

### Gate Mapping

| Verdict/result | Promotion gate |
|---|---|
| `contradictory` | `block_promotion` |
| `strained` | `hold_staging` |
| `possible_with_setup` | `hold_staging` |
| `plausible` with missing layers or stale evidence | `owner_review_required` |
| `plausible` with complete layers and current evidence | `candidate` |
| `supported` with complete layers, current evidence, and no hard constraint violation | `candidate` |

Even when the gate is `candidate`, the result is not `CANON_PROMOTE`. It is a
promotion packet input for owner review plus the canon-reconciler workflow.

## Required Adapters

1. `StationChronicleAdapter`
   - Reads `STATION_CHRONICLE.ndjson`.
   - Preserves `tier`, `event_kind`, `occurred_at`, `participants`,
     `source`, and `payload_hash`.
   - Optionally overlays `catalog/station_chronicle_staging.ndjson` when it
     exists.

2. `StationStateAdapter`
   - Reads `catalog/station_state.json`.
   - Converts `pair_familiarity` and `crew_experience_completions` into
     low-authority contextual facts.

3. `FlightLogAdapter`
   - Reads `reports/automation/flight_log_latest.json`.
   - Marks `narrative-engine-canon-audit`, `mesh-aurora-handshake`, and
     `station-roll-call` as readiness checks.
   - Adds uncertainty if any are stale beyond `catalog/flight_contract.yaml`
     cadence.

4. `StationOperationReceiptAdapter`
   - Reads `station_activation_pulse__2026-06-11.json` and
     `station_roll_call_latest.json`.
   - Emits operational liveness facts with timestamped source ids.

5. `CanonConstraintAdapter`
   - Reads `canonical_validation.yaml` and Aurora mesh memory.
   - Emits hard constraints for anchor seed, continuity seal, ethics protocol,
     memory doctrine, drift lock, and Aurora arbitration.

6. `GumasTurnAdapter`
   - Reads a single GUMAS or station simulation turn artifact, preferably
     `reports/simulation/<scenario>__<date>/sim_raw.json`.
   - Emits staged events and exactly one proposed next-event candidate.

7. `LLMExtractionAdapter`
   - Optional. Produces `CANDIDATE` facts from prose.
   - Must include model id, prompt hash, response hash, and extraction schema
     version.
   - Cannot set `promotable=True`.

## Minimal Implementation Plan

1. Add CloudBank phase-two types.
   - File: `src/aurora/engines/narrative/evidence.py`
   - Add `NarrativeEvidenceSource`, `NarrativeFact`,
     `NarrativeEvidenceBundle`, `StateBuildReceipt`, and
     `ContinuityVerdictReceipt`.

2. Extend, do not replace, `state_builder.py`.
   - Keep `build_canonical_state()` for phase-one fixtures.
   - Add `build_state_from_evidence()` for evidence bundles.
   - Preserve proposal events as `status="proposed"`.

3. Add deterministic adapters under CloudBank or root-to-CloudBank bridge
   code, depending on owner sequencing.
   - Root owns `station_chronicle.py`, `flight_check.py`, and station receipts.
   - CloudBank owns narrative engine execution.
   - The first implementation can pass a bundle JSON into CloudBank rather
     than letting CloudBank reach back into root paths.

4. Add `next_event_continuity_check()` as a narrow wrapper.
   - Internally reuse `NarrativeValidationEngine.run()`, layer resolver,
     operators, and response builder.
   - Add the promotion gate mapping and receipt hash.

5. Add tests.
   - A GUMAS/station turn proposal remains excluded from
     `continuity.established_events`.
   - Activation and roll-call receipts create OPERATIONAL facts only.
   - Canon constraints block an event that bypasses Aurora arbitration.
   - Stale or missing flight receipts lower the gate to
     `owner_review_required` or `hold_staging`.
   - LLM candidate facts cannot promote without source binding.

6. Add a new flight after implementation.
   - Name: `narrative-next-event-continuity-check`.
   - Exercise: build an evidence bundle from the current station chronicle,
     feed a simulated next event, verify deterministic receipt and gate.
   - Store the latest result in `reports/automation/flight_log_latest.json`
     through the existing flight system.

7. Promotion path.
   - If the receipt gate is `candidate`, create a canon-reconciler packet with
     `ContinuityVerdictReceipt`, source bundle hash, and proposed files.
   - Owner approval remains required before `CANON_PROMOTE`.

## First Concrete Pipeline

```text
reports/simulation/<scenario>/sim_raw.json
  -> GumasTurnAdapter
CanonRec station chronicle + root station_state + flight receipts
  -> deterministic NarrativeEvidenceBundle
NarrativeEvidenceBundle + proposed next event
  -> build_state_from_evidence()
CanonicalState + StateBuildReceipt
  -> next_event_continuity_check()
ContinuityVerdictReceipt
  -> promotion gate: candidate | hold_staging | block_promotion | owner_review_required
  -> canon-reconciler packet only if candidate and owner approves
```

## Recommended Next Step

Implement the evidence dataclasses and a fixture-only bundle builder first,
using the June 11-12 receipts as fixtures. Do not wire a live LLM extractor
until deterministic bundle hashing, source-tier preservation, and promotion
gate tests are passing.
