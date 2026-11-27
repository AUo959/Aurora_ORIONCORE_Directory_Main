# aurora-cloudbank-symbolic#1530: security(playground): fail closed when isolated sandbox runtime is unavailable

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1530
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T03:03:27Z
- Updated: 2026-08-18T03:05:46Z
- Labels: bug, security
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1547 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260831-0627` @ `1ae40d53ec9b3c43445c07e4d78b869b987ff7ed`
- aurora-cloudbank-symbolic#1580 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260907-0627` @ `a71ef88de7b4d0cf91e12014ae3db08ea267c245`
- aurora-cloudbank-symbolic#1592 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260914-0628` @ `63925666199e49b35769bfb41cd321e30cb7d759`
- aurora-cloudbank-symbolic#1624 — fix(playground): refuse execution without isolated sandbox — closed (draft) — `codex/cloudbank-issue-1530-work` @ `3b9df9ed0fe9f2b26ba07a0dc268afa21687e809`
- aurora-cloudbank-symbolic#1626 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261005-0634` @ `ce94a1c31e41872657cf17b7106550b773da9441`
- aurora-cloudbank-symbolic#1636 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261012-0634` @ `fbeec39d1309f54ab4cc0881bb716aff940660aa`
- aurora-cloudbank-symbolic#1650 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261019-0628` @ `67c5f16a0edb0385d779577ab062ebb33e0ef22b`
- aurora-cloudbank-symbolic#1662 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261026-0628` @ `3ab7cbaa2503354ea167f5a97207f34472e1a46f`

## Branches named in the issue

- none

## Original body

## Summary

The Playground is the modern successor to the older Aurora **Developer Mode** intent: a user-facing experimentation surface with limited control that must not be able to alter Aurora's protected core.

Authentication/session ownership from closed #652 is now present in `src/playground/api.py`, but the execution boundary still fails open in a way that conflicts with that original safety intent and with the current Playground architecture specification.

## Current evidence

`docs/specs/PLAYGROUND_ARCHITECTURE.md` defines the Playground as an L2 experimental environment and describes execution as sandboxed, request-driven, authenticated, resource-limited, and non-autonomous.

`src/playground/api.py` now requires a valid bearer/CSRF-bound session for session creation, execution, result access, sharing, and WebSocket access. This is a strong successor to the access-control portion of #652.

`src/playground/sandbox.py`, however, currently does:

```python
if not self.client:
    logger.warning("Docker SDK unavailable, falling back to local subprocess execution")
    return self._run_local(language, code, stdin, task_id)
```

and `_run_local(...)` executes submitted Python or Node code using host `subprocess.run(...)`.

The Docker path sets `network_disabled=True`, a read-only filesystem, CPU/memory limits, and container isolation. The local fallback does not preserve those isolation guarantees.

## Why this is a distinct issue from #652

#652 was primarily an unauthenticated execution/session-ownership vulnerability. Its acceptance criteria required that local subprocess fallback not be reachable from **unauthenticated** requests.

That issue is correctly closed after auth/ownership hardening.

The remaining problem is different:

> An authenticated Playground user can still cause submitted code to execute directly on the application host whenever Docker is unavailable.

Authentication does not make untrusted code safe to execute on the host.

## Recovered design-intent relationship

Native Aurora architecture previously defined a public-facing Developer Mode whose central constraint was that external users could experiment without being able to fundamentally change the core system.

The current Playground is a substantially better implementation descendant of that concept, but local host fallback breaks the isolation invariant that makes the descendant equivalent in intent.

This issue therefore treats the old mode name as lineage evidence, not as a request to restore a literal global `Developer Mode` switch.

## Required behavior

For untrusted/user-supplied Playground execution:

```text
isolated sandbox ready
       ├── yes → execute under declared limits
       └── no  → refuse execution / report unavailable
```

Never:

```text
sandbox unavailable → execute user code on application host
```

## Proposed implementation

1. Remove or disable `_run_local(...)` as an automatic fallback for request-driven Playground execution.
2. If Docker/container runtime is unavailable, return an explicit fail-closed execution result such as:
   - `sandbox_unavailable`, or
   - service-unavailable error at the API/queue boundary.
3. Keep any local runner needed for trusted development/tests behind a separate explicit developer-only code path that cannot be reached by normal Playground requests.
4. Ensure health reporting exposes whether isolated execution is actually ready.
5. Add startup/runtime logging that distinguishes:
   - Docker SDK missing,
   - daemon unavailable,
   - image unavailable,
   - sandbox ready.
6. Preserve no-network, read-only filesystem, resource limits, and timeout constraints on the supported execution path.

## Security invariant

**No user-submitted Playground program may execute in the application host namespace merely because the configured isolation provider is unavailable.**

This should be treated as fail-closed infrastructure, not graceful degradation.

## Acceptance criteria

- [ ] Request-driven Playground execution never calls host `subprocess.run(...)` for submitted code.
- [ ] Docker/container unavailability causes an explicit execution refusal rather than local execution.
- [ ] Health/status output distinguishes `sandbox_ready` from unavailable/degraded states.
- [ ] Tests cover Docker SDK missing and daemon unavailable cases.
- [ ] Tests assert that no local subprocess is spawned for user requests when isolation is unavailable.
- [ ] Existing authenticated session ownership behavior from #652 remains intact.
- [ ] Network-disabled/read-only/resource-limited sandbox behavior remains intact when execution is available.
- [ ] Any trusted local development runner is separately invoked and cannot be reached from mounted Playground routes.
- [ ] Documentation states that the public/user-facing execution boundary fails closed.

## Non-goals

- redesigning the Playground UI;
- changing L2/L1 classification;
- adding autonomous execution;
- replacing the container backend in this issue;
- restoring a literal historical Developer Mode toggle;
- weakening current authentication requirements.

## Design principle

**Loss of the sandbox must reduce capability, never reduce isolation.**


## Comments (0)
