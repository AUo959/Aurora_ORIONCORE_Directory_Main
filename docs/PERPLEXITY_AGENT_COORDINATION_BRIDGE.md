# Perplexity Agent Coordination Bridge

**Status:** Control-plane coordination protocol. Not implementation canon by itself.  
**Applies to:** Aurora work involving Perplexity, ChatGPT project-space agents, Codex, Claude Code, and human maintainers.  
**Primary repos:**

- `AUo959/aurora-cloudbank-symbolic`
- `AUo959/Aurora_ORIONCORE_Directory_Main`

## Purpose

Perplexity Aurora is an active, implementation-capable Aurora contributor when the user authorizes that role. It may read code, inspect issues and pull requests, propose patches, and open GitHub pull requests.

This bridge makes Perplexity visible to the rest of the Aurora GitHubOps workflow so that agents do not duplicate work, overwrite each other, or treat side-channel conclusions as canon before GitHub evidence exists.

## Core rule

Perplexity work becomes canonical only through GitHub.

A Perplexity answer, thread, or recommendation is pre-canonical until it is represented in one of these durable surfaces:

1. A Git commit.
2. A GitHub issue or issue comment.
3. A GitHub pull request.
4. A PR review or review comment.
5. A control-plane report or handoff committed to the repository.

If Perplexity output and current GitHub evidence disagree, current GitHub evidence wins.

## Perplexity role model

Perplexity may operate in any of these roles when explicitly assigned:

| Role | Allowed work | Required coordination |
|---|---|---|
| Research | Search, summarize, compare approaches, identify risks | Cite sources and identify assumptions |
| Review | Inspect existing issue, PR, branch, or diff | Include issue/PR number, head SHA if available, CI state, and review findings |
| Handoff | Produce implementation instructions for Codex, Claude Code, ChatGPT, or a human | Include exact files, tests, acceptance criteria, and conflicts checked |
| Implementation | Modify code and open PRs | Must check current issue/PR/branch state first and route through normal PR review/merge gates |

Implementation-capable does not mean merge-authorized. Merge authority remains a separate maintainer decision and requires current evidence.

## Required inbound context packet

Before assigning Perplexity work, provide a packet like this:

```md
Aurora Perplexity coordination packet

Role requested:
<Research / Review / Handoff / Implementation>

Primary repo:
<owner/repo>

Control-plane repo:
AUo959/Aurora_ORIONCORE_Directory_Main

Task target:
<Issue # / PR # / branch / file path / workflow run / open question>

Current GitHub evidence:
- Issue/PR state:
- Branch/head SHA:
- Changed files or intended paths:
- CI/status:
- Review threads/comments:

Known active agents:
- ChatGPT:
- Codex:
- Claude Code:
- Perplexity:
- Human:

Known active claims or blockers:
<claim id / issue broker state / unknown>

Do not duplicate:
<existing PRs / branches / linked issues / overlapping files>

Required output format:
- Observed
- Derived
- Recommended
- Blocked
- Assumption

Canon rule:
Do not treat this thread as canon. Durable project state lives in GitHub and committed control-plane files.
```

## Required Perplexity outbound handoff

Perplexity outputs that affect project work should use this structure:

```md
Perplexity Aurora handoff

Role performed:
<Research / Review / Handoff / Implementation>

Target:
<repo, issue, PR, branch, files>

Observed:
<facts directly verified from repo, issue, PR, CI, docs, or source citations>

Derived:
<reasoned conclusions from observed facts>

Recommended:
<next actions, with priority and risk>

Blocked:
<missing evidence, inaccessible state, unresolved conflicts>

Assumptions:
<temporary assumptions that must not drive mutation without verification>

Conflict check:
- Existing linked PRs checked:
- Existing branches checked:
- Active claims checked:
- Overlapping paths checked:

Implementation summary, if applicable:
- Branch:
- Commit/head SHA:
- Files changed:
- Tests run:
- CI/status:
- Rollback path:
```

## Duplicate-work prevention

Before implementation, Perplexity should check or be given current evidence for:

1. Existing GitHub issue body and comments.
2. Existing PRs linked to the issue.
3. Open PRs touching the same files.
4. Existing branches with similar names or issue numbers.
5. Control-plane `catalog/session_state.json` where available.
6. Session claims or issue-broker state where available.
7. Current CI/status for relevant PR heads.

If any of these cannot be checked, Perplexity must mark coordination status as **Blocked** or **Assumption**, not safe-to-claim.

## Branch and PR naming

Perplexity-authored branches should be easy to identify. Preferred patterns:

- `perplexity/issue-<number>-<short-slug>`
- `perplexity/review-<pr-number>-<short-slug>`
- `perplexity/docs-<short-slug>`

Perplexity-authored PRs should include:

- Linked issue or explicit reason no issue exists.
- Claimed files or affected paths.
- Evidence checked before implementation.
- Tests run locally or in CI.
- Known risks.
- Rollback path.
- Statement that all current GitHub evidence must be refreshed before merge.

Use `Fixes #NNN` only when the PR fully resolves the issue. Use `Refs #NNN` or `Addresses part of #NNN` for partial work.

## Conflict and collision rules

If Perplexity proposes or opens work that overlaps another agent:

1. Do not merge until overlap is reviewed.
2. Compare changed files and issue acceptance criteria.
3. Decide whether to supersede, split, rebase, close duplicate, or combine work.
4. Record the decision in a GitHub issue, PR comment, or committed control-plane handoff.
5. Prefer the smallest issue-scoped PR over umbrella changes.

High-risk overlap areas include:

- Authentication and token validation.
- Secrets and environment handling.
- PII detection, logging, middleware, telemetry.
- Ethics gates and simulation determinism.
- Ledger writes, tenant isolation, persistence, and cache boundaries.
- CI workflows and release automation.

## Merge gates for Perplexity-authored PRs

Perplexity-authored PRs follow the same merge gates as any other agent-authored PR:

- Current PR metadata verified.
- Current head SHA verified.
- Diff and changed files reviewed.
- Linked issue acceptance criteria checked.
- CI/status checks reviewed for the current head SHA.
- Review threads checked.
- Security-sensitive behavior reviewed when applicable.
- Rollback path identified.
- Explicit maintainer merge instruction received.

No Perplexity thread, even a correct one, bypasses these gates.

## Two-way visibility pattern

### GitHub/control-plane to Perplexity

Use the inbound context packet before Perplexity begins work.

### Perplexity to GitHub/control-plane

Promote useful Perplexity output into one or more durable surfaces:

- Issue comment.
- PR comment or review.
- Control-plane report in `reports/analysis/`.
- Implementation spec committed to `docs/` or `reports/analysis/`.
- PR body with evidence ledger.

Do not rely on a private Perplexity thread as the only record of a decision.

## Evidence labels

Use the standard Aurora GitHubOps evidence labels:

- **Observed** — directly verified in files, issues, PRs, CI logs, tool output, or cited sources.
- **Derived** — reasoned from observed facts.
- **Recommended** — proposed action, not yet executed.
- **Blocked** — verification or execution failed.
- **Assumption** — temporary hypothesis; do not mutate based on it alone.

## Practical operating loop

1. Human or coordinator chooses an issue/PR/task.
2. Coordinator checks current GitHub state and active claims.
3. Coordinator gives Perplexity an inbound context packet.
4. Perplexity performs its assigned role.
5. Perplexity returns an outbound handoff.
6. Coordinator mirrors durable findings into GitHub/control-plane if useful.
7. Any implementation work proceeds through branch, PR, CI, review, and merge gates.
8. After completion, update the issue, PR, or control-plane handoff with final evidence.

## Non-authority statement

This document coordinates agents. It does not authorize automatic mutation, merge, closure, deletion, or canon promotion.

Current GitHub evidence and explicit maintainer decisions remain authoritative.
