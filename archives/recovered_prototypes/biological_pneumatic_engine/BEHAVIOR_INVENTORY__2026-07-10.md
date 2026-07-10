# Behavior Inventory — Biological Pneumatic Engine (P7)

Date: 2026-07-10
Subject: `biological_pneumatic_engine.py` (497 lines, SHA-256 `20df6280…`)
Scope: docket P7 next-gate deliverable ("small behavior inventory before code
migration"). Describes observed code behavior only; no claims beyond repo
evidence.

## Purpose

Standalone prototype modeling dialogue processing as pressure-differential
information flow. Cited research anchors (docstring): microfluidic pneumatic
logic (Jensen et al., 2007), breathing-cognition coupling (Heck et al.,
2019/2022), dialogue rhythm entrainment (Wynn et al., 2022), consciousness
gradient information flow (Margulies et al., 2016).

Dependencies: numpy (used throughout), asyncio, dataclasses.
scipy was imported but never used (removed from the operative copy 2026-07-10).

## Components

### 1. `PneumaticLogicGate`
- Async Boolean gates: AND, OR, NOT, XOR, NAND; unknown type raises ValueError.
- Threshold comparator (default 50.0) over float inputs; constants
  VACUUM_PRESSURE=87 kPa, ATMOSPHERIC=0.
- Each `compute()` awaits `asyncio.sleep(2.5ms)` to simulate pneumatic
  response time — wall-clock delay, not simulated time.

### 2. `BreathingCognitionCoupler`
- Sinusoidal phase accumulator: default 0.25 Hz (15 breaths/min),
  `phase = (phase + 2π·f·dt) mod 2π`.
- `get_cognitive_modulation()` = 0.7 baseline + 0.15·sin(phase).
- `get_task_optimal_phase()` maps task type → phase window
  (encoding: inhalation [0, π]; retrieval: exhalation [π, 2π];
  attention: [0, π/2]; else full cycle).

### 3. `PneumaticInformationProcessor`
- Operates on a `ConsciousnessGradient` (default 5 nodes:
  input → attention → semantic → creative → output).
- `compute_flow()`: Hagen-Poiseuille analogy — flow_i =
  (P_i − P_{i+1}) / viscosity × mean(attention_i, attention_{i+1});
  mass-conserving pressure updates (±0.5·flow·dt per node pair).
- `get_processing_latency()`: 5.0 ms base + 0.3·Σ|flow| −
  0.5·cos(breathing_phase), floor 2.0 ms.
- `process_information()`: seeds node-0 pressure from input, iterates
  duration_ms/10 timesteps with 1 ms async sleeps; efficiency =
  1 − latency/50 (clamped ≥ 0), relative to a 50 ms "classical" baseline.

### 4. `DialogueRhythmEntrainment`
- Rolling 10-turn window of user vs AI rhythm (words/sec).
- Entrainment = (1 − mean|Δrhythm|/5.0) × rhythm_perception; requires ≥3
  turns, else 0. Not clamped to [0,1] in the prototype (fallback
  reimplementation clamps).
- `get_optimal_ai_rhythm()`: converges AI rhythm toward mean of last 3 user
  rhythms at rate 0.3·entrainment.
- `estimate_conversational_quality()` = min(0.5 + 0.4·entrainment +
  0.1·rhythm_perception, 1.0).

### 5. `BiologicalPneumaticEngine` (integrator)
- Config keys: `consciousness_nodes`, `viscosity` (0.1), `breathing_frequency`
  (0.25), `rhythm_perception` (0.75).
- Instantiates three gates (attention_gate AND, flow_control OR,
  coherence_check XOR) — **constructed but never invoked** in any code path;
  dead wiring in the prototype.
- `process_dialogue_turn(input)` → dict: response (output pressure),
  latency_ms, efficiency, quality, entrainment, optimal_ai_rhythm,
  cognitive_state, breathing_phase. Hardcoded AI rhythm = 5.0 words/sec.
- `get_performance_summary()` → means over per-turn metric history.

## I/O contract (per dialogue turn)

Input: `{message: str, pressure: float=100.0, attention_focus: List[float]
(len 5 default), user_rhythm: float=4.0}`
Output keys: response, latency_ms, efficiency, quality, entrainment,
optimal_ai_rhythm, cognitive_state, breathing_phase.

## Validation targets (committed)

Source: `03_SPECIFICATIONS/Bootstrap_Standards/pneumatic_validation_metrics.csv`
→ `pdp_v2_mvp/config/targets.yaml`: latency <10 ms, efficiency >0.85,
entrainment >0.70, cognitive boost >10%.

Observed (2026-07-10 smoke test, fallback adapter, single turn): latency
5.48 ms, efficiency 0.89 — latency/efficiency targets pass; entrainment needs
≥3 turns to register.

## Downstream consumers

- `pdp_v2_mvp/core/pneumatic_engine.py` — `PneumaticEngineAdapter` prefers
  this engine (`use_scipy=True`), with a deterministic pure-Python fallback
  mirroring the same math (no numpy, no wall-clock sleeps, clamped
  entrainment).
- `pdp_v2_mvp/services/pdp_service.py` — session orchestration; adapter
  metrics feed the biofeedback tracker, attention fusion, and metrics
  validator.
- `skills/aurora-skill-finder` — registers
  `pdp_v2_mvp/core/pneumatic_engine.py` as a hotspot routing to
  `aurora-python-ingest-autowire`.

## Known defects / migration notes

1. (fixed in operative copy 2026-07-10) Dead scipy import blocked external
   mode in scipy-less environments.
2. (fixed in operative copy 2026-07-10) Adapter blanket `except Exception`
   masked real engine defects as silent fallback.
3. Logic gates are dead wiring — never invoked. Migration should either wire
   them into flow control or drop them.
4. Wall-clock `asyncio.sleep` in gates and processor makes turn processing
   O(duration_ms) real time; a migrated runtime version should use simulated
   time.
5. Prototype entrainment is not clamped to [0,1]; fallback clamps. Any
   migration should adopt the clamped form.
6. `efficiency` can reach 0 but latency floor (2 ms) bounds it ≤ 0.96.
7. **External/fallback divergence (verified 2026-07-10):** under default
   config (viscosity 0.1, 5 nodes, pressure 100), the external prototype's
   flow-complexity penalty (0.3·Σ|flow|, with flow ≈ ΔP/0.1) dominates
   latency: observed ~202 ms, efficiency 0.0 — it fails its own committed
   targets. The fallback computes its gradient from attention values instead
   of node pressures and passes (5.2–5.5 ms, efficiency ~0.89). The two
   engines are NOT behaviorally equivalent despite the adapter treating them
   as interchangeable; any migration must decide which latency model is
   canonical and either retune viscosity/penalty constants or fix the flow
   term. PDP v2 MVP tests (7/7 passing) exercise only the fallback path.
