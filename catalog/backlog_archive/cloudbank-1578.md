# aurora-cloudbank-symbolic#1578: ci: the SIMULATION_STATE freshness gate outlived its premise and is now unsatisfiable

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1578
- State at archive: open
- Author: AUo959
- Created: 2026-09-06T15:48:11Z
- Updated: 2026-09-06T15:48:19Z
- Labels: ci, repo-hygiene
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1240 — fix: GAP-010 — SIMULATION_STATE.json staleness (3-layer fix per #1083) — merged — `fix/simulation-state-freshness-1083` @ `7d2880677b2f77db2cc633040d2806b018a405b1`
- aurora-cloudbank-symbolic#1461 — feat(l1): clear Orion preflight bootstrap blockers — merged — `agent/l1-preflight-alignment` @ `af4f23273f924a1c099057271b1bf870a7d2374d`
- aurora-cloudbank-symbolic#1491 — fix(ai): separate catalog availability from routing policy — merged — `codex/cloudbank-issue-1329-catalog-routing-alerts` @ `b9fd06e84b3f5241720048a322b3374048cc1810`

## Branches named in the issue

- none

## Original body

## Symptom

`check-state-freshness` is the **only** remaining red check on `main`. It fails because `.aurora/SIMULATION_STATE.json` was last committed 2026-07-13 and the policy caps age at 14 days:

```
::error::.aurora/SIMULATION_STATE.json is 50 days old — exceeds the 14-day
freshness policy (GAP-010, issue #1083).
```

It cannot be satisfied by any legitimate action, because the file it polices has since been deliberately frozen.

## The premise was true when the gate was written, and is not true now

| Date | Event |
|---|---|
| 2026-06-21 | #1083 (GAP-010) filed, describing `SIMULATION_STATE.json` as *"the canonical runtime state file and primary session continuity anchor"* |
| **2026-07-13** | `ab9419ce` (#1240) adds `simulation-state-freshness.yml` — and makes the last-ever update to the file, in the same commit |
| **2026-08-08** | `7e0ad613` (#1461) rewrites `.aurora/load_simulation.py` into a legacy shim that **demotes the file** |

At the moment the gate was added, `load_simulation.py` still opened with *"Aurora CloudBank - Simulation State Loader… ensures the Aurora simulation context is loaded and active"*. After #1461 it opens with:

> **Legacy Orion bootstrap compatibility shim.**
> This module is retained so old references fail safely instead of recreating the pre-2026 initialization model. **It is not the canonical L1 INIT path.**

So the gate predates the architectural change that invalidated it by about three and a half weeks.

## Why it is now unsatisfiable

The same module actively refuses to write the file:

```python
def save_simulation_state(state: Dict[str, Any]) -> bool:
    """Refuse legacy state mutation.

    Live run persistence belongs to ``simulation/l1_runtime.py`` and must stay
    outside the repository.
    """
    del state
    return False
```

Three consequences, all fatal to the policy:

1. the file is **not canonical** — `init_l1.py` is;
2. the code **refuses to mutate it**;
3. live state deliberately persists **outside the repository**, so there is nothing in-tree left to freshness-check.

The only way to turn this check green is to touch a file that is explicitly retained as a frozen historical record — which would falsify the very provenance it preserves. GAP-010's concern (*"state diverges silently from repo truth"*) was answered by #1461 removing the file from the live path altogether, not by keeping it fresh.

## Options

1. **Retire the check.** The artifact it guards is now historical, and the divergence risk it was written against no longer exists. Simplest and matches the current architecture.
2. **Repoint it** at whatever the canonical L1 path does persist in-repo. Needs someone to say what that is — `init_l1.py` writes live state outside the repository, so there may be no in-tree target.
3. **Keep it and unfreeze the file**, reversing part of #1461. Not recommended: it recreates exactly the pre-2026 initialization model the shim exists to prevent.

Recommend option 1, cross-referencing #1083 and #1461 in the removal so the governance trail stays intact.

Not acting unilaterally: #1083 was a deliberate HIGH-severity governance response, so retiring its enforcement should be an explicit call even though the evidence that it no longer applies is unambiguous.

Found on 2026-09-06 while clearing the other three red checks on `main` (#1566, AUo959/qgia-knowledge-spine#9).


## Comments (0)
