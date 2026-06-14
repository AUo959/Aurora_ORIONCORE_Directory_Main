# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-14T20:46:39Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

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
| 42 | 0.375 | 0.390 | 0.332 | 3 | 66 | 79 | 0.83 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.374 | 0.386 | 0.304 | 5 | 77 | 87 | 0.89 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.370 | 0.386 | 0.316 | 4 | 60 | 70 | 0.86 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.7, 1.05, 1.3, 0.75, 0.85, 2.25, 2.35, 0.8, 1.65, 1.5, 1.2]` — 3 wave(s), peaks at era(s) [3, 7, 9]; 288 civil-war-turns, 79 insurgencies formed.
- **Shepard (off-ramps):** 66 negotiated settlements vs military suppression — of which **35 (53%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.1, 0.25, 0.2, 0.25, 0.45, 0.35, 0.35, 0.3, 0.35, 0.55, 0.15]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.609, 0.611, 0.579, 0.551, 0.516, 0.482, 0.449, 0.425, 0.417, 0.405, 0.386, 0.39]` (floor 0.375); the **honest** internal-conflict-aware metric plateaus at 0.332 (floor 0.278) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.604, 0.574, 0.561, 0.54, 0.522, 0.508, 0.493, 0.481, 0.475, 0.447, 0.447]`; complacency/era `[0.047, 0.241, 0.413, 0.374, 0.416, 0.453, 0.355, 0.348, 0.335, 0.317, 0.275, 0.269]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 5 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'sunk_cost': 0.098, 'hyper_rational': 0.202, 'status_quo': 0.131, 'zero_sum': 0.089}` — spread 11% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Tanaka (engine):** 79 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3125 migrations, 0 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.65, 2.15, 2.65, 1.95, 2.6, 2, 2, 1.55, 2.7, 2.05, 2.8]` — 5 wave(s), peaks at era(s) [3, 5, 7, 9, 11]; 462 civil-war-turns, 87 insurgencies formed.
- **Shepard (off-ramps):** 77 negotiated settlements vs military suppression — of which **40 (52%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.1, 0.2, 0.4, 0.3, 0.25, 0.45, 0.35, 0.35, 0.45, 0.45, 0.55]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.605, 0.587, 0.555, 0.523, 0.499, 0.455, 0.438, 0.412, 0.409, 0.397, 0.396, 0.384]` (floor 0.374); the **honest** internal-conflict-aware metric plateaus at 0.304 (floor 0.276) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.602, 0.565, 0.554, 0.542, 0.519, 0.506, 0.486, 0.476, 0.457, 0.46, 0.442]`; complacency/era `[0.047, 0.254, 0.394, 0.342, 0.348, 0.329, 0.285, 0.275, 0.253, 0.285, 0.301, 0.271]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 7 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'sunk_cost': 0.058, 'hyper_rational': 0.185, 'status_quo': 0.186, 'zero_sum': 0.065}` — spread 13% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Tanaka (engine):** 87 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3156 migrations, 9 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.55, 1.6, 0.25, 0.2, 1.1, 1.85, 0.6, 1, 2.35, 2.3, 3.1]` — 4 wave(s), peaks at era(s) [2, 6, 9, 11]; 298 civil-war-turns, 70 insurgencies formed.
- **Shepard (off-ramps):** 60 negotiated settlements vs military suppression — of which **39 (65%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0, 0.25, 0.2, 0.2, 0.35, 0.25, 0.25, 0.3, 0.5, 0.45, 0.25]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.612, 0.621, 0.581, 0.549, 0.515, 0.497, 0.467, 0.433, 0.419, 0.398, 0.393, 0.385]` (floor 0.370); the **honest** internal-conflict-aware metric plateaus at 0.316 (floor 0.284) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.651, 0.608, 0.573, 0.558, 0.531, 0.535, 0.523, 0.495, 0.482, 0.468, 0.463, 0.447]`; complacency/era `[0.047, 0.256, 0.371, 0.372, 0.44, 0.377, 0.285, 0.35, 0.426, 0.322, 0.199, 0.256]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path). 8 peace accords broke (MECH-DIP-003) — settled peace binds but is not unconditional; a broken brokered peace burns the broker's trust.
- **Velin (authentic decisions):** settlement rate by culture `{'zero_sum': 0.066, 'status_quo': 0.139, 'hyper_rational': 0.193, 'sunk_cost': 0.06}` — spread 13% (MECH-GOV-002). Belligerent/face-saving cultures (zero-sum, sunk-cost) grind on; rational/survivalist orders take the off-ramp — same conditions, different choices.
- **Tanaka (engine):** 70 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3123 migrations, 7 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy now shows **dynamic** behaviour, not merely controlled. Conflict still recurs in waves (the complacency cycle, MECH-SOC-006), but civil wars now **end**: a grinding, costly, stalemated insurgency can reach a negotiated **settlement** (MECH-REB-004) that retires it and spends its grievance, so the conflict **cast rotates** (dozens of distinct insurgencies form and resolve, where pre-graft the same ~13 reopened forever). War is no longer the only off-ramp. The honest, internal-conflict-aware stability (D1) sits well below the engine's headline number — the civil-war load the old metric masked — and is reported as the true reading. Nothing here is tuned to a target; the de-escalation rule is the engine's own (`calc_deescalation_probability`).

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
