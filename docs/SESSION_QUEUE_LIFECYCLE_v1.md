# Aurora Session Queue Lifecycle v1

## Purpose

The shared session queue must keep executable work moving without weakening
Aurora's real authority boundaries. The lifecycle separates routine work from
consequential decisions, gives every open item a review clock, and makes the
active slot clear automatically when work finishes or becomes non-executable.

Canonical surfaces:

- State: `catalog/session_state.json`
- Contract: `catalog/schemas/session_state.schema.json`
- Policy: `catalog/session_queue_policy.json`
- Writer: `tools/session_state_io.py`
- Health audit: `tools/session_queue_health.py`

## Task states

| State | Location | Meaning | Required exit |
| --- | --- | --- | --- |
| `active` | `active_task` | Work is being executed now. | Complete, suspend briefly, wait, park, or cancel. |
| `suspended` | `active_task` | A short continuation has an executable next action and `resume_by`. | Resume or triage by `resume_by`. |
| `ready` | `task_queue` | Actionable work requiring no external decision. | Start when selected. |
| `waiting` | `task_queue` | A concrete external event or decision is required. | Reassess at `review_at` or when `trigger` fires. |
| `parked` | `task_queue` | Deliberately deferred for a documented reason. | Reassess at `review_at`; never park without a trigger. |
| `completed` / `cancelled` | `completed_tasks` | Closed with a receipt. | Reopen only with `reopened_at` and `reopen_reason`. |

`pending_for_next_session` is retained only as a deprecated compatibility key
and must remain empty.

## Selection and aging

Selection precedence is:

1. The user's explicit current request.
2. A relevant suspended task with an executable continuation.
3. Ready work by priority, then `review_at`, then age.

Every queued item has `review_at`. Suspended work has `resume_by`. Queue health
surfaces due reviews and aging suspensions through session startup, workspace
verification, and Mission Control. A task may be renewed only when its evidence,
next action, and review trigger are refreshed.

## Owner gates

Owner approval gates apply to a concrete consequential decision, not to the
work needed to understand or prepare that decision. Policy-approved scopes are
listed in `catalog/session_queue_policy.json` and include canon promotion,
credential or external-account action, public-license selection, authority
selection, and irreversible destructive action.

An owner-gated item must be `kind=decision`, `status=waiting`,
`waiting_on=owner`, `assigned_to=owner`, and include:

- the exact decision and trigger;
- the owner;
- evidence references;
- at least two concrete options;
- a review date.

Read-only investigation, diagnosis, tests, reversible local edits, draft or PR
preparation, and evidence-packet preparation do not require an owner gate. If
those steps resolve the ambiguity, complete the task without manufacturing a
decision. If a consequential choice remains, create the smallest decision
packet at that point.

## Canonical commands

```bash
make queue-health
python3 tools/session_state_io.py add-item <id> \
  --description "..." --next-action "..." --definition-of-done "..." \
  --review-at 2026-08-08T12:00:00Z
python3 tools/session_state_io.py start-item <id>
python3 tools/session_state_io.py ready-item <id> \
  --review-at 2026-08-08T12:00:00Z
python3 tools/session_state_io.py complete-active --detail "..."
python3 tools/session_state_io.py suspend-active \
  --next-step "..." --resume-by 2026-08-03T12:00:00Z
python3 tools/session_state_io.py wait-active \
  --waiting-on external --trigger "..." --review-at 2026-08-08T12:00:00Z
python3 tools/session_state_io.py park-active \
  --reason "..." --review-at 2026-08-15T12:00:00Z
```

Complete a true owner decision only with its approval receipt:

```bash
python3 tools/session_state_io.py complete-item <id> \
  --approval-evidence "Owner decision recorded in <evidence>."
```

Never hand-edit lifecycle state when a canonical command can express the
transition. Run `make session-state-check` after any state mutation.

If an owner gate was misapplied, correct it explicitly rather than leaving the
task stranded:

```bash
python3 tools/session_state_io.py ready-item <id> \
  --reason "Reversible investigation was incorrectly classified as an owner decision." \
  --assigned-to either --review-at 2026-08-08T12:00:00Z
```

The command preserves a gate-reclassification timestamp and reason.
