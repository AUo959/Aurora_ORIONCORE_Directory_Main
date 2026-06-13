# L2 Canon — Genesis & Lineage (deep iCloud dig)

**Date:** 2026-06-13 | Companion to `simulation_discovery_index__2026-06-13.md`.
**Prompt:** the L2 canon is some of the oldest material in the project, reworked
several times — trace it to source and find high-value unintegrated work.

## The genesis: an educational political RPG

The entire L2 galactic simulation began as a classroom exercise.
`intake/text_gov_game.txt` (**5,813 lines**) opens:

> "Can you help me design a role-playing game for my students where they take
> on historical or political roles to learn through experience?"
> → **"Crisis & Compromise: A Historical Role-Play Experience."**

"Crisis & Compromise" appears nowhere else in the workspace — the original
student-RPG framing was abstracted, across successive reworks, into the
"Galactic Union" and ultimately GUMAS. This is the literal seed of the whole
simulation, and it is the oldest design layer.

## The original mechanics (designed at genesis)

- **`intake/text_early_sim_logic.txt`** — the original math, reinforcement-
  learning shaped:
  - State update: `S_new = S_old + α·E_success − β·E_failure`
  - **Q-learning**: `Q(s,a) ← Q(s,a) + α[R + γ·max Q(s',a') − Q(s,a)]`
  - Trust dynamics: `T_new = T_old − λ·B + δ·A`
- **`intake/text_factions_reg.txt`** — the original `factions_registry`
  (Galactic Union: "Centralized Interstellar Government", Federal democracy
  with Senate governance, alignment "Union Loyalist").
- **`intake/text_L2_characters .txt`, `text_characters_zylox.txt`** — the
  original cast with a **numeric reputation/relationship system**: e.g.
  Chancellor Zylox (+12 Senate Influence, +7 Military Trust, −8 Separatist
  Relations); Dr. Adrienne Kovas (+9 R&D Trust, +4 Fleet Respect, −3 Political
  Influence), with explicit relationship edges (Trusted by Rhen Kailo, Rival
  of Vos).

## The rework chain (oldest → present)

1. **Genesis conversations** — `intake/text_gov_game.txt` (5,813 lines),
   `text_early_sim_logic.txt`, `text_factions_reg.txt`,
   `text_L2_characters .txt`, `text_characters_zylox.txt`, `text_gov_game`,
   `text_mem_system*` — the raw design (educational RPG → Galactic Union).
2. **Consolidated export** — `intake/textAu.txt` (~2,820 lines). Per
   `_staging/recovered_textAu__2026-03-13/SOURCE_MAP.md`: lines 83–166 = L2
   scenario seed; 168–371 = leadership + Judicator Prime cast; **375–1437 =
   mechanics, diplomacy/economy models, peace-path, memory optimization**.
3. **Structured recovery (2026-03-13)** — `_staging/recovered_textAu…/L2/`:
   `01_galactic_union_canon_reconciliation.md`,
   `02_galactic_union_character_roster.md`,
   `03_galactic_union_mechanics_and_models.md` (210 lines), plus
   `dossiers/` (polity/ship/character JSON) and the
   **`l2_mechanic_registry__recovered_textAu.md`**.
4. **Promotion candidate (bounded)** — `recovered_galactic_union_core__2026-03-13`
   (6 polities + 10 characters); **explicitly excluded**: Judicator Prime cast,
   `POL-AI-HARDLINE-001`, `CHAR-GU-DRAYEN-01`, `SHIP-GU-JUDICATOR-01`, and the
   L2 mechanic registry.
5. **Promoted L2 canon (2026-03-19/20)** — `SIM_ENGINE_OUTPUTS/L2_CANON__2026-03-19/`
   (~30 entities: characters, locations, organizations, mobile_assets).
6. **Engine realization** — `scenarios.py` (13 factions / 28 leaders),
   `formulas.py`, `models.py`, `engine_advanced.py`.

That is **six reworks** of the same seed, exactly as the owner described.

## Implemented vs. design-only (the critical gap)

| Original design mechanic | In the engine? |
|---|---|
| Numeric reputation / relationship system | **YES** — `formulas.py`, `models.py`, `engine_base.py` carry reputation |
| Named cast (Zylox, Kovas, Judicator) | Partial — ~2 refs in `scenarios.py`; fuller set in L2_CANON |
| **Memory-driven faction decisions** — Q-learning + retrieval of past betrayals/negotiations (`MECH-GOV-001` "Faction Decision Retrieval Model") | **NO** — zero match for q-learning / retrieved_memory / bayesian in engine or FORGE |

**The original vision — adaptive factions that decide by combining current
state with *remembered* prior outcomes — was specified at genesis, formalized
in the recovered mechanic registry, and never coded.** The current engine uses
simpler stateless formulas. This is the single largest "the design already
exists" finding: realizing memory-driven faction behavior means implementing
`MECH-GOV-001`, not inventing it.

## High-value unintegrated work (recovery priority)

1. **L2 Mechanic Registry** (`dossiers/l2_mechanic_registry__recovered_textAu.md`)
   — structured mechanics (MECH-GOV-001 …). Blocked **only on a validator gap**
   ("the L2 validator defines a `mechanic` type but its entity_kind rules do
   not fully accept that path yet"), not on quality. Fix the gate, promote.
2. **`MECH-GOV-001` implementation** — the memory-retrieval/Q-learning faction
   decision model: designed, never built. Directly addresses the seed-42
   runaway-instability lesson (smarter factions de-escalate).
3. **`03_galactic_union_mechanics_and_models.md`** (210 lines) + textAu
   lines 375–1437 — the diplomacy/economy/peace-path models. Compare against
   `formulas.py`; likely contains unbuilt dynamics.
4. **Excluded cast & polities** — Judicator Prime cast, `POL-AI-HARDLINE-001`,
   `CHAR-GU-DRAYEN-01`, `SHIP-GU-JUDICATOR-01`. Deliberately held back in March;
   owner decision on whether to promote now.
5. **Unmined exports** — ~25 of the 244 `intake/text_*.txt` carry galactic
   content; the recovery processed `textAu.txt` primarily. `text_gov_game.txt`
   (5,813 lines) is largely unextracted and may hold further mechanics.
6. **`text_mem_system*` / L3 memory architecture** — the memory subsystem that
   `MECH-GOV-001` depends on (also the heavily-duplicated `gumas_memory_*.py`).

## Structural recommendation

- **Route L2 canon into CanonRec** (`canon/L2/`), mirroring the L1 station
  canon, with the promoted entities + the mechanic registry (after the
  validator fix). L2 canon currently lives only in `SIM_ENGINE_OUTPUTS/`.
- **Sequence the engine work**: fix the L2 `mechanic` entity_kind gate →
  promote the mechanic registry → implement `MECH-GOV-001` → re-run the long
  galactic sim with memory-driven factions and compare to seed-42.
- **Owner triage**: the excluded cast/polities; whether to do a second mining
  pass over the ~25 galactic exports.
