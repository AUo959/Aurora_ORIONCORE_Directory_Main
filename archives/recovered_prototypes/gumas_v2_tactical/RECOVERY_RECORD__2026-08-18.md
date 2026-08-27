# Recovery Record — GUMAS v2.0 Tactical Package

Date: 2026-08-18 (source recovered 2026-08-12)
Lane decision (owner, 2026-08-18): **root recovered-prototype archive**, per the
P7 precedent in `archives/recovered_prototypes/biological_pneumatic_engine/`
Executed by: claude (Cowork session), owner-directed
Companion audits: `docs/ORION__AUDIT__GUMAS_ENGINE_LINEAGE__v1.0__2026-08-18.md`,
`docs/ORION__AUDIT__GUMAS_DEDUP_MANIFEST_REAUDIT__v1.0__2026-08-18.md`,
`docs/ORION__ADR_LITE__GUMAS_V3_ENGINE_BINDING__v1.0__2026-08-18.md`

## What this is

The only *attempt* at a tactical layer in the Aurora corpus — the sole source of
`CombatResolver`, `FleetState`, `CombatState`, `FLEET_MOVEMENT`, and
`FLEET_BATTLE`. Thirteen modules, 10,081 LOC, written 2026-02-07 22:26–22:53.

**It never worked.** Fifteen call sites in `engine.py` disagree with the
signatures they call, across ten of the fifteen phases. `_update_leader_hooks`
(Phase 2) passes a `BiasType` where `formulas.calc_bias_evolution` requires a
float, raising `TypeError` at `formulas.py:115`. All five defined scenarios share
`_build_canonical_factions` and `_build_canonical_leaders`, so **no scenario
avoids Phase 2**. The package cannot complete a single tick.

This is an abandoned in-progress rewrite, preserved for its provenance value. It
is not a lost capability.

It was not retired or superseded. A 2026-02-15 deduplication pass matched files
by **basename rather than content**, declared three load-bearing files duplicates
of smaller unrelated files with the same names, and moved them into
`_REDUNDANT_FILES_ARCHIVED/02_FORMAT_DUPLICATES/` — a directory whose own
`REORGANIZATION_SUMMARY.txt` still reads *"Safe to delete ✓"* and
*"Option 3: Delete all redundant files (recommended)."*

| Condemned | Bytes | Declared duplicate of | Bytes |
|---|---:|---|---:|
| `modules/gumas/engine.py` | 64,942 | `26_Engine_1.2/engine.py` | 54,786 |
| `modules/gumas/scenarios.py` | 59,277 | `26_Engine_1.2/scenarios.py` | 18,821 |
| `modules/gumas/__init__.py` | 1,412 | `modules/__init__.py` | **0** |

Removing those three made the package un-importable — no entrypoint, no
scenarios, no package initialiser.

**No causal claim is made about the release.** `GUMAS_SIM_2.5` was packaged
2026-02-16 from `26_Engine_1.3`, and the deduplication pass ran 2026-02-15. An
earlier draft of this record read those two dates as cause and effect. They are
not: v2.0 could not complete a tick, so it was never a candidate for that
release. The deduplication pass swept up a branch that had already been
abandoned. Both facts are real; the causal link between them was inferred and is
withdrawn.

## Provenance

| Artifact | Path | SHA-256 |
|---|---|---|
| Frozen archive snapshot (this directory) | `archives/recovered_prototypes/gumas_v2_tactical/modules/` | per `MANIFEST_SHA256.txt`, 14/14 verified |
| Preservation package (locked read-only) | `recovery/GUMAS_V2_TACTICAL_RECOVERY__2026-08-12.zip` | `039c0f48341aa9847b8400e45a29e41fef734a2b2e80b78bfe3de1abc165ec07` |
| Archive witness A | `archives/sim_archives/GUMAS_SIM_2.0.zip` | `1f9dae31d916e8d3815ca465177007f5359544bf9ade6e23a5bd8a123ff7ed23` |
| Archive witness B | `archives/sim_archives/GUMAS_SIM_2.0 2.zip` | `606314440661ed9ddd17d0dc1b794595e9c2bdaccd12c4bbe61899a8a4d0166f` |
| Cold storage | `iCloud Drive/Aurora_ORIONCORE_Directory_Main/_COLD_STORAGE__2026-08-18/` | 37 files, manifest verified |
| Operative derivative | `AUo959/aurora-cloudbank-symbolic` → `simulation/runtime/gumas_v2_restored/` | vendored payload re-hashes to `039c0f48…` |

### Three independent witnesses

1. **Two archive ZIPs** created independently, with matching CRC-32s per entry
   and matching on-disk SHA-256.
2. **Thirteen `.pyc`** compiled by CPython 3.10 (magic 3439) on 2026-02-07,
   timestamp-validated, whose embedded source mtimes and sizes match these bytes
   exactly. Independent corroboration that these are the files that existed.

The witness ZIPs are **not committed** — 28 MB of binaries do not belong in git.
They are held on disk and in iCloud cold storage, identified here by hash. This
follows the P7 precedent, which recorded the deleted source path by hash rather
than committing it.

## Key file digests

| File | LOC | Bytes | SHA-256 |
|---|---:|---:|---|
| `combat.py` | 374 | 12,350 | `ff486487b9dbac8abbc87824ead5ae0aadfdce7ab366c0a0cc164bb36053bfb6` |
| `topology.py` | 905 | 25,884 | `5375e91c95d49885ac4573f17b009c32b38fda8b755020f12f501beddc865d0b` |
| `engine.py` | 1,620 | 64,942 | `5a0517646285fcfc1dd54c229361c69110d13a468e3ac6aa2561ac0f14258598` |
| `scenarios.py` | 1,837 | 59,277 | `305053324231d9d87650319bbbdbf3899bec7aae0aedfeb6e716b194e0d78648` |
| `models.py` | 1,095 | 36,597 | `75a464ac6d1986a70b9baeed249f00241797d61b31340368b93cc9fc00d7bbed` |
| `formulas.py` | 921 | 26,037 | `d5435511abec6d734d28828669ecb6d3c37cb1c8cc52886758bd982b11bb9a9e` |
| `__init__.py` (package) | 34 | 1,412 | `81a3a120873df3e7507b6c76210e42746cf00697d3f985b379f7136695a60b38` |

Full list in `MANIFEST_SHA256.txt`.

## Disposition

- **Archive lane selected.** Not promoted to canon. Not made operative.
- **These bytes are frozen and must not be edited.** Fifteen integration defects
  are documented in `BEHAVIOR_INVENTORY__2026-08-18.md`; none is repaired here.
  Repairing an archival artifact destroys its evidentiary value and pre-empts a
  decision that belongs to the owner.
- **Remediation happens downstream**, in
  `aurora-cloudbank-symbolic/simulation/runtime/gumas_v2_restored/`, which
  materialises this package from a verified ZIP, imports it under a scoped
  context manager, and subclasses it without unpacking or rewriting a single
  recovered file. That is the correct pattern and it should stay that way.
- **The live copies under `projects/GUMAS_SIM_2.0/` are gitignored** and always
  were — `/projects/*` is excluded by the root allowlist. This snapshot is the
  first time any of this source has been under version control.

## Post-recovery divergence

None. Unlike P7, no fix was applied to any copy of these bytes. The restored
derivative in `aurora-cloudbank-symbolic` is separately versioned
(`2.0.1-restored.2`) and carries its own source digest.

## Why the loss was survivable

Only because two undocumented archive ZIPs happened to exist. Of 308 records in
the same deduplication manifest, **169 are wrong** by the same basename logic;
29 condemned files survive *only* inside those two ZIPs, and 68 archive members
survive nowhere at all. See
`docs/ORION__AUDIT__GUMAS_DEDUP_MANIFEST_REAUDIT__v1.0__2026-08-18.md`.

That the tactical layer was recoverable was luck, not design. This record and
this lane exist so the next one does not depend on luck.
