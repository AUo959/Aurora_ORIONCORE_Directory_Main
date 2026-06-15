# Salvage P2-P4 Reconciliation - 2026-06-14

Status: promotion-safe extraction plan. P1 ORD policy-family promotion was
intentionally skipped per the resumed task request. No legacy, staging, archive,
or iCloud material was promoted into canon or runtime by this pass.

## Scope And Current State

Read first:

- `catalog/session_state.json`
- `AGENTS.md`
- `README.md`
- `catalog/workspace_manifest.yaml`
- `catalog/repo_registry.yaml`
- `reports/analysis/salvage_docket__2026-06-12.md`
- `reports/analysis/aurora_salvage_report_latest.md`
- `reports/analysis/ord_integration__2026-06-12.md`
- `reports/analysis/orion_station_spec_recovery__2026-06-12.md`
- `reports/analysis/remote_branch_sweep__2026-06-11.md`
- `reports/analysis/integration_pass__2026-06-11.md`

Observed repo state:

- Root `main` is `bbc9268` and 16 commits ahead of `origin/main`; the worktree
  already had unrelated dirty files before this report.
- CloudBank local `main` is `96e4818f`, behind `origin/main` by one docs commit
  (`078f99c6`, issue 1015 stale report classification). CloudBank also has
  unrelated dirty files: `.env_status.json` and `tests/test_mesh_router_v1.py`.
- CloudBank PR `#1016` is landed locally as `068f3756 feat(ord): ORD-Series
  Drone Fleet policy family`.

Validation and diagnostics run:

- `tests/ord`, `tests/test_quantum_forge_v2.py`, and
  `tests/test_quantum_forge_v3.py`: 79 passed, 1 failed on first run.
  The failure was `TestJoyEvolutionEngine.test_evolve`, where stochastic
  mutation reduced average fitness below the test threshold. A focused rerun of
  that single test passed, so this is a current owner-surface flake, not a
  recovered-protocol requirement.
- `zipwiz-governance-scan` on the root workspace: `PASS`, 0 blocking findings,
  0 warnings, 1 informational evolution milestone.
- `py_compile` with `PYTHONPYCACHEPREFIX=/tmp/aurora_pycache` passed for
  `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/zipwiz_bridge.py`
  and `relay_handshake.py`.
- `importlib.util.find_spec("zipwiz")` returned `None`; the recovered Python
  bridge dependency is not importable in the current root runtime.
- CloudBank dependency manifests searched for `zipwiz`, `zip-wizard`,
  `ZipWizard`, and `ZIPWIZ`; no Python `zipwiz` dependency declaration was
  found.

## P2 - ORD Legacy Fleet Source

Decision: `backup_only` with test extraction only.

Compared sources:

- Legacy Apple Notes source:
  `_staging/apple_notes_recovery__2026-03-16/L1/ord_drone_fleet_v1.0.py`
- Legacy workbench source:
  `_staging/orion_ord_review_fix/package/staging/legacy_pack/SOURCE__Recovered__ORD_DroneDispatch__v0.1__2026-03-10.py`
- Current owner surface:
  `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/modules/ord/`
  and `tests/ord/`

Already represented in current CloudBank:

- Drone identity and dispatch ordering for Gamma Swarm, Delta Scout, Shadowfax,
  and Wisp.
- Pure policy-layer `MissionBrief` to `DispatchOrder` behavior.
- Governance threshold registry with drift, reconnaissance, inspection, secure
  transport, quarantine, and quantum-seal thresholds.
- Hostname-based trust checks and spoofing regression tests.
- Nested sensitive-key classification for restricted transport.
- Shadowfax quarantine/sanitization policy and deterministic receipt hashing.

Missing behavior or tests worth carrying forward:

1. Add explicit threshold tests for `risk_level >= quantum_seal_threshold`.
   Current code appears to support this, but no test pins the combined
   `full_scan`, `threat_abort_threshold`, `quarantine_on_drift`, and Wisp
   `quantum_seal_required` behavior.
2. Add an inspection test for `encoding_anomaly=True` requiring
   `SanitizationAction.NORMALIZE_ENCODING`. The enum and branch exist, but the
   current tests do not pin it.
3. Keep runtime execution behavior out of this lane. Legacy `DeltaScout`,
   `GammaSwarm`, and `Wisp` execution classes include network/probing and
   payload transformation semantics that belong only in a later adapter
   contract after the MCP dispatch integration is explicitly approved.
4. Do not carry `REMOVE_DUPLICATES` into current policy yet. The legacy
   sanitizer contains it, but current CloudBank is intentionally a pure policy
   layer, and no current owner-surface requirement needs content-level duplicate
   removal.

Concrete next edits:

- In a clean CloudBank worktree based on `origin/main`, add tests to
  `tests/ord/test_ord_policy_engine.py`:
  - `test_high_risk_mission_enables_quantum_seal_and_full_scan`
  - `test_restricted_payload_requires_secure_transport_below_risk_threshold`
    if the existing nested-key test is not considered enough coverage.
- Add `test_encoding_anomaly_requests_normalization` to
  `tests/ord/test_ord_inspection_policy.py`.
- Run `PYTHONPYCACHEPREFIX=/tmp/cloudbank_pycache .venv/bin/python -m pytest -q tests/ord -p no:cacheprovider`.
- No source edit should be necessary unless those tests expose a regression.

## P3 - Quantum Agent Forge Protocol

Decision: include as spec reconciliation and policy wrapper, not runtime copy.

Compared sources:

- Recovered protocol:
  `_staging/apple_notes_recovery__2026-03-16/L2/QUANTUM_AGENT_FORGE_PROTOCOL_v1.0.md`
- Current owner surface:
  `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/modules/quantum_forge/`
  plus `tests/test_quantum_forge_v2.py` and `tests/test_quantum_forge_v3.py`

Already represented in current CloudBank:

- Agent generation through `QuantumForge.generate_agent`.
- `GUMAS_Thermax` ethics thresholds and violation logging.
- Symbolic memory node creation and intent-based reactivation.
- Agent export/import, quantum conversion, entanglement, coherence refresh,
  system flow orchestration, ethics-aware quantum gates, topology mapping, and
  joy evolution.

Missing behavior or tests worth carrying forward:

1. Route-before-spawn decision tree. Current `generate_agent` can be called
   directly; there is no policy object that proves standing department coverage,
   prior spec lookup, and direct Aurora competency were checked before spawning.
2. Explicit lifecycle records. Current agents persist in `self.agents`; the
   recovered protocol requires a bounded scope, temporary status, dissolution,
   and retained execution log.
3. Capability expansion authorization. Current metadata can contain arbitrary
   purpose/context, but there is no test that an agent cannot self-expand
   capabilities without Aurora authorization.
4. Retention review schema. Current memory creation and export/import are not a
   substitute for the protocol's `store as spec`, `promote to module`,
   `archive`, or `discard` decisions.
5. Pilot transparency / high-risk acknowledgment. Current ethics enforcement
   blocks low alignment but does not model "high-risk spawn requires pilot
   acknowledgment".
6. Current v3 owner surface has a flaky stochastic joy-evolution test. Stabilize
   that before adding protocol-lifecycle tests so future failures are not
   ambiguous.

Concrete next edits:

- First stabilize current owner-surface flake in
  `modules/quantum_forge/joy_evolution_engine.py` or its test:
  - clamp mutated `joy_index` into `0.0..1.0`; and/or
  - make `TestJoyEvolutionEngine.test_evolve` deterministic with a fixed seed
    or a non-stochastic assertion.
- Add a pure policy module, not a quantum-engine rewrite:
  `modules/quantum_forge/forge_lifecycle_policy.py`.
- Suggested module surface:
  - enums: `ForgeRouteDecision`, `RetentionOutcome`, `ForgeScope`
  - dataclasses: `ForgeTaskRequest`, `StandingCoverage`,
    `ForgeAuthorization`, `ForgeLifecycleRecord`, `RetentionReview`
  - class: `QuantumAgentForgePolicy`
  - methods: `evaluate_route`, `authorize_spawn`, `record_spawn`,
    `request_capability_expansion`, `dissolve`, `review_retention`
- Add `tests/test_quantum_forge_lifecycle_policy.py` covering:
  - standing department coverage prevents spawn
  - prior retained spec prevents a new spawn
  - direct competency prevents spawn
  - no coverage routes to `spawn_quantum_agent`
  - high-risk spawn is blocked without pilot acknowledgment
  - lifecycle record has `forge_id`, enumerated capabilities, bounded scope,
    and `temporary=True`
  - capability expansion without Aurora authorization is denied
  - dissolution records log retention and clears active status
  - retention review maps novel/profound output to spec/module/archive/discard,
    with pilot override
- Only after tests pass, consider a short reconciliation doc under
  `docs/` explaining that the recovered protocol is implemented as lifecycle
  policy around the existing Forge engine.

Canon route:

- Do not promote the recovered protocol text into CanonRec from this pass.
- If the lifecycle policy becomes normative doctrine, route a separate CanonRec
  reconciliation as `L2 protocol_update` after implementation review.

## P4 - ZipWiz Python Bridge Candidate

Decision: include candidate, blocked on owner-surface decision and dependency
verification. Do not promote the recovered Python bridge into CloudBank as-is.

Compared sources:

- Recovered bridge:
  `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/zipwiz_bridge.py`
- Recovered relay helper:
  `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/relay_handshake.py`
- Current CloudBank owner surface:
  `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/bridges/zip-wizard/bridge.ts`
- Registered owner repo surface:
  `zip_wizard` is `~remote~` in `catalog/repo_registry.yaml`.

Already represented in current CloudBank:

- A TypeScript bridge class is wired into `src/index.ts` and included in
  constellation status.
- The current bridge is a stub: it logs operations and returns synthetic
  success data without proving any ZIPWIZ service or archive operation ran.
- Other CloudBank surfaces already use ZIPWIZ handshake language, especially
  bridge and sensor handshakes, but that does not validate archive operations.

Recovered Python behavior worth carrying forward:

1. Archive preflight via `inspect`.
2. Safe extraction semantics for zip-slip, zip bombs, and symlink attacks.
3. Deterministic manifests with anchor and ethics metadata.
4. Manifest diff and delta scoring.
5. PII/threat scan summary.
6. Structured beacon emission with `EOS_SEED_ORION` and `Picard_Delta_3`.
7. Relay handshake result structure with threadseal metadata.

Blockers to direct promotion:

- The recovered module depends on a `zipwiz` Python package that is not
  importable in this environment and is not declared in the CloudBank manifests
  inspected during this pass.
- `zip_wizard` is registered as a remote-only repo, so the actual package
  owner surface was not locally verified.
- The recovered Python bridge claims to replace a TypeScript bridge, but the
  current CloudBank integration point is TypeScript and service-oriented.
- The ZIPWIZ governor pass found no packaging-governance blockers in curated
  roots, but that pass does not prove the recovered Python dependency is
  available or safe to install into CloudBank.

Concrete next edits:

1. Decide owner surface before code:
   - `zip_wizard` repo if this is a package/library feature.
   - CloudBank `src/bridges/zip-wizard/bridge.ts` if this is only a service
     client facade.
   - Root control plane only if it remains governance/scan tooling.
2. If `zip_wizard` is the owner:
   - clone or otherwise make `AUo959/zip_wizard` locally available;
   - verify the package exports `inspect_zip`, `extract_zip_safe`,
     `build_manifest_for_zip`, `diff_manifests`, `compute_delta_score`,
     `scan_zip`, `build_beacon_payload`, and `create_threadseal`;
   - run repo-local tests plus gitleaks/security review;
   - add tests for zip-slip rejection, bomb limits, symlink defense,
     deterministic manifest hashing, anchor/ethics beacon fields, and scan
     output paths.
3. If CloudBank is the owner:
   - replace fake-success tests first by adding tests for
     `src/bridges/zip-wizard/bridge.ts`;
   - require real service acknowledgement or explicit `unavailable` status;
   - validate endpoint configuration and timeout behavior;
   - ensure `createArchive`, `extractArchive`, and `listArchive` do not report
     success from local logging alone;
   - keep archive path validation at the service boundary, not in ad hoc
     TypeScript string checks.
4. Do not add a Python bridge file to CloudBank until the `zipwiz` package
   owner is verified and an explicit Python integration surface exists.

## Recommended Execution Order

1. Use a clean CloudBank worktree, not the dirty canonical checkout.
2. Fast-forward or branch from CloudBank `origin/main` so the issue 1015 docs
   commit is included.
3. Land P2 as test-only coverage first; no legacy code copy.
4. Stabilize the current Quantum Forge v3 stochastic test.
5. Land P3 as a pure lifecycle policy module plus tests.
6. Gate P4 on an explicit owner-surface decision. If `zip_wizard` is selected,
   verify that repo first; if CloudBank is selected, convert the TypeScript stub
   into a real unavailable-or-acknowledged client contract.

## Summary Dispositions

| Lane | Disposition | Carry Forward | Direct Copy? |
|---|---|---|---|
| P2 ORD legacy fleet | `backup_only` | threshold and encoding tests, later adapter contract | No |
| P3 Quantum Agent Forge protocol | `include` as spec reconciliation | lifecycle policy, retention schema, tests | No |
| P4 ZipWiz bridge | `include_candidate` but blocked | archive/manifest/beacon contract after owner decision | No |
