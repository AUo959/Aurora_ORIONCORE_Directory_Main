# Session Claims Workflow v1

Session claims are local coordination records for reducing collisions when
Codex and Claude Code work in the same Aurora / ORIONCORE workspace at the
same time.

They do not replace `catalog/session_state.json`. The state file remains the
durable handoff and task queue. Claims are short-lived, machine-local leases
for paths a platform is about to mutate.

## Storage

- Live claim directory: `catalog/session_claims/`
- Live claim files: `catalog/session_claims/*.json`
- Git posture: live claim JSON files are ignored; the workflow and ignore rules
  are versioned.

Ignoring live claim files prevents the coordination mechanism from creating
new Git conflicts while still letting both platforms see claims on this
machine.

## When To Claim

Create a claim before mutating root control-plane files when another platform
might be active, especially before:

- editing shared docs, catalogs, tools, tests, skills, `.github`, `.claude`, or
  plugin files
- creating or switching branches
- committing or pushing
- running broad generated-surface refreshes

Read-only review does not need to block other work. Use
`--mutation-posture read_only` when the claim is purely advisory.

## Basic Commands

Check for existing claims before starting a root-wide mutation:

```bash
python3 tools/session_claim.py check --repo root --paths . --json
```

Create a scoped claim:

```bash
python3 tools/session_claim.py create \
  --platform codex \
  --task-id session-claims \
  --repo root \
  --paths tools/session_claim.py tests/test_session_claim.py docs/SESSION_CLAIMS_WORKFLOW_v1.md \
  --mutation-posture editing \
  --ttl-minutes 180
```

Refresh a claim during long work:

```bash
python3 tools/session_claim.py refresh --claim-id <claim-id> --ttl-minutes 180
```

Release the claim when done:

```bash
python3 tools/session_claim.py release --claim-id <claim-id>
```

List local claims:

```bash
python3 tools/session_claim.py list
```

## Conflict Semantics

A claim blocks another mutating operation only when all of these are true:

- both claims target the same `repo`
- both claims have mutating postures
- at least one requested path overlaps one claimed path
- the existing claim is active and not expired

Stale claims are non-blocking and appear in output as `stale_claims`.
Released claims are ignored by conflict checks.

Path overlap is prefix-based. For example, a claim on `tools` overlaps
`tools/session_claim.py`, and a claim on `.` overlaps the whole repo.

## Relationship To Session State

Use `catalog/session_state.json` for durable cross-platform handoff:

- suspended tasks
- platform capability routing
- task queue and pending work
- last session summary
- known repo state

Use session claims for short-lived collision prevention:

- intended repo and paths
- mutation posture
- branch and worktree
- TTL and stale detection
- release after completion

If a task pauses and needs to survive thread or platform changes, write the
resume details to `catalog/session_state.json`; do not rely on an active claim
as the only handoff record.

## Session-Start Announcements

Project-focus announcements live in
`catalog/project_focus_announcements.json`. They are tracked advisory focus
guidance, not task ownership and not a mutation claim.

The SessionStart hook surfaces active announcements through:

```bash
python3 tools/project_focus_announcement.py --summary
```

Already-running sessions can discover the same focus by running that command,
`make project-focus`, or Mission Control (`make mission-control`). Mission
Control includes active announcements as advisory operator-inbox items so
current agents can see project focus without restarting their session.

## Claim Schema (v2)

Each claim file carries:

- `scope`: `"local"` (current) or `"remote"` (future multi-machine)
- `machine_id`: stable UUID per machine, persisted at `~/.codex/.machine_id`
- `host`: human-readable hostname
- All other fields from v1 (platform, task_id, paths, TTL, etc.)

## Scaling to Multiple Machines

Claims are currently `scope: "local"` — machine-local, gitignored, visible only
on one machine. This is the right default for a single-developer, single-machine
workflow.

To scale to multiple machines or multiple developers:

1. **No code changes required to the schema** — `scope`, `machine_id`, and `host`
   are already present in every claim.

2. **Change the backend** via the `CLAIM_BACKEND_URL` environment variable:
   ```
   CLAIM_BACKEND_URL=local://           # default — file system
   CLAIM_BACKEND_URL=redis://host:6379  # future — Redis TTL keys per claim_id
   CLAIM_BACKEND_URL=github://owner/repo # future — GitHub Issues as claims
   ```
   The backend reads and writes the same JSON payload regardless of transport.

3. **`catalog/session_state.json` remains the authoritative record** across all
   machines — it is committed and pushed on session end. Claims are a
   best-effort coordination optimization, not the source of truth. Multi-machine
   operation works even without shared claims; it just has higher collision risk.

4. **The `machine_id` field** lets future backends filter claims by origin machine
   without requiring coordination to assign unique IDs.
