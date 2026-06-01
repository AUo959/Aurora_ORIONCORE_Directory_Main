# CloudBank Issue Broker Workflow v1

This workflow makes the command "resolve CloudBank issues" safe when Codex and
Claude Code may both be active. The broker is a root-control-plane planning and
claiming layer for the nested `aurora-cloudbank-symbolic-main` repo.

The broker does not replace GitHub issue truth, does not mutate the CloudBank
nested repo, and does not close issues. It creates local session claims before
either platform creates a CloudBank worktree or edits files.

## Authority

- Target repo: `aurora-cloudbank-symbolic-main`
- Canonical path:
  `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- Repo registry: `catalog/repo_registry.yaml`
- Local lock storage: `catalog/session_claims/*.json`
- Tool: `tools/cloudbank_issue_broker.py`

## Required Flow

1. Refresh root handoff state.
   - Read `catalog/session_state.json`.
   - Check active session claims.
   - Check CloudBank local worktrees.
   - Refresh live GitHub issue/PR state before treating labels, comments, or
     closure status as current.

2. Build an issue plan.
   ```bash
   python3 tools/cloudbank_issue_broker.py plan --issue 842 --issue 843
   ```

3. Pick only claim-ready issues.
   - If an issue has an active claim, use another issue or arrange a handoff.
   - If a local worktree already names the issue, inspect it before claiming.
   - If the canonical CloudBank checkout is dirty, do not use it as the work
     surface.

4. Claim before editing.
   ```bash
   python3 tools/cloudbank_issue_broker.py claim \
     --platform codex \
     --issue 842 \
     --label auth \
     --paths src/middleware/fastapi_security.py tests/test_security_middleware.py \
     --validation-command ".venv/bin/python -m pytest -q tests/test_security_middleware.py"
   ```

5. Create the CloudBank worktree only after the claim succeeds.
   - Use the emitted `worktree_command`.
   - Work from `origin/main`.
   - Keep the branch issue-specific.

6. Publish through PR.
   - Use `Fixes #NNN` in the PR body.
   - Include claimed paths and validation evidence.
   - Close the issue through merge, not by direct issue mutation.

7. Release the claim.
   ```bash
   python3 tools/cloudbank_issue_broker.py release --issue 842
   ```

## Command Reference

Show local CloudBank claims and worktrees:

```bash
python3 tools/cloudbank_issue_broker.py status
```

Check whether planned paths can be claimed:

```bash
python3 tools/cloudbank_issue_broker.py check \
  --issue 842 \
  --paths src/middleware/fastapi_security.py tests/test_security_middleware.py
```

Claim an issue:

```bash
python3 tools/cloudbank_issue_broker.py claim \
  --platform claude-code \
  --issue 843 \
  --label ci \
  --paths .github/workflows/ci.yml tests
```

Emit machine-readable output:

```bash
python3 tools/cloudbank_issue_broker.py plan --issue 842 --json
```

## Collision Semantics

The broker blocks new work when either condition is true:

- An active local session claim already owns the same CloudBank issue.
- An active local session claim for `aurora-cloudbank-symbolic-main` overlaps
  any requested path.

The broker also reports local CloudBank worktrees whose branch or path names
mention the issue. Worktrees are advisory blockers: inspect them before
claiming or explicitly transfer ownership.

## GitHub Posture

Local claims protect this machine only. For durable cross-thread visibility,
post a GitHub issue comment or PR note when write access is approved:

```text
Claimed by <codex|claude-code> for issue #NNN; branch `<branch>`; paths:
<paths>; validation: <command>; expires: <UTC time>.
```

Do not post, label, close, merge, or mutate GitHub state unless the user has
authorized that operation for the current session.

## Routing Guidance

- Prefer Claude Code for Codacy/lint fixes, CI workflows, secret scanning, and
  broad surgical edits.
- Prefer Codex for PR comment addressing, governance/context checks, browser or
  runtime verification, and Aurora-aware integration decisions.
- Avoid simultaneous claims on shared hotspots such as `.github/`,
  dependency manifests, auth/security middleware, or broad shared test trees.
