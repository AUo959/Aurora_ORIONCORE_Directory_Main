# Root hygiene disposition — 2026-09-24

## Baseline and scope

The cleanup branch starts at merged root PR #86, `cb52b48a23606a1ddbb773a52f7e99f2adb4b95d`.
It carries the completion handoff from `4880cae3` forward onto that baseline.
This change concerns root metadata and records; nested repository publication,
canon promotion, and runtime execution remain separate work.

## Dispositions

| Surface | Evidence and disposition |
|---|---|
| Workspace manifest, map, scan summary | Regenerated from the canonical checkout. The extra top-level entry is `.DS_Store`, classified as an ignored ephemeral cache. The cache itself is not published. |
| Relocation plan, aliases, wave-4 rollback | Regenerated using `workspace_plan_moves.py`. `ecguard_pr_body.md` and `recovery` remain proposals: `approved=false`, `applied_at=null`, aliases `pending`. Sources exist and destinations are absent. Publishing this plan does not approve or execute either move. |
| `recovery` proposal | Historical salvage audit identifies restoration bundles in this tree. Keep it in place; any later move requires a separate reference, backup, and rollback review. |
| Registry | The pre-existing local CanonRec pin `72f504b397a09cecc5e39250e9ae2cb7ea0f01f5` remains unstaged and byte-identical. Published registry still pins `4db0c2de8a43007c5950aca236b9211b23e7ad0b`. No nested commit is published by this cleanup. |
| Skill-sync report | Only its timestamp differed. Backed up the original and restored the committed report; fresh `make skills-check` found zero changes across 16 project skills. |
| Historical simulation directories | Verified all 36 SHA-256 values in [the existing evidence inventory](live_review_20260924/evidence.json). August 11/15 remain tracked; August 18/19 remain untracked, nine files each. Raw bytes and paths are unchanged. |

The August 18/19 `run_meta.json` records a pytest parent and a sandbox execution
context. These are historical test outputs, not current station-run evidence.
Classification is recorded here without rewriting provenance, adding exemptions,
rerunning a simulation, or treating the files as canon. A later archival change
must preserve the recorded hashes and explicitly review any consumers of the paths.

## Validation and remaining boundaries

The canonical workspace verifier reports zero blockers and three warning categories:
historical execution-context paths, remote-only registry coverage, and 29 overdue
queue items. `make devkit-check` has no install actions; it reports the existing
paused toolkit watcher and CloudBank Python-environment warnings. No automation
was resumed and no package was installed.

The two local simulation directories and the unpublished CanonRec registry edit
remain visible in Git status deliberately. They are classified holds, not a claim
that the checkout is clean. No relocation, branch deletion, or simulation advancement
was performed.

Original dirty files and both untracked directories were backed up under
`/private/tmp/aurora-root-cleanup-20260924/original/`, with SHA-256 inventory in
`original_hashes.json` alongside it. This temporary backup is a local recovery aid;
the original simulation files remain at their source paths.

## Follow-up — 2026-09-25 UTC

The owner authorized resolving the remaining holds. A fresh CanonRec fetch now
confirms local HEAD and `origin/main` both equal
`72f504b397a09cecc5e39250e9ae2cb7ea0f01f5`. The unpublished classification above
is superseded; the root registry pin was regenerated through
`tools/registry_sync_heads.py`. No nested push was needed.

The 18 August 18/19 files were moved, byte-for-byte, into
[the historical simulation archive](../../archives/historical_simulation_outputs/README.md).
Its manifest maps original paths to current locations and pins every byte count
and SHA-256. All hashes match the earlier evidence inventory. The two tracked
August 11/15 directories remain unchanged. No simulation ran, provenance was
not rewritten, and no execution-context exemption was added.
