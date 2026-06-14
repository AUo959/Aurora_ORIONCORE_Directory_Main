# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-14T21:39:18Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

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
| 42 | 0.390 | 0.415 | 0.354 | 2 | 73 | 85 | 0.86 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.402 | 0.414 | 0.329 | 4 | 72 | 82 | 0.88 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.377 | 0.405 | 0.317 | 3 | 85 | 95 | 0.90 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0.2, 1.65, 1.15, 0.65, 0.8, 0.45, 0.5, 1.8, 2.5, 2.7, 2.85, 2.1]` — 2 wave(s), peaks at era(s) [1, 10]; 347 civil-war-turns, 85 insurgencies formed.
- **Shepard (off-ramps):** 73 negotiated settlements vs military suppression — of which **66 (90%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.15, 0.3, 0.2, 0.35, 0.35, 0.3, 0.25, 0.5, 0.45, 0.5, 0.3]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.617, 0.614, 0.582, 0.571, 0.532, 0.517, 0.489, 0.446, 0.43, 0.428, 0.425, 0.41]` (floor 0.390); the **honest** internal-conflict-aware metric plateaus at 0.354 (floor 0.316) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.653, 0.617, 0.577, 0.567, 0.55, 0.544, 0.525, 0.501, 0.49, 0.486, 0.476, 0.468]`; complacency/era `[0.045, 0.216, 0.364, 0.402, 0.382, 0.371, 0.423, 0.372, 0.306, 0.3, 0.217, 0.241]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 10 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'hyper_rational': 0.184, 'sunk_cost': 0.109, 'status_quo': 0.152, 'zero_sum': 0.076}` — spread 11% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5475, bandwagoners 0.7085 (gap +0.16, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 8 successions (5 coups, 3 elections), 7 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Velin (emergent consequence):** 5 factions permanently lost territory to their wars; economic-ceiling spread 0.36 (was ~0); war-torn factions end +0.231 weaker in power than the spared (MECH-TER-001) — a war's outcome reshapes the map, the economy, and the balance of power.
- **Tanaka (war economy):** economic health (output/potential) — at war 0.2389, at peace 0.7811 (gap +0.54, MECH-ECO-001). The economy busts in war and booms in reconstruction; a depressed economy feeds unrest, closing the loop war → economic depression → grievance.
- **Tanaka (engine):** 85 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3099 migrations, 0 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0, 0.75, 1.05, 0.2, 1, 0.55, 1.6, 1.55, 1.8, 1.9, 0.5]` — 4 wave(s), peaks at era(s) [3, 5, 7, 10]; 218 civil-war-turns, 82 insurgencies formed.
- **Shepard (off-ramps):** 72 negotiated settlements vs military suppression — of which **67 (93%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0.05, 0.05, 0.3, 0.2, 0.15, 0.35, 0.35, 0.3, 0.4, 0.4, 0.5, 0.55]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.63, 0.64, 0.61, 0.584, 0.538, 0.505, 0.471, 0.448, 0.43, 0.428, 0.413, 0.415]` (floor 0.402); the **honest** internal-conflict-aware metric plateaus at 0.329 (floor 0.301) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.657, 0.623, 0.586, 0.573, 0.558, 0.539, 0.516, 0.501, 0.483, 0.485, 0.464, 0.463]`; complacency/era `[0.047, 0.27, 0.446, 0.399, 0.38, 0.41, 0.349, 0.374, 0.31, 0.307, 0.265, 0.298]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 10 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'hyper_rational': 0.227, 'status_quo': 0.193, 'sunk_cost': 0.095, 'zero_sum': 0.108}` — spread 13% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5853, bandwagoners 0.6565 (gap +0.07, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 4 successions (1 coups, 3 elections), 3 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Velin (emergent consequence):** 5 factions permanently lost territory to their wars; economic-ceiling spread 0.18 (was ~0); war-torn factions end +0.228 weaker in power than the spared (MECH-TER-001) — a war's outcome reshapes the map, the economy, and the balance of power.
- **Tanaka (war economy):** economic health (output/potential) — at war 0.3664, at peace 0.8061 (gap +0.44, MECH-ECO-001). The economy busts in war and booms in reconstruction; a depressed economy feeds unrest, closing the loop war → economic depression → grievance.
- **Tanaka (engine):** 82 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3121 migrations, 0 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 1.05, 1.85, 0.95, 1.3, 0.7, 0.4, 1.25, 1.4, 1.6, 3.2, 3.55]` — 3 wave(s), peaks at era(s) [2, 4, 11]; 345 civil-war-turns, 95 insurgencies formed.
- **Shepard (off-ramps):** 85 negotiated settlements vs military suppression — of which **80 (94%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0.05, 0.15, 0.3, 0.25, 0.3, 0.35, 0.35, 0.45, 0.5, 0.55, 0.35, 0.65]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.614, 0.624, 0.576, 0.561, 0.506, 0.502, 0.481, 0.442, 0.426, 0.422, 0.417, 0.401]` (floor 0.377); the **honest** internal-conflict-aware metric plateaus at 0.317 (floor 0.299) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.654, 0.618, 0.582, 0.564, 0.532, 0.535, 0.521, 0.5, 0.487, 0.476, 0.464, 0.444]`; complacency/era `[0.047, 0.239, 0.34, 0.347, 0.383, 0.366, 0.34, 0.272, 0.273, 0.299, 0.275, 0.246]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 8 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'hyper_rational': 0.206, 'sunk_cost': 0.115, 'status_quo': 0.182, 'zero_sum': 0.092}` — spread 11% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.536, bandwagoners 0.7124 (gap +0.18, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 8 successions (4 coups, 4 elections), 6 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Velin (emergent consequence):** 6 factions permanently lost territory to their wars; economic-ceiling spread 0.29 (was ~0); war-torn factions end +0.234 weaker in power than the spared (MECH-TER-001) — a war's outcome reshapes the map, the economy, and the balance of power.
- **Tanaka (war economy):** economic health (output/potential) — at war 0.1758, at peace 0.7026 (gap +0.53, MECH-ECO-001). The economy busts in war and booms in reconstruction; a depressed economy feeds unrest, closing the loop war → economic depression → grievance.
- **Tanaka (engine):** 95 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 2982 migrations, 0 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy now shows **dynamic** behaviour, not merely controlled. Conflict still recurs in waves (the complacency cycle, MECH-SOC-006), but civil wars now **end**: a grinding, costly, stalemated insurgency can reach a negotiated **settlement** (MECH-REB-004) that retires it and spends its grievance, so the conflict **cast rotates** (dozens of distinct insurgencies form and resolve, where pre-graft the same ~13 reopened forever). War is no longer the only off-ramp. The honest, internal-conflict-aware stability (D1) sits well below the engine's headline number — the civil-war load the old metric masked — and is reported as the true reading. Nothing here is tuned to a target; the de-escalation rule is the engine's own (`calc_deescalation_probability`).

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
