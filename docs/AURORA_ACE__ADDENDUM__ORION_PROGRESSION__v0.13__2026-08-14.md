# Aurora Canon Engine — Governed Orion L1 Progression Addendum

**ACE version:** v0.13  
**Date:** 2026-08-14  
**Status:** acceptance candidate

## Purpose

ACE v0.13 adds a local operator control boundary for advancing an already-existing Orion L1 run through CloudBank's native `OrionL1Runtime`. ACE does not implement a second simulation clock and does not acquire L1 ownership.

The execution chain is:

`existing persisted run -> exact owner binding -> owner preflight -> owner resume gate -> load existing run -> non-mutating state snapshot -> explicit state-bound authorization -> exactly one native advance(15) -> persisted-state validation -> external receipt`

## Owner boundary

The registered owner is CloudBank at the exact repository pin recorded by OrionCore's repository registry. The bound owner surface is:

- `simulation/l1_runtime.py`
- class `OrionL1Runtime`
- `preflight()`
- `load_run()`
- `advance()`
- `export_state()`

ACE verifies both the registered CloudBank commit and the exact Git blob of the owner source before loading it.

## Readiness boundary

ACE requires both:

1. `preflight.ready == true`
2. `preflight.resume_ready == true`

This distinction is deliberate. A structurally valid runtime is not automatically authorized to resume when required L1 embodiments/providers remain unbound or blocked. ACE does not repair, activate, or bypass those providers as part of progression.

## Authorization

Preview is non-mutating. The resulting confirmation token is bound to:

- run ID;
- current tick;
- station-cycle minute and cycle length;
- exact persisted `state.json` SHA-256;
- semantic exported-state SHA-256;
- seed and deterministic replay position;
- deterministic RNG-position fingerprint;
- run CloudBank and CanonRec revisions;
- registered CloudBank commit;
- exact owner-source Git blob;
- Pilot principal;
- authority reference;
- elapsed minutes;
- exactly one authorized tick.

The token is a state-bound confirmation receipt. It is not an authentication credential.

Any change to the persisted run after preview changes the authorization state and causes commit refusal before `advance()` is invoked.

## Mutation semantics

A successful authorization permits exactly:

`OrionL1Runtime.advance(elapsed_minutes=15)`

once.

ACE then reopens the persisted run through a fresh runtime instance and verifies:

- tick advanced by exactly one;
- station-cycle minute advanced by exactly fifteen minutes modulo the cycle length;
- deterministic replay position advanced by exactly one;
- persisted state bytes changed;
- the resulting state still passes owner validation.

## Uncertain-state rule

If the owner raises after persisted state changes, if persisted state becomes unreadable after the call, if post-advance validation cannot establish the new state, or if the external progression receipt cannot be sealed after a successful advance, ACE returns `state_uncertain` semantics through `OrionProgressionStateUncertain`.

Automatic retry is forbidden. Operator reconciliation is required because another call could create a second real tick.

## Explicit prohibitions

v0.13 does not permit:

- `init_run()`;
- creation of a new Orion run;
- provider activation or repair;
- automatic resume;
- more than one tick per authorization;
- arbitrary elapsed-time selection;
- automatic retry after ambiguity;
- HTTP exposure;
- MCP exposure;
- CanonRec or primary-canon mutation;
- promotion of run state to canon;
- a parallel ACE tick engine.

## Receipts

Progression receipts are written outside OrionCore and CloudBank, under the local operator receipt root. They are non-canonical control-plane provenance and cannot overwrite an existing tick receipt.

## CI acceptance boundary

CI may load the exact registered CloudBank runtime owner and call `preflight()` to verify the integration binding.

CI must not load a registered live run and must never call `advance()` on a real Orion run. Transaction/replay/uncertain-state behaviors are exercised only through synthetic fake runtimes and temporary external run roots.

## Acceptance invariant

> ACE may advance Orion only when the existing L1 owner says the run is resumable, the operator explicitly authorizes the exact observed state, and exactly one native runtime tick can be proven afterward.
