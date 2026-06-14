# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-14T21:09:28Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

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
| 42 | 0.400 | 0.415 | 0.335 | 3 | 91 | 99 | 0.92 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.381 | 0.398 | 0.320 | 4 | 76 | 87 | 0.87 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.397 | 0.425 | 0.338 | 4 | 72 | 83 | 0.87 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0.05, 0.3, 0.55, 1.15, 1.9, 1.2, 1.05, 1.5, 2.2, 2, 2.8, 2.6]` — 3 wave(s), peaks at era(s) [4, 8, 10]; 346 civil-war-turns, 99 insurgencies formed.
- **Shepard (off-ramps):** 91 negotiated settlements vs military suppression — of which **88 (97%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.15, 0.15, 0.35, 0.35, 0.4, 0.25, 0.7, 0.45, 0.6, 0.5, 0.65]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.62, 0.612, 0.584, 0.572, 0.551, 0.477, 0.465, 0.461, 0.44, 0.428, 0.413, 0.417]` (floor 0.400); the **honest** internal-conflict-aware metric plateaus at 0.335 (floor 0.313) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.651, 0.602, 0.573, 0.56, 0.551, 0.519, 0.51, 0.496, 0.488, 0.471, 0.464, 0.456]`; complacency/era `[0.046, 0.25, 0.438, 0.392, 0.363, 0.363, 0.375, 0.378, 0.244, 0.289, 0.303, 0.264]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 13 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'status_quo': 0.2, 'sunk_cost': 0.163, 'hyper_rational': 0.229, 'zero_sum': 0.103, 'fear_based': 0.118}` — spread 13% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5271, bandwagoners 0.7759 (gap +0.25, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 9 successions (7 coups, 2 elections), 6 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Tanaka (engine):** 99 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3107 migrations, 0 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0, 0.2, 1.2, 1.6, 0.75, 0.6, 2.3, 1.35, 1.85, 1.25, 3.45]` — 4 wave(s), peaks at era(s) [4, 7, 9, 11]; 291 civil-war-turns, 87 insurgencies formed.
- **Shepard (off-ramps):** 76 negotiated settlements vs military suppression — of which **73 (96%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0, 0.25, 0.25, 0.3, 0.2, 0.45, 0.25, 0.6, 0.45, 0.6, 0.45]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.612, 0.612, 0.61, 0.577, 0.534, 0.477, 0.469, 0.446, 0.428, 0.43, 0.409, 0.397]` (floor 0.381); the **honest** internal-conflict-aware metric plateaus at 0.320 (floor 0.304) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.603, 0.578, 0.558, 0.543, 0.518, 0.516, 0.496, 0.47, 0.471, 0.455, 0.438]`; complacency/era `[0.047, 0.27, 0.488, 0.421, 0.354, 0.377, 0.404, 0.338, 0.321, 0.337, 0.308, 0.264]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 11 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'sunk_cost': 0.073, 'status_quo': 0.167, 'hyper_rational': 0.223, 'zero_sum': 0.119}` — spread 15% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.4892, bandwagoners 0.8029 (gap +0.31, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 9 successions (5 coups, 4 elections), 7 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Tanaka (engine):** 87 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3035 migrations, 0 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.65, 1.15, 0.3, 0.35, 1.55, 1.65, 1.55, 1.2, 2.9, 1.9, 2.35]` — 4 wave(s), peaks at era(s) [2, 6, 9, 11]; 311 civil-war-turns, 83 insurgencies formed.
- **Shepard (off-ramps):** 72 negotiated settlements vs military suppression — of which **68 (94%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0, 0.3, 0.25, 0.2, 0.35, 0.3, 0.25, 0.3, 0.55, 0.5, 0.6]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.618, 0.631, 0.582, 0.56, 0.525, 0.507, 0.491, 0.467, 0.423, 0.435, 0.428, 0.425]` (floor 0.397); the **honest** internal-conflict-aware metric plateaus at 0.338 (floor 0.314) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.652, 0.609, 0.565, 0.557, 0.536, 0.528, 0.52, 0.508, 0.477, 0.481, 0.46, 0.454]`; complacency/era `[0.047, 0.254, 0.403, 0.407, 0.412, 0.35, 0.322, 0.325, 0.391, 0.308, 0.3, 0.272]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 12 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'zero_sum': 0.094, 'sunk_cost': 0.093, 'status_quo': 0.176, 'hyper_rational': 0.216, 'fear_based': 0.137}` — spread 12% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Shepard (power politics):** trust toward the hegemon — balancers 0.5162, bandwagoners 0.771 (gap +0.25, MECH-POW-001). Proud/defensive cultures balance *against* the strongest; pragmatic/survivalist ones bandwagon *with* it — power politics decided by culture.
- **Sato (internal politics):** 9 successions (6 coups, 3 elections), 7 factions changed regime + culture (MECH-GOV-003) — a fallen leader's grip lost to scandal and illegitimacy; the new order decides differently, so politics shifts the faction's trajectory.
- **Tanaka (engine):** 83 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3064 migrations, 0 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy now shows **dynamic** behaviour, not merely controlled. Conflict still recurs in waves (the complacency cycle, MECH-SOC-006), but civil wars now **end**: a grinding, costly, stalemated insurgency can reach a negotiated **settlement** (MECH-REB-004) that retires it and spends its grievance, so the conflict **cast rotates** (dozens of distinct insurgencies form and resolve, where pre-graft the same ~13 reopened forever). War is no longer the only off-ramp. The honest, internal-conflict-aware stability (D1) sits well below the engine's headline number — the civil-war load the old metric masked — and is reported as the true reading. Nothing here is tuned to a target; the de-escalation rule is the engine's own (`calc_deescalation_probability`).

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
