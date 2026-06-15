# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-15T03:36:39Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

> Senior staff convened in the Observatory to run the living-galaxy dynamic under standing conditions for a full 240-turn horizon — twice the canonical sim window — and certify it from instruments, not memory.

## Watch stations

| Officer | Seat | Station |
|---|---|---|
| Cmdr. Alex Thorne | Station Commander | presiding — go/no-go on the verdict |
| Lt. Cmdr. Maya Shepard | Executive Officer | conflict trajectory + wave analysis |
| Dr. Amira Sato | Chief Ethics Officer | legitimacy erosion + surveillance load |
| Jiro Tanaka | Chief Engineering Officer | engine telemetry integrity |
| Dr. Amina Velin | Symbolic Systems Research Lead | oscillation + attractor analysis |

## Verdict (Cmdr. Thorne): **DYNAMIC GALAXY — CERTIFIED**

*Living* (control) requires: conflict **recurs**, the galaxy does **not** freeze into permanent peace, and does **not** collapse. *Dynamic* adds two more, from MECH-REB-004: conflict has an **off-ramp besides war** (negotiated settlement), and the conflict **cast rotates** (wounds close and new ones open, instead of the same ~13 reopening). Determinism (same seed → identical trajectory): **CONFIRMED**.

> **D9 note (collapse criterion):** collapse is judged on the conflict **load**, not a stability scalar. Calibration showed the honest internal-conflict-aware stability reads ~0.29 at *known* collapse (the permanent-war baseline) and ~0.31 here — the scalar can't separate health from collapse, because conflict is only 10% of the index. What separates them is that the baseline pins ~4 civil wars with zero settlements; a healthy galaxy runs <3 that resolve. Both stability numbers are reported below for transparency; neither gates the verdict.

## Cross-seed summary

| Seed | floor | mature plateau | honest plateau | waves | settlements | onsets | off-ramp share | recurs | off-ramp | rotates | DYNAMIC |
|---|---|---|---|---|---|---|---|:--:|:--:|:--:|:--:|
| 42 | 0.401 | 0.413 | 0.348 | 4 | 75 | 85 | 0.88 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.390 | 0.407 | 0.340 | 4 | 71 | 82 | 0.87 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.392 | 0.412 | 0.325 | 4 | 83 | 93 | 0.89 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0.2, 1.65, 1.15, 0.65, 0.8, 0.45, 0.5, 1.8, 2.15, 1.25, 1.75, 1.95]` — 4 wave(s), peaks at era(s) [1, 4, 8, 11]; 286 civil-war-turns, 85 insurgencies formed.
- **Shepard (off-ramps):** 75 negotiated settlements vs military suppression — of which **69 (92%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.15, 0.3, 0.2, 0.35, 0.35, 0.3, 0.25, 0.5, 0.35, 0.6, 0.4]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.617, 0.615, 0.583, 0.571, 0.532, 0.517, 0.489, 0.447, 0.43, 0.432, 0.42, 0.411]` (floor 0.401); the **honest** internal-conflict-aware metric plateaus at 0.348 (floor 0.311) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.653, 0.618, 0.579, 0.568, 0.55, 0.544, 0.525, 0.502, 0.492, 0.488, 0.474, 0.46]`; complacency/era `[0.045, 0.216, 0.364, 0.402, 0.382, 0.371, 0.423, 0.372, 0.306, 0.324, 0.251, 0.266]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 9 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'hyper_rational': 0.194, 'sunk_cost': 0.103, 'status_quo': 0.163, 'zero_sum': 0.1}` — spread 9% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5579, bandwagoners 0.7012 (gap +0.14, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 4 successions (3 coups, 1 elections), 2 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Velin (emergent consequence):** 5 factions permanently lost territory to their wars; economic-ceiling spread 0.33 (was ~0); war-torn factions end +0.277 weaker in power than the spared (MECH-TER-001) — a war's outcome reshapes the map, the economy, and the balance of power.
- **Tanaka (war economy):** economic health (output/potential) — at war 0.2545, at peace 0.7813 (gap +0.53, MECH-ECO-001). The economy busts in war and booms in reconstruction; a depressed economy feeds unrest, closing the loop war → economic depression → grievance.
- **Sato (cultural cost of conquest):** holding reconquered ground, 115 assimilation-impositions bred identity grievance vs 138 tolerant accommodations earning legitimacy (MECH-CUL-002) — conquest costs differently depending on the conqueror's culture (modest by design).
- **Tanaka (engine):** 85 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3087 migrations, 0 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0, 0.75, 1.05, 0.2, 1, 0.55, 1.6, 1.55, 1.8, 1.75, 0.8]` — 4 wave(s), peaks at era(s) [3, 5, 7, 9]; 221 civil-war-turns, 82 insurgencies formed.
- **Shepard (off-ramps):** 71 negotiated settlements vs military suppression — of which **66 (93%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0.05, 0.05, 0.3, 0.2, 0.15, 0.35, 0.35, 0.3, 0.4, 0.4, 0.6, 0.4]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.63, 0.64, 0.61, 0.584, 0.538, 0.505, 0.471, 0.448, 0.43, 0.427, 0.414, 0.404]` (floor 0.390); the **honest** internal-conflict-aware metric plateaus at 0.340 (floor 0.303) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.657, 0.623, 0.586, 0.574, 0.558, 0.54, 0.516, 0.501, 0.484, 0.484, 0.468, 0.459]`; complacency/era `[0.047, 0.27, 0.446, 0.399, 0.38, 0.41, 0.349, 0.374, 0.31, 0.307, 0.265, 0.296]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 10 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'hyper_rational': 0.221, 'status_quo': 0.198, 'sunk_cost': 0.092, 'zero_sum': 0.123}` — spread 13% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5869, bandwagoners 0.6518 (gap +0.06, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 7 successions (3 coups, 4 elections), 5 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Velin (emergent consequence):** 5 factions permanently lost territory to their wars; economic-ceiling spread 0.21 (was ~0); war-torn factions end +0.205 weaker in power than the spared (MECH-TER-001) — a war's outcome reshapes the map, the economy, and the balance of power.
- **Tanaka (war economy):** economic health (output/potential) — at war 0.364, at peace 0.8075 (gap +0.44, MECH-ECO-001). The economy busts in war and booms in reconstruction; a depressed economy feeds unrest, closing the loop war → economic depression → grievance.
- **Sato (cultural cost of conquest):** holding reconquered ground, 116 assimilation-impositions bred identity grievance vs 52 tolerant accommodations earning legitimacy (MECH-CUL-002) — conquest costs differently depending on the conqueror's culture (modest by design).
- **Tanaka (engine):** 82 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3112 migrations, 0 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 1.05, 1.85, 1.6, 1.9, 0.5, 1.7, 1.3, 2.75, 3.45, 3.05, 3.05]` — 4 wave(s), peaks at era(s) [2, 4, 6, 9]; 444 civil-war-turns, 93 insurgencies formed.
- **Shepard (off-ramps):** 83 negotiated settlements vs military suppression — of which **77 (93%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0.05, 0.15, 0.3, 0.25, 0.25, 0.3, 0.3, 0.45, 0.4, 0.6, 0.5, 0.6]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.614, 0.624, 0.576, 0.566, 0.525, 0.495, 0.443, 0.463, 0.432, 0.421, 0.418, 0.408]` (floor 0.392); the **honest** internal-conflict-aware metric plateaus at 0.325 (floor 0.307) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.654, 0.618, 0.583, 0.568, 0.544, 0.527, 0.505, 0.514, 0.486, 0.472, 0.468, 0.461]`; complacency/era `[0.047, 0.239, 0.34, 0.351, 0.36, 0.395, 0.389, 0.374, 0.297, 0.273, 0.263, 0.255]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 8 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'hyper_rational': 0.23, 'sunk_cost': 0.119, 'status_quo': 0.121, 'zero_sum': 0.102}` — spread 13% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5678, bandwagoners 0.688 (gap +0.12, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 8 successions (4 coups, 4 elections), 5 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Velin (emergent consequence):** 6 factions permanently lost territory to their wars; economic-ceiling spread 0.50 (was ~0); war-torn factions end +0.283 weaker in power than the spared (MECH-TER-001) — a war's outcome reshapes the map, the economy, and the balance of power.
- **Tanaka (war economy):** economic health (output/potential) — at war 0.1952, at peace 0.7479 (gap +0.55, MECH-ECO-001). The economy busts in war and booms in reconstruction; a depressed economy feeds unrest, closing the loop war → economic depression → grievance.
- **Sato (cultural cost of conquest):** holding reconquered ground, 238 assimilation-impositions bred identity grievance vs 190 tolerant accommodations earning legitimacy (MECH-CUL-002) — conquest costs differently depending on the conqueror's culture (modest by design).
- **Tanaka (engine):** 93 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 2989 migrations, 2 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy now shows **dynamic** behaviour, not merely controlled. Conflict still recurs in waves (the complacency cycle, MECH-SOC-006), but civil wars now **end**: a grinding, costly, stalemated insurgency can reach a negotiated **settlement** (MECH-REB-004) that retires it and spends its grievance, so the conflict **cast rotates** (dozens of distinct insurgencies form and resolve, where pre-graft the same ~13 reopened forever). War is no longer the only off-ramp. The honest, internal-conflict-aware stability (D1) sits well below the engine's headline number — the civil-war load the old metric masked — and is reported as the true reading. Nothing here is tuned to a target; the de-escalation rule is the engine's own (`calc_deescalation_probability`).

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
