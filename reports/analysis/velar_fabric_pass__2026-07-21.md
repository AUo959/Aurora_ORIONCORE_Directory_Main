# Velar Imperium Fabric-Invariants Pass — 2026-07-21

**Queue item:** `velar-fabric-pass` (high, either)
**Spec:** CanonRec `canon/L2/mechanics/FABRIC_INVARIANTS__v0.1__2026-07-21.md` (STAGING, owner-ratified in scope)
**Method:** (1) static check via new `tools/fabric_invariants_check.py`; (2) enforcement
trace of `aurora-cloudbank-symbolic-main`; (3) deterministic engine run
(GUMASAdvancedEngine, scenario `gumas_canonical_v1`, seed 42, 40 turns) with
event-ledger verification (1,349 events, 153 Velar-touching).

## 1. Static check (6 Velar-bound entities scanned)

| Invariant | Result | Detail |
|---|---|---|
| T1 | PASS | Both timeline files monotonic (eras oldest→newest); cross-file event timeframes identical; Marshal-Council conquest era (~300 ybp, ARCHIVE_MINING_ADDENDUM) coheres with Sahn'Darith Accord IA-E1 (~300 ybp). |
| T2 | PASS | No stated cycle:year ratio ≠ 1:1 anywhere in canon corpus. |
| T3 | INFO | virex_talvaren recent_actions undated — statically unverifiable; assumed Present-window per snapshot convention. |
| P1 | **VIOLATION ×2** | `loc_vel_surak` and `loc_vel_surak_megacity_…` claim `canonical_position_status: canon`, but the map authority table (source of truth per P1) lists both rows at **STAGING** with "placement TBD". Entity records overstate placement certainty. |
| P2 | PASS (vacuous) / GAP | No Velar-bound mobile assets exist. Schema-level: no vessel record carries a `placement_rule` field — P2 is enforced only at reconciler validation, not in the record schema. |
| P3 | GAP ×3 | Both Velar locations have `region_id: null` (no adjacency anchor, though the map defines Velar Crescent zones); megacity record's "collapse into vel_surak parent" note was never structurally executed (no parent link field). |
| C1 | GAP | Character capsules (virex_talvaren checked) have no location/vessel binding field — one-body-one-place is unenforceable statically or in-engine. Matches spec enforcement-map note. |
| C2 | PASS | Single, vocabulary-valid status on every Velar entity. |
| C3 | PASS | One living incumbent per office: Lord Marshal / Supreme Military Commander (Velar) = virex_talvaren only; no cross-faction collision (Durn = GU, Torr-Kai = Separatist). |
| C4 | PASS | All named actors in Velar knowledge text resolve ("Chancellor Zylox" → zylox_rhaegos). |

Machine-readable findings: run `python3 tools/fabric_invariants_check.py --domain velar --json <path>`
(deterministic; exit 1 = violations present).

## 2. aurora-cloudbank-symbolic enforcement trace (4 modules + tests)

| Module | What it actually enforces | Fabric invariants covered |
|---|---|---|
| `src/monitoring/ethics_engine.py` | Operational conduct rules (safety, human oversight, transparency, fairness, consent); rule/violation persistence; blocking on severity | **None** of T/P/C — categories are operational, not fabric |
| `src/agents/drift_responder.py` | Runbook-driven responses to `DriftAlert`s (log/notify/alert/throttle/suspend/rebaseline/escalate) | **None directly** — generic responder; no fabric-aware detector feeds it today. Natural integration sink for a fabric checker emitting DriftAlerts |
| `src/utils/file_lock.py` | `DirLock` PID-file mutual exclusion on storage dirs | Structural analogue of **C2** only (prevents concurrent contradictory writes); no semantic check |
| `src/sensors/` (`core/layer_interpreter.py`, `core/reading_types.py`) | Layer provenance discipline: L2 signals literal-within-sim, `actionable=False`; flags L1↔L2 cross-layer contamination | Closest to **T4** boundary semantics; none of T1–T3/P/C |

**Conclusion:** the symbolic layer enforces **zero fabric invariants semantically**.
Recommended wiring (owner decision): `fabric_invariants_check` findings → `DriftAlert` →
`DriftResponder` runbooks (severity: VIOLATION→alert/escalate, GAP→log/notify).

## 3. Engine verification (seed 42, 40 turns, deterministic)

- **T1 PASS:** event ledger strictly ordered under engine key (turn, phase, ordinal); event_ids unique; payloads sha256-hashed. Final: stability 0.479, risk 0.548.
- **T4 PASS with note:** events are purely turn-indexed, no calendar/cycle claims. Note: all 118 `TECH_NODE_UNLOCKED` events (8 Velar, incl. `prop_1` Hyperlane Mapping) fire at turn 1 — an initialization backfill. Any canon promotion citing engine turns must state the turn→cycle mapping **and** treat the turn-1 burst as initialization, not narrative moment.
- **P4 GAP:** 420 `POPULATION_MIGRATION` events (57 Velar) carry origin/destination/reason but never cite a canonical drive/route (hyperlane/jump/corridor), despite Hyperlane Mapping being unlocked. Cross-region movement mechanism is implicit, contra P4.
- **P1–P3 N/A:** engine has no spatial model below faction granularity — cannot violate, cannot enforce.
- **C1–C3 vacuous:** no leader location bindings; zero succession/death events this run (confirms spec enforcement-map: "leaders have no location binding").
- **C4 PASS:** only canonical faction ids appear; no invented named actors.
- Velar event profile: 153 events — 57 migration, 40 surveillance-expansion, 31 intel-compromise, 11 refugee-crisis, 8 tech, 5 diplomatic, 1 rebellion-onset (coheres with divide-and-rule internal-instability canon).

## 4. Owner rulings queued (no canon records modified by this pass)

1. **RULING-VELAR-P1:** resolve Vel-Surak placement — either fix placement on the map authority table (promoting the rows past STAGING/TBD) or downgrade `canonical_position_status` on both location entities. Map is source of truth; current state is contradictory.
2. **RULING-VELAR-P3:** after P1 ruling, populate `region_id` (Velar Crescent zone entities may need creation) and either execute or drop the megacity "collapse into parent" plan.
3. **RULING-FABRIC-SCHEMA:** approve schema additions — `placement_rule` on mobile assets (P2), location/vessel binding on character capsules (C1) — plus reconciler checks for both.
4. **RULING-FABRIC-WIRING:** approve (or defer) fabric-checker → DriftAlert → DriftResponder integration in aurora-cloudbank-symbolic.
5. **RULING-ENGINE-P4:** decide whether migration events must cite canonical routes (engine change) or P4 is satisfied by reason-tagged faction-level flows.

## 5. Receipts

- Linter: `tools/fabric_invariants_check.py` (new, stdlib-only, deterministic).
- Engine artifacts: `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/advanced_skill_output.json` + `advanced_event_ledger.ndjson` (seed 42, engine 4.0.0-synth, export 2026-07-21T03:52Z).
- CanonRec: `canon/L2/velar/VELAR_FABRIC_PASS__2026-07-21.md` (ledger LEDGER-VELAR-0001..0006) + DRIFT_LOG entry.
- Spec status: FABRIC_INVARIANTS v0.1 remains **STAGING**; T1/T2/C2/C3/C4 now carry Velar-pass verification evidence.
