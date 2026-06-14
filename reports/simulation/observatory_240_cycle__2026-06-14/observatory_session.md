# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-14T13:43:17Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

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
| 42 | 0.368 | 0.381 | 0.319 | 3 | 61 | 71 | 0.86 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.372 | 0.384 | 0.321 | 4 | 73 | 84 | 0.87 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.369 | 0.384 | 0.315 | 4 | 66 | 77 | 0.86 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.15, 0.35, 0.75, 1, 1.4, 0.65, 1.6, 2.25, 1.4, 1.95, 1.05]` — 3 wave(s), peaks at era(s) [5, 8, 10]; 251 civil-war-turns, 71 insurgencies formed.
- **Shepard (off-ramps):** 61 negotiated settlements vs military suppression — of which **31 (51%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.05, 0.15, 0.15, 0.25, 0.3, 0.2, 0.35, 0.5, 0.3, 0.45, 0.35]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.609, 0.613, 0.586, 0.532, 0.503, 0.474, 0.444, 0.419, 0.395, 0.394, 0.386, 0.382]` (floor 0.368); the **honest** internal-conflict-aware metric plateaus at 0.319 (floor 0.268) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.602, 0.57, 0.542, 0.536, 0.518, 0.503, 0.482, 0.463, 0.456, 0.444, 0.437]`; complacency/era `[0.047, 0.251, 0.435, 0.429, 0.399, 0.362, 0.359, 0.375, 0.288, 0.254, 0.272, 0.277]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path).
- **Tanaka (engine):** 71 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3119 migrations, 0 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.8, 0.9, 2, 1.25, 1.25, 1.8, 1.6, 1.95, 2.95, 1.25, 1.9]` — 4 wave(s), peaks at era(s) [3, 6, 9, 11]; 353 civil-war-turns, 84 insurgencies formed.
- **Shepard (off-ramps):** 73 negotiated settlements vs military suppression — of which **29 (40%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0.05, 0.05, 0.25, 0.25, 0.3, 0.3, 0.45, 0.3, 0.4, 0.5, 0.45, 0.35]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.605, 0.599, 0.574, 0.543, 0.523, 0.473, 0.426, 0.413, 0.404, 0.396, 0.387, 0.384]` (floor 0.372); the **honest** internal-conflict-aware metric plateaus at 0.321 (floor 0.275) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.609, 0.576, 0.557, 0.547, 0.516, 0.499, 0.482, 0.469, 0.456, 0.444, 0.438]`; complacency/era `[0.047, 0.25, 0.384, 0.358, 0.352, 0.373, 0.346, 0.341, 0.324, 0.255, 0.301, 0.271]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path).
- **Tanaka (engine):** 84 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3132 migrations, 0 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.4, 0.4, 1.5, 1.2, 1.65, 0.95, 1.65, 0.5, 0.65, 2.25, 2.1]` — 4 wave(s), peaks at era(s) [3, 5, 7, 10]; 265 civil-war-turns, 77 insurgencies formed.
- **Shepard (off-ramps):** 66 negotiated settlements vs military suppression — of which **37 (56%) brokered by a trusted neighbour** (MECH-DIP-002), the rest ground to exhaustion. settlements/era `[0, 0.1, 0.2, 0.35, 0.2, 0.3, 0.3, 0.4, 0.25, 0.4, 0.55, 0.25]` — war is no longer the only way a civil war ends, and diplomacy is the faster path.
- **Velin (oscillation + honesty):** engine stability/era `[0.612, 0.605, 0.577, 0.54, 0.502, 0.464, 0.441, 0.426, 0.403, 0.397, 0.392, 0.383]` (floor 0.369); the **honest** internal-conflict-aware metric plateaus at 0.315 (floor 0.274) — D1 reveals the civil-war load the engine number masks.
- **Sato (legitimacy/complacency):** legitimacy/era `[0.651, 0.601, 0.569, 0.553, 0.537, 0.512, 0.509, 0.481, 0.469, 0.457, 0.449, 0.444]`; complacency/era `[0.047, 0.257, 0.44, 0.372, 0.399, 0.409, 0.358, 0.377, 0.369, 0.424, 0.342, 0.189]` — complacency builds in calm; conflict and *settlement* both renew the order (the latter is the peaceful path).
- **Tanaka (engine):** 77 insurgencies formed and retired (cast rotation; was ~13 pre-graft), 3163 migrations, 0 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy now shows **dynamic** behaviour, not merely controlled. Conflict still recurs in waves (the complacency cycle, MECH-SOC-006), but civil wars now **end**: a grinding, costly, stalemated insurgency can reach a negotiated **settlement** (MECH-REB-004) that retires it and spends its grievance, so the conflict **cast rotates** (dozens of distinct insurgencies form and resolve, where pre-graft the same ~13 reopened forever). War is no longer the only off-ramp. The honest, internal-conflict-aware stability (D1) sits well below the engine's headline number — the civil-war load the old metric masked — and is reported as the true reading. Nothing here is tuned to a target; the de-escalation rule is the engine's own (`calc_deescalation_probability`).

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
