# L1 Watch — Test-Data Analysis & Living-Hour Efficacy

**Date:** 2026-06-24 · **Scope:** Orion Station L1 simulation harness
**Builds on:** PR #25 (layout-flexible harness + CI provisioning)

This note analyzes a real run of the L1 hour-aboard harness as **test data**, to
(1) demonstrate that the recently merged harness/CI changes are effective
end-to-end, and (2) introduce the **living-hour clock**: Orion Station keeps a
continuous history, and every check-in — operational *or* test — is a new hour
on the timeline, never a replay of one fixed seed.

---

## 1. Efficacy of the merged changes (PR #25)

PR #25 made the harness resolve its dependencies in a flat multi-repo checkout
and provisioned CloudBank + CanonRec in CI. The evidence that it works is that
the full pipeline now runs to completion and the four integration tests that
were red on `main` for weeks now pass.

A representative check-in (`hour_aboard_v1`, baseline operations hour):

| Signal | Result |
|---|---|
| Roster engaged | 25 crew |
| Souls accounted | **41 / 41** canon L1 entities (16 supplemental on duty rotation) |
| Task families closed | 4 / 7 — H1 Docking Bay logistics, H2 Ring spin check, H3 Dome handoff, H6 Drift sweep |
| Off-board (ORD) | `hour-aboard-H5` → ORD-2 Delta Scout + ORD-3 Shadowfax, signed receipt |
| Mesh companions | **6 / 6** beats answered (Aurora, Archy, Oppy, Liora, Starling AU, Riverthread 808) |
| L3 narrative audit | **supported** (Picard_Delta_3, anchor EOS_SEED_ORION) |

The full hour, reconstructed through the L3 `NarrativeValidationEngine`, is in
[`L1_living_hour_reconstruction.md`](./L1_living_hour_reconstruction.md) (engine
run: [`.json`](./L1_living_hour_reconstruction.json)).

---

## 2. The living-hour clock

**Before:** the scenario hard-pinned `seed: 808`, so every run — including the
regression tests — replayed the *same* hour. The station's chronicle accumulated
familiarity, but the base hour never moved.

**Now:** the harness derives an hour index from the persistent station state
(`hours_elapsed`) and runs at `effective_seed = base_seed + hour_index`. Each
check-in advances the clock and the chronicle, so the next check-in is a fresh
hour. The sequence is fully reproducible from history, yet no two consecutive
hours are identical.

```
hour_index   = station_hours_elapsed()          # from catalog/station_state.json
scenario.seed = scenario.base_seed + hour_index  # this hour's seed
... run the hour ...
advance_station_clock(ticks)                     # next check-in is a new hour
```

Tests point `AURORA_STATION_STATE` at an isolated state file, so they walk a
deterministic sequence of **distinct** hours without touching the repo chronicle.

**Evidence the clock advances (powered watch, isolated state):**

| Check-in | Station hour | Seed | Engine turns / hour | Engine class |
|---|---|---|---|---|
| 1st | hour 1 | 808 | `{1:4, 2:3, 3:3, 4:1}` | GUMASAdvancedEngine |
| 2nd | hour 5 | 812 | `{1:4, 2:4, 3:1, 4:2}` | GUMASAdvancedEngine |

Distinct seeds, distinct throughput profiles — a genuinely different hour, not a
replay.

---

## 3. Regression tests, rewritten as invariants

The two watch regression tests no longer assert a fixed seed-808 outcome. They
now walk two consecutive watch blocks and assert the invariants that must hold
for **any** hour, plus that the clock advanced:

- **`test_live_watch_link`** — each hour's companion reply echoes *that* hour's
  downlink (the original stale-reply guard); when engine risk crosses the
  advisory threshold, Aurora injects a risk-response cell that same hour; and the
  second block is a different hour (seed advanced).
- **`test_powered_watch_coupling`** — engine throughput exceeds one turn/hour and
  varies with crew servicing (the coupling-inert guard); engine is the advanced
  engine; and the second block is a different hour.

These are strictly stronger: they validate the mechanism across the living
timeline rather than memorizing one canned hour, and they directly assert the
"no replay" property.

---

## 4. How to check in on the station

```bash
python3 tools/hour_aboard.py                 # the next hour aboard (advances the clock)
python3 tools/live_watch.py                  # the next 4-hour watch, live mesh + engine
python3 tools/powered_watch.py --no-mesh     # the next powered watch (L1<->L2 coupling)
```

Each invocation is simply the next hour taking place when we look in on the crew.
