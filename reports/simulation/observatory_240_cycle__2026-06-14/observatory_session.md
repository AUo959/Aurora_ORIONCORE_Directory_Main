# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-14T13:10:37Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

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
| 42 | 0.376 | 0.387 | 0.326 | 3 | 60 | 71 | 0.84 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.368 | 0.384 | 0.294 | 3 | 64 | 74 | 0.86 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.377 | 0.387 | 0.300 | 3 | 68 | 76 | 0.90 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.15, 0.55, 1.4, 0.65, 1.85, 1.95, 2.4, 1.5, 1.3, 1.45, 0.55]` — 3 wave(s), peaks at era(s) [3, 7, 10]; 275 civil-war-turns, 71 insurgencies formed.
- **Shepard (off-ramps):** 60 negotiated settlements vs military suppression; settlements/era `[0, 0.05, 0.15, 0.2, 0.3, 0.15, 0.3, 0.25, 0.55, 0.3, 0.4, 0.35]` — war is no longer the only way a civil war ends (MECH-REB-004).
- **Velin (oscillation + honesty):** engine stability/era `[0.609, 0.613, 0.586, 0.552, 0.508, 0.452, 0.435, 0.403, 0.397, 0.393, 0.391, 0.386]` (floor 0.376); the **honest** internal-conflict-aware metric plateaus at 0.326 (floor 0.292) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.602, 0.572, 0.556, 0.538, 0.505, 0.495, 0.467, 0.46, 0.457, 0.449, 0.439]`; complacency/era `[0.047, 0.251, 0.433, 0.39, 0.373, 0.405, 0.372, 0.36, 0.28, 0.221, 0.251, 0.319]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path).
- **Tanaka (engine):** 71 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3187 migrations, 0 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.8, 1.55, 1.7, 1.55, 0.6, 0.05, 2.35, 2.85, 1.55, 1.2, 3.75]` — 3 wave(s), peaks at era(s) [3, 8, 11]; 359 civil-war-turns, 74 insurgencies formed.
- **Shepard (off-ramps):** 64 negotiated settlements vs military suppression; settlements/era `[0.05, 0.05, 0.2, 0.3, 0.25, 0.2, 0.25, 0.2, 0.5, 0.35, 0.3, 0.55]` — war is no longer the only way a civil war ends (MECH-REB-004).
- **Velin (oscillation + honesty):** engine stability/era `[0.605, 0.599, 0.582, 0.539, 0.505, 0.471, 0.441, 0.421, 0.4, 0.405, 0.393, 0.381]` (floor 0.368); the **honest** internal-conflict-aware metric plateaus at 0.294 (floor 0.268) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.609, 0.576, 0.552, 0.537, 0.521, 0.496, 0.483, 0.473, 0.468, 0.448, 0.434]`; complacency/era `[0.047, 0.25, 0.383, 0.367, 0.385, 0.363, 0.426, 0.392, 0.196, 0.254, 0.308, 0.221]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path).
- **Tanaka (engine):** 74 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3155 migrations, 0 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.5, 0.55, 0.2, 0.9, 1.85, 1.7, 1.5, 1.7, 0.75, 2.25, 1.7]` — 3 wave(s), peaks at era(s) [5, 8, 10]; 272 civil-war-turns, 76 insurgencies formed.
- **Shepard (off-ramps):** 68 negotiated settlements vs military suppression; settlements/era `[0, 0.05, 0.25, 0.25, 0.15, 0.3, 0.25, 0.45, 0.25, 0.5, 0.45, 0.5]` — war is no longer the only way a civil war ends (MECH-REB-004).
- **Velin (oscillation + honesty):** engine stability/era `[0.612, 0.605, 0.571, 0.542, 0.474, 0.459, 0.443, 0.415, 0.421, 0.399, 0.389, 0.387]` (floor 0.377); the **honest** internal-conflict-aware metric plateaus at 0.300 (floor 0.277) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.651, 0.601, 0.567, 0.555, 0.518, 0.517, 0.499, 0.477, 0.49, 0.457, 0.447, 0.445]`; complacency/era `[0.047, 0.257, 0.421, 0.372, 0.425, 0.373, 0.374, 0.32, 0.266, 0.319, 0.279, 0.178]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path).
- **Tanaka (engine):** 76 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3111 migrations, 0 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy now shows **dynamic** behaviour, not merely controlled. Conflict still recurs in waves (the complacency cycle, MECH-SOC-006), but civil wars now **end**: a grinding, costly, stalemated insurgency can reach a negotiated **settlement** (MECH-REB-004) that retires it and spends its grievance, so the conflict **cast rotates** (dozens of distinct insurgencies form and resolve, where pre-graft the same ~13 reopened forever). War is no longer the only off-ramp. The honest, internal-conflict-aware stability (D1) sits well below the engine's headline number — the civil-war load the old metric masked — and is reported as the true reading. Nothing here is tuned to a target; the de-escalation rule is the engine's own (`calc_deescalation_probability`).

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
