# GUMAS Engine Series — Source Digests v1.0

**Date:** 2026-08-18
**Layer:** L2
**Status:** lineage resolved to hash-identified artifacts; supersedes the `26_Engine 1.x` placeholder node
**Method:** derivational order established by content — pairwise line similarity, function-set Jaccard, and declared tick-phase structure. No version label was used as evidence.
**Source:** local forensic sweep, 2026-08-18. Full record: `GUMAS_RECOVERY_ADDENDUM_F` (cold storage / `recovery/`)
**Repository:** `AUo959/Aurora_ORIONCORE_Directory_Main`
**Frozen source:** `archives/recovered_prototypes/gumas_v2_tactical/`
**Downstream restoration:** `AUo959/aurora-cloudbank-symbolic` → `simulation/runtime/gumas_v2_restored/` (branch `agent/gumas-flash-rebellion-battle-baseline`)

## Executive finding

`GUMAS_SIM_2.5` is **`26_Engine_1.3` with its imports flattened.** It is not a successor to the recovered v2.0 tactical package, and the recovered v2.0 package has **no descendants**.

| Comparison | Line similarity |
|---|---:|
| `26_Engine_1.3` → `GUMAS_SIM_2.5.zip :: engine.py` | **0.997** |
| `26_Engine_1.3` → `SIM_ENGINE_OUTPUTS/engine_base.py` | 0.989 |
| `26_engine_2.0` → `GUMAS_SIM_2.5.zip :: engine.py` | **0.053** |

v2.0's nearest relative anywhere in the lineage is v1.0 at 0.081. It is an isolate.

## Scope — what "no descendants" does and does not mean

`26_engine_2.0` is the sole source of `CombatResolver`, `FleetState`,
`FLEET_MOVEMENT`, and `FLEET_BATTLE` in the corpus. It is also an **abandoned
in-progress rewrite that never ran**: fifteen call sites in `engine.py` disagree
with the signatures they call, across ten of the fifteen phases, and
`_update_leader_hooks` (Phase 2) raises `TypeError` at `formulas.py:115` under
every one of the five scenarios the package defines.

This table is a provenance record, not a capability inventory. That v2.0 has no
descendants is a fact about lineage; it should not be read as a working tactical
layer having been lost. `docs/ORION__AUDIT__GUMAS_DEDUP_MANIFEST_REAUDIT__v1.0__2026-08-18.md` and the cloudbank RCA
established the preservation defect, and that finding stands on its own evidence
— the deduplication pass condemned files by basename regardless of whether the
package they belonged to worked.

No causal claim is made linking the 2026-02-15 deduplication pass to the
2026-02-16 `GUMAS_SIM_2.5` packaging. v2.0 could not complete a tick and was
never a candidate for that release.

## Two node identities corrected

`GUMAS__LINEAGE__V1_V2_V25_V3_REATTRIBUTION__v1.0` models `26_Engine 1.x` and
`L2_GUMAS_ENGINE v1.0.0` as parent and child. **They are the same file.**

`L2_GUMAS_ENGINE__v1.0.0__2026-02-06.zip :: modules/gumas/engine.py` and
`26_Engine_1.3.zip :: engine.py` are byte-identical:
`761ed8c2877eec7f6a28181942265cd7f683c5766207d84102f4bbfaf7192b7b`, 63,012 B,
2026-02-06 04:33. The same blob also appears in
`L2_GUMAS_ENGINE__CLEAN_PACKAGE__v1.0.1.zip` and `New_Engine_Archive.zip`.

Second: **`Version: 1.0.0` does not identify an implementation.** Seven distinct
engines declare `Anchor: GUMAS-ENGINE-CORE-V1` / `Version: 1.0.0`, spanning
37,128 → 99,134 bytes and four months. Only `26_engine_2.0` declares `2.0.0` /
`GUMAS-ENGINE-CORE-V2`. The existing warning against pinning authority on
`GUMASEngine` / `GUMASState` must extend to the version banner.

## The series

| # | Artifact | Bytes | LOC | Phases | defs | mtime | SHA-256 |
|---|---|---:|---:|:-:|---:|---|---|
| 1 | `GUMAS_26_Engine.zip :: engine.py` | 37,128 | 969 | 6 | 27 | 02-05 23:37 | `2c9f4ffb36ec9cd6380011170fb3d1d6e65828420ee0d9b8307ac0c3afe57528` |
| 2 | `26_Engine1.1.zip :: engine.py` | 44,546 | 1,120 | 6 | 27 | 02-05 23:50 | `fe0bb570821eaac5d02348372ee451412f18adaf94603b08b655d2aeade8dbcc` |
| 3 | `26_Engine_1.2 / engine.py` | 54,786 | 1,329 | 6 | 28 | 02-06 00:03 | `e1531aa243b9c41a8d1a6e47f586d4481af4981fead5b1111583d8715a26f0fd` |
| 4 | **`26_Engine_1.3` = `L2_GUMAS_ENGINE v1.0.0`** | 63,012 | 1,541 | 6 | 33 | 02-06 04:33 | `761ed8c2877eec7f6a28181942265cd7f683c5766207d84102f4bbfaf7192b7b` |
| 5 | `26_engine_1.4 / engine.py` | 99,134 | 2,417 | 6 | 43 | 02-06 14:02 | `d0be3ae2429fec988edb111efcae016396fdaa943e19cfcecff07b3b892c8176` |
| 6 | **`26_engine_2.0 / modules/gumas/engine.py`** | 64,942 | 1,620 | **15** | **69** | 02-07 22:50 | `5a0517646285fcfc1dd54c229361c69110d13a468e3ac6aa2561ac0f14258598` |
| 7 | `GUMAS_SIM_2.5.zip :: engine.py` | 62,909 | 1,539 | 6 | 33 | 02-16 21:30 | `7c807c1e3b3ed4d1d2f9cc6c6203384723e29e313de9db27b50fb79f48b1a73e` |
| 8 | `FORGE…/engine_v3_patch.py` | 20,799 | 499 | 16–20 | 10 | 02-19 19:38 | `500bec252ac017c7258cf2fbee9775abafaa92c222fffd1335ccab276c8773d7` |
| 9 | `SIM_ENGINE_OUTPUTS/engine.py` (shim) | 950 | 38 | — | 1 | 03-05 07:46 | `145733ebbc1af7395b71601b40d328944d24abcc3343b99d73b25dc5d01ee68e` |
| 10 | `SIM_ENGINE_OUTPUTS/engine_base.py` | 63,835 | 1,554 | 6 | 33 | 03-15 04:21 | `6ba1c21337b060579df50e80a52c74c2d3cbde714af6a7b5f1782a997029eaa4` |
| 11 | `SIM_ENGINE_OUTPUTS/engine_advanced.py` | 45,562 | 1,175 | — | 33 | 03-15 04:22 | `3917d25311f157ae3c21d7259323b4d2180aeca7319bed0570f5e3aadd9a57e3` |

All eleven parse under `ast.parse()`. None was executed.

### Source containers

| Archive | SHA-256 |
|---|---|
| `GUMAS_26_Engine.zip` | `063a2bc1af3f51ba…` |
| `26_Engine1.1.zip` | `31016c53af4301ce…` |
| `26_Engine_1.2.zip` | `2c99c7d52c114f9b…` |
| `26_Engine_1.3.zip` | `a7eda7248b009dae…` |
| `26_engine_1.4.zip` | `63c29679f6095932…` |
| `New_Engine_Archive.zip` | `58af1ed63718feb2…` |
| `L2_GUMAS_ENGINE__v1.0.0__2026-02-06.zip` | `23c066ef90baa83f55d65fc1435923dd3892813099d06504f3f018fe2bad6532` |
| `GUMAS_SIM_2.5.zip` | `6d91d36104b2da89d66e37f6b9b97691470762d4793763784988fb8db84db8c5` |

## Corrected lineage

```text
26_Engine v1.0 -> v1.1 -> v1.2 -> v1.3  (= L2_GUMAS_ENGINE v1.0.0 = CLEAN_PACKAGE v1.0.1)
                                    |
     +------------------------------+------------------------------+
     | 0.768                        | 0.997                        | rewrite
     v                              v                              v
  26_engine_1.4                GUMAS_SIM_2.5              26_engine_2.0
  monolith, 6 phases           (2026-02-16)               15 phases, FLEET COMBAT
  NO DESCENDANTS                    |                     NO DESCENDANTS
                                    +--> engine_base -> engine_advanced
                                    ^
                        FORGE v3.0 mixin — written for v2.0, bound here
```

## The exact GUMAS_SIM_2.5 delta

Against `L2_GUMAS_ENGINE__v1.0.0__2026-02-06.zip`:

| File | v1.0.0 | 2.5 | Verdict |
|---|---:|---:|---|
| `models.py` | 12,450 | 12,450 | **identical** |
| `formulas.py` | 12,106 | 12,106 | **identical** |
| `engine.py` | 63,012 | 62,909 | −103 B |
| `scenarios.py` | 19,159 | 19,145 | −14 B |

Four edits, ten changed lines. Three flatten import paths
(`from modules.gumas.X import` → `from X import`). One rewrites a defensive
`dict.get` default into a conditional expression. **Nothing was added.**

The v1.0.0 bundle also ships `engine.cpython-311.pyc`,
`test_gumas_engine.cpython-311-pytest-8.2.2.pyc` and a pytest `nodeids` cache —
that engine was executed and tested. v2.0 never was.

## v3 binding — structural proof

Each engine declares its tick sequence explicitly:

| Engine | Phases |
|---|---|
| v1.0 – v1.4, `GUMAS_SIM_2.5`, `engine_base` | **1 – 6** (plus a 4.5) |
| `26_engine_2.0` | **1 – 15** |
| `engine_v3_patch` | adds **16 – 20** |

`engine_v3_patch.py` states it adds five phases *"after the existing 15"* — true
only of v2.0. Its import at line 389 resolves through `../SIM_ENGINE_OUTPUTS`,
where a 950-byte shim aliases `GUMASEngine = GUMASAdvancedEngine`, a v1.3
descendant with six phases. Phases 16–20 therefore execute directly after
Phase 6, skipping v2.0 Phases 7–15:

| Phase | v2.0 method |
|---:|---|
| 7 | `_coalition_lifecycle` |
| **8** | **`_fleet_movement_tick`** |
| **9** | **`_combat_resolution_tick`** |
| 10–15 | `_economic_tick`, `_media_tick`, `_precursor_tick`, `_sentinel_tick`, `_doctrine_tick`, `_culture_tick` |

This is re-derivable from `vendor/recovery_b64/` plus the engine archives, without
access to the originating device.

## Consequence

Authority references must cite a source digest. `26_Engine 1.x`,
`L2_GUMAS_ENGINE v1.0.0`, and `Version: 1.0.0` each name more than one artifact
or none at all.
