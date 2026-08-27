# ORION — ADR-lite — Orion v0.13 CloudBank re-baseline

**Status:** decided
**Date:** 2026-08-20
**Decision:** re-attest the ACE Orion v0.13 owner binding at CloudBank `a19870a5`
(was `9c34d8e9`), owner blob `5b6d9351` (was `dd3ae6f7`).
**Closes:** `ace-v1-orion-owner-compatibility`

---

## The question

`catalog/ace/policies/orion_progression_v0_13.json` pinned CloudBank at
`9c34d8e9`. `catalog/repo_registry.yaml` tracks CloudBank `main`, which had
advanced to `a19870a5`. `registered_cloudbank()` requires the two to be equal,
so `test_registered_owner_binding_calls_preflight_only` failed with
`registered CloudBank has invalid field(s): head_sha`.

The registry is right to track live `main`; the policy is a **reviewed
attestation**, not a mirror, so it is legitimately allowed to trail. The real
question is therefore not "are these equal" but **"did anything the v0.13 owner
contract depends on actually change?"**

## What changed

`9c34d8e9..a19870a5` spans exactly one commit touching the owner file:

| | |
|---|---|
| Commit | `18fed59d feat(l1): add governed staffing runtime (#1501)` |
| File | `simulation/l1_runtime.py` |
| Diff | **+272 / −0** — purely additive |
| Methods added | 16, all staffing (`plan_staffing`, `apply_staffing`, `observe_personnel`, …) |
| Methods removed | 0 |

The four methods the policy names — `preflight`, `load_run`, `advance`,
`export_state` — are **byte-identical** across the range.

## The part that nearly got missed

Byte-identical entry points do **not** imply unchanged behaviour. Comparing all
76 pre-existing methods (not just the four named ones) found one changed helper:

```python
 def _validate_loaded_state(self, state):
     ...
     self._validate_loaded_fleet(state)
+    self._validate_loaded_staffing(state)
     self._validate_loaded_embodiments(state)
```

`_validate_loaded_state` is on `load_run`'s call path. The new validation raises
`PreflightError` when `world_state["population"]` is not a dict. So `load_run`
became **strictly more demanding of persisted state** while its own source did
not change at all.

With `require_existing_run: true` and `require_resume_ready: true`, that is
exactly the shape of change that could break resume for runs written before
`#1501` — and a check limited to the four named methods would have returned a
confident, wrong "safe".

## Why it is nonetheless safe

Verified against the persisted runs that actually exist, not against
assumptions:

| Check | Result |
|---|---|
| Runs under `~/.aurora/l1-runs` | 4 (Aug 8–10, all pre-`#1501`) |
| `world_state` is a dict | 4 / 4 |
| `world_state["population"]` is a dict | 4 / 4 — first failure mode cannot fire |
| `population["run_staffing"]` | `None` in all 4 |
| `staffing` key present | absent in all 4 |
| `StaffingRunState.from_payload(None)` | empty ledger; `validate()` passes |
| Resulting path | no actions and projection `None` and no personnel/seats → early `return` |

`_validate_loaded_staffing` is therefore a no-op on every run in existence. The
re-baseline does not change observable behaviour for any persisted state.

**This is an empirical finding about live data, not a structural guarantee.** A
future run that persists staffing state, or one whose `world_state` lacks
`population`, would behave differently. The finding is recorded rather than
generalised for that reason.

## What had to move

The attestation is stated in **five** places, all of which must move together:

1. `catalog/ace/policies/orion_progression_v0_13.json` → `cloudbank_repository_sha`
2. same file → `owner.git_blob_sha`
3. `tools/ace/orion_runtime_owner.py` → `_OWNER_FIELDS["git_blob_sha"]`
4. `tools/ace/orion_progression.py` → `_OWNER_HELPER_BLOB` (tamper-evidence over
   #3's own file — editing it *at all*, comments included, invalidates this)
5. `tests/test_aurora_ace_orion_progression.py` → `CLOUDBANK_SHA`, `OWNER_BLOB`

Plus `catalog/repo_registry.yaml`, which already tracked `a19870a5`.

Moving them one at a time produced three different red states in sequence, each
naming a different component than the one actually left behind. That is
defence-in-depth working as intended, but it makes a baseline move a five-point
edit with a misleading failure mode at every partial step.

## Consequences

- `test_registered_owner_binding_calls_preflight_only` passes; Aurora CI goes
  from 6 failures to 0.
- `tools/ace_owner_contract_diff.py` is added so the next baseline move is
  answered by evidence rather than reading. It exits `1` (REVIEW REQUIRED) — not
  `0` — when named methods are identical but a helper on their call path
  changed, because that is precisely the case that produced a false safe verdict
  here.
- `tests/test_ace_orion_policy_pin_coherence.py` pins the internal agreement
  between copies 1–3 and 5, so a half-done bump fails with a message naming the
  right file.

## Alternatives rejected

- **Leave the pin and mark the test expected-fail.** Hides a real signal and
  leaves CI red, which is what let five unrelated failures accumulate unnoticed
  since 2026-08-15.
- **Auto-sync the policy from the registry.** Destroys the attestation. The pin
  exists precisely so a CloudBank change cannot silently become authorised.
- **Bump only `cloudbank_repository_sha`.** Fails closed on the blob check, and
  would have skipped the analysis that found the `_validate_loaded_state` delta.
