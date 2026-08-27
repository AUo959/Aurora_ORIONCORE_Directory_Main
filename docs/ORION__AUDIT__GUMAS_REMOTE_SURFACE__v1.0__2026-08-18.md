# GUMAS Remote Surface Reconciliation v1.0

**Date:** 2026-08-18
**Layer:** L2
**Status:** last named search surface closed; lineage record reconciled
**Scope:** `AUo959/aurora-cloudbank-symbolic` and `AUo959/CanonRec` — all branches, tags, PR heads, and full object stores including unreachable objects
**Source:** local forensic sweep. Full record: `GUMAS_RECOVERY_ADDENDUM_G` (cold storage / `recovery/`)
**Repository:** `AUo959/Aurora_ORIONCORE_Directory_Main`
**Frozen source:** `archives/recovered_prototypes/gumas_v2_tactical/`
**Downstream restoration:** `AUo959/aurora-cloudbank-symbolic` → `simulation/runtime/gumas_v2_restored/` (branch `agent/gumas-flash-rebellion-battle-baseline`)

## Executive finding

`REMOTE_SURFACE_CLEARED — NO_UNSEEN_TACTICAL_SOURCE`

`GUMAS__LINEAGE__V1_V2_V25_V3_REATTRIBUTION__v1.0` lists
*"network-only GitHub branch/PR enumeration"* as a remaining inaccessible surface.
It is now closed, and the result is clean.

| Surface | Scanned | Result |
|---|---|---|
| `aurora-cloudbank-symbolic` — branches / tags / PR heads | 34 / 5 / 1,058 | — |
| `CanonRec` — branches / tags / PR heads | 7 / 0 / 7 | — |
| Blobs examined, both repos, incl. unreachable | 17,524 | — |
| Blobs **mentioning** tactical symbols | 39 | 34 documentation, 5 Python |
| Those 5 Python blobs | all reachable | `restored_engine.py` ×2, `restoration_smoke.py` ×2, `__init__.py` — all post-2026-08-12 derivatives |
| Blobs **defining** `CombatResolver` / `FleetState` / `CombatState` / `resolve_battle` / `resolve_combat` / `calc_combat_outcome` | **0** | — |
| Unreachable blobs bearing tactical symbols | 15 | superseded Markdown/JSON drafts of these recovery documents; **0 Python** |

Every tactical definition in existence, across every surface now searched — local
and remote — resides in the thirteen files of `26_engine_2.0`. The retirement of
the missing-core-trio hypothesis in v1.0 §"v2.0 completeness" is confirmed on two
further surfaces.

## Recovery payload verified in place

`simulation/runtime/gumas_v2_restored/vendor/recovery_b64/part-000…008.b64`
decodes to a 75,052-byte ZIP with SHA-256
`039c0f48341aa9847b8400e45a29e41fef734a2b2e80b78bfe3de1abc165ec07` — matching the
recovery package digest asserted in `GUMAS__RESTORATION__V2_COMBAT_CONTRACT__v1.0`.
All 13 module digests agree with the local recovered tree.

## Reconciliation of v1.0's "reported" evidence class

v1.0 deliberately separated independently re-hashed material from claims
"reported" by the local sweep. Every reported claim is now resolved.

| Claim in v1.0 | Status |
|---|---|
| `GUMAS_SIM_2.5` is a v1.0.0 derivative, not a v2.0 successor | **CONFIRMED** — 0.997 line similarity, Jaccard 1.00 |
| `models.py` byte-identical to v1.0.0 | **CONFIRMED** — both 12,450 B, same SHA-256 |
| `formulas.py` byte-identical to v1.0.0 | **CONFIRMED** — both 12,106 B, same SHA-256 |
| `engine.py` / `scenarios.py` differ by twelve lines total | **CONFIRMED** — 10 changed lines, 4 edits |
| Payload lacks combat/topology/fleet symbols | **CONFIRMED** — 18-symbol scan across 11 lineage engines |
| v3.0 resolves its parent through the v1-derived branch | **CONFIRMED** — upgraded to structural proof via phase fingerprint |
| No alternate tactical revision | **CONFIRMED** on 588 local archives and 17,524 remote blobs |
| Three incompatible historical combat API contracts | **CONFIRMED** |
| Mid-integration abandonment | **CONSISTENT** — v2.0 has no descendants and never executed either combat path |
| Gap: GitHub branch/PR enumeration | **CLOSED** |
| Gaps: `~/Documents`, `~/.Trash`, Time Machine/APFS | **STILL OPEN** |

**No claim in v1.0 was contradicted.** Two node identities require correction —
see `docs/ORION__AUDIT__GUMAS_ENGINE_LINEAGE__v1.0__2026-08-18.md`:

1. `26_Engine 1.x` and `L2_GUMAS_ENGINE v1.0.0` are the **same file**, not parent
   and child. Pin: `761ed8c2877eec7f…`.
2. `Version: 1.0.0` is shared by seven distinct engines and identifies none of
   them. The v1.0 warning about ambiguous symbols extends to the version banner.

## Remaining gaps

| Gap | Status | Reason |
|---|---|---|
| `~/Documents`, `~/.Trash` | open | not connected folders on the originating device |
| Time Machine / APFS local snapshots | open | `tmutil` absent from the device sandbox — verified, not assumed |
| External volumes | open | not exposed to the sandbox |
| GitHub Issues, PR discussion, Actions logs | open | REST API gated; git transport reaches refs and objects only. PR *heads* were fetched and swept; PR comments were not. |
| 2 PDF↔MD dedup pairs | open | no `pdftotext` on the device shell |

Each is a tested limit, not an assumed one.

## Method note

Two capability limits asserted in earlier local addenda were wrong, and both were
false negatives produced by testing a proxy instead of the behaviour:

- *"the device mount refuses `chmod`"* — the mount synthesizes the mode bits it
  reports; `chmod -R a-w` is in fact enforced, confirmed by write probe.
- *"no network egress for GitHub branches/PRs"* — the REST API is gated, but
  anonymous `git clone` and `git fetch '+refs/pull/*/head:refs/remotes/pr/*'`
  both work. The second error hid five days of restoration work in this
  repository from the forensic sweep.

A third instance was mechanical: the sweep tooling detected repositories by
looking for a `.git` *directory*, and therefore reported *"0 repositories,
0 hits"* against bare clones — indistinguishable from a searched-and-empty
result. Fixed to use `git rev-parse --git-dir`.

All three share one shape, and it is the same one as the original basename bug:
**a reported attribute trusted over an observed one.**
