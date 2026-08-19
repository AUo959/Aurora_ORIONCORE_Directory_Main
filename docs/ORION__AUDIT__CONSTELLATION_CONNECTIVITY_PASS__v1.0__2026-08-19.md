# Constellation Connectivity & Integration Pass — v1.0 (2026-08-19)

**Scope**: cross-repo connectivity between Aurora repos under `AUo959`.
**Method**: static audit of every local clone under `~/dev`, read against the
declared topology in `catalog/constellation-config.json`,
`catalog/repo_registry.yaml`, `catalog/repo_authority_policy.yaml`, and the hub's
`constellation-contracts/`.
**Branch**: `integration/connectivity-pass-2026-08-19` in four repos (root, hub,
spine, library).

---

## 0. Headline

The constellation is **wired but not conducting**. Every declared edge exists as a
workflow file, and **none of the event edges can currently deliver a valid
message**. Three independent defects each break the path on their own, and they
mask each other — the two live emitters fail schema validation at the hub, so the
hub's routing bug (an unbounded self-dispatch loop) has never had a chance to
fire. Fixing validation without fixing routing would have started that loop.

A second structural finding: the repo that `repo_authority_policy.yaml` names the
**control plane** was not a node. `Aurora_ORIONCORE_Directory_Main` had no
`.aurora/constellation.json`, no `repository_dispatch` surface of any kind, no
entry in its own `catalog/repo_registry.yaml`, and no entry in the hub's
health-audit list. It governed a topology it was not in.

---

## 1. Topology: intended vs. actual

| Node | Repo | Manifest at `.aurora/constellation.json` | Emits | Receives | Verdict |
|---|---|---|---|---|---|
| CONSTELLATION-PRIME | `aurora-cloudbank-symbolic` | present | router re-dispatch | `repository_dispatch` × 8 types | hub live, routing defective |
| QGIA-SPINE | `qgia-knowledge-spine` | present | 2 emitters (1 malformed, 1 valid) | none | emit-only, half-broken |
| QGIA-CORPUS | `qgia-knowledge-library` | present | 1 emitter, permanently gated off | none | **dead link** |
| AURORA-RUNTIME | `AuroraOS` | unverified (not cloned) | unknown | unknown | unverified |
| QUANTUM-VAULT | `cloudbank-quantum-en` | unverified (not cloned) | unknown | unknown | unverified |
| ZIPWIZ-ENGINE | `zip_wizard` | unverified (not cloned) | unknown | unknown | unverified |
| SENTINEL-COORDINATOR | `aurora-cloudbank-symbolic` | shares the hub's repo | — | — | manifest exists, no repo of its own |
| ORIONCORE-CONTROL | `Aurora_ORIONCORE_Directory_Main` | **was absent** | **none** | **none** | **was not a node at all** |
| — | `CanonRec` | absent | none | none | registered, outside topology |
| — | `DuelSim_v2.0` | absent | none | none | registered, outside topology |
| — | `aurora_exhibit_site` | absent | none | none | **not a git repo, unregistered** |

Four different definitions of "the constellation" were in play, none of them
equal: the hub manifest's `downstream` list (5 s.tags), the health auditor's
`REPOS` array (5 repos), the router's subscriber matrix (6 repos), and
`repo_registry.yaml` (9 entries). No single file was authoritative.

---

## 2. Findings

### F-1 — `qgia-knowledge-library` has never published to the hub  *(severity: high)*

`.github/workflows/constellation-knowledge-index.yml`, publish step:

```yaml
- name: Publish event to Constellation Hub
  if: success() && env.HAS_TOKEN == 'true'
  env:
    HAS_TOKEN: ${{ secrets.CONSTELLATION_TOKEN != '' }}
```

A step's own `env:` block is not visible to that step's `if:` — GitHub evaluates
the condition before the step environment is materialised. `env.HAS_TOKEN` reads
as the empty string, the condition is never true, and the step is skipped on
every run. The job goes green. QGIA-CORPUS has emitted nothing since this gate
was introduced.

**Patched**: `HAS_TOKEN` moved to job level; an explicit `::warning::` step now
fires when the token is genuinely absent, so an unconfigured link is loud rather
than invisible.

### F-2 — `spine-notify-hub.yml` emits a payload the hub must reject  *(severity: high)*

The workflow dispatched `{sha, ref, actor, committed_at, spoke_tag, contracts}`.
The hub's router validates every `client_payload` against
`constellation-event.schema.json`, whose `required` list is
`["event_type", "source_node", "timestamp", "payload"]`. **None of the four were
present.** `validate-event` failed on every push to spine `main`; `route-event` is
gated on `needs.validate-event.outputs.valid == 'true'`, so nothing routed.

Meanwhile `.aurora/constellation.json` has advertised
`"closed_loop_stage": "dispatch-live"` since 2026-06-08 and its
`"dispatch_event"` field said `spine-knowledge-update` — an event type that
appears in no workflow and no schema enum.

**Patched**: payload made schema-conformant; manifest corrected to
`qgia.knowledge.updated` and downgraded to
`dispatch-wired-pending-hub-verification` until a green hub run is observed.

### F-3 — duplicate emitter on the spine  *(severity: medium)*

`spine-notify-hub.yml` (push → main) and `constellation-knowledge-index.yml`
(push → main, path-filtered) both dispatched `qgia.knowledge.updated`. Any push
touching the filtered paths produced two hub events with different shapes and
different correlation IDs.

**Patched**: `constellation-knowledge-index.yml` owns the routine path;
`spine-notify-hub.yml` is now `workflow_dispatch`-only, retained as the manual
re-fire / recovery lever.

### F-4 — the reusable publisher never built its envelope  *(severity: high)*

`constellation-event-publisher.yml` — the workflow every spoke is supposed to
call — wrote its assembled envelope to `/tmp/event_envelope.json` and only ever
put `correlation_id` into `$GITHUB_OUTPUT`. The dispatch step read
`${{ steps.envelope.outputs.envelope || inputs.payload }}`, and since
`outputs.envelope` was always empty it always fell through to the raw caller
payload. `event_type`, `timestamp`, `correlation_id` and `provenance` were
computed and discarded on every call. Any spoke adopting the official publisher
would have been rejected by the hub exactly like F-2.

It also had no `source_node` input at all, despite `source_node` being a
required, enum-constrained schema field — the workflow could not have produced a
valid event even in principle.

**Patched**: envelope written to `$GITHUB_OUTPUT` via a heredoc delimiter;
`source_node` added as a required input and validated against the live schema
enum; the caller payload is nested under `payload` as the contract specifies; the
envelope is validated against the hub schema *before* a dispatch is spent; and
caller-controlled strings moved out of `run:` interpolation into `env:`
(script-injection hardening).

### F-5 — the router self-dispatches, unbounded  *(severity: high — latent)*

`constellation-event-router.yml` subscribes to eight event types and, for three
of them, listed `aurora-cloudbank-symbolic` — itself — as a subscriber:

```yaml
- event: qgia.knowledge.updated
  subscriber: aurora-cloudbank-symbolic   # the hub, routing to the hub
```

GitHub suppresses recursive workflow triggers only for events dispatched with the
built-in `GITHUB_TOKEN`. This routes with `secrets.CONSTELLATION_TOKEN`, a PAT,
so **suppression does not apply**. Each self-route re-triggers the router, which
self-routes again. This has never fired only because F-2 and F-4 mean no event
has ever passed validation.

**Patched**: self-routes removed (the hub consumes those events in-repo via
`constellation-knowledge-aggregator.yml`); a `Reject self-route` guard fails the
job if a self-referential matrix entry is ever reintroduced; a `hop` counter is
added to the schema and enforced with a limit of 3.

### F-6 — the control plane was not in the constellation  *(severity: high)*

`repo_authority_policy.yaml` rule `ROOT_CONTROL_PLANE_ALL_PROJECT_REPOS` makes
this repo authoritative for routing, registration and audit posture across all
project repos. It nonetheless had no `.aurora/constellation.json`, no
`repository_dispatch` trigger in any of its seven workflows, no self-entry in
`catalog/repo_registry.yaml`, and no line in the hub's health-audit `REPOS` array.

Compounding this: `catalog/constellation-config.json` — the file that *looks*
like this repo's node manifest — is actually the **QGIA-SPACE-NODE (Perplexity
Space)** manifest, `"repo": "perplexity-space-foreign-policy-global-politics"`.
It lives here but describes a different node, at a path the hub never reads.

**Patched**: `.aurora/constellation.json` created for `ORIONCORE-CONTROL`;
`constellation-health-respond.yml` added as the receive surface;
`ORIONCORE-CONTROL` added to the schema's `source_node` enum; the repo added to
the hub health-audit list, the router's `constellation.health.check` fan-out, and
its own registry.

### F-7 — the root `.gitignore` would have swallowed the manifest  *(severity: medium)*

`.gitignore` line 1 is `/*` — a deny-all allowlist. `.aurora/` was not
un-ignored, so a node manifest placed at the conventional path would have been
invisible to git and never published. The hub would have reported
`⚠️ Manifest not found` forever with the file sitting on disk.

**Patched**: `!/.aurora/` and `!/.aurora/**` added with a comment explaining why.

### F-8 — inconsistent action pinning across the constellation  *(severity: medium)*

The hub pins every action to a 40-char SHA. Spine and library used floating tags
(`peter-evans/repository-dispatch@v3.0.0`, `actions/checkout@v4.2.2`) — and the
action holding `CONSTELLATION_TOKEN`, a cross-repo PAT, was the least pinned
thing in the chain.

**Patched**: `repository-dispatch` pinned to `28959ce…` (v4.0.1) in spine and
library, matching the hub. `checkout` / `setup-python` in the spoke workflows are
still tag-pinned — see Deferred.

### F-9 — `aurora_exhibit_site` is published content with no version control  *(severity: medium)*

`~/dev/aurora_exhibit_site` has a `.vercel` project link and
`canon.html` / `forecast.html` / `index.html`, and **no `.git` directory at all**.
No history, no review path, no registry entry, no CODEOWNERS.

**Patched (registry only)**: registered as
`remote_status: not_a_git_repository` so the control plane stops being blind to
it. Initialising it is an owner decision — see Deferred.

### F-10 — registry entries carried no topology linkage  *(severity: low)*

`repo_registry.yaml` recorded paths and SHAs but nothing tying an entry to its
constellation node, so "registered" and "connected" could drift apart silently —
which is exactly what happened.

**Patched**: each entry gains a `constellation` block
(`node_designation`, `symbolic_tag`, `topology_role`, `manifest_path`,
`manifest_status`). Anything not `manifest_status: present` is an open gap by
construction.

### F-11 — the workspace scanner would have relocated the new manifest  *(severity: medium)*

Creating `.aurora/` made `tools/workspace_scan.py` classify it as an
`intake_collection` with `planned_path: intake/.aurora` and
`status: planned_move`. The hub fetches `.aurora/constellation.json` by exact
path from every node, so the next move wave would have quietly un-noded the
control plane again — the same class of failure as F-6, arriving by a different
route.

**Patched**: pinned in `catalog/classification_overrides.yaml` as
`control_surface` / `managed`, `planned_path: .aurora`, with the reasoning
recorded in the override's `notes`. Any node manifest added to this repo in
future needs the same treatment.

### F-12 — the registry erased its own annotations on every scan  *(severity: high)*

`catalog/repo_registry.yaml` is **generated** by `tools/workspace_scan.py`. The
generator rebuilt each locally-discovered entry from scratch and carried over only
entries marked `remote_status: remote_only`. Any owner-authored field on a local
repo's entry — and any entry for a path the scanner cannot walk as a nested git
repo, such as the root itself or a sibling directory — was silently dropped on
the next scan.

This was found the hard way: the F-10 `constellation` blocks and both new registry
entries were written, committed, and then destroyed by a routine
`workspace_scan.py` run in the same session. It is also the mechanical reason the
registry never carried topology linkage in the first place. Anyone who has ever
hand-edited this file has lost the edit without being told.

**Patched**: `workspace_scan.py` now merges three classes of surviving state —
`remote_only` entries (as before), entries whose `path` is not a discovered nested
repo (the root, `~sibling~/…`, anything not yet a repo), and owner-authored *keys*
on entries that are regenerated. Generated keys stay generated, so `branch` and
`head_sha` still track reality automatically; everything else is preserved.
Verified by re-running the scan and confirming all 11 entries and their
`constellation` blocks survive.

### F-13 — the nested workspace was not reconstructible  *(severity: medium)*

The five nested repos are ordinary working clones excluded by the root
`.gitignore` (`/*`, `/GUMAS_SIM_2.5/*`). Nothing in the tree recorded how to
recreate them: registry entries carried `remote_status: configured` but no
`remote_url`. A fresh clone of the control plane therefore produced a workspace
where five registry paths do not exist and the `repo_head_match` /
`repo_branch_match` gates cannot run at all.

**Patched**: `remote_url` added to all five local entries, and
`tools/registry_bootstrap.py` added (`make registry-bootstrap` /
`registry-bootstrap-check`) to clone each registered repo and check it out at its
pinned `head_sha`. The registry is now the operative link rather than a
description of one — and the pins it reads are the same pins
`tools/registry_sync_heads.py` writes, so this stays compatible with a later move
to submodules.

---

## 3. What was NOT verified

Remote-only checks could not be completed in this pass. Neither shell available
to the audit could reach `github.com`: the session's API token is scoped away
from these repositories, and the local mount has no network route. Chrome control
was available for navigation but not page reads.

Outstanding, all requiring a browser or a `gh`-authenticated shell:

- **Does `CONSTELLATION_TOKEN` exist in each spoke?** If it is missing from
  spine or library, F-1's new warning will now say so out loud — but the hub and
  the four uncloned repos are unchecked. A PAT is also the constellation's single
  point of failure and its expiry is unknown.
- **Do `AuroraOS`, `cloudbank-quantum-en`, and `zip_wizard` have
  `.aurora/constellation.json`?** The health auditor reports drift when a
  manifest is absent. Their registry notes say "not yet wired to constellation
  dispatch", which suggests no.
- **Actions run history.** F-1, F-2 and F-4 predict specific, repeated failures.
  The spine's router runs should show `validate-event` red; the library's publish
  step should show as skipped. Confirming this converts three static findings
  into observed behaviour.
- **Has `constellation-health-audit.yml` ever run?** Weekly since some point;
  its drift issues would be the fastest read on real topology state.
- **`zip_wizard`'s committed `.env`.** Already flagged in the registry from a
  2026-06-11 sweep and still open. If it holds a live `CONSTELLATION_TOKEN`, the
  cross-repo dispatch chain is compromised. Owner action — rotate, then purge
  from history.

---

## 4. Deferred (owner decisions, not patched)

| # | Decision |
|---|---|
| D-1 | `CanonRec` and `DuelSim_v2.0` are registered but have no node identity. Adopt as constellation nodes, or record as intentionally out of topology? |
| D-2 | `SENTINEL-COORDINATOR` has a manifest declaring `repo: aurora-cloudbank-symbolic` — the hub's own repo. Two designations, one repo. Give it a repo, fold it into CONSTELLATION-PRIME, or retire the manifest? |
| D-3 | `aurora_exhibit_site`: `git init` and publish under `AUo959`, or fold into an existing repo? It is currently the only Aurora surface with published content and zero history. |
| D-4 | `aurora-cloudbank-symbolic1` — single "Initial commit" Node skeleton, untouched since 2025-09-23, name-collides with the hub. Archive or delete. |
| D-5 | Nested repos are working clones, not submodules; `repo_registry.yaml` is the only pin. This pass made that pin operative (F-13) rather than replacing it. Adopt submodules for a git-native pin, or keep the registry mechanism and add a CI check that each recorded `head_sha` matches `origin/main`? The latter needs network access CI has and this audit did not. |
| D-6 | Pin `checkout` / `setup-python` to SHAs in spine and library to match hub policy — mechanical, but it touches workflows outside this pass's blast radius. |
| D-7 | `constellation_version` is `1.0.0-alpha` in every node manifest and the health auditor compares them for equality. Contracts were bumped to `1.1.0-alpha` (separate `VERSION` file) deliberately, so this pass does **not** trip the drift alarm. A real node-version bump needs to land in all nodes at once. |

---

## 5. Verification sequence (recommended order)

1. Push the four branches; open PRs. Do not merge yet.
2. In `qgia-knowledge-library`, run **QGIA Knowledge Index Publisher** manually.
   Expect either a successful hub dispatch or the new explicit missing-token
   warning — both are informative; silence is not.
3. In `qgia-knowledge-spine`, run **Spine → Hub Notify (manual)**. Watch the hub's
   `constellation-event-router` run: `validate-event` should pass for the first
   time.
4. Confirm the router's `route-event` matrix does **not** target the hub, and that
   `Reject self-route` did not fire.
5. In the hub, run **Constellation Health Audit** manually. The control plane
   should now appear in the report table instead of being absent from it.
6. Only then merge, and only in this order: hub (contracts and router first),
   then spine and library, then root.

Step 6's ordering matters: the spoke emitters now validate against the hub's
published schema at dispatch time, so the widened `source_node` enum must be on
the hub's `main` before the spokes rely on it.

---

## 6. Verification evidence

Run offline against the patched schema, so these results hold regardless of what
GitHub Actions later reports.

**Schema conformance** — every emitter payload replayed against the real
`constellation-event.schema.json` with `jsonschema`:

| Payload | Result |
|---|---|
| Old publisher output (the raw-payload fallthrough of F-4) | **FAIL** — `'event_type' is a required property` |
| Old `spine-notify-hub.yml` payload (F-2) | **FAIL** — `'event_type' is a required property` |
| Patched publisher envelope | PASS |
| Patched `spine-notify-hub.yml` payload | PASS |
| Patched library knowledge-index payload | PASS |
| New ORIONCORE `constellation.health.response` | PASS |

The two failures are the reproduction: they are what the hub's `validate-event`
job has been receiving. The publisher case was produced by running the workflow's
own `jq` pipeline, not by hand-writing the expected output.

**Workflow lint** — `actionlint 1.7.7` over all seven touched workflows
(root health-respond; hub publisher, router, health-audit; spine notify and
knowledge-index; library knowledge-index): **0 findings**.

**Repo gates** — `tools/workspace_verify.py`: `blocking_count: 0`. Three
pre-existing warnings remain and are untouched by this pass (`skill_sync` stale
codex target, `repo_registry_coverage` for placeholder paths, and
`session_state_freshness`).

**Registry durability** — `catalog/repo_registry.yaml` re-checked after a full
`tools/workspace_scan.py` run: 11 entries, all `constellation` blocks intact,
`branch` and `head_sha` correctly regenerated. This is the regression test for
F-12; before the fix, the same run destroyed them.

**Workspace reconstructibility** — `tools/registry_bootstrap.py --check`:
5 in sync, 6 skipped (placeholder paths and pins), exit 0.
