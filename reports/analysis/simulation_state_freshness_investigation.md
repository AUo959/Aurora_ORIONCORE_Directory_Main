# Simulation-state freshness: authority and repair investigation

## Conclusion

The recurring red check is a policy/consumer migration gap, not evidence that
the supported L1 runtime needs a new snapshot. The check measures the Git age
of a file that later authority explicitly retired as live genesis. Updating its
timestamp, counters or mission records to make CI pass would misrepresent a
historical snapshot and would not establish a current run.

There is a separate, reproducible presentation problem: the read-only L1 API
still labels that historical file as current canonical state and reports an
operational station from it. Repair must address those consumers as well as
replace the obsolete age requirement with substantive containment checks.

This investigation changes no CloudBank file, freshness rule, simulation state,
canon, lockpoint, run, provider binding or external service.

## Fixed evidence boundary

- CloudBank: `b68c4717332f57b5bca0d07e06b448380ad3b76d`.
- Root: `e1b07d38df5aff9d78c0a5c69021ee437584f51b`.
- Historical state Git blob: `1749f609a82fb982e3b18a420f575e363d55ac41`.
- Historical state SHA-256 before/after all probes:
  `beaca1677cac1c058c8d33c529d2148724c546429e53a9cdc20457795c2517bf`.
- Root and CloudBank worktrees were clean at investigation start. The source
  worktree remains clean after probes and tests.

## Authority and timeline

1. [Issue #1083](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1083)
   described the former manual mission-closeout/update model. It is **closed**,
   since July 13, 2026 in New York (July 14 UTC). Treat its proposal as historical
   issue evidence, not current permission to regenerate runtime state.
2. Commit `ab9419ce009a4ac570ff8b93d0dd1dbc6a9217c6`, PR #1240,
   backfilled the snapshot, added continuity events/taxonomy, and created the
   14-day Git-age workflow. It is still the last commit touching the file.
   Top-level `last_updated` is July 13; nested `simulation.last_updated` remains
   April 6. The workflow reads neither field: it uses the last Git committer
   timestamp. It reported 119 whole days at this investigation's probe.
3. August 8 commit `7e0ad613f98ea8545eed03cb8ef569ecc82cd5f8`, PR #1461,
   explicitly retired the old builder and loader as bootstrap authorities.
   `config/l1_runtime_baseline.json:117` declares `historical_project_state`
   and `genesis_authority: false`. `CANON_INDEX.md:76` independently maps the
   file to provenance/reference only.
4. The current supported contract is
   `docs/architecture/AURORA_L1_RUNTIME_CONTRACT.md`, with the executable
   baseline in `config/l1_runtime_baseline.json` and lifecycle documentation
   in `.aurora/SIMULATION_INIT_PROTOCOL.md`. The prose runtime-contract header
   says 1.2.0 while the executable baseline is 1.3.0; repair should reference
   the executable baseline, not hard-code the older document-header version.
5. `simulation/l1_runtime.py:95` defaults persistence to external user state
   under `~/.aurora/l1-runs`, configurable with `AURORA_L1_RUN_ROOT`.
   `simulation/l1_runtime_support.py:704` rejects repository-contained run roots.
   Persistence is run-ID scoped, written atomically, and distinct from canon.
   No existing private run directory was inspected in this investigation.

## Producers and consumers

| Surface | Current behavior | Repair implication |
| --- | --- | --- |
| `.aurora/build_canonical_state.py:49` | Builder raises; CLI refuses rewriting; `--status` is read-only | Preserve refusal; do not restore an updater |
| `.aurora/load_simulation.py:36` | Historical JSON may be read; `save_simulation_state` returns false | Keep compatibility/provenance boundary explicit |
| `.aurora/init_l1.py preflight` | Validates supported runtime without creating a run | Use for readiness validation, not heartbeat generation |
| Live L1 persistence | Governed per-run external state, pinned revisions and replay position | Separate runtime monitoring requires an explicitly selected run/deployment |
| `.github/workflows/simulation-state-freshness.yml:19` | Fails when last Git touch of historical file exceeds 14 days | Policy target is obsolete; content-only touches can also falsely reset its age |
| `src/api/l1_station_api.py:83` | JSON load implies `operational`; historical station fields are returned | Separate source readability from live runtime availability |
| `src/api/l1_station_api.py:114` | Returns historical file as current canonical simulation state | Label source authority and historical status; do not infer a live run |
| `api/aurora_api.py:877` | Includes the L1 station router | Presentation mismatch is reachable through app wiring, not merely dead code |
| `tests/test_l1_station_api.py` | Explicitly expects historical-file load to mean operational | Tests currently preserve the old semantics; update with the consumer repair |
| `scripts/aurora_onboard.py:107` | Requires readable historical JSON; context lockpoint warning is retained | Preserve readable-reference check but identify supported runtime authority |
| `AURORA_CONTEXT.json:52` | Warns of stale data but still describes the pre-July April gap and closed #1083 as unresolved | Reconcile warning to retired authority and real historical dates |
| `.aurora/README.md:25` | Calls file primary state; instructs direct mission/timestamp writes | Replace current operational instructions; preserve historical examples as labeled history |
| Generated API/catalog/index documents | Repeat legacy source/endpoint descriptions | Regenerate from corrected authoritative descriptions after code/docs repair |

No active autonomous writer to this historical path was found in the searched
Python/shell/JavaScript consumers under `.aurora`, `api`, `src`, `modules`,
`simulation` and `scripts`. This is a bounded repository search, not a claim
about every external deployment or old branch.

## Read-only verification

Commands run with the existing hash-installed Python environment:

```bash
AURORA_L1_RUN_ROOT=/workspace/work/freshness-investigation-no-run \
  python .aurora/init_l1.py preflight
python -m pytest tests/test_l1_bootstrap_containment.py \
  tests/test_l1_station_api.py tests/test_aurora_onboard.py -q
```

Preflight exits zero: `ready: true`, empty blockers, `tick: 0`,
`run_created: false`. The designated absent run root remains absent.
Quarantined population, exact-locus/light-time and fleet-authority warnings
remain visible; readiness does not resolve those facts.

A controlled FastAPI TestClient mounted only the existing L1 router and issued
the two GETs. Health reports `operational`, `ACTIVE`, `FULL_OPERATIONAL`,
`current_crew: 81`, and cycle `865192` from the historical snapshot. The state
wrapper reports `success`/`loaded`. Those observations prove legacy-file
readability and presentation behavior; they do not establish a current live
station or type the historical aggregate as a present human complement.

All **20 selected tests pass** (0.18 seconds). The containment tests also
verify the retired builder refuses writes and the loader refuses save/physical
Pilot routing. Passing tests expose the distinction here: they preserve the
existing boundary and old API expectations, not freshness of a running world.
The historical file's byte hash is unchanged after probes/tests. No INIT,
advance, live restore, canon promotion, wall-clock cycle catch-up, re-lock or
external backend request was performed. A full suite was unnecessary for this
read-only investigation; no product source changed.

## Recommended repair: align checks and consumers with established authority

Implement as a new, independently reviewed CloudBank patch after the existing
CI review debt is cleared; it should not stack changes in that CI domain.

1. **Consumer honesty first.** Add explicit historical/provenance source
   metadata to the compatibility endpoints. Report live-runtime availability
   as unbound/unavailable unless a separately authorized run is actually bound.
   Stop equating a parsed snapshot with live station operational health.
   Keep historical payload available with unmistakable labeling, and document
   a compatibility/deprecation policy for existing response fields rather than
   silently replacing them with invented current values.
2. **Correct onboarding and maintained documentation.** Point to the current
   executable preflight/runtime baseline, label old snapshot and lockpoint as
   historical, and remove instructions to update the legacy file after routine
   development. Reconcile AURORA_CONTEXT's outdated chronology without changing
   the historical snapshot itself. Update generated API descriptions from their
   source after this correction.
3. **Replace the calendar-age gate with meaningful retirement/authority
   validation.** Validate the legacy/non-genesis baseline, read-only preflight,
   refused legacy writes, explicit historical API labeling, and external
   persistence boundary. Keep blocking failure for actual contract regressions.
   A frozen historical artifact must not fail merely because time passes.
   Review workflow consumers and required checks before renaming/replacing
   the lane. Do not merely delete or disable the red check without replacement.
4. **Keep live-run liveness separate.** If a deployment needs freshness alarms,
   define its selected run, lifecycle states (including idle/paused), heartbeat
   source, owner and service-level threshold. Git commit age is not run liveness.
   This operational monitoring is a separately scoped follow-up, not implicit
   authorization to discover, create, bind or advance a run.

A temporary alternative is to retain legacy age as a clearly named archival-age
advisory while adding blocking authority/containment checks. This preserves a
historical diagnostic but adds noise and still requires consumer labeling.
The recommended replacement has the cleaner long-term contract. Neither
alternative requires fabricating a new snapshot.

## Verification required for the implementation

- Legacy snapshot bytes and historical counters remain unchanged.
- Preflight creates no run and does not touch tracked state.
- Reactivating a legacy builder/save or treating legacy state as genesis fails.
- Missing/corrupt historical JSON remains observable; it never implies a live run.
- An unbound runtime is explicit in API output even if the historical file is
  present; historical aggregate 81 is not asserted as current live population.
- The replacement CI check passes on an unchanged old snapshot, fails when
  authority/containment is violated, and runs on PRs as well as relevant main
  changes. Its test must not pass because the target workflow was not triggered.
- Review required-check/consumer mappings, API compatibility, and generated
  documentation; run relevant full suites and inspect hosted PR/main results.
- Preserve CanonRec and the pinned simulation owner source. If implementation
  would change that owner, make it an explicit additional reviewed scope.

## Handoff

The investigation is complete. A repair task is queued with an artifact wait
for the existing CI review receipt. No approval, active-run freshness or repair
completion is inferred from this report. The original #1083 stays recorded as
closed; any new issue should describe the later authority/consumer migration
mismatch instead of pretending its old acceptance criteria still govern genesis.

Root handoff validation: session state validates; all six integration-gate
subprocesses return zero. Its warning verdict retains existing environment,
installed-skill and overdue-review advisories. Hosted freshness check
`129593490083` independently reports the 119-day failure on the fixed source
commit. The legacy file still has the same SHA-256 after the selected tests.
