# CloudBank Guide Markers — 2026-06-08

**Status:** Orientation only. Not implementation canon. Not merge authority.

These notes preserve observations and suggested next review paths so human and LLM agents do not need to rediscover the same repo state. They are guide markers only. Before implementation, merge, closure, issue comment, label change, or any GitHub mutation, refresh current GitHub evidence: repository files, issue body/comments, PR metadata, head SHA, changed files, CI/status, and review threads.

## Scope

- Implementation repo: `AUo959/aurora-cloudbank-symbolic`
- Control-plane repo: `AUo959/Aurora_ORIONCORE_Directory_Main`
- Snapshot basis: ChatGPT project-space read-only review on 2026-06-08
- Intended readers: human maintainers, Codex, Claude Code, ChatGPT project-space agents, and other repo-management assistants

## Hard verification rule

Do **not** implement from this document alone.

Use it to decide where to look first, then verify from current GitHub evidence before changing files, assigning work, closing issues, reviewing PRs, or merging anything.

Treat every claim here as stale by default after creation unless refreshed against live repository state.

## Current snapshot markers

- CloudBank appears to be in a review-and-stabilization phase, not a clean merge phase.
- Many open PRs are draft `claude/issue-*` branches and should be treated as review candidates, not merge-ready work.
- The most useful next step is reviewing existing issue-linked PRs rather than creating new duplicate implementation.
- The highest-priority first review cluster is MCP connector boundary/security work.
- The second-priority review cluster is ethics/traceability work.
- Privacy/middleware PRs require extra review for logging safety, request/response body handling, and middleware order.
- Public README production-readiness claims should be verified against current tests/CI before being repeated externally.

## Suggested first review path

| Order | Target | Why it is useful | Required refresh before action |
|---:|---|---|---|
| 1 | PR #889 / issue #825 | MCP tool argument schema validation at dispatch | PR metadata, diff, issue body/comments, CI for current head SHA |
| 2 | PR #891 / issue #823 | Raw exception sanitization on MCP model-facing boundary | PR metadata, diff, issue body/comments, CI for current head SHA |
| 3 | PR #890 vs PR #899 / issues #824 and #826 | Potential overlap in bridge fail-closed auth, retries, headers, and sanitized bridge errors | Both diffs, changed files, linked issue criteria, CI, collision review |
| 4 | PR #888 / issue #822 | Replace substring Pilot seal validation with HMAC | Diff, tests, env docs, issue acceptance criteria, CI |
| 5 | PR #920 / issue #776 | Ethics gate for quantum simulation | Diff, fail-open/fail-closed decision, tests, CI |
| 6 | PR #912 / issue #778 | PII detection middleware | Diff, body replay behavior, log safety, middleware ordering, CI |

## Observed guidance from snapshot

### MCP connector boundary cluster

The MCP connector cluster is currently the cleanest first review target because the issues appear security/boundary-facing and already have candidate PRs.

Guide markers to verify live:

- `connector/server.py` should validate tool arguments against declared `inputSchema` before `tool.run(arguments)`.
- Model-facing tool errors should use stable sanitized error codes rather than raw exception strings.
- `connector/transport/bridge.py` should fail closed when connector auth is missing if the connector is intended to gate model access to the API.
- Outbound connector requests should include provenance headers such as `User-Agent` and `X-Source-Client`.
- Pilot seal validation should not rely on a literal substring match for elevated/write operations.

### Ethics / traceability cluster

PR #920 looked like a focused review candidate during the snapshot because it claimed a small ethics-gate addition around quantum simulation.

Guide markers to verify live:

- Confirm whether ethics unavailability should fail open or fail closed for quantum simulations.
- Confirm violation details returned to callers are safe and do not leak internal structures unnecessarily.
- Confirm tests prove both blocked and allowed paths.
- Confirm the change preserves deterministic simulation behavior except where explicitly intended.

### Privacy / middleware cluster

PR #912 looked like a focused privacy/middleware review candidate during the snapshot.

Guide markers to verify live:

- Confirm request body inspection does not consume bodies in a way that breaks downstream handlers.
- Confirm response scanning/redaction is safe for non-JSON, large, streaming, and error responses.
- Confirm logs report PII types only, not values.
- Confirm middleware order is intentional and covered by tests.

### Public documentation / production-readiness claims

The CloudBank README contains strong production-readiness and test/completeness claims. Treat those as public-facing claims requiring periodic verification, especially while many security, ethics, privacy, and persistence PRs remain open.

Potential future work:

- Add a README claim-verification checklist.
- Add a project-space rule to distinguish README claims from verified current repo state.
- Consider a docs issue if claims become stale or unsupported by current CI evidence.

## Suggested evidence format for future agents

When refreshing any marker above, use this table:

| Claim | Label | Live evidence | Confidence | Next action |
|---|---|---|---|---|
| `<claim>` | Observed / Derived / Recommended / Blocked / Assumption | `<file / issue / PR / CI / command>` | High / Medium / Low | `<one action>` |

## Snapshot limitations

- Exact total open PR count was not verified in the snapshot because tool output was truncated.
- Exact total open issue count was not verified in the snapshot because tool output was truncated.
- PR/issue status may have changed after this file was created.
- CI status must be refreshed per PR head SHA before any merge-readiness recommendation.
- Local session claims and worktrees may not be visible from GitHub alone.

## Project-space improvement marker

Future repo snapshots should explicitly report:

- exact counts verified
- exact counts blocked
- open PR count
- draft PR count
- open issue count
- security-sensitive PR count where possible
- stale snapshot warning

This prevents future agents from turning partial queue visibility into false precision.

## Non-authority statement

This file is a coordination aid. It does not override:

1. Current committed repository files.
2. Current GitHub issue and PR state.
3. Current CI/status checks.
4. Current control-plane `catalog/session_state.json` and active claim records.
5. Explicit maintainer decisions.

If this file and live evidence disagree, live evidence wins.
