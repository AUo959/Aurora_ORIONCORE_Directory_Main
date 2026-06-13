# Seed-42 Stability — Solution (the attractor is broken)

**Date:** 2026-06-13 | Implements the two-sided plan from
`seed42_stability_review__2026-06-13.md`. The prior non-war-progression design,
finally built, plus the exit edge it never had.

## The two faults, both fixed

| Fault (review) | Fix | Module |
|---|---|---|
| Conflict **onset** over-weighted; no DSI gate; non-war progression never built | **MECH-SOC-003** — DSI onset gate `(P+E+S)/(C+M)` → governance legitimacy → fewer onsets | `DiplomaticStabilityModel` |
| Civil war has **no exit**; RESOLVED never assigned; SUPPRESSED gate unreachable | **MECH-SOC-002** — war-weariness erodes war-weary support so the engine's own SUPPRESSED gate becomes reachable | `WarWearinessModel` |

Both are pure governed code in `tools/mech_gov_001.py`, wired via the
`gumas_memory_run.py` harness writing to persistent engine fields
(`public_legitimacy` for the gate; `popular_support`/`insurgent_strength` for
war-weariness). No engine-internal rewrite.

## Result — generalizes across seeds (120/100 turns)

| Seed | stability (base → mem) | risk (base → mem) | active civil wars (base → mem) |
|---|---|---|---|
| 42 | 0.357 → **0.406** (+0.049) | 0.651 → **0.543** (−0.108) | **4 → 0** (peak 5 → 2) |
| 7  | 0.366 → **0.459** (+0.092) | 0.626 → **0.511** (−0.115) | **3 → 0** (peak 5 → 1) |
| 99 | 0.360 → **0.412** (+0.052) | 0.649 → **0.539** (−0.111) | **4 → 0** (peak 5 → 1) |

The seed-42 baseline reproduces the canonical run exactly (4 active civil wars
at close, all in civil_war phase — lessons §summary). In **every** seed the
attractor that *never exited in 122 turns* now resolves to **zero active civil
wars**: the DSI gate cuts inflow (peak 5 → 1–2) and war-weariness drains the
survivors to SUPPRESSED. Risk falls ~0.11 (seed 7 clears the 0.540 threshold);
stability lifts +0.05–0.09. Deterministic (re-runs identical).

## Honesty / emergence

- **Not coefficient-forced.** The DSI formula `(P+E+S)/(C+M)` and the
  resource-exhaustion/war-weariness mechanic are the *recovered canon design*
  (`non_war_progression_mechanics.md`, lessons §1.2), realized — not tuned to
  chase a number. Resolution is made *reachable*; whether a given war ends
  emerges from its own trajectory (peak >0 then resolving, not "never formed").
- **Full above-threshold stability is approached, not guaranteed.** Stability
  reaches ~0.41–0.46 (threshold 0.480); residual instability remains from the
  non-rebellion sources the lessons flagged (intelligence compromise with no
  response surface, fragmentation/conscription with no downstream effect). Those
  are separate, named levers for a later pass.

## Tests & governance

`tests/test_mech_gov_001.py` — 11 tests: faction decisions, grievance memory,
DSI capacity, war-weariness, determinism. The mechanic models live governed in
`tools/`; the eventual move of the resolution transition *into* the engine's
rebellion phase remains a separate, owner-cleared step in the untracked engine
dir. CanonRec `a08f3ee`; registry annotated MECH-SOC-002/003 IMPLEMENTED.
