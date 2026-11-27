# Backlog archive (GitHub issue migration, 2026-11-27)

These files preserve open GitHub issues from `AUo959/aurora-cloudbank-symbolic` and
`AUo959/Aurora_ORIONCORE_Directory_Main` that were moved into the root task queue
(`catalog/session_state.json` → `task_queue`, ids `gh-<repo>-<number>`) so the issues
could be closed without losing work.

Each `<repo>-<number>.md` holds, as of archive time:

- the issue metadata (URL, author, dates, labels, milestone);
- every pull request linked to or mentioned by the issue, with its state, head branch and head SHA
  (closed PR heads stay fetchable as `refs/pull/<n>/head`);
- branches named in the issue and whether they still exist on the remote;
- the original issue body and the full comment history, verbatim.

`manifest.json` is the machine-readable index of the same data.

To resume an item: read its archive file, then pick up the matching `gh-*` task-queue item.
Reopening the GitHub issue is always possible; the archive is the durable copy.
