# Aurora / ORIONCORE Codex Operating Instructions

## Mission

You are operating inside the Aurora / ORIONCORE ecosystem.

Improve the system without damaging:

- canon authority
- layer boundaries
- reproducibility
- auditability
- symbolic continuity

Optimize for coherence, evidence, and maintainability over cleverness.

## Scope: Root Control Plane

This repository is the root control-plane repo for
`Aurora_ORIONCORE_Directory_Main`. It does not replace the nested implementation
repos.

Named repos for this workspace:

- `root`
  - this repo
- `aurora-cloudbank-symbolic-main`
  - `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `CanonRec`
  - `GUMAS_SIM_2.5/CanonRec`
- `DuelSim_v2.0`
  - `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`

Authoritative nested-repo paths live in `catalog/repo_registry.yaml`.

## Repo Authority Model

The root repo governs repo-management policy, routing, registration, and audit
posture for all Aurora / ORIONCORE project repos. It does not replace the
source-history authority of those repos.

Default authority rules:

- the root repo is the control plane for the whole project workspace, not only
  the repos currently registered today
- a nested repo checkout is a working clone, not an authoritative source merely
  because it exists on disk
- for a named repo, the published GitHub branch, normally `origin/main`, is the
  source-history baseline unless an explicit publication flow says otherwise
- local-only nested-repo work is `draft` or `local` state until committed and
  pushed
- `catalog/repo_registry.yaml` is the machine-readable list of repos currently
  registered for automation and audit; it is not the eternal definition of the
  whole project
- if a project repo belongs in the workspace but is missing from
  `catalog/repo_registry.yaml`, treat that as a control-plane registration gap,
  not permission to improvise around the boundary

If a request says only "the repo" and multiple repos are plausible:

- ask one short clarification question

## Workspace Topology

This root repo is metadata-first. It primarily tracks workspace docs, manifests,
policies, reports, and tooling.

Top-level control or routing zones include:

- `archives/`
- `catalog/`
- `docs/`
- `intake/`
- `projects/`
- `reports/`
- `repos/`
- `tools/`
- `_staging/`

Important path hazard:

- `Aurora_Sim_Architecture/` at the root is cataloged as an intake collection
  planned to move
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` resolves to the
  root repo, not the registered nested repo boundary
- the authoritative nested Git repo is
  `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`

Do not infer repo boundaries from similar names alone. Check
`catalog/repo_registry.yaml` and confirm with `git rev-parse --show-toplevel`
before doing nested-repo work.

## Authority Order

If rules, status, or canon are unclear, prefer evidence in this order:

1. committed canonical files in the relevant repo
2. manifests, registries, schemas, trust anchors, and validation artifacts
3. deterministic reports and receipts
4. human-facing docs
5. summaries, notes, or conversational context

Never silently promote draft, recovered, staged, or generated material into
canonical truth.

If a proposed change alters canon behavior or lifecycle state, make that explicit
in your summary.

## Constitutional Rules

### 1) Canon Authority Is Absolute

If a rule, interface, or status is unclear:

- prefer committed canonical files over summaries
- prefer manifests, schemas, registries, and validation artifacts over prose
- do not silently upgrade draft material into canonical truth

### 2) Preserve Layer Boundaries

Treat these layers as distinct unless the task explicitly says otherwise:

- control plane / workspace governance
- runtime / orchestration
- simulation or forecast engine
- knowledge / corpus
- archive / staging / intake

Do not move logic across layers merely for convenience.

### 3) No Mythology as Substitute for State

Symbolic or narrative language is allowed, but implementation must cash out in:

- files
- schemas
- receipts
- tests
- manifests
- versioned artifacts

When in doubt, convert narrative claims into machine-checkable structure.

### 4) Evidence Over Assumption

Do not claim a subsystem is `active`, `live`, `complete`, `validated`, or
`canonical` unless the repo contains concrete evidence.

When evidence is missing:

- say so
- leave a TODO or validation hook if appropriate
- do not invent current-state truth

### 5) Do Not Silently Delete Ambiguity

If the workspace contains competing states or contradictory documents:

- do not erase one side without recording the resolution path
- prefer status marking over destructive cleanup
- use labels such as `draft`, `staged`, `active`, `superseded`, `canonical`

### 6) Preserve Backward Meaning Where Possible

Do not rename core concepts casually. High-sensitivity terms include:

- `canon`
- `anchor`
- `trust`
- `relay`
- `drift`
- `THREADCORE`
- `Picard_Delta_3`
- `L1` / `L2` / `L3`
- `constellation`
- `runtime`
- `control plane`

If renaming is necessary:

- explain why
- update references consistently
- avoid partial migrations

## File Classes and Edit Policy

Before changing anything substantial:

- identify which repo and layer you are in
- identify whether the target is source, generated output, report, or attached
  artifact
- avoid editing generated artifacts unless the task explicitly requires it

In this root repo, treat these as generated control surfaces unless the task is
specifically about repairing them:

- `catalog/workspace_manifest.yaml`
- `catalog/repo_registry.yaml`
- `docs/workspace-map.md`
- `catalog/relocation_plan.json`
- `reports/analysis/workspace_verify_latest.json`

Preferred regeneration paths:

- `python3 tools/workspace_scan.py`
- `python3 tools/workspace_plan_moves.py`
- `python3 tools/workspace_verify.py --persist-report`

Persistent non-default classification belongs in
`catalog/classification_overrides.yaml`. Do not hand-edit the generated manifest
to force routing.

The root workspace currently also contains loose recovered or attached artifacts
such as `text_*.txt`, PDFs, and one-off analysis batches. Treat those as intake,
evidence, or derived materials unless a manifest or explicit task promotes them.
Do not treat them as canonical just because they sit at the root.

Any generated file should identify:

- generator or source
- timestamp
- version
- whether it is authoritative or derived

## Simulation and Diagnostics Discipline

For simulation, forecast, or engine work:

- distinguish run modes explicitly
- preserve determinism unless the task explicitly changes it
- keep counters, formulas, and event handling auditable
- surface drift instead of normalizing outputs by hand

Where relevant, preserve or add fields such as:

- `run_mode`
- `runtime_state`
- `event_pipeline_mode`
- `turn_range`
- `run_id`
- `parent_run_id`
- `counters_scope`

Never let a bulk diagnostic or replay artifact masquerade as a live runtime
report.

At the root-control-plane layer, avoid framing Aurora as `simulation as
product`. Use simulation language precisely for `L2`; keep higher-level posture
aligned to forecast, governance, and auditable decision support.

## Validation and Receipts

Every meaningful change should leave a receipt where appropriate, such as:

- validation output
- schema checks
- manifest updates
- status markers
- report metadata
- timestamps
- checksums or version fields

Prefer machine-checkable truth over prose-only truth whenever practical.

Supported root verification commands:

- `python3 tools/workspace_scan.py`
- `python3 tools/workspace_plan_moves.py`
- `python3 tools/workspace_apply_moves.py --batch-id <batch_id>`
- `python3 tools/workspace_verify.py`
- `python3 tools/workspace_verify.py --persist-report`
- `python3 tools/workspace_verify.py --report-out /tmp/workspace_verify.json`
- `python3 tools/workspace_verify.py --check-determinism --exercise-relocation`

`python3 tools/workspace_verify.py` is side-effect free by default. The
pre-commit hook uses `python3 tools/workspace_verify.py --git-pre-commit`.

Do not delete duplicates directly. Quarantine or plan the move first, verify
hashes, and preserve a recovery path before any hard delete.

Do not restore `.git_decommissioned_*`; those directories are rollback artifacts
only.

## Git and Worktree Discipline

Root and nested repos have separate Git boundaries, remotes, and publication
decisions.

- publishing the root repo does not publish nested repos
- root governance does not make a nested local checkout authoritative
- do not add or change nested repo remotes unless the user names the target repo
- prefer SSH over HTTPS
- prefer `origin` as the primary remote name
- prefer private GitHub repos unless the user explicitly says otherwise
- never assume "everything is synced" just because the root repo has a remote
- do not treat local-only nested-repo changes as published project state until
  they are committed and pushed to the repo's GitHub baseline
- before automation or audit treats a repo as in-scope, register it in
  `catalog/repo_registry.yaml` or record the registration gap explicitly

Project-owned GitHub skill:

- `skills/gitwiz-github-manager/`

Use it for:

- remote setup
- SSH-first auth flow
- local-vs-remote sync audits
- PR packet drafting
- safe branch publication
- backup-before-force replacement of bootstrap remote history
- named nested repo publishing

In Codex worktrees, root pre-commit validation may fail if it expects nested
repo paths that exist only in the canonical workspace path. Treat that as an
environment-path issue first, not automatic content failure.

Use `--no-verify` only when:

- the failure is clearly due to worktree path mismatch
- the user still wants the commit

## What Persists Across Threads

These persist on this machine:

- repo state on disk
- Git remotes on disk
- SSH keys and SSH config in `~/.ssh/`
- committed project files
- locally installed Codex skills in `~/.codex/skills/`

These do not persist automatically:

- conversational memory
- intent from prior threads unless it is written into repo files or local skill
  files

Only tracked, committed, and pushed content in the target repo syncs to GitHub.
Local machine state such as `~/.codex/skills/...` does not.

If a fact should survive thread changes, write it into one of:

- `AGENTS.md`
- `README.md`
- versioned skills under `skills/`
- machine-readable repo metadata under `catalog/`

Do not rely on conversational carry-over.

## Communication Style

Report in operational language. At the end of a task, summarize:

- what changed
- why it changed
- what evidence supports it
- what remains uncertain
- what should be validated next

Be explicit about uncertainty. Prefer phrases such as:

- `confirmed by file X`
- `inferred from manifest structure`
- `not verified in this repo`
- `likely a run-mode mismatch`
- `requires canonical promotion`

Do not overclaim.

## Preferred Outcome

The ideal Codex contribution does at least one of the following:

- strengthens canon authority
- sharpens a boundary
- converts prose into contract
- improves validation
- reduces drift
- clarifies lifecycle state
- preserves continuity while enabling change
