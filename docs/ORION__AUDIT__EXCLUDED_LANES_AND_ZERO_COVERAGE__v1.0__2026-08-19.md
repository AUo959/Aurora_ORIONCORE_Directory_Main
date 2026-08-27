# Excluded Lanes and Zero-Coverage Governance v1.0

**Date:** 2026-08-19
**Layer:** L3
**Status:** defect demonstrated and fixed (§4a); lane disposition (§4b) still requires owner decision
**Repository:** `AUo959/Aurora_ORIONCORE_Directory_Main`
**Method:** every claim below was executed, not inferred. The zero-coverage result in §3 is a real run against a real empty directory.

## Executive finding

`ZIPWIZ_GOVERNANCE_RETURNS_PASS_ON_ZERO_COVERAGE`

Running the ZIPWIZ governance scanner against a **completely empty directory**
produces:

```
verdict              : PASS
promotion_readiness  : READY
total_artifacts      : 0
total_findings       : 0
exit code            : 0
```

Three canonical roots configured. None existed. Nothing was scanned. The report a
reviewer reads says *"Blocking Findings — None"*.

A fresh clone of this repository reproduces exactly this state, because **11 of
the 12 governance scan roots are excluded by `.gitignore` and exist in no
clone.**

## 1. The five content-excluded lanes

`.gitignore` is a root allowlist (`/*` plus explicit `!` entries). Five lanes are
present as directories but excluded as content:

| Lane | Files on disk | Size | Tracked |
|---|---:|---:|---:|
| `archives/` | 3,506 | 9.0 GB | 4 |
| `projects/` | 1,221 | 710 MB | 1 |
| `intake/` | 422 | 42 MB | 1 |
| `_staging/` | 120 | 1.3 MB | 5 |
| `repos/` | 1 | 4 KB | 1 |
| **total** | **5,270** | **~9.8 GB** | **12** |

Only `.gitkeep` and `README.md` are allowlisted in each. `archives/recovered_prototypes/`
is the sole exception — an existing committed-provenance lane created after a
prior salvage (`.gitignore:103`, *"salvage docket P7+"*).

## 2. Tracked code resolves paths into untracked lanes

Four tracked consumers hard-code twelve paths into excluded content:

| Tracked consumer | Paths into excluded lanes |
|---|---:|
| `skills/aurora-governance-orchestrator/scripts/orchestrate_governance.py` | 6 |
| `skills/zipwiz-governor/scripts/zipwiz_rules.py` | 2 |
| `skills/aurora-narrative-tone-governor/scripts/narrative_tone_scan.py` | 2 |
| `.gitleaks.toml` | 2 |

**All twelve resolve on this disk. None is in git. 12/12 would be absent from a
fresh clone.** `skills/threadcore-governor/scripts/threadcore_rules.py` adds two
more.

Of the twelve fallback scan roots across these skills, exactly one —
`GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19`, 13 files — is tracked.

## 3. The failure is silent, not loud

`zipwiz_rules.py:114`:

```python
def _iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists() or not root.is_dir():
        return []          # <- missing root contributes nothing, reports nothing
```

The scanner does not crash on a missing root. It scans zero files and passes.
`scan_meta.roots` does list the paths it was *given*, so the evidence is in the
JSON — but nothing compares configured roots against roots that exist, and
neither the verdict, the summary, nor the markdown report reflects the
difference.

### Not all four skills were affected — corrected

An earlier draft of this record implied all four governance consumers shared the
defect. **They did not.** `aurora-governance-orchestrator` was tested against the
same empty directory and returns:

```
status     : BLOCKED
confidence : low
BLOCK rules: B_SCAN_EXECUTION_FAILED, B_SCAN_ROOTS_UNRESOLVED
```

It already encodes the correct behaviour — `B_SCAN_ROOTS_UNRESOLVED` is raised
with `blocking_scope: execution_health` and forces confidence to `low`. The
orchestrator is the model; three leaf scanners diverged from it. Someone had
already solved this at the orchestration layer.

| Skill | Empty-directory behaviour before | After |
|---|---|---|
| `zipwiz-governor` | `PASS` / `READY` | `NO_COVERAGE` / `UNKNOWN` |
| `threadcore-governor` | `PASS` / `READY` | `NO_COVERAGE` / `UNKNOWN` |
| `aurora-narrative-tone-governor` | `PASS` / `READY` | `NO_COVERAGE` / `UNKNOWN` |
| `aurora-governance-orchestrator` | **`BLOCKED` / `low`** | unchanged — was never affected |

**This is the same defect shape as four other things found in this corpus:**

| Site | Empty result presented as a clean result |
|---|---|
| The 2026-02-15 dedup manifest | basename match reported as content identity |
| `sweep_git.py` (this session's own tooling) | bare repos → *"0 repositories, 0 hits"* |
| `GUMASEngineV3` | `ImportError` → fabricated state, one log line, no caller checks |
| `build_qforge_ops_report.py` | base engine unrecorded; three different runs indistinguishable |
| **ZIPWIZ governance** | **zero roots → PASS / READY** |

Each was independently introduced. The pattern is the finding.

## 4. Proposed dispositions

Ordered by evidence, not by lane size.

### 4a. Fix the reporting, not the exclusion — **DONE 2026-08-19**

Coverage is not the same as compliance. A scanner that inspected nothing must not
return `PASS`.

Implemented in the three affected scanners:

- `scan_meta.coverage` now carries `roots_configured`, `roots_resolved`, and
  `roots_missing`.
- `roots_resolved == 0` yields verdict `NO_COVERAGE` and readiness `UNKNOWN`.
- The ZIPWIZ markdown report opens with an explicit **NO COVERAGE** callout, or a
  partial-coverage line when some roots resolve.

Verified:

| Check | Result |
|---|---|
| Empty directory, all three scanners | `NO_COVERAGE` / `UNKNOWN` |
| Populated repo, ZIPWIZ | `REVIEW` / `CONDITIONAL`, 187 artifacts, 139 findings, roots 3/3 and 2/2 — unchanged |
| Populated repo, narrative-tone | `BLOCK` / `NOT_READY`, 37 files, 196 findings, roots 4/4 — unchanged |
| `zipwiz-governor` suite | 23 tests OK (20 existing + 3 new regression tests) |
| `threadcore-governor` suite | 13 tests OK |
| `aurora-governance-orchestrator` suite | 8 tests OK |

The three new tests assert that absent roots yield `NO_COVERAGE`, that a resolved
root with no findings still passes, and that partial coverage is reported without
being downgraded.

Additive only. No finding path, rule, or severity was changed.

### 4b. The exclusion is correct — the system already decided this

An earlier draft of this record proposed adding committed sub-lanes to
`archives/` and `projects/`. **That proposal is withdrawn.** The workspace already
resolves this question, in three places, and resolves it the other way:

| Authority | What it says |
|---|---|
| `catalog/repo_authority_policy.yaml` | root repo `role: control_plane`, `scope: all_project_repos`. `NESTED_REPOS_KEEP_SOURCE_HISTORY_AUTHORITY`; `LOCAL_CLONES_ARE_NOT_AUTHORITATIVE` |
| `tools/workspace_verify.py:379` `verify_gitignore` | asserts by probe that `projects/`, `archives/`, `intake/`, `_staging/`, `repos/` content **stays ignored** — *"so workspace content zones and nested repos remain untracked at the root level"* |
| `.gitignore:103` | the one sanctioned exception, `archives/recovered_prototypes/`, *"committed provenance (salvage docket P7+)"* |

The exclusion is deliberate, documented, and enforced by a tracked test. Adding
sub-lanes would trip `verify_gitignore`. The frozen GUMAS package went into
`archives/recovered_prototypes/`, which is the exception the policy already
carves out — that placement was correct and needs no new lane.

**The residual finding is real, and it is a different one.**

`catalog/repo_authority_policy.yaml` rule `REGISTRATION_REQUIRED_FOR_AUTOMATION_SCOPE`:

> *"Repos must be registered in `catalog/repo_registry.yaml` before automation or audit treats them as in-scope."*

Checked against the registry (11 entries):

| Governance scan root | Registered? |
|---|---|
| `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging` | **no** |
| `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents` | **no** |
| `projects/GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0` | **no** |
| `projects/GUMAS_SIM_2.0/03_SIMULATION/Location_Data/Sim_Locations` | **no** |
| `projects/Aurora_Project_Cloudhub_Deploy` | **no** |
| `projects/GUI_Cloudhub` | **no** |

Three governance skills default their scan roots into **deliberately
non-authoritative local content that the policy says automation must not treat
as in-scope.** That is the inconsistency — not the exclusion.

Two dispositions, both already expressible in the existing system:

1. **Register the corpora** in `catalog/repo_registry.yaml`, which is what
   `REGISTRATION_REQUIRED_FOR_AUTOMATION_SCOPE` prescribes for anything
   automation should scan. `aurora-cloudbank-symbolic-main` and `CanonRec` are
   already registered this way.
2. **Or re-point the skill defaults** at registered repos, so governance scans
   authoritative baselines rather than working directories.

Either way the §4a coverage reporting is what makes the choice visible: a scan
against an unregistered, absent root now says `NO_COVERAGE` instead of `PASS`.

### 4c. Stale manifest references — separate, smaller finding

`catalog/workspace_manifest.yaml` and `catalog/classification_overrides.yaml`
reference `intake/` paths that do not exist (`intake/.aurora`,
`intake/Aurora_Sim_Architecture`, `intake/recovery`, `intake/warrant-lens`, and
others). Tracked config pointing at absent untracked content — the same shape,
lower stakes. Worth a pass, not urgent.

## 5. What this does not claim

- **Not** that the excluded lanes should be committed. That was proposed in an
  earlier draft and is withdrawn: `tools/workspace_verify.py` asserts the
  exclusion, and `repo_authority_policy.yaml` explains why.
- **Not** that the governance skills are broken. They work; they report coverage
  they did not have.
- **Not** that data has been lost from these lanes. That was not tested here.
  The GUMAS case is the only measured loss, and it was recoverable.

## 6. Recommended sequence

1. ~~**4a** — coverage reporting.~~ **Done.** Three scanners fixed, one was
   already correct, 44 tests green.
2. **4b** — register the six governance scan roots in
   `catalog/repo_registry.yaml`, or re-point the skill defaults at registered
   repos. The exclusion itself is correct and stays.
3. **4c** — reconcile the `catalog/` manifests against what exists.

Nothing here was changed. The scanner run in §3 wrote only into a temporary
directory; no repository file was modified.
