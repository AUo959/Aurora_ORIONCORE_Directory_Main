# Observatory Exercise — 240-Turn Complacency-Cycle Test Case

**Run:** 2026-06-14T05:32:19Z | **Horizon:** 240 turns | **Seeds:** 42, 7, 99 | **Pipeline:** committed mechanic stack via `gumas_memory_run`

> Senior staff convened in the Observatory to run the living-galaxy dynamic under standing conditions for a full 240-turn horizon — twice the canonical sim window — and certify it from instruments, not memory.

## Watch stations

| Officer | Seat | Station |
|---|---|---|
| Cmdr. Alex Thorne | Station Commander | presiding — go/no-go on the verdict |
| Lt. Cmdr. Maya Shepard | Executive Officer | conflict trajectory + wave analysis |
| Dr. Amira Sato | Chief Ethics Officer | legitimacy erosion + surveillance load |
| Jiro Tanaka | Chief Engineering Officer | engine telemetry integrity |
| Dr. Amina Velin | Symbolic Systems Research Lead | oscillation + attractor analysis |

## Verdict (Cmdr. Thorne): **LIVING GALAXY — CERTIFIED**

Three independent tests must all hold per seed: conflict **recurs**, the galaxy does **not** freeze into permanent peace, and it does **not** collapse to the pinned-conflict floor. Determinism (same seed → identical trajectory): **CONFIRMED**.

## Cross-seed summary

| Seed | floor | ceiling | mature plateau | plateau wars | waves | recurs | not frozen | not collapsed | LIVING |
|---|---|---|---|---|---|:--:|:--:|:--:|:--:|
| 42 | 0.372 | 0.625 | 0.382 | 7.3 | 2 | ✓ | ✓ | ✓ | **✓** |
| 7 | 0.369 | 0.618 | 0.382 | 7.0 | 2 | ✓ | ✓ | ✓ | **✓** |
| 99 | 0.366 | 0.643 | 0.376 | 6.4 | 2 | ✓ | ✓ | ✓ | **✓** |

## Seed 42 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 1.15, 1.9, 3.8, 3.5, 2.55, 2.25, 4, 6.45, 10.25, 9, 6.45]` — 2 wave(s), peaks at era(s) [3, 9]; 1026 civil-war-turns, 13 insurgencies formed.
- **Velin (oscillation):** stability/era `[0.609, 0.613, 0.591, 0.545, 0.509, 0.457, 0.439, 0.409, 0.405, 0.386, 0.379, 0.384]` — floor 0.372, ceiling 0.625, mature attractor 0.382 (never below the 0.30 collapse floor).
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.606, 0.576, 0.559, 0.536, 0.518, 0.508, 0.485, 0.482, 0.455, 0.445, 0.448]`; complacency/era `[0.047, 0.241, 0.388, 0.37, 0.352, 0.34, 0.37, 0.319, 0.219, 0.063, 0.057, 0.087]` — complacency builds in calm and is purged by conflict (the cycle driver).
- **Tanaka (engine):** 3150 migrations, 40 negotiations concluded, 12 fragmentation events — engine phases all live.

## Seed 7 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.35, 3.85, 5, 2.45, 0.6, 1.45, 5.15, 7.95, 9.5, 7, 6.95]` — 2 wave(s), peaks at era(s) [3, 9]; 1005 civil-war-turns, 13 insurgencies formed.
- **Velin (oscillation):** stability/era `[0.605, 0.602, 0.57, 0.534, 0.501, 0.48, 0.445, 0.408, 0.393, 0.38, 0.379, 0.383]` — floor 0.369, ceiling 0.618, mature attractor 0.382 (never below the 0.30 collapse floor).
- **Sato (legitimacy/complacency):** legitimacy/era `[0.649, 0.602, 0.573, 0.558, 0.537, 0.525, 0.501, 0.473, 0.465, 0.451, 0.447, 0.448]`; complacency/era `[0.047, 0.26, 0.347, 0.339, 0.342, 0.372, 0.428, 0.328, 0.176, 0.093, 0.107, 0.141]` — complacency builds in calm and is purged by conflict (the cycle driver).
- **Tanaka (engine):** 3059 migrations, 44 negotiations concluded, 51 fragmentation events — engine phases all live.

## Seed 99 — trajectory (12 eras x 20 turns)

- **Shepard (conflict):** civil-wars/era `[0, 0.55, 3.15, 4.5, 2.35, 0.4, 2.55, 5, 6.55, 6.8, 7, 6.05]` — 2 wave(s), peaks at era(s) [3, 10]; 898 civil-war-turns, 13 insurgencies formed.
- **Velin (oscillation):** stability/era `[0.612, 0.621, 0.577, 0.509, 0.497, 0.477, 0.436, 0.417, 0.4, 0.395, 0.38, 0.376]` — floor 0.366, ceiling 0.643, mature attractor 0.376 (never below the 0.30 collapse floor).
- **Sato (legitimacy/complacency):** legitimacy/era `[0.651, 0.608, 0.569, 0.54, 0.537, 0.521, 0.5, 0.486, 0.464, 0.462, 0.441, 0.431]`; complacency/era `[0.047, 0.256, 0.369, 0.339, 0.353, 0.395, 0.386, 0.33, 0.25, 0.128, 0.131, 0.198]` — complacency builds in calm and is purged by conflict (the cycle driver).
- **Tanaka (engine):** 3098 migrations, 34 negotiations concluded, 7 fragmentation events — engine phases all live.

## Reading

Over the full 240-turn horizon the galaxy holds the living dynamic the complacency cycle (MECH-SOC-006) was built for: conflict recurs in waves rather than firing once and flatlining, and stability oscillates down into a turbulent mature attractor (~0.38) **without** collapsing — neither of the two degeneracies (permanent war, permanent peace) reappears at long range. This is reported as measured; nothing here is tuned to a target.

_Artifacts: `metrics.json` (full machine-readable), `per_turn.csv` (every turn x every metric). Re-run: `python3 tools/observatory_240_cycle.py`._
