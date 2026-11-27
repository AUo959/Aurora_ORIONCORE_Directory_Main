# aurora-cloudbank-symbolic#1504: Outside review: agent-legibility strengths, regrowth-prone sprawl, and a ratchet-first roadmap

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1504
- State at archive: open
- Author: AUo959
- Created: 2026-08-11T04:13:39Z
- Updated: 2026-09-14T09:17:31Z
- Labels: documentation, stale, audit, repo-hygiene
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#33 — deps: bump plotly from 5.22.0 to 6.2.0 — merged — `dependabot/pip/plotly-6.2.0` @ `eb1277fead910266121d0128028d125e6170df3d`
- aurora-cloudbank-symbolic#46 — deps: bump dotenv from 17.0.0 to 17.0.1 — closed — `dependabot/npm_and_yarn/dotenv-17.0.1` @ `71b5dfce8e55d94042850236ccd674aa4cb6f213`
- aurora-cloudbank-symbolic#47 — deps: bump dotenv from 17.0.0 to 17.1.0 — merged — `dependabot/npm_and_yarn/dotenv-17.1.0` @ `eb9f426ea72b2f4a995ea25bebb92b675b637820`
- aurora-cloudbank-symbolic#1343 — feat: add the triggered Narrative River scene workflow — merged — `agent/narrative-river-adapter-spec` @ `24d2b3f396eb3d338abd24e7156352b4d7987bdb`
- aurora-cloudbank-symbolic#1381 — feat(continuity): add neutral Universal Thread Beacon schema and offline validator — merged — `feat/1377-utb-neutral-schema` @ `83dcf25f8e092e8295b76f1302a30fd955e54710`
- aurora-cloudbank-symbolic#1476 — fix(ci): make the SonarCloud reporter answer why the gate failed — merged — `claude/cloudbank-issues-prs-0dvl1n-sonar-reporter` @ `5a21152ee5e38ff039c39ddb8c9e7c97d515a13b`
- aurora-cloudbank-symbolic#1482 — feat(l1): bind deterministic fleet runtime — merged — `codex/cloudbank-issue-1481-l1-fleet-runtime` @ `b07de9eb8b0fb195ad1e7dbcd0aedef5b919df39`
- aurora-cloudbank-symbolic#1487 — fix(ops): reconcile gate registry projection — merged — `codex/cloudbank-issue-1446-gate-registry-coherence` @ `b0c96de3f33b0b1fade708964b67ef3e0798e5dc`
- aurora-cloudbank-symbolic#1488 — fix(repo): unify QGIA path casing — merged — `codex/cloudbank-issue-1424-qgia-casefold-hygiene` @ `7beef42377f2c7cba44523713b9394d08fdd4b97`
- aurora-cloudbank-symbolic#1492 — aurora(queue): record gate escalation surfacing — merged — `queue/escalation-surfaced-20260810-0655` @ `f78a960395bd85d20e000a6772c66dbaaa2ed099`
- aurora-cloudbank-symbolic#1500 — fix(l1): harden restored fleet authority evidence — merged — `codex/cloudbank-issue-1481-postmerge-1482-hardening` @ `18dc169d9c17b8068aa58622e5043e6c46266cd9`
- aurora-cloudbank-symbolic#1501 — feat(l1): add governed staffing runtime — merged — `codex/cloudbank-issue-1453-l1-staffing-runtime` @ `b27ecb7138f06c38a90eabd46c6caea33daf6f7d`
- aurora-cloudbank-symbolic#1502 — feat(characters): add identity continuity registry — merged — `codex/cloudbank-issue-1457-character-identity-provenance` @ `aaf4e23bb8c28bf7c205461283429e42691c4469`
- aurora-cloudbank-symbolic#1503 — fix(l1): reject reactivated locus claims — merged — `codex/cloudbank-issue-1456-locus-conflict-validation` @ `d5ee0bcf8ef8215ebea668e5f9bb908f32a2b994`
- aurora-cloudbank-symbolic#1509 — feat(ci): declaration gate for root objects and dependency-file set (#1504) — merged — `codex/cloudbank-issue-1504-declaration-gates` @ `00f30c0143aa98f1336323df4dbb335374f2341f`
- aurora-cloudbank-symbolic#1511 — feat(contracts): OPAL2 shipment-manifest schema with worked example (#1510) — merged — `codex/cloudbank-issue-1510-shipment-manifest` @ `86fde15158c5b5b02dc904c2f9d469f397c1df82`
- aurora-cloudbank-symbolic#1512 — docs(opal2): complete shipment-manifest checklist path — merged — `codex/cloudbank-issue-1510-shipment-checklist-closeout-20260815` @ `8103f45e57eb4e0054fe89afb489e8ae63720891`
- aurora-cloudbank-symbolic#1513 — docs: record AI-assisted authorship provenance — merged — `codex/cloudbank-issue-1504-ai-authorship` @ `42d7bf7234801c4aff4c92bb9aaaaf0a8eedb9d0`
- aurora-cloudbank-symbolic#1514 — ci: enforce root declaration in pre-commit — merged — `codex/cloudbank-issue-1504-root-declaration-precommit` @ `742ff7270339d9b4568389279df4fae9a18aacbd`

## Branches named in the issue

- none

## Original body

## Outside Review — Aurora CloudBank Symbolic

**Reviewer:** External agentic-model review (Kimi K3 persona), commissioned by the maintainer
**Date:** 2026-08-11
**Method:** Live GitHub API audit of repository structure, commit history (Apr 2025 → Aug 2026), open issues, and open PRs. Every claim below was verified against live data; an initial draft was self-audited and corrected before filing.
**Scope:** Architecture-and-process review. This is not a line-level code audit.

---

## Executive summary

Aurora CloudBank Symbolic is one of the most agent-legible repositories this reviewer has encountered: a full onboarding curriculum for AI assistants (`CLAUDE.md`, `COPILOT_INSTRUCTIONS.md`, `AGENTS.md`, toolset manifests), genuinely fail-closed safety semantics, and CI depth above most production repos. Its primary structural weakness is not architectural confusion but **regrowth**: the repository has been consolidated before (requirements 7→3, Oct 2025; 909 files removed the same day) and the sprawl returned (nine requirements files today; `ops/` + `operations/`; `extracted_aumemmanager/` + `extractions/`). The fix is not another cleanup — it is fences.

Overall assessment: **7.4/10** — ambitious, governed, sprawling; prune once, then ratchet.

---

## What the git history shows (four seasons)

1. **Germination (Apr 2025):** repo created Apr 9, 2025; five consecutive "Add files via upload" commits in an 8-minute window. Root sprawl is sediment from this informal origin — a laboratory, not negligence.
2. **Greenhouse (mid–late 2025):** ceremonial commit culture (thread anchors, memory seals, persona-authored commits by `Aurora CloudBank <aurora@cloudbank.dev>`). This culture is the direct ancestor of today's hash-verified authority receipts — the ritual became the protocol.
3. **First weeding, then winter (Oct 2025 – Feb 2026):** requirements consolidated 7→3 with a written report; 909 files / 25MB removed; then on **2026-02-09 a deliberate reset** disabled essentially every workflow via `if: false` (CodeQL, Codacy, code-quality, auto-labeler, deploy-pages, symbolic-bundle, agent runner).
4. **Disciplined garden (May–Aug 2026):** conventional commits, Codex-authored PR branches, drift-threshold stratification wired into the PR template, MCP connector scaffold, and a fully gated merge pipeline (13 gated merges in 8 minutes on 2026-08-11). PR numbering: ~#33 in Jun 2025 → #1500+ now.

---

## Strengths (verified)

- **Agent legibility (9/10):** CLAUDE.md (41KB), COPILOT_INSTRUCTIONS.md (15KB), AGENTS.md, `.copilot-bash-profile`, `aurora_copilot_toolsets.jsonc`, `ARCHITECTURE_QUICKMAP.md`, `CANON_INDEX.md`. An agent can ingest the entire instruction stack in one pass and be immediately operational.
- **Fail-closed safety posture (9/10):** #1482 promoted the L1 fleet runtime only after full CI/CodeQL/PR-evaluation/authority-hardening validation; hash-verified authority receipts; identity metadata pinned to receipts; legacy v1.1 payloads rejected rather than coerced; ORD adapter state restricted to ORD assets.
- **CI/CD & supply chain (8.5/10):** CodeQL, SonarCloud, Bandit, flake8, pylint, pre-commit, pip-audit with hashed requirements, grouped dependabot. The SonarCloud reporter now degrades correctly (#1476) — good failure engineering.
- **Canon/provenance rigor:** typed population semantics (#1455), identity provenance and alias supersession (#1457, PR #1502), reproducible seeds with a canon-promotion boundary (#1458), and CanonRec correctly split out as an external reconciliation authority.

## Findings (verified, with corrections applied)

1. **Regrowth, not neglect.** Nine requirements files at HEAD (`requirements.txt`, `-dev`, `-test`, `-optional`, `-lock`, `-hashed`, `-ci-hashed`, `-opal2.txt`, `-opal2.lock`) despite the documented 7→3 consolidation of Oct 2025. Duplicate directory pairs persist: `ops/` + `operations/`, `extracted_aumemmanager/` + `extractions/`. (Correction: `QGIA_Integration`/`QGIA_integration` casing duplication was **resolved** by #1488; an earlier draft of this review claimed otherwise from a stale ref.)
2. **#1477 is the highest-leverage fix in the tracker.** `SONAR_TOKEN` is 401-unauthorized. Analysis and pass/fail gates still work (Automatic Analysis); what is broken is CI's ability to ask *why* a gate is red — and **#1381's gate has been red since 2026-07-28 and is blocked on this**. It is an owner-only secret rotation, currently open and assigned.
3. **Long-open PRs are blocked, not rotting — but the queue should say so.** #1343 (Narrative River, 673 comments, active 2026-08-11) carries a `ci: failed` label; #1381 is blocked on #1477. The gating philosophy is enforced at merge time; the *surfacing* of blocked state is manual.
4. **Planning-burst artifact drops.** 13 issues (#1368–#1380) were filed in a 20-minute window on 2026-07-28; none have been updated since. The tracker functions partly as a write-mostly store.
5. **Six deployment surfaces with no declared primary:** Vercel, Replit, devcontainer, k8s, docker-compose, GitHub Pages.
6. **Workflow tombstones.** If any workflows disabled via `if: false` on 2026-02-09 remain dead-by-flag rather than rebuilt or deleted, they are sprawl of a second kind.
7. **Agent authorship is real but unstated.** Commit cadence (24 commits in ~3 hours; 13 merges in 8 minutes) indicates heavy agent orchestration under a single human committer. The project applies provenance discipline to simulation state; the code itself deserves the same standard.

---

## Roadmap (ratchet-first, in dependency order)

### Phase 0 — Unblock the queue (owner-only, ~30 min)
- [ ] **Fix #1477:** rotate `SONAR_TOKEN` (SonarCloud Account → Security, scoped to `AUo959_aurora-cloudbank-symbolic`), replace the repo secret, then dry-run the reporter against #1381 (`Actions → SonarCloud Issue Reporter → pull_request_number: 1381`). Acceptance criteria are already written in #1477.
- [ ] Unblock #1381 once its failing rule is identifiable; land or close it.
- [ ] Land or close #1343 (Narrative River) — it is active and close; the `ci: failed` gate is the only blocker.

### Phase 1 — Install the fences (the core of this review)
- [ ] **Root-file allowlist check:** CI fails any PR that adds a root-level file or directory not on an explicit allowlist. Model it on the casefold guard from #1488 (nine hardening iterations already proven in production).
- [ ] **Requirements-count gate:** CI fails if the number of `requirements*.txt/.lock` files at root exceeds the declared set; new dependency files require an exemption comment.
- [ ] **Workflow tombstone sweep:** for each workflow disabled via `if: false` (2026-02-09), either rebuild it properly or delete the file. No dead-by-flag workflows.
- [ ] **Blocked-state surfacing:** extend the queue/gate registry work (#1487, #1492) so blocked PRs (failed gate, blocked-by-issue) are labeled and reported automatically, not discovered by reading comment threads.

### Phase 2 — One consolidation pass (only after fences exist)
- [ ] Merge `ops/` and `operations/` into one tree; same for `extracted_aumemmanager/` and `extractions/`.
- [ ] Re-run the requirements consolidation (9 → 3–4), citing the Oct 2025 report as precedent; the hashed/CI-hashed/opal2 lock files may be legitimately distinct — document which are load-bearing.
- [ ] Declare one primary deployment target; demote the rest to `deployment/experimental/` with a README stating status.

### Phase 3 — Provenance and tracker hygiene
- [ ] **AI_AUTHORS.md** (or per-subsystem provenance notes): state plainly that agent assistants author substantial portions of the codebase under maintainer direction. This is a strength — document it like one.
- [ ] Triage the 2026-07-28 planning-burst issues (#1368–#1380): label as backlog/epic, convert to a single tracking epic, or close with rationale. A tracker that is partly a write-mostly store undermines the gate discipline everywhere else.
- [ ] Ship the distilled context pack: the multi-MB GUMAS knowledge bundles are ideal for 1M-context models but punitive for smaller-context assistants. A ≤200KB distilled pack alongside the full bundles would widen the contributor pool.

### Phase 4 — Strategic (already tracked, endorsed by this review)
- [ ] **#1380 (execution-default-off controls)** before shipping more agent-facing runtimes such as the L1 staffing runtime (#1501). Execution-default-off should be the whole project's motto, not one issue's.
- [ ] **#1459 (SHERLOCK/WATSON evidence-to-understanding product)** — a good lane; neutral evidence handling complements the provenance work.

---

## Closing note

The arc from "Add files via upload" at 3 AM in April 2025 to hash-verified authority receipts in August 2026 is the real artifact here. The garden metaphor is accurate — and gardens are defined by whether the fences hold between weedings. This roadmap is ordered so that the fences (Phase 1) land before the next weeding (Phase 2), because the git history shows what happens to un-fenced gardens: they regrow.

*Filed at the maintainer's request. The reviewer has no affiliation with the project beyond this commissioned review.*

## Comments (5)

### AUo959 — 2026-08-11T04:23:14Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1504#issuecomment-5248958992>

## Addendum — ecosystem exploration (CanonRec, ORIONCORE, deeper cloudbank)

Post-filing exploration of the two satellite repos and deeper cloudbank structure. Three amendments to the review above, plus findings.

### Amendments

1. **Finding 7 (agent authorship) — reframe.** CanonRec and ORIONCORE already attribute agent authorship at the git-author level (`claude-code` appears as a distinct commit author on canon curation commits). The recommendation changes from "invent AI_AUTHORS.md" to **"propagate the satellites' author-attribution pattern to cloudbank"** (and keep AI_AUTHORS.md as the human-readable index of it).
2. **Phase 1 blocked-state surfacing — downgrade from "build" to "audit and extend."** `.github/workflows/stale-and-blocked-report.yml` (6.1KB) already exists. Verify its coverage against the blocked-PR population (#1343, #1381) and extend rather than create.
3. **New ecosystem finding — duplicated governance questions.** CloudBank #1380 (trust, consent, revocation, retention, execution-default-off) and ORIONCORE #46 (canonical trust, consent, retention, revocation, execution-risk policy) are the same question open in two repos. Link them explicitly or consolidate under ORIONCORE #47 (the federation epic connecting QGIA, CanonRec, GUMAS, AuroraOS, and CloudBank).

### Findings from the satellites

**CanonRec — content discipline extraordinary, packaging 2025-era:**
- Canon curation commits show exceptional epistemic rigor: reference-integrity sweeps (243 records, 0 dangling references, 0 alias collisions), explicit NOT-promoted lists with reasoning ("a shared name fragment is not evidence of reference"), name-collision flags with all readings recorded, and disambiguation blocks on every collision.
- The Velar lineage-prefix system (Vel- noble, Varn- military, Rynn- reformist) *predicts* independently written canon — a falsifiable internal-consistency check on fictional material. Noted as a genuinely novel pattern.
- Packaging: eight versioned ZIPs at root (`CanonRec_v1.3.zip` → `v1.3.6`, including two `(1)` duplicates), `Archive.zip` (349KB), `text.txt` (7KB) at root, and `requirements-dev.txt` is 15 bytes. **Amendment to the roadmap: CanonRec's root needs the same ratchet as cloudbank's.**
- Tracker health is excellent: 2 open issues, both substantive (#1 formatting churn, #5 canon-ops contracts).

**ORIONCORE — the control plane works:**
- Born in the disciplined era: AGENTS.md (27KB), `SPEC__WARRANT_LENS__v1.md`, ruff/gitleaks/pre-commit from creation.
- `catalog/` is the federation nervous system: `repo_registry.yaml`, `repo_authority_policy.yaml`, `workspace_manifest.yaml`, `session_state.json` (81KB), `archive_inventory.jsonl` (270KB).
- Fossil evidence of a coordinated March 2026 workspace operation: `blank_file_triage__2026-03-10.json`, `quarantine_review_bucket__2026-03-10.json`, four rollback-wave manifests, `relocation_plan.json` — consistent with cloudbank's 178MB → 29MB shrinkage between Oct 2025 and now.
- Every CanonRec canon commit is shadowed by a `chore(catalog): sync CanonRec pin` commit here. The pin/queue mechanism is functioning as designed.
- The 2026-08-10 executive decision brief honestly tracks carried debt: AWS IAM key at 72 days (owner-only), `qgia-knowledge-library-main` at 54 days with an uncommitted feature. Worth surfacing in the roadmap's Phase 3 hygiene pass.

### Deeper cloudbank

- **Workflow tombstones confirmed structurally.** Seven stub-sized files (278–624 bytes) at `.github/workflows/` exactly match the set disabled via `if: false` on 2026-02-09 (`codeql-unified`, `codacy`, `codacy-analysis`, `collab-sync`, `auto-labeler`, `deploy-pages`, `symbolic-bundle`, `aurora_agent_runner`). Active workflows run 3–18KB. The Phase 1 tombstone sweep is validated without reading file bodies.
- **The sprawl is fractal** — the duplication pattern repeats at every level: `src/bridge/` + `src/bridges/`, `src/collab/` + `src/collaboration/`, `src/interface/` + `src/interfaces/`, `src/visual/` + `src/visualization/`; `modules/hr/` + `modules/hr_system/`, `modules/ethics/` + `modules/ethics_field/`; stub files shadowing packages (`src/quantum_decision_oracle.py`, 578B, vs. `modules/quantum_decision_oracle/`). The Phase 1 root-file allowlist should consider extending to `src/` and `modules/` once proven at root.
- Queue-as-code infrastructure is real: `queue-decision-escalation.yml`, `queue-issue-ingestion.yml`, `queue-validation.yml` workflows — the blocked-state amendment above builds on this.

### Unaffected

All scores, the phase ordering, and the core thesis (fences before weeding) stand as filed.

### AUo959 — 2026-08-11T04:44:28Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1504#issuecomment-5249079465>

## Addendum 2 — Simulation layer review (audited, with retractions)

Deep-dive on the simulation layer across cloudbank `simulation/`, ORIONCORE `GUMAS_SIM_2.5/`, and the CanonRec coupling. **Every observation below was audited against live evidence before posting; three initial claims were wrong and are retracted plainly.** Verified via directory listings, path-filtered commit history, and code search with text fragments (file bodies were not readable through the review connector, which downloads rather than inlines).

### Verified topology

| Layer | Home | Evidence |
|---|---|---|
| L1 — Orion station runtime | cloudbank `simulation/` | `l1_runtime.py` (54KB) + support (26KB) + types (26KB) + `l1_fleet.py` (25KB); declared "Live L1 runtime implementation" in CANON_INDEX.md |
| Fleet assets | cloudbank `simulation/fleet/` | 8 vessel manifests (ORS-01..05, ORP-1/2, ORF-01) + `ORD_SERIES.json` (47KB) |
| L2 — GUMAS engine | ORIONCORE `GUMAS_SIM_2.5/` | `SIM_ENGINE_OUTPUTS/` (v2.0 core: engine.py 1,905 LOC) + `FORGE__GUMAS_v3.0__2026-02-19/` (v3.0 modules) + synthesized `engine_advanced.py` — marked "active" in the June 2026 discovery index, wired into the ORIONCORE Makefile (`gumas-validate`, `gumas-api`), and declared the authoritative root in the forge API contract |
| Canon authority | CanonRec | Reference-integrity sweeps; promotion/refusal discipline (see Addendum 1) |

### What the audit RETRACTED from the draft review

1. **"Version-suffix file pairs are sprawl" — retracted.** `triplex_handshake_simulator.py` carries an in-file header: "STATUS (corrected 2026-08-03, #1132): maintained copy; prefer this one." `orion_station_simulation_v2.py` is designated in CANON_INDEX.md as the canonical historical Phase-1 benchmark, distinct from the live `l1_runtime.py`. These are curated pairs with declared canonical roles, not version-control-by-filename.
2. **"Character canon authority is ambiguous" — retracted.** CANON_INDEX.md declares `simulation/L1_CANON_CHARACTER_ROSTER.md` as the canon character roster; SIMULATION_INIT_PROTOCOL.md calls it the authoritative staff projection. Authority is declared — see the *real* finding below.
3. **"GUMAS forge drop is stale; modules/gumas is hollow" — retracted/overstated.** The forge directory is the live, wired-in engine (Makefile targets, `tools/gumas_api.py`, skill contract). `modules/gumas` in cloudbank contains `naming.py` (22.9KB) plus an `api/` subdirectory — narrow, not hollow. The cross-repo split (bridge/naming in cloudbank, engine in ORIONCORE) is intentional and documented.

### Findings that SURVIVED the audit

1. **Roster validation gap (self-identified by the project).** The 166KB `L1_CANON_CHARACTER_ROSTER.md` is canonical by declaration, but the project's own work queue (`ops/work_queue/QUEUE.md`, #1135) flags that it "has no validation against QGIA or Orion registries." With CanonRec now minting character identity provenance (#1457 → merged PR #1502, `config/l1_character_identity_registry.json`), the open question is whether CanonRec becomes the roster's upstream source. Recommend: a validation pass closing #1135, explicitly deciding the CanonRec↔roster direction of authority.
2. **Museum artifacts beside the runtime (archive candidates, not defects).** `simulation/` holds six CODEX_PHASE completion reports with technical registers (~120KB combined) and four Tobias Qin integration docs (~67KB). Given the project's demonstrated in-tree provenance culture (CANON_INDEX), these are plausibly deliberate — but a `reports/` or annex home would keep the runtime's directory readable without losing history.
3. **Nested-copy exposure (new, surfaced by the audit).** The June 2026 simulation discovery index lists `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/simulation/` — a nested copy of cloudbank's simulation layer inside ORIONCORE, marked "active (in use)" as the watch harness. If deliberate vendoring, it needs a freshness contract (which the CanonRec pin-sync pattern already models); if accidental, it's the federation's largest silent duplication.
4. **`l1_runtime.py` at 54KB** — approaching god-object territory (judgment call, flagged as such). The open population-model issues (#1452, #1453, #1455) all land in this file's neighborhood; consider splitting before they merge.

### What the audit CONFIRMED as strengths

- The canon→runtime pipeline ran end-to-end last night: issues #1456/#1457 → `codex/` branches → gated merges #1502/#1503, with ORIONCORE pin-syncs shadowing each canon commit.
- Fail-closed runtime posture: #1500 migrates pre-digest 1.2 runs safely rather than trusting them; restored runs need hash-verified receipts; reactivated locus claims rejected (#1503).
- `docs/architecture/` genuinely documents the layer model: LAYER_ARCHITECTURE.md, AURORA_L1_RUNTIME_CONTRACT.md, RUNTIME_TOPOLOGY_AND_L3_AUTHORITY.md, and a RUNTIME_PATH_DRIFT_LEDGER.md that tracks the project's own drift.

### Revised assessment

Simulation layer: **6.7/10 → 7.6/10.** More governed than first credited — canonical roles are declared, the GUMAS split is intentional, the pairs are curated. The honest remaining critique: close the roster-validation gap (#1135), settle the nested-copy freshness question, and archive the museum.

**Meta-note, in the spirit of this project's provenance culture:** the two retractions above came from the same failure mode — pattern-matching structure to defect classes without reading the index that governs the structure. CANON_INDEX.md exists precisely to prevent that. The reviewer should have read it first.

### AUo959 — 2026-08-12T04:41:35Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1504#issuecomment-5262362552>

## Addendum 3 — Nested-copy investigation: RESOLVED (finding withdrawn, two minor items remain)

Follow-up investigation of Addendum 2's finding #3 ("nested-copy exposure"). **The finding is withdrawn** — the arrangement is deliberate, documented, and reviewed. Two small residual items remain.

### What the path actually is

`GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` is a **local nested git repository**, not committed content — it does not exist in ORIONCORE's git tree (verified: the path 404s against the API). But it is extensively *declared* in committed documentation:

- **ORIONCORE README** lists it first among "active nested Git repositories" (with `GUMAS_SIM_2.5/CanonRec`, `DuelSim_v2.0`, `qgia-knowledge-library-main`) — branch `main`, remote configured.
- **`docs/workspace-map.md`** maps it as a workspace member and records that the legacy *root-level* `Aurora_Sim_Architecture` tree was relocated to `intake/` during the wave-4 rollback cleanup, while the authoritative nested repo stayed under `GUMAS_SIM_2.5/`.
- **`docs/repo-boundary-notice.md`** explicitly disambiguates the legacy archive root from the active nested repo.
- **`skills/zipwiz-governor/references/canonical_roots.md`** lists it as a default canonical root for packaging operations.
- **`docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md`** runs cloudbank's own test suite from inside the nested copy's venv — a working checkout, not a snapshot.
- Decisive: **`reports/recovered_canon/AURORA_SIM_ARCHITECTURE_RUNTIME_EXCEPTION_REVIEW__2026-04-12.md`** — "Keep the root-level Aurora_Sim_Architecture surface as a deliberate deferred runtime exception." Reviewed in April, kept deliberately.

### Why the finding inverts

Addendum 2 flagged this as possibly "the federation's largest silent duplication." It is neither silent nor ungoverned: a declared nested-repo workspace member with a boundary notice, registry presence, canonical-root status, and a reviewed deferral. Consistent with the rest of the ORIONCORE pattern (`repos/` and `intake/` empty-but-registered; local checkouts coordinated via `catalog/repo_registry.yaml`). The June 2026 discovery index was correct to call it "active (in use)"; my error was treating a committed-docs reference as evidence of a committed copy.

### Residual items (minor)

1. **The deferral has no visible review-by date.** The 2026-04-12 exception review defers the runtime exception without scheduling a revisit. Four months on, nothing in the committed record forces the question. One-line fix: add a revisit date to the exception record so the deferral cannot silently become permanent.
2. **The June 2026 discovery index has drifted in detail.** It lists `SIM_ENGINE_OUTPUTS/` containing `topology.py`, `combat.py`, `crisis_escalation.py`, and `engine.py` at 1,905 LOC. At HEAD those three files are absent and `engine.py` is a 950-byte shim — the real engine is `engine_base.py` (63.8KB) + `engine_advanced.py` (45.5KB), consistent with the March 2026 refactor commits. Same defect class as the validator-vocabulary drift fixed on 2026-08-10: a reference document drifting from the thing it indexes. A freshness stamp or regeneration date on discovery indexes would catch the class.

### Confirmed along the way

The 2026-07-21 commit "Marshal Charter derivation receipts (seed 42, deterministic)" corresponds to a real committed artifact: `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/MARSHAL_CHARTER_RUN__seed42__2026-07-20.json`. The receipts culture checks out at the file level.

### Net effect

Addendum 2, finding #3: **withdrawn**. Simulation-layer assessment unchanged at 7.6/10 — the workspace federation pattern is, if anything, more coherent than the committed tree alone suggested. The standing simulation-layer items are now exactly two: close the roster-validation gap (#1135, deciding the CanonRec↔roster direction of authority) and archive-or-annex the museum artifacts in `simulation/`.

This closes the review's open loop. All three addenda, all corrections, and all withdrawals are now on the record in this issue.

### AUo959 — 2026-08-15T06:37:20Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1504#issuecomment-5300973022>

## Backlog execution update — 2026-08-15

Completed or materially advanced:

- Phase 0: #1343 merged as `c8ffca60`; #1381 merged as `7902a044` after full gate repair.
- Phase 1 root declaration fence: #1509 merged the machine-readable root registry, fail-closed checker, and focused tests. The remaining pre-commit and required-CI wiring is still open.
- Phase 3 tracker hygiene: created `epic` and `backlog` labels; marked #1369 and #1376 as the two parent epics and #1368/#1370-#1375/#1377-#1380 as their backlog children.
- Stale trackers #1342 and #1362 were re-audited against current `main` and closed with implementation/test evidence.
- Productization fence: #1511 and #1512 merged; #1510 closed with its schema, CI validation, fail-closed canon/license rules, and checklist-to-manifest path complete.

Current blockers / remaining work:

- #1477 is still owner-secret gated: the repository has no usable `SONAR_TOKEN`, so the reporter cannot query rule/file/line detail.
- Root declaration enforcement is not complete until `scripts/check_root_declaration.py` is wired into both pre-commit and required CI.
- The broader requirements-count fence, workflow tombstone sweep, blocked-state surfacing, consolidation pass, deployment-primary decision, AI authorship documentation, and distilled context pack remain open.

This update records implementation progress only; it does not resolve owner decisions or authorize deployment/INIT/canon promotion.

### github-actions[bot] — 2026-09-14T09:17:30Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1504#issuecomment-5661733338>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.
