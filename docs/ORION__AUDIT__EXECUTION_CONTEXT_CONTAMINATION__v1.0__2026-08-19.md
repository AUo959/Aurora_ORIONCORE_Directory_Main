# Execution-Context Contamination v1.0

**Date:** 2026-08-19  
**Layer:** L3  
**Status:** known defect class, partially remediated; three uncovered surfaces and confirmed artifact contamination  
**Extends:** `tests/test_devkit_execution_context.py`, `tools/aurora_devkit.py:600`  
**Repository:** `AUo959/Aurora_ORIONCORE_Directory_Main`

## This is not a new finding

The defect is already named, analysed, and tested in this repository. From
`tests/test_devkit_execution_context.py`:

> *"Devkit findings describe the machine the scan RAN ON, but nothing recorded which machine that was. Run from a sandboxed container, `gh is missing` was emitted as a blocker and surfaced by Mission Control as a P1 — a fact about the container presented as a fact about the workspace. The 2026-08-10 executive brief traced four of Mission Control's five P1s to exactly this... A checker whose loudest output is routinely wrong is worse than no checker: it trains people to scroll past P1s."*

The remediation asymmetry is deliberate and documented: detection is strict,
non-canonical contexts are demoted to warnings, because a demoted real problem
stays visible while a false canonical verdict lets a throwaway clone raise
blockers about its own tooling.

**What this record adds:** the class is wider than the devkit, the remediation
is not generalised, and it has already written false facts into tracked
artifacts.

## 1. Confirmed contamination of tracked artifacts — MEASURED

`git grep` for sandbox paths in committed content:

```
reports/analysis/aurora_devkit_latest.json
reports/simulation/hour_aboard_v1__2026-08-11/run_meta.json
reports/simulation/hour_aboard_v1__2026-08-15/run_meta.json
tests/test_devkit_execution_context.py          (the analysis itself — expected)
```

Two distinct sandbox session ids are embedded in tracked content:
`/sessions/abc/` and `/sessions/clever-ecstatic-meitner/`.

The committed `reports/analysis/aurora_devkit_latest.json` (2026-08-15) records:

| Field | Committed value | Reality on the owner's Mac |
|---|---|---|
| `root` | `/sessions/clever-ecstatic-meitner/mnt/Aurora_ORIONCORE_Directory_Main` | `/Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main` |
| `gh.status` | `missing` | `ok` |
| `gh.path` | `null` | `/Users/travisstreets/.local/bin/gh` |
| `gh.output` | `""` | `gh version 2.88.0` |
| `git.output` | `git version 2.34.1` | `git version 2.50.1 (Apple Git-155)` |

**A sandbox session's view of its own container has been the repository's
tracked record of the workspace toolchain for four days.** The severity demotion
works; the artifact still asserts the wrong machine as fact.

The corrected version — generated from a real-machine run — is currently
uncommitted in the working tree. It is one `git checkout` from being lost, or
one sandbox run from being overwritten again.

## 2. The remediation is not generalised — MEASURED

`is_canonical_workspace_context()` is defined at `tools/aurora_devkit.py:600` and
referenced in exactly two places: `aurora_devkit.py` itself and its test. No
other tool imports it.

Surfaces that produce execution-context-dependent findings without it:

| Surface | Symptom observed 2026-08-19 |
|---|---|
| `tools/workspace_verify.py` | *"Configured repos are unavailable in this execution context: ['.', '~remote~', '~sibling~/aurora_exhibit_site']"* — a warning, correctly, but the phrasing is hand-rolled rather than shared |
| `reports/simulation/**/run_meta.json` | records the sandbox path as run provenance, committed |
| Governance scanners (`zipwiz`, `threadcore`, `narrative-tone`) | returned `PASS` / `READY` when their roots did not resolve — the same "absence read as health" shape, fixed in this PR by independently reinventing the devkit's asymmetry |

The last row is the strongest evidence that the pattern recurs: the coverage gate
landed in this branch reaches the same conclusion the devkit reached in August,
by the same reasoning, without either knowing about the other.

## 3. The same pipeline corrupted this session's own reporting

Recorded because it is the clearest available demonstration, and because these
claims were relayed to the owner as findings before being tested:

| Claim made | Reality | Cause |
|---|---|---|
| *"the device mount refuses `chmod`"* (Addenda A–E) | `chmod -R a-w` is enforced | mount synthesises the mode bits it reports |
| *"no network egress for GitHub"* (Addendum C) | anonymous clone and `refs/pull/*` fetch both work | tested the REST API, not the git transport |
| *"`.git/index.lock` is stuck from the connectivity agent"* | it was GitHub Desktop's own, created at launch | inferred an owner from a timestamp |
| *"the other agent is rewriting `catalog/` mid-commit"* | the pre-commit hook self-heals regenerable surfaces by design | inferred a race from a diff |
| *"`repo_local_skills_not_installed`, 0 installed skills"* | the sync had been working; `~/.codex` is not visible from the mount | quoted a devkit finding produced under the very defect this record describes |
| `sweep_git.py` → *"0 repositories, 0 hits"* | bare clones have no `.git` directory | detection by directory name |
| *"the connected folder is the owner's Mac"* | the bridge shell runs in a Linux VM (Ubuntu 22.04, aarch64) with the Mac's folders mounted; `gh` is absent there and present on the Mac | conflated the mount with the host |

Seven instances in one session, all the same shape: **a property of the observing
context reported as a property of the observed system.**

## 4. Why this class is worse than an ordinary bug

An ordinary false finding is noise. This class is worse in three specific ways:

1. **It is louder than true findings.** Missing tooling reads as a blocker; a real
   but subtle defect reads as a warning. The 2026-08-10 brief's 4-of-5 P1 ratio is
   the measured version of this.
2. **It is durable.** The finding is written to a tracked artifact, committed, and
   then read by later tooling as input. `aurora_devkit_latest.json` feeds the
   pre-push gate.
3. **It is self-confirming.** The next sandbox run reproduces it, so the finding
   looks stable across runs — which reads as corroboration rather than as the same
   error repeated.

## 5. Recommendation

Ordered by cost.

1. **Commit the corrected `aurora_devkit_latest.json`** now, from the real-machine
   run currently sitting uncommitted. One commit; removes a four-day-old false
   record from the tracked state.
2. **Promote `is_canonical_workspace_context()` to `tools/_workspace_common.py`**,
   where the other workspace tools already share helpers. It is currently good
   analysis trapped in one module.
3. **Stamp every generated report with execution context** — canonical yes/no,
   plus the root it ran from — as a schema field rather than as prose in a
   finding. `reports/automation/skill_sync_latest.json` is the model: it records
   `dest` and a per-file change list, which is why its output is auditable.
4. **Treat `run_meta.json` provenance the same way.** A simulation run recorded
   against a sandbox path cannot be reproduced from its own metadata.
5. **Consider a pre-commit check** that refuses to stage a tracked report
   containing `/sessions/`. Cheap, and it makes the class self-arresting.

## 6. What this record does not claim

- **Not** that sandboxed execution is wrong. It is how this work gets done, and
  the same session produced the recovery, the audits, and this record.
- **Not** that the devkit fix is inadequate. The severity demotion is the right
  asymmetry and it works; the gap is generalisation and artifact provenance.
- **Not** that every finding quoted from a sandbox is false. Most are correct.
  The problem is that nothing in the artifact distinguishes which.
